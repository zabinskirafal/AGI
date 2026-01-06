# Safety and Controlled Autonomy

Safety in AGI Pragma is implemented **before action execution**,
not as an afterthought.

---

## Safety-by-Design Principles

1. **Self-harm equals failure**
   - Actions leading to irreversible loss are explicitly blocked.

2. **Risk-aware autonomy**
   - Autonomy is conditional and dynamically constrained.

3. **Explicit decision gates**
   - No action bypasses risk evaluation.

4. **Explainability**
   - Each decision produces auditable risk traces.

---

## Circuit Breaker States

- **OK** — normal autonomous operation
- **WARN** — elevated risk detected
- **SLOW** — exploration and decision depth restricted
- **STOP** — autonomy suspended, only safest fallback allowed

---

## Scope

AGI Pragma does not claim moral reasoning or consciousness.
Its safety model focuses on:

- preventing irreversible damage,
- maintaining operational control,
- enabling post-hoc auditing.

This makes it suitable for research in:
AI safety, decision governance, and controlled autonomy.
