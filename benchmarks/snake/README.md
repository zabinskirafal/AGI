# Snake Benchmark — Safety & Controlled Autonomy

This benchmark provides a minimal and interpretable environment for evaluating
**decision integrity, self-harm avoidance, and controlled autonomy** in AGI Pragma.

Snake is intentionally simple. Its value lies not in gameplay performance,
but in exposing whether an agent filters actions **before execution**
to avoid catastrophic outcomes.

---

## Core Principle

**Self-harm = loss**

Any collision with a wall or with the agent’s own body is:
- irreversible,
- catastrophic,
- immediately terminal.

An intelligent agent should therefore:
- detect such actions *before* execution,
- block them systematically,
- prefer survival and stability over short-term reward.

---

## What This Benchmark Tests

The Snake benchmark evaluates whether an agent can:

- filter unsafe actions prior to execution,
- recognize critical paths leading to inevitable failure,
- balance goal pursuit with risk avoidance,
- maintain controlled autonomy under uncertainty,
- produce auditable and explainable decision traces.

It does **not** test:
- human-like cognition,
- optimal reinforcement learning performance,
- large-scale generalization.

---

## Mapping to AGI Pragma

Each decision step follows the AGI Pragma pipeline:

1. **Branching**
   - Enumerate feasible actions (movement directions).

2. **Critical Path Estimation**
   - Monte Carlo rollouts estimate:
     - probability of death within a horizon,
     - probability of entering a trap or dead-end,
     - expected steps until failure.

3. **Risk Assessment (FMEA)**
   - Failure modes are evaluated using:
     - Severity (S),
     - Occurrence (O),
     - Detection difficulty (D).
   - A Risk Priority Number (RPN) is computed per action.

4. **Decision Integrity Gate**
   - Actions exceeding the RPN threshold are blocked.

5. **Circuit Breaker**
   - Autonomy is dynamically constrained:
     - OK → WARN → SLOW → STOP.

6. **Decision Selection**
   - Among allowed actions, utility balances survival,
     progress toward food, and residual risk.

7. **Belief Update**
   - Bayesian trackers update internal estimates of
     hazard and trap frequencies.

---

## Output Artifacts

Each run produces reproducible artifacts:

- **De**
