from dataclasses import dataclass
from typing import Tuple

@dataclass
class CriticalPathResult:
    p_death: float
    p_trap: float
    expected_steps_to_death: float

def critical_path_estimate(simulator, first_action: str, rollouts=200, depth=25, seed_base=0) -> CriticalPathResult:
    """
    Estimates:
    - probability of death within horizon
    - probability of trap (no safe moves encountered) within horizon
    - expected steps until death (within horizon, else depth)
    Uses Monte Carlo rollouts with random policies after first action.
    """
    deaths = 0
    traps = 0
    steps_to_death_sum = 0.0

    for i in range(rollouts):
        env = simulator.clone(seed=seed_base + i)
        r = env.step(first_action)
        if not r.alive:
            deaths += 1
            steps_to_death_sum += 1
            continue

        died_at = None
        trapped = False

        for t in range(1, depth):
            safe = env.safe_actions()
            if not safe:
                trapped = True
                # trapped usually implies imminent death / no legal moves
                died_at = t
                break

            a = env.rng.choice(list("UDLR"))
            rr = env.step(a)
            if not rr.alive:
                died_at = t + 1
                break

        if died_at is not None:
            deaths += 1
            steps_to_death_sum += died_at
        else:
            steps_to_death_sum += depth

        if trapped:
            traps += 1

    p_death = deaths / max(1, rollouts)
    p_trap = traps / max(1, rollouts)
    expected_steps = steps_to_death_sum / max(1, rollouts)

    return CriticalPathResult(
        p_death=p_death,
        p_trap=p_trap,
        expected_steps_to_death=expected_steps
    )
