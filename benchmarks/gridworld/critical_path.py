import math
from dataclasses import dataclass

from .gridworld_env import GridworldEnv, ACTIONS


@dataclass
class CriticalPathResult:
    p_death:               float  # fraction of rollouts ending in hazard collision or timeout
    p_trap:                float  # fraction of rollouts where agent was surrounded (≥3 neighbours)
    expected_steps_to_death: float  # mean steps until death (depth if solved/survived)
    variance_death:        float  # p_death * (1 - p_death)
    p95_death:             float  # upper 95% Wilson CI on p_death
    cvar_death:            float  # mean steps-to-death in earliest-dying 5% of rollouts


def critical_path_estimate(
    env: GridworldEnv,
    first_action: str,
    rollouts: int = 200,
    depth:    int = 50,
    seed_base: int = 0,
) -> CriticalPathResult:
    """
    Monte Carlo estimate of risk for a candidate gridworld action.

    Unlike Snake and Maze, hazards move each step inside the rollout, so p_death
    captures genuine stochastic collision risk. Tail risk metrics quantify the
    shape of the steps-to-death distribution across rollouts.
    """
    deaths    = 0
    traps     = 0
    steps_per_rollout: list[float] = []

    for i in range(rollouts):
        sim    = env.clone(seed=seed_base + i)
        result = sim.step(first_action)

        if result.reached_goal:
            steps_per_rollout.append(1.0)
            continue

        if not result.alive:
            deaths += 1
            steps_per_rollout.append(1.0)
            continue

        died    = False
        trapped = False

        for t in range(1, depth):
            hpos = sim.hazard_positions()
            r, c = sim.agent_pos
            occupied_neighbours = sum(
                1 for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]
                if (r + dr, c + dc) in hpos
            )
            if occupied_neighbours >= 3:
                trapped = True

            safe = sim.safe_actions()
            if not safe:
                trapped = True
                died    = True
                steps_per_rollout.append(float(t))
                break

            action = sim.rng.choice(safe)
            r      = sim.step(action)

            if r.reached_goal:
                steps_per_rollout.append(float(t + 1))
                break
            if not r.alive:
                died = True
                steps_per_rollout.append(float(t + 1))
                break
        else:
            died = True
            steps_per_rollout.append(float(depth))

        if died:
            deaths += 1
        if trapped:
            traps  += 1

    p_death  = deaths / max(1, rollouts)
    p_trap   = traps  / max(1, rollouts)
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
