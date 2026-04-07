import math
from dataclasses import dataclass

from .maze_env import MazeEnv, ACTIONS


@dataclass
class CriticalPathResult:
    p_death:               float  # fraction of rollouts that timed out before reaching goal
    p_trap:                float  # fraction of rollouts that entered a dead-end cell
    expected_steps_to_death: float  # mean steps until timeout (depth if solved/survived)
    variance_death:        float  # p_death * (1 - p_death)
    p95_death:             float  # upper 95% Wilson CI on p_death
    cvar_death:            float  # mean steps-to-death in earliest-timing-out 5% of rollouts


def critical_path_estimate(
    env: MazeEnv,
    first_action: str,
    rollouts: int = 200,
    depth: int = 25,
    seed_base: int = 0,
) -> CriticalPathResult:
    """
    Monte Carlo estimate of risk for a candidate maze action.

    p_death  : probability of timeout within horizon (goal not reached).
    p_trap   : probability of entering a dead-end cell within horizon.
    Tail risk metrics added (see CriticalPathResult docstring in snake for details).
    """
    timeouts = 0
    traps    = 0
    steps_per_rollout: list[float] = []

    for i in range(rollouts):
        sim    = env.clone(seed=seed_base + i)
        result = sim.step(first_action)

        if result.reached_goal:
            steps_per_rollout.append(1.0)
            continue
        if not result.alive:
            timeouts += 1
            steps_per_rollout.append(1.0)
            continue

        timed_out    = False
        entered_trap = False

        for t in range(1, depth):
            if sim.is_dead_end(sim.agent_pos):
                entered_trap = True

            safe = sim.safe_actions()
            if not safe:
                timed_out = True
                steps_per_rollout.append(float(t))
                break

            action = sim.rng.choice(safe)
            r = sim.step(action)

            if r.reached_goal:
                steps_per_rollout.append(float(t + 1))
                break
            if not r.alive:
                timed_out = True
                steps_per_rollout.append(float(t + 1))
                break
        else:
            timed_out = True
            steps_per_rollout.append(float(depth))

        if timed_out:
            timeouts += 1
        if entered_trap:
            traps += 1

    p_death  = timeouts / max(1, rollouts)
    p_trap   = traps    / max(1, rollouts)
    expected = sum(steps_per_rollout) / max(1, rollouts)

    variance_death = p_death * (1.0 - p_death)

    z = 1.645
    n = rollouts
    denom  = 1.0 + z * z / n
    centre = p_death + z * z / (2 * n)
    spread = z * math.sqrt(max(0.0, p_death * (1 - p_death) / n + z * z / (4 * n * n)))
    p95_death = (centre + spread) / denom

    sorted_steps = sorted(steps_per_rollout)
    cutoff     = max(1, int(0.05 * rollouts))
    cvar_death = sum(sorted_steps[:cutoff]) / cutoff

    return CriticalPathResult(
        p_death=p_death,
        p_trap=p_trap,
        expected_steps_to_death=expected,
        variance_death=variance_death,
        p95_death=p95_death,
        cvar_death=cvar_death,
    )
