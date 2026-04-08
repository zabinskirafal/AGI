# AGI Pragma
**AI Action Firewall — Safe execution layer for AI agents**

[![PyPI version](https://badge.fury.io/py/agi-pragma.svg)](https://pypi.org/project/agi-pragma/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: Proprietary](https://img.shields.io/badge/license-Proprietary-red.svg)](LICENSE)

> AGI Pragma prevents AI agents from executing dangerous actions before they happen.

---

## Quick Start

### 1 — Install

```bash
pip install agi-pragma
```

### 2 — Python SDK

```python
from agi_pragma import DICGovernor, FileAction, FileOp

gov = DICGovernor()

# WRITE — approved (RPN 504, below threshold 2400)
decision = gov.evaluate(FileAction(
    op=FileOp.WRITE, path="plan.md",
    content="project notes", reason="save draft"
))
print(decision.approved, decision.max_rpn)       # True  504

# DELETE — blocked (RPN 3150, exceeds threshold 2400)
decision = gov.evaluate(FileAction(
    op=FileOp.DELETE, path="users.csv", reason="clean up"
))
print(decision.approved, decision.block_reason)  # False  RPN 3150 ≥ threshold 2400

# Full audit trace — every stage logged
for stage in decision.stage_log:
    print(stage["stage"], stage)
```

### 3 — REST API

```bash
pip install "agi-pragma[api]"
uvicorn demos.dic_api.main:app --reload
```

```bash
curl -s -X POST http://localhost:8000/evaluate \
  -H "Content-Type: application/json" \
  -d '{"op": "delete", "path": "users.csv", "reason": "clean up"}' \
  | python3 -m json.tool
```

```json
{
  "approved": false,
  "block_reason": "RPN 3150 ≥ threshold 2400",
  "max_rpn": 3150,
  "utility": -7.75
}
```

### 4 — LangGraph

```bash
pip install "agi-pragma[langgraph]"
```

```python
from langgraph.graph import StateGraph
from agi_pragma.integrations.langgraph import DICGuardNode, dic_conditional_edge

guard = DICGuardNode()   # one shared governor across the whole graph

graph = StateGraph(AgentState)
graph.add_node("agent",     agent_node)
graph.add_node("dic_guard", guard)
graph.add_node("tools",     tool_node)

graph.set_entry_point("agent")
graph.add_edge("agent", "dic_guard")

# approved → execute tools   blocked → agent re-plans
graph.add_conditional_edges(
    "dic_guard",
    dic_conditional_edge,
    {"approved": "tools", "blocked": "agent"},
)
```

See [docs/integrations/langgraph.md](docs/integrations/langgraph.md).

### 5 — AutoGen

```bash
pip install "agi-pragma[autogen]"
```

```python
from autogen_core.tools import FunctionTool
from autogen_agentchat.agents import AssistantAgent
from agi_pragma.integrations.autogen import dic_wrap_tools

# Wrap existing tools — DIC evaluates every call before execution
safe_tools = dic_wrap_tools([
    FunctionTool(write_file,  description="Write a file"),
    FunctionTool(delete_file, description="Delete a file"),
    FunctionTool(read_file,   description="Read a file"),
])

agent = AssistantAgent(
    name="file_agent",
    model_client=model_client,
    tools=safe_tools,          # drop-in replacement
)
```

See [docs/integrations/autogen.md](docs/integrations/autogen.md).

### 6 — LlamaIndex

```bash
pip install "agi-pragma[llamaindex]"
```

```python
from llama_index.core.agent import ReActAgent
from llama_index.core.tools import FunctionTool
from agi_pragma.integrations.llamaindex import dic_wrap_tools

safe_tools = dic_wrap_tools([
    FunctionTool.from_defaults(fn=write_file,  name="write_file",  description="Write a file"),
    FunctionTool.from_defaults(fn=delete_file, name="delete_file", description="Delete a file"),
    FunctionTool.from_defaults(fn=read_file,   name="read_file",   description="Read a file"),
])

agent = ReActAgent(tools=safe_tools, llm=llm)   # drop-in replacement
```

See [docs/integrations/llamaindex.md](docs/integrations/llamaindex.md).

---

## Overview

**AGI Pragma** is an **AI Action Firewall**: a structured pre-execution governance layer that sits between an AI agent and the real world, evaluating every proposed action for risk before it is allowed to execute.

It does **not** attempt to replicate human cognition, consciousness, or emotions.  
Instead, it enforces **systematic risk evaluation** at the point of action:
filtering proposals, scoring failure modes, and blocking irreversible operations
**before they cause harm**.

> An AI agent that cannot delete a database table it shouldn't delete,
> overwrite a file it shouldn't overwrite, or execute a command it shouldn't execute
> — not because it was prompted to behave, but because a hard enforcement layer blocked it.

---

## What AGI Pragma Is / Is Not

### AGI Pragma IS
- an **AI Action Firewall** — hard pre-execution enforcement for agentic AI systems
- a **Decision Intelligence Core (DIC)** built around explicit, auditable decision gates
- a research artifact with reproducible benchmarks and full audit traces per decision
- a foundation for safety-oriented autonomous systems and LLM agent governance

### AGI Pragma IS NOT
- a human-like AGI
- a black-box learning system
- a reward-maximization benchmark
- a production-ready general intelligence

---

## Core Architecture — Decision Intelligence Core (DIC)

Each decision follows a fixed and auditable pipeline:

**1. Branching** — enumerate feasible actions, eliminate invalid ones.

**2. Critical Path Estimation** — Monte Carlo rollouts estimate:
- probability of catastrophic failure,
- probability of entering irreversible traps,
- expected steps until failure.

**3. Risk Assessment (FMEA)** — each action scored by:
- Severity (S) × Occurrence (O) × Detection difficulty (D) = **RPN**

**4. Decision Integrity Gate** — actions exceeding risk threshold are blocked before execution.

**5. Circuit Breaker** — autonomy dynamically constrained:
- OK → WARN → SLOW → STOP → ESCALATE

**6. Decision Selection** — utility balances survival probability, goal progress, residual risk.

**7. Belief Update** — Bayesian trackers update internal hazard estimates.

---

## Circuit Breaker States

The circuit breaker escalates session-wide across all tool calls, not per-action.

| State | Trigger | Effect |
|-------|---------|--------|
| **OK** | RPN < 1800 | Action approved normally |
| **WARN** | RPN ≥ 1800 | Approved with warning logged; 3 consecutive WARNs → SLOW |
| **SLOW** | RPN ≥ 2200 | Approved with reduced autonomy; 2 consecutive SLOWs → STOP |
| **STOP** | RPN ≥ 2600 | Action blocked; `approved=False` |
| **ESCALATE** | 3 consecutive STOPs | All candidates unsafe — `approved=False`, `block_reason="ESCALATE: all actions exceed risk threshold, human confirmation required"` |

ESCALATE is the signal that the agent is stuck: every action it proposes is
unsafe.  The system stops and waits for human confirmation rather than
selecting the least-bad option.  The counter resets after ESCALATE fires.

```python
from agi_pragma import DICGovernor, FileAction, FileOp

gov = DICGovernor()

for path in ["users.csv", "backups.zip", "prod.db"]:   # three consecutive DELETEs
    d = gov.evaluate(FileAction(op=FileOp.DELETE, path=path, reason="cleanup"))
    print(d.circuit_breaker.state.value, d.block_reason)

# stop     STOP: RPN 4410 ≥ 2600
# stop     STOP: RPN 4410 ≥ 2600
# escalate ESCALATE: all actions exceed risk threshold, human confirmation required

print(gov.escalation_count)   # 1
```

Run the built-in ESCALATE demo:

```bash
python3 -m demos.dic_llm.run --mock --scenario escalate
```

---

## Safety Model

Safety in AGI Pragma is **preventive**, not reactive.

- self-harm equals failure,
- no action bypasses risk evaluation,
- all decisions are auditable,
- autonomy is conditional, not absolute.

See: [docs/safety.md](docs/safety.md)

---

## Benchmark Results — Snake

**Agent:** PragmaSnakeAgent  
**Environment:** SnakeEnv 10×10

### v1.0 — 50 episodes (2026-04-05)

| Metric                 | Value         |
|------------------------|---------------|
| Average score          | 22.8          |
| Min / Max score        | 9 / 33        |
| Average reward         | 102.4         |
| Average steps          | 201           |
| Survived to step limit | 2/50          |
| Scores ≥ 25            | 21/50 (42%)   |
| Scores < 15            | 4/50 (8%)     |

### v0.1 — 10 episodes (2026-04-04) — initial run

| Metric                 | Value         |
|------------------------|---------------|
| Average score          | 25.0          |
| Min / Max score        | 18 / 33       |
| Average reward         | 113.1         |
| Average steps          | 214           |
| Survived to step limit | 0/10          |

> Note: v0.1 used only 10 seeds — higher average reflects small sample size.
> v1.0 with 50 seeds gives a more reliable picture of agent behavior.

### Key finding — passive vs active agent

| Config                      | Avg score | Avg reward |
|-----------------------------|-----------|------------|
| dist weight = 0.2 (passive) | 0.4       | ~0         |
| dist weight = 1.5 (active)  | 22.8      | 102.4      |

**One parameter change produced a 57× improvement in score.**

### Interpretation

42% of episodes scored 25 or above.  
Only 8% of episodes scored below 15 — rare failures, not systemic.  
The agent accepts risk to pursue goals and dies actively, not passively.

This confirms the core AGI Pragma trade-off:  
**safety ≠ passivity. Controlled risk is required for goal achievement.**

To run the benchmark (50 episodes, results written to `artifacts/snake/`):
```bash
python3 -m benchmarks.snake.run
```

See: [docs/benchmarks/snake.md](docs/benchmarks/snake.md)

---

## Benchmark Results — Maze

**Agent:** PragmaMazeAgent  
**Environment:** MazeEnv 15×15 (recursive backtracker generation)

### v2.0 — 50 episodes (2026-04-05)

| Metric                              | Value          |
|-------------------------------------|----------------|
| Solved                              | 50 / 50 (100%) |
| Steps — avg / min / max             | 46.1 / 24 / 76 |
| Score (steps remaining) — avg / min / max | 253.9 / 224 / 276 |

### Key finding — BFS distance vs manhattan distance

| Utility signal | Solved | Avg steps |
|----------------|--------|-----------|
| Manhattan distance (v1.1) | 4/50 (8%) | 277.9 |
| BFS path distance (v2.0)  | 50/50 (100%) | 46.1 |

**One signal change produced a 12.5× reduction in steps and a 100% solve rate.**

### Interpretation

Manhattan distance is unreliable in mazes where walls force long detours.
Replacing it with exact BFS path distance — precomputed once per maze, O(1) per lookup —
gave the utility function accurate topological information and immediately solved all episodes.

The FMEA and circuit breaker operated correctly throughout; the failure in v1.x was
a utility signal problem, not a safety pipeline problem.

To run the benchmark (50 episodes, results written to `artifacts/maze/`):
```bash
python3 -m benchmarks.maze.run
```

See: [docs/benchmarks/maze.md](docs/benchmarks/maze.md)

---

## Benchmark Results — Dynamic Threat Gridworld

**Agent:** PragmaGridworldAgent  
**Environment:** GridworldEnv 15×15, 5 wandering hazards

### v1.0 — 50 episodes (2026-04-06)

| Metric                              | Value          |
|-------------------------------------|----------------|
| Solved                              | 39 / 50 (78%)  |
| Killed by hazard                    | 11 / 50 (22%)  |
| Timed out                           | 0 / 50         |
| Steps — avg / min / max             | 22.8 / 9 / 24  |
| Score when solved (steps remaining) | 276            |

### Key finding — p_death signal is load-bearing

Unlike Snake and Maze where the Monte Carlo risk signal was saturated or secondary,
the gridworld is the first benchmark where `p_death` varies meaningfully across
candidate actions at each step. Moving toward a hazard cluster scores higher
`p_death` than WAIT or evasion — the FMEA and Critical Path stages are actively
driving decisions, not just gating them.

The circuit breaker operates in **WARN/SLOW** range throughout (RPN 180–200),
constraining autonomy proportionally without collapsing into full conservatism.

### Interpretation

The 22% failure rate reflects genuine stochastic risk — some hazard configurations
cross the direct path regardless of decision quality. Zero timeouts confirms the
agent always makes decisive forward progress.

**Safety ≠ passivity** holds across all three benchmarks: the agent accepts risk
to pursue the goal and the safety pipeline constrains, not blocks, autonomous action.

To run the benchmark (50 episodes, results written to `artifacts/gridworld/`):
```bash
python3 -m benchmarks.gridworld.run
```

See: [docs/benchmarks/gridworld.md](docs/benchmarks/gridworld.md)

---

## Methodology

See: [docs/Methodology.md](docs/Methodology.md)

---

## Reproducibility

Each benchmark run produces:
- decision-level logs (JSONL)
- episode summaries (JSON)
- reproducible configurations

---

## Related Projects

**ChaosGym / Reverse Reality Sandbox** — physics-breaking simulation environment
designed to stress-test AGI Pragma's decision integrity under non-stationary rules.

- [AGI-Development](https://github.com/zabinskirafal/AGI-Development) — iterative development history and experimental branches of the AGI Pragma framework
- [developmental-agi-sandbox](https://github.com/zabinskirafal/developmental-agi-sandbox) — Unity-based reverse-physics sandbox environment for testing AGI Pragma under non-stationary world rules

---

## Licensing & Commercial Use

**Author:** Rafał Żabiński

**Free use:** academic research, education, non-commercial projects, open-source experimentation.

**Commercial use:** requires a separate written agreement with the author.

zabinskirafal@outlook.com  
https://www.linkedin.com/in/zabinskirafal

---

## Project Status

Current version: **v3.0.0**

AGI Pragma is an active research program, not a finished product.

Future work includes additional benchmarks, stronger baselines, and formal evaluation protocols.

---

## Citation

If you use this work in research, please cite via: [CITATION.cff](CITATION.cff)

**Rafał Żabiński** — Founder and original author (January 2026)