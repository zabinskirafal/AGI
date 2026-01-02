# Evaluation Metrics (AGI Pragma)

This document defines the metrics used to evaluate adaptive intelligence
in the AGI Pragma framework.

The focus is on robustness, independent reasoning, and adaptability
under dynamically changing environment rules.

---

## 1. Core Performance Metrics

### Success Rate
Percentage of episodes in which the agent successfully completes
the assigned task.

---

### Episode Reward
Total accumulated reward per episode (environment-specific).

Reported as:
- mean
- median
- percentile (P10 / P90)

---

## 2. Robustness Metrics (Monte Carlo Based)

### Robustness Score
Performance evaluated across many stochastic environment realizations
using Monte Carlo simulation.

Recommended summary:
- median performance
- worst-case percentile (P10)

---

### Catastrophic Failure Rate
Percentage of Monte Carlo runs in which performance drops below
a critical threshold.

---

## 3. Adaptation Metrics

### Adaptation Speed
Number of steps or episodes required for an agent to recover
above X% of baseline performance after a rule change.

---

### Generalization Gap
Performance difference between:
- low-chaos environments
- high-chaos environments

---

## 4. Sensitivity Metrics (Tornado Analysis)

### Parameter Impact Ranking
Ranking of environment parameters by their influence on outcome variance.

Computed using one-way sensitivity (Tornado) analysis.

---

## 5. Social and Independence Metrics

### Collaboration Lift
Difference in performance between collaborative and isolated modes.

---

### Independence Score
Ratio of isolated performance to collaborative performance.

---

### Isolation Recovery Time
Time required to recover performance after enforced isolation.

---

### Belief Stability
Variance of internal belief estimates during isolation.

---

## 6. Reporting Guidelines

All metrics should be reported with:
- random seed information,
- number of Monte Carlo runs,
- confidence intervals or percentiles.

This ensures reproducibility and auditability.


## Independence Metrics

- CollaborationLift:
  performance_collab - performance_isolated

- IndependenceScore:
  performance_isolated / performance_collab

- IsolationRecoveryTime:
  steps to return above X% performance after isolation

- BeliefSelfConsistency:
  stability of internal beliefs without peer input
