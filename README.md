# AGI Pragma
**Decision Intelligence Framework for Controlled Autonomy under Uncertainty**

> *Intelligence as iterative decision-making, not opaque optimization.*

---

## Overview

**AGI Pragma** is a research framework for **decision intelligence under dynamic and uncertain environments**.

It does **not** attempt to replicate human cognition, consciousness, or emotions.  
Instead, it formalizes **human-like adaptive decision mechanisms**:
filtering reality, assessing risk, and updating beliefs **before acting**.

> Intelligent behavior emerges from systematically **constraining decisions**
> under uncertainty — not from unconstrained optimization.

---

## What AGI Pragma Is / Is Not

### AGI Pragma IS
- a methodology-first framework for risk-aware autonomy,
- a **Decision Intelligence Core (DIC)** built around explicit decision gates,
- a research artifact with reproducible benchmarks and auditable traces,
- a foundation for safety-oriented autonomous systems.

### AGI Pragma IS NOT
- a human-like AGI,
- a black-box learning system,
- a reward-maximization benchmark,
- a production-ready general intelligence.

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
- OK → WARN → SLOW → STOP

**6. Decision Selection** — utility balances survival probability, goal progress, residual risk.

**7. Belief Update** — Bayesian trackers update internal hazard estimates.

---

## Safety Model

Safety in AGI Pragma is **preventive**, not reactive.

- self-harm equals failure,
- no action bypasses risk evaluation,
- all decisions are auditable,
- autonomy is conditional, not absolute.

See: [docs/safety.md](docs/safety.md)

---

## Benchmark Results — Snake (v1.0)

**Date:** 2026-04-04  
**Agent:** PragmaSnakeAgent  
**Environment:** SnakeEnv 10×10  
**Episodes:** 10 (seeds 0–9)

### Results

| Metric | Value |
|---|---|
| Average score | 25.0 |
| Best score | 33 |
| Average reward | 113.1 |
| Average steps | 214 |
| Survival rate | 0/10 (agent plays aggressively) |

### Baseline comparison

| Config | Avg score | Avg reward |
|---|---|---|
| dist weight = 0.2 (passive) | 0.4 | ~0 |
| dist weight = 1.5 (active) | 25.0 | 113.1 |

**One parameter change produced a 60× improvement in score.**

### Interpretation

The agent with low dist weight survived all episodes but scored near zero —
paralysed by excessive risk aversion.

Increasing dist weight unlocked active play: the agent now seeks food
aggressively, accepts risk, and scores consistently above 20.

This demonstrates the core AGI Pragma trade-off:  
**safety ≠ passivity. Controlled risk is required for goal achievement.**

Run:
```bash
python3 -m benchmarks.snake.run
```

See: [docs/benchmarks/snake.md](docs/benchmarks/snake.md)

---

## Methodology

See: [docs/Methodology.md](docs/Methodology.md)

---

## Reproducibility

Benchmark runs produce:
- decision-level logs (JSONL),
- episode summaries (JSON),
- reproducible configurations.

---

## Related Projects

**ChaosGym / Reverse Reality Sandbox** — physics-breaking simulation environment
designed to stress-test AGI Pragma's decision integrity under non-stationary rules.

- [AGI-Development](https://github.com/zabinskirafal/AGI-Development)
- [developmental-agi-sandbox](https://github.com/zabinskirafal/developmental-agi-sandbox)

---

## Licensing & Commercial Use

**Author:** Rafał Żabiński

**Free use:** academic research, education, non-commercial projects, open-source experimentation.

**Commercial use:** requires a separate written agreement with the author.

📧 zabinskirafal@outlook.com  
🔗 https://www.linkedin.com/in/zabinskirafal

---

## Project Status

Current version: **v3.0.0**

AGI Pragma is an active research program, not a finished product.  
Future work: additional benchmarks, stronger baselines, formal evaluation protocols.

---

## Citation

If you use this work in research, please cite via: [CITATION.cff](CITATION.cff)

**Rafał Żabiński** — Founder and original author (January 2026)