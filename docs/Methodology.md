# Methodology

AGI Pragma is a research framework designed to evaluate adaptive
intelligence under dynamically changing environment rules.

The framework focuses on robustness, independent reasoning,
and adaptability rather than static performance optimization.

---

## Core Principles

1. Dynamic Environment Rules  
   Environment rules may change unpredictably during execution,
   including physical laws, causal relations, or reward structures.

2. Decision Branching  
   Agents explore decision spaces using explicit branching
   (e.g. YES / NO), rather than relying solely on gradient optimization.

3. Probabilistic Belief Updating  
   Agents update internal beliefs using Bayesian inference
   based on observed outcomes.

4. Robustness Evaluation  
   Performance is evaluated across many stochastic realizations
   using Monte Carlo simulation.

5. Sensitivity Analysis  
   Tornado analysis is used to identify which environment parameters
   have the highest impact on outcomes.

6. Collaboration and Forced Independence  
   Agents alternate between collaborative and isolated modes
   to validate independent reasoning capability.

---

## Evaluation

Evaluation metrics are defined in
[metrics.md](metrics.md).

---

## Reproducibility

Experiments should be conducted with:
- fixed random seeds,
- logged environment parameters,
- clearly reported Monte Carlo sample sizes.

This ensures auditability and reproducibility of results.
