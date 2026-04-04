# Collaboration and Forced Independence

## Motivation
Performance achieved in collaborative settings does not guarantee
independent understanding.

AGI Pragma explicitly separates:
- collective problem solving
- individual reasoning capability

to avoid imitation, free-riding, and group dependency.

---

## Operational Modes

### Collaborative Mode
Agents:
- can exchange beliefs, hypotheses, and partial solutions,
- may observe actions and outcomes of other agents,
- can coordinate strategies.

Purpose:
- accelerate exploration,
- expose agents to diverse hypotheses.

---

### Forced Independence Mode (FIP)
Agents:
- have no access to other agents’ beliefs or actions,
- cannot observe peer behavior,
- must infer world rules independently.

Agents are not informed explicitly that isolation has occurred.

Purpose:
- validate true individual understanding,
- detect over-reliance on collaboration,
- test robustness under information deprivation.

---

## Mode Switching
The environment may switch modes:
- periodically,
- randomly,
- or triggered by performance thresholds.

Mode switching is treated as part of environmental uncertainty.

---

## Evaluation Metrics
- Collaboration Lift:
  performance_collaborative − performance_isolated
- Independence Score:
  performance_isolated / performance_collaborative
- Isolation Recovery Time:
  steps required to regain X% performance after isolation
- Belief Stability:
  variance of internal beliefs during isolation
