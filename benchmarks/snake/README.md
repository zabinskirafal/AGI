# Snake Benchmark (AGI Pragma)

This benchmark implements a minimal "self-harm = loss" philosophy:

- Colliding with wall or own body is a catastrophic failure.
- The agent uses a decision gate before acting:
  - Critical Path estimation (Monte Carlo rollouts)
  - FMEA risk scoring (S/O/D → RPN)
  - Circuit-breaker style blocking of risky actions

## Run

```bash
python benchmarks/snake/run.py
