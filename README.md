# AGI Pragma  
**Decision Intelligence Framework for Controlled Autonomy under Uncertainty**

> *Intelligence as iterative decision-making, not opaque optimization.*

---

## Overview

**AGI Pragma** is a research framework for **decision intelligence under dynamic and uncertain environments**.

It does **not** attempt to replicate human cognition, consciousness, or emotions.  
Instead, it formalizes **human-like adaptive decision mechanisms**:
filtering reality, assessing risk, and updating beliefs **before acting**.

The core idea is simple:

> Intelligent behavior emerges from systematically **constraining decisions**
> under uncertainty — not from unconstrained optimization.

---

## What AGI Pragma Is / Is Not

### AGI Pragma **IS**
- a methodology-first framework for risk-aware autonomy,
- a **Decision Intelligence Core (DIC)** built around explicit decision gates,
- a research artifact with reproducible benchmarks and auditable traces,
- a foundation for safety-oriented autonomous systems.

### AGI Pragma **IS NOT**
- a human-like AGI,
- a black-box learning system,
- a reward-maximization benchmark,
- a production-ready general intelligence.

---

## Core Architecture — Decision Intelligence Core (DIC)

Each decision follows a fixed and auditable pipeline:

### 1. Branching
Enumerate feasible actions and eliminate logically or physically invalid ones.

### 2. Critical Path Estimation
Monte Carlo rollouts estimate:
- probability of catastrophic failure,
- probability of entering irreversible traps,
- expected steps until failure.

### 3. Risk Assessment (FMEA)
Each action is evaluated using **Failure Mode and Effects Analysis**:
- Severity (S)
- Occurrence (O)
- Detection difficulty (D)

RPN = S × O × D

yaml
Skopiuj kod

### 4. Decision Integrity Gate
Actions exceeding the risk threshold are blocked **before execution**.

### 5. Circuit Breaker (Controlled Autonomy)
Autonomy is dynamically constrained:
- **OK → WARN → SLOW → STOP**

### 6. Decision Selection
Among allowed actions, utility balances:
- survival probability,
- goal progress,
- residual risk.

### 7. Belief Update
Bayesian trackers update internal hazard estimates
(e.g. trap frequency, near-death probability).

---

## Safety Model

Safety in AGI Pragma is **preventive**, not reactive.

- self-harm equals failure,
- no action bypasses risk evaluation,
- all decisions are auditable,
- autonomy is conditional, not absolute.

See:  
📄 [docs/safety.md](docs/safety.md)

---

## Benchmarks

### Snake — Safety & Controlled Autonomy

A minimal benchmark where **self-harm equals loss**.

The Snake benchmark demonstrates:
- pre-action risk filtering,
- critical path avoidance,
- FMEA-based gating,
- circuit breaker–driven autonomy control.

Run:
```bash
python -m benchmarks.snake.run
Docs:
📄 docs/benchmarks/snake.md

Metrics
AGI Pragma evaluates decision quality under uncertainty, not raw performance.

Metrics cover:

survival and catastrophic failure,

risk exposure (RPN, trap probability),

decision integrity (blocked actions, circuit breaker states),

adaptive belief updates.

See:
📄 docs/metrics.md

Methodology
The full research methodology is described here:
📄 docs/Methodology.md

Reproducibility
Benchmark runs produce:

decision-level logs (JSONL),

episode summaries (JSON),

reproducible configurations.

Artifacts enable:

auditing,

comparison across versions,

research replication.

Related Projects
ChaosGym / Reverse Reality Sandbox
A physics-breaking simulation environment designed to stress-test
AGI Pragma’s decision integrity under non-stationary and adversarial rules.

The sandbox intentionally violates classical assumptions:

gravity inversion,

entropy reversal,

causal instability,

dynamically changing physical laws.

This project serves as a downstream environment for evaluating
how AGI Pragma behaves when stable world models no longer apply.

Repository:

https://github.com/zabinskirafal/AGI-Development

https://github.com/zabinskirafal/developmental-agi-sandbox

Licensing & Commercial Use
Author: Rafał Żabiński

Free Use (100%)
academic research,

education,

non-commercial projects,

open-source experimentation.

Commercial Use
Any commercial use (including SaaS, paid services, enterprise systems,
closed training, or licensing) requires a separate commercial agreement
with the author.

Contact:

📧 zabinskirafal@outlook.com

🔗 https://www.linkedin.com/in/zabinskirafal

Project Status
Current version: v. 3.0.0

AGI Pragma is an active research program, not a finished product.
Future work focuses on:

additional benchmarks,

stronger baselines,

formal evaluation protocols.

Citation
If you use this work in research, please cite it via:
📄 CITATION.cff

Rafał Żabiński
Founder and original author
(January 2026)
