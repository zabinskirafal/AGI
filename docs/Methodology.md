# Methodology

AGI Pragma is a research framework for decision intelligence under dynamic and
uncertain environments.

It does not aim to replicate human cognition, consciousness, or emotions.
Instead, it formalizes **human-like adaptive decision mechanisms**:
filtering reality, managing risk, and updating beliefs before acting.

---

## Core Assumption

Intelligent behavior does not require evaluating all possible outcomes.
It requires **systematic reduction of the decision space** to what is:

- plausible,
- relevant,
- and safe in a given context.

AGI Pragma operationalizes this principle through a structured decision pipeline.

---

## Decision Pipeline

Each decision follows the same ordered stages:

### 1. Branching
- Enumerate feasible actions.
- Exclude physically or logically impossible actions.

### 2. Critical Path Estimation
- Monte Carlo rollouts estimate:
  - probability of catastrophic failure within a finite horizon,
  - probability of entering a trap or dead-end,
  - expected steps until failure.
- This approximates whether an action lies on a **critical path** to loss.

### 3. Risk Assessment (FMEA)
- Failure modes are evaluated using:
  - Severity (S),
  - Occurrence (O),
  - Detection difficulty (D).
- A Risk Priority Number is computed:  
  **RPN = S × O × D**

### 4. Decision Integrity Gate
- Actions exceeding a risk threshold are blocked.
- This prevents catastrophic behavior *before execution*.

### 5. Circuit Breaker
- Autonomy is dynamically constrained based on risk:
  - OK → WARN → SLOW → STOP

### 6. Decision Selection
- Among allowed actions, utility balances:
  - survival probability,
  - progress toward goals,
  - residual risk.

### 7. Belief Update
- Bayesian trackers update internal estimates of hazard rates
  (e.g. trap likelihood, near-death frequency).

---

## Design Philosophy

AGI Pragma prioritizes:

- robustness over maximal reward,
- interpretability over opaque optimization,
- prevention over post-hoc correction.

The methodology is domain-agnostic and applicable to:
simulation, decision-support systems, and controlled autonomous agents.
