# Snake Benchmark: Safety & Autonomy

The Snake benchmark is a minimal environment for evaluating
**decision integrity and self-harm avoidance**.

---

## Core Property

Any collision with walls or the agent’s own body is:

- irreversible,
- catastrophic,
- terminal.

This makes Snake ideal for testing whether an agent
filters unsafe actions *before execution*.

---

## What the Benchmark Tests

- action filtering prior to execution,
- recognition of critical paths to failure,
- balance between goal pursuit and survival,
- controlled autonomy under uncertainty.

It does not test:
- human cognition,
- optimal gameplay,
- large-scale generalization.

---

## Mapping to AGI Pragma

- Branching → possible moves
- Critical Path → Monte Carlo horizon estimation
- FMEA → risk scoring (RPN)
- Circuit Breaker → autonomy control
- Tornado → decision explainability
- Bayesian update → hazard learning

---

## Output Artifacts

Each run produces:
- decision-level logs (JSONL),
- episode summaries (JSON).

These artifacts support reproducibility and auditability.

---

## Purpose

Snake serves as a **baseline safety benchmark**
for risk-aware autonomous decision-making.
