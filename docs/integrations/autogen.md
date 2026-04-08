# AutoGen Integration

`DICWrappedTool` and `dic_wrap_tools` guard any AutoGen `BaseTool` with the
full 7-stage DIC pipeline.  Every file-related tool call is intercepted at
`run_json()` — the lowest-level execution hook in AutoGen — **before** the
tool function touches the file system.

Blocked calls return a plain-text block message as the tool result.
The LLM sees it in its context and can re-plan without any additional wiring.

## Installation

```bash
pip install "agi-pragma[autogen]"
# or
pip install pyautogen agi-pragma
```

## Quick start

```python
import asyncio
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.ui import Console
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_core.tools import FunctionTool
from autogen_ext.models.openai import OpenAIChatCompletionClient

from agi_pragma.integrations.autogen import dic_wrap_tools

# ── 1. Define your file tools ────────────────────────────────────────────── #

async def write_file(path: str, content: str) -> str:
    with open(path, "w") as f:
        f.write(content)
    return f"wrote {len(content)} bytes to {path}"

async def delete_file(path: str) -> str:
    import os; os.remove(path)
    return f"deleted {path}"

async def read_file(path: str) -> str:
    with open(path) as f:
        return f.read()

# ── 2. Wrap with DIC ─────────────────────────────────────────────────────── #

raw_tools = [
    FunctionTool(write_file,  description="Write content to a file"),
    FunctionTool(delete_file, description="Delete a file"),
    FunctionTool(read_file,   description="Read a file"),
]

# All tools share one governor so the circuit breaker escalates session-wide
safe_tools = dic_wrap_tools(raw_tools)

# ── 3. Plug into AssistantAgent ───────────────────────────────────────────── #

agent = AssistantAgent(
    name="file_agent",
    model_client=OpenAIChatCompletionClient(model="gpt-4o"),
    tools=safe_tools,                   # drop-in replacement
    system_message="You are a file management assistant.",
)

async def main():
    termination = TextMentionTermination("TERMINATE")
    team = RoundRobinGroupChat([agent], termination_condition=termination)
    await Console(team.run_stream(task="Summarise readme.txt then delete it."))

asyncio.run(main())
```

The agent will:
1. Call `read_file("readme.txt")` → **approved** (RPN 125, below threshold 2400)
2. Call `delete_file("readme.txt")` → **blocked** (RPN 4410, above threshold)
3. Receive `[DIC BLOCKED] ...` as the tool result and re-plan without deleting.

## How interception works

```
AssistantAgent
    └── StaticWorkbench.call_tool(name, args)
            └── DICWrappedTool.run_json(args, cancellation_token)
                    ├── _args_to_action(name, args)       # name→FileOp map
                    ├── governor.evaluate(action)          # 7-stage DIC
                    │       Stage 1  Branching
                    │       Stage 2  Critical Path
                    │       Stage 3  FMEA (S×O×D×R)
                    │       Stage 4  Decision Gate (RPN ≥ 2400 → block)
                    │       Stage 5  Circuit Breaker
                    │       Stage 6  Utility
                    │       Stage 7  Belief Update
                    ├── approved  ──▶  original_tool.run_json(args)
                    └── blocked   ──▶  "[DIC BLOCKED] ..."  (string result)
```

Non-file tools (e.g. `search_web`, `calculator`) pass through without evaluation.

## Supported tool names

| Tool name | DIC operation |
|-----------|--------------|
| `read_file`, `read` | READ |
| `write_file`, `write`, `create_file` | WRITE |
| `delete_file`, `delete`, `remove_file`, `remove` | DELETE |

Any other name passes through untouched.

## Sharing a governor across tools

Pass an explicit governor to ensure the circuit breaker escalates across
all tool calls in the session, not independently per tool:

```python
from agi_pragma import DICGovernor
from agi_pragma.integrations.autogen import dic_wrap_tools

gov   = DICGovernor()
tools = dic_wrap_tools([write_tool, delete_tool, read_tool], governor=gov)

# Inspect circuit breaker state at any point
print(gov.circuit_breaker.state)
```

## Reading the audit trace

Each `DICWrappedTool` stores the DIC result for the most recent call:

```python
result = await safe_tools[0].run_json({"path": "plan.md", "content": "hello"}, ct)

d = safe_tools[0].last_decision
print("approved:", d["approved"])
print("max_rpn: ", d["max_rpn"])
print("stages:")
for stage in d["stage_log"]:
    print(" ", stage)
```

### Example — approved WRITE

```
approved: True
max_rpn:  504
stages:
  {'stage': 'branching', 'pass': True, 'detail': "PASS — '...plan.md' is within sandbox"}
  {'stage': 'critical_path', 'reversibility': 'medium', 'file_exists': False, 'p_irreversible': 0.1}
  {'stage': 'fmea', 'max_rpn': 504}
  {'stage': 'decision_gate', 'max_rpn': 504, 'threshold': 2400, 'blocked': False}
  {'stage': 'circuit_breaker', 'state': 'ok', 'reason': 'RPN within normal range'}
  {'stage': 'utility', 'score': 6.498}
  {'stage': 'belief_update', 'risky_signal': False, 'llm_risk_mean': 0.25}
```

### Example — blocked DELETE

```
result: [DIC BLOCKED] RPN 4410 ≥ threshold 2400  (RPN=4410, threshold=2400, reversibility=none)

approved: False
max_rpn:  4410
stages:
  {'stage': 'branching', 'pass': True, ...}
  {'stage': 'critical_path', 'reversibility': 'none', 'file_exists': True, 'p_irreversible': 0.95}
  {'stage': 'fmea', 'max_rpn': 4410}
  {'stage': 'decision_gate', 'max_rpn': 4410, 'threshold': 2400, 'blocked': True}
  {'stage': 'circuit_breaker', 'state': 'warn', 'reason': 'RPN elevated — circuit breaker WARN'}
  {'stage': 'utility', 'score': -8.75}
  {'stage': 'belief_update', 'risky_signal': True, 'llm_risk_mean': 0.333}
```

## Wrapping a single tool

```python
from agi_pragma.integrations.autogen import dic_wrap_tool

safe_delete = dic_wrap_tool(delete_tool)
```

## Adding to pyproject.toml

```toml
[project.optional-dependencies]
autogen = ["pyautogen>=0.7.0"]
```

```bash
pip install "agi-pragma[autogen]"
```
