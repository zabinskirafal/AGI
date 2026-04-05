# Contributing to AGI Pragma

AGI Pragma is an active research project. Contributions are welcome in the areas of
new benchmarks, additional domain applications, core DIC improvements, and documentation.

**Commercial use of contributions requires a separate written agreement with the author.**
See [Licensing & Commercial Use](README.md#licensing--commercial-use) in the README.

---

## Setup

**Requirements:** Python 3.10+ (the codebase uses `match` syntax and `X | Y` type unions),
`numpy >= 1.21.0`, `scipy >= 1.7.0`.

```bash
git clone https://github.com/zabinskirafal/AGI.git
cd AGI
pip install -r requirements.txt
```

Verify your setup by running the Snake benchmark:

```bash
python3 -m benchmarks.snake.run
```

This runs 50 episodes and writes JSON summaries to `artifacts/snake/`.
Expected average score: ~22–23. If the run completes without error, your environment is correct.

---

## Project Structure

```
core/                   # Decision Intelligence Core (DIC) components
benchmarks/snake/       # Snake 10×10 benchmark — reference implementation
docs/                   # Methodology, safety model, domain applications
artifacts/snake/        # Benchmark output (gitignored except .gitkeep)
config/                 # Agent configuration files
Scripts/                # Unity/C# components for the reverse-physics sandbox
```

The `core/` and `benchmarks/snake/` directories are the primary places for code changes.
`docs/` is the primary place for new domain applications and methodology notes.

---

## How to Contribute

### 1. New benchmark

A benchmark must follow the structure of `benchmarks/snake/`:

- **Environment** — a class with `reset()`, `step(action)`, and `score` / `alive` attributes.
- **Agent** — uses the DIC pipeline: branching → critical path → FMEA → circuit breaker → selection → Bayesian update.
- **Runner** — a `run_episode()` function and a `__main__` block matching `benchmarks/snake/run.py`.
- **Artifact writer** — use `benchmarks/snake/artifacts.py` as a reference; write summaries to `artifacts/<benchmark_name>/`.
- **Documentation** — add `docs/benchmarks/<benchmark_name>.md` with methodology notes and results.

The Snake benchmark (`benchmarks/snake/pragma_agent.py`) is the canonical reference for
how a compliant agent wires together the DIC components.

### 2. New domain application

Add a file to `docs/applications/` (create the directory if needed) following the structure
of `docs/applications.md`:

- map the 7 DIC pipeline stages to the new domain,
- define domain-specific failure modes for the FMEA table,
- include an example decision trace with concrete values.

### 3. Core DIC improvement

Changes to `core/` must preserve the pipeline contract:

| Component | File | Contract |
|---|---|---|
| Decision tree / branching | `core/decision_tree.py` | returns enumerable action candidates |
| Critical path | `core/critical_path_analyzer.py` | returns criticality flag per node |
| FMEA engine | `core/fmea_engine.py` | returns `{rpn, is_critical_path, metrics: {S, O, D}}` |
| Circuit breaker | `core/circuit_breaker.py` | returns `{status: PROCEED\|HALTED, ...}` |
| Bayesian updater | `core/bayesian_updater.py` | stateful; `update_beliefs(action, context)` |

Do not change return shapes without updating all call sites and the relevant benchmark agent.

---

## Benchmarking Standards

When reporting results, include:

- number of episodes (minimum 50 for a reliable estimate),
- random seeds used (sequential from 0 is the project convention),
- all agent configuration parameters (`rollouts`, `depth`, `rpn_threshold`),
- the full metrics table: average score, min/max, average reward, average steps,
  survived-to-limit count, score distribution bands.

See the Snake results in [README.md](README.md#benchmark-results--snake) for the expected format.

---

## Submitting Changes

1. Fork the repository and create a branch from `main`.
2. Make your changes. Keep commits focused — one logical change per commit.
3. Run the Snake benchmark to confirm nothing regressed:
   ```bash
   python3 -m benchmarks.snake.run
   ```
4. Open a pull request against `main` with a clear description of what changed and why.

For significant changes (new benchmarks, architectural changes to `core/`), open an issue
first to discuss the approach before investing time in implementation.

---

## Contact

**Rafał Żabiński** — zabinskirafal@outlook.com  
https://www.linkedin.com/in/zabinskirafal
