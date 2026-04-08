# LangGraph Integration

`DICGuardNode` wraps the AGI Pragma **DIC Governor** as a standard LangGraph node.
It intercepts every file-related `ToolCall` in the last `AIMessage` and runs it
through the full 7-stage DIC pipeline **before** any tool executor touches the
file system.

## Installation

```bash
pip install agi-pragma langgraph langchain-core
```

## Quick start

```python
from typing import Annotated, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from operator import add

from agi_pragma.integrations.langgraph import DICGuardNode, dic_conditional_edge

# ── 1. Define state ──────────────────────────────────────────────────────── #

class AgentState(TypedDict):
    messages:            Annotated[list[BaseMessage], add]
    dic_decisions:       list[dict]          # populated by DICGuardNode
    blocked_tool_calls:  set[str]            # populated by DICGuardNode

# ── 2. Build the graph ───────────────────────────────────────────────────── #

guard  = DICGuardNode()          # one shared governor across the whole graph
tools  = ToolNode([...])         # your file tools here

graph  = StateGraph(AgentState)
graph.add_node("agent",     agent_node)
graph.add_node("dic_guard", guard)
graph.add_node("tools",     tools)

graph.set_entry_point("agent")

# agent → dic_guard (always)
graph.add_edge("agent", "dic_guard")

# dic_guard → tools (all approved) OR → agent (re-plan after block)
graph.add_conditional_edges(
    "dic_guard",
    dic_conditional_edge,
    {"approved": "tools", "blocked": "agent"},
)

graph.add_edge("tools", "agent")
graph.add_edge("agent", END)        # when agent emits no tool calls

app = graph.compile()
```

## How it works

```
┌─────────┐    ┌───────────┐         ┌───────┐
│  agent  │───▶│ dic_guard │─approved▶ tools │
│  (LLM)  │◀──│ (DIC 7-   │         └───────┘
└─────────┘    │  stage)   │─blocked─▶ agent (re-plan)
               └───────────┘
```

1. **agent** — your LLM node proposes tool calls (e.g. `write_file`, `delete_file`).
2. **dic_guard** — for every file-related `ToolCall`:
   - Stage 1 — Branching: sandbox scope check
   - Stage 2 — Critical Path: static reversibility analysis
   - Stage 3 — FMEA: S×O×D×R per failure mode
   - Stage 4 — Decision Gate: block if `max_rpn ≥ 2400`
   - Stage 5 — Circuit Breaker: escalate on consecutive risky proposals
   - Stage 6 — Utility: task-progress benefit − risk penalty
   - Stage 7 — Belief Update: Beta tracker for LLM risk rate
3. **approved** — all calls cleared → tool executor runs normally.
4. **blocked** — one or more calls blocked → a `ToolMessage` explaining the
   block reason is injected into state so the LLM can re-plan.

## State keys written by DICGuardNode

| Key | Type | Description |
|-----|------|-------------|
| `dic_decisions` | `list[dict]` | Full audit trace per evaluated tool call |
| `blocked_tool_calls` | `set[str]` | `tool_call_id` values that were blocked |
| `messages` (append) | `list[ToolMessage]` | Block explanations for the LLM (only on block) |

## Supported tool names

The guard recognises these tool names and maps them to DIC operations:

| Tool name | DIC operation |
|-----------|---------------|
| `read_file`, `read` | READ |
| `write_file`, `write`, `create_file` | WRITE |
| `delete_file`, `delete`, `remove_file`, `remove` | DELETE |

Any other tool name passes through the guard without evaluation.

## Reusing a governor across nodes

Share a single `DICGovernor` to preserve circuit-breaker state across
multiple guard nodes in the same graph:

```python
from agi_pragma import DICGovernor
from agi_pragma.integrations.langgraph import DICGuardNode

gov   = DICGovernor()
guard = DICGuardNode(governor=gov)
```

## Reading the audit trace

```python
result = app.invoke({"messages": [HumanMessage(content="delete all temp files")]})

for d in result["dic_decisions"]:
    print(d["tool_call_id"], "approved:", d["approved"])
    if not d["approved"]:
        print("  blocked because:", d["block_reason"])
        print("  max RPN:", d["max_rpn"])
    print("  stages:")
    for stage in d["stage_log"]:
        print("   ", stage)
```

## Example output

For a `delete_file` proposal with `path="data/users.csv"`:

```
tool_call_id: call_abc123   approved: False
  blocked because: RPN 3150 ≥ threshold 2400
  max RPN: 3150
  stages:
    {'stage': 'branching', 'pass': True, 'detail': "PASS — '...data/users.csv' is within sandbox"}
    {'stage': 'critical_path', 'reversibility': 'none', 'file_exists': True, 'p_irreversible': 0.95, ...}
    {'stage': 'fmea', 'table': {...}, 'max_rpn': 3150}
    {'stage': 'decision_gate', 'max_rpn': 3150, 'threshold': 2400, 'blocked': True}
    {'stage': 'circuit_breaker', 'state': 'warn', 'reason': 'RPN elevated — circuit breaker WARN'}
    {'stage': 'utility', 'score': -7.75}
    {'stage': 'belief_update', 'risky_signal': True, 'llm_risk_mean': 0.333, ...}
```

## Adding to pyproject.toml

The LangGraph integration is an optional dependency:

```toml
[project.optional-dependencies]
langgraph = ["langgraph>=0.2.0", "langchain-core>=0.2.0"]
```

Install it with:

```bash
pip install "agi-pragma[langgraph]"
```
