import math
from dataclasses import dataclass
from typing import Tuple


@dataclass
class CriticalPathResult:
    p_death:               float  # fraction of rollouts that ended in death
    p_trap:                float  # fraction of rollouts that hit a no-safe-moves state
    expected_steps_to_death: float  # mean steps until death across rollouts (depth if survived)
    variance_death:        float  # p_death * (1 - p_death) — uncertainty; max at p=0.5
    p95_death:             float  # upper 95% Wilson CI on p_death — conservative bound
    cvar_death:            float  # mean steps-to-death in earliest-dying 5% of rollouts (lower = worse tail)


def critical_path_estimate(
    simulator,
    first_action: str,
    rollouts: int = 200,
    depth: int = 25,
    seed_base: int = 0,
) -> CriticalPathResult:
    """
    Monte Carlo estimate of risk for a candidate Snake action.

    Tail risk metrics:
      variance_death : p * (1-p) — maximum uncertainty at p=0.5, zero at extremes.
      p95_death      : upper 95% Wilson confidence interval on p_death. Conservative
                       bound: with 95% confidence the true death probability is at
                       most this value. Useful for gate decisions under small rollout N.
      cvar_death     : mean steps-to-death in the worst 5% of rollouts (those that die
                       earliest). Lower = fatter left tail = worse tail risk. Survivors
                       contribute steps=depth; early deaths pull this metric down.
    """
    deaths = 0
    traps  = 0
    steps_per_rollout: list[float] = []   # steps-to-death per rollout; depth if survived

    for i in range(rollouts):
        env = simulator.clone(seed=seed_base + i)
        r = env.step(first_action)

        if not r.alive:
            deaths += 1
            steps_per_rollout.append(1.0)
            continue

        died_at = None
        trapped = False

        for t in range(1, depth):
            safe = env.safe_actions()
            if not safe:
                trapped = True
                died_at = t
                break

            a = env.rng.choice(list("UDLR"))
            rr = env.step(a)
            if not rr.alive:
                died_at = t + 1
                break

        if died_at is not None:
            deaths += 1
            steps_per_rollout.append(float(died_at))
        else:
            steps_per_rollout.append(float(depth))

        if trapped:
            traps += 1

    p_death  = deaths / max(1, rollouts)
    p_trap   = traps  / max(1, rollouts)
    expected = sum(steps_per_rollout) / max(1, rollouts)

    # Tail risk metrics
    variance_death = p_death * (1.0 - p_death)

    z = 1.645  # one-sided 95%
    n = rollouts
    denom = 1.0 + z * z / n
    centre = p_death + z * z / (2 * n)
    spread = z * math.sqrt(max(0.0, p_death * (1 - p_death) / n + z * z / (4 * n * n)))
    p95_death = (centre + spread) / denom

    sorted_steps = sorted(steps_per_rollout)   # ascending: earliest deaths first
    cutoff = max(1, int(0.05 * rollouts))
    cvar_death = sum(sorted_steps[:cutoff]) / cutoff

    return CriticalPathResult(
        p_death=p_death,
        p_trap=p_trap,
        expected_steps_to_death=expected,
        variance_death=variance_death,
        p95_death=p95_death,
        cvar_death=cvar_death,
    )
