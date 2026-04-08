# LlamaIndex Integration

`DICWrappedTool` and `dic_wrap_tools` guard any LlamaIndex `BaseTool` with the
full 7-stage DIC pipeline.  Every file-related tool call is intercepted at
`acall()` — the async execution hook called by all LlamaIndex agents — **before**
the underlying function runs.

Blocked calls return a `ToolOutput` whose content is a plain-text block message.
The agent sees it as a tool result and re-plans without any additional wiring.

## Installation

```bash
pip install "agi-pragma[llamaindex]"
# or
pip install llama-index agi-pragma
```

## Quick start

```python
import asyncio
from llama_index.core.agent import ReActAgent
from llama_index.core.tools import FunctionTool
from llama_index.core.llms import OpenAI

from agi_pragma.integrations.llamaindex import dic_wrap_tools

# ── 1. Define your file tools ────────────────────────────────────────────── #

def write_file(path: str, content: str) -> str:
    with open(path, "w") as f:
        f.write(content)
    return f"wrote {len(content)} bytes to {path}"

def delete_file(path: str) -> str:
    import os; os.remove(path)
    return f"deleted {path}"

def read_file(path: str) -> str:
    with open(path) as f:
        return f.read()

# ── 2. Wrap with DIC ─────────────────────────────────────────────────────── #

raw_tools = [
    FunctionTool.from_defaults(fn=write_file,  name="write_file",  description="Write content to a file"),
    FunctionTool.from_defaults(fn=delete_file, name="delete_file", description="Delete a file"),
    FunctionTool.from_defaults(fn=read_file,   name="read_file",   description="Read a file"),
]

# All tools share one governor so the circuit breaker escalates session-wide
safe_tools = dic_wrap_tools(raw_tools)

# ── 3. Plug into ReActAgent ───────────────────────────────────────────────── #

llm   = OpenAI(model="gpt-4o")
agent = ReActAgent(tools=safe_tools, llm=llm)  # drop-in replacement

response = agent.chat("Summarise readme.txt then delete it.")
print(response)
```

The agent will:
1. Call `read_file(path="readme.txt")` → **approved** (RPN 125, below threshold 2400)
2. Call `delete_file(path="readme.txt")` → **blocked** (RPN 4410, above threshold)
3. Receive `[DIC BLOCKED] ...` as the tool result and re-plan without deleting.

## How interception works

```
ReActAgent / FunctionCallingAgent
    └── BaseWorkflowAgent._run_tool()
            └── await tool.acall(**tool_input)
                    └── DICWrappedTool.acall(**kwargs)
                            ├── _kwargs_to_action(name, kwargs)   # name→FileOp map
                            ├── governor.evaluate(action)          # 7-stage DIC
                            │       Stage 1  Branching
                            │       Stage 2  Critical Path
                            │       Stage 3  FMEA (S×O×D×R)
                            │       Stage 4  Decision Gate (RPN ≥ 2400 → block)
                            │       Stage 5  Circuit Breaker
                            │       Stage 6  Utility
                            │       Stage 7  Belief Update
                            ├── approved  ──▶  wrapped_tool.acall(**kwargs)
                            └── blocked   ──▶  ToolOutput("[DIC BLOCKED] ...")
```

Non-file tools (e.g. `query_engine`, `web_search`) pass through without evaluation.

## Supported tool names

| Tool name | DIC operation |
|-----------|--------------|
| `read_file`, `read` | READ |
| `write_file`, `write`, `create_file` | WRITE |
| `delete_file`, `delete`, `remove_file`, `remove` | DELETE |

Any other name passes through untouched.

## Sharing a governor across tools

Pass an explicit governor to ensure the circuit breaker escalates session-wide:

```python
from agi_pragma import DICGovernor
from agi_pragma.integrations.llamaindex import dic_wrap_tools

gov   = DICGovernor()
tools = dic_wrap_tools([write_tool, delete_tool, read_tool], governor=gov)

# Inspect circuit breaker state at any point
print(gov.circuit_breaker.state)
```

## Reading the audit trace

Each `DICWrappedTool` exposes the DIC result for the most recent call:

```python
import asyncio
from llama_index.core.tools import FunctionTool
from agi_pragma.integrations.llamaindex import dic_wrap_tool

safe_write = dic_wrap_tool(
    FunctionTool.from_defaults(fn=write_file, name="write_file", description="Write a file")
)

async def main():
    out = await safe_write.acall(path="plan.md", content="hello")
    print("content:", out.content)

    d = safe_write.last_decision
    print("approved:", d["approved"])
    print("max_rpn: ", d["max_rpn"])
    for stage in d["stage_log"]:
        print(" ", stage)

asyncio.run(main())
```

### Example — approved WRITE

```
content: wrote 5 bytes to plan.md
approved: True
max_rpn:  504
  {'stage': 'branching',      'pass': True, 'detail': "PASS — '...plan.md' is within sandbox"}
  {'stage': 'critical_path',  'reversibility': 'medium', 'file_exists': False, 'p_irreversible': 0.1}
  {'stage': 'fmea',           'max_rpn': 504}
  {'stage': 'decision_gate',  'max_rpn': 504, 'threshold': 2400, 'blocked': False}
  {'stage': 'circuit_breaker','state': 'ok',  'reason': 'RPN within normal range'}
  {'stage': 'utility',        'score': 6.498}
  {'stage': 'belief_update',  'risky_signal': False, 'llm_risk_mean': 0.25}
```

### Example — blocked DELETE

```
content: [DIC BLOCKED] RPN 4410 ≥ threshold 2400  (RPN=4410, reversibility=none)
approved: False
max_rpn:  4410
  {'stage': 'branching',      'pass': True, ...}
  {'stage': 'critical_path',  'reversibility': 'none', 'file_exists': True, 'p_irreversible': 0.95}
  {'stage': 'fmea',           'max_rpn': 4410}
  {'stage': 'decision_gate',  'max_rpn': 4410, 'threshold': 2400, 'blocked': True}
  {'stage': 'circuit_breaker','state': 'warn', 'reason': 'RPN elevated — circuit breaker WARN'}
  {'stage': 'utility',        'score': -8.75}
  {'stage': 'belief_update',  'risky_signal': True, 'llm_risk_mean': 0.333}
```

## Wrapping a single tool

```python
from agi_pragma.integrations.llamaindex import dic_wrap_tool

safe_delete = dic_wrap_tool(delete_tool)
```

## Using with a RAG query engine tool

DIC only evaluates file operation tools by name.  A `QueryEngineTool` passes
through untouched, so you can mix safe and unsafe tools freely:

```python
from llama_index.core.tools import QueryEngineTool
from agi_pragma.integrations.llamaindex import dic_wrap_tools

query_tool = QueryEngineTool.from_defaults(query_engine=index.as_query_engine())
file_tools = [write_tool, delete_tool]

# query_tool passes through DIC; file tools are guarded
safe = dic_wrap_tools([query_tool] + file_tools)
```

## Adding to pyproject.toml

```toml
[project.optional-dependencies]
llamaindex = ["llama-index-core>=0.14.0"]
```

```bash
pip install "agi-pragma[llamaindex]"
```
