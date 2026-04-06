from dataclasses import dataclass

from .gridworld_env import GridworldEnv, ACTIONS


@dataclass
class CriticalPathResult:
    p_death:               float  # fraction of rollouts ending in hazard collision or timeout
    p_trap:                float  # fraction of rollouts where agent was surrounded (≥3 neighbours occupied)
    expected_steps_to_death: float


def critical_path_estimate(
    env: GridworldEnv,
    first_action: str,
    rollouts: int = 200,
    depth:    int = 50,
    seed_base: int = 0,
) -> CriticalPathResult:
    """
    Monte Carlo estimate of risk for a candidate action in the dynamic gridworld.

    Unlike Snake and Maze, hazards move each step inside the rollout, so p_death
    captures genuine stochastic collision risk — not just a saturated timeout signal.
    A rollout is a failure if:
      - the agent contacts a hazard (collision death), or
      - the rollout depth is exhausted without reaching the goal (timeout).

    p_trap: fraction of rollouts where the agent found itself surrounded —
    3 or more of the 4 orthogonal neighbours occupied by hazards simultaneously.
    Surrounded states are not always fatal immediately but strongly predict
    imminent death and forced bad moves.

    Rollout policy: uniform random over safe actions (no wall / no current hazard).
    If no safe actions exist, the agent is trapped — counted as both death and trap.
    """
    deaths    = 0
    traps     = 0
    steps_sum = 0.0

    for i in range(rollouts):
        sim    = env.clone(seed=seed_base + i)
        result = sim.step(first_action)

        if result.reached_goal:
            steps_sum += 1
            continue

        if not result.alive:
            # Killed on first action (walked into hazard)
            deaths    += 1
            steps_sum += 1
            continue

        died      = False
        trapped   = False

        for t in range(1, depth):
            # Check surrounded condition before choosing action
            hpos = sim.hazard_positions()
            r, c = sim.agent_pos
            occupied_neighbours = sum(
                1 for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]
                if (r+dr, c+dc) in hpos
            )
            if occupied_neighbours >= 3:
                trapped = True

            safe = sim.safe_actions()
            if not safe:
                # Fully enclosed by hazards — imminent death
                trapped   = True
                died      = True
                steps_sum += t
                break

            action = sim.rng.choice(safe)
            r      = sim.step(action)

            if r.reached_goal:
                steps_sum += t + 1
                break
            if not r.alive:
                died      = True
                steps_sum += t + 1
                break
        else:
            # Depth exhausted without reaching goal — count as timeout failure
            died      = True
            steps_sum += depth

        if died:
            deaths += 1
        if trapped:
            traps  += 1

    p_death  = deaths / max(1, rollouts)
    p_trap   = traps  / max(1, rollouts)
    expected = steps_sum / max(1, rollouts)

    return CriticalPathResult(
        p_death=p_death,
        p_trap=p_trap,
        expected_steps_to_death=expected,
    )
