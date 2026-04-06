"""
Baseline vs AGI Pragma — comparison runner.

Baseline agent: random action selection from safe actions only.
  - No FMEA, no Monte Carlo, no circuit breaker, no belief update.
  - safe_actions() is used to filter immediately fatal moves (walls,
    self-collision in Snake, current hazard positions in Gridworld).
  - This isolates the value of the full DIC pipeline from the basic
    branching filter that both agents share.

Run:
    python3 -m benchmarks.baseline.run_all
"""

import random
import statistics
from typing import Any, Dict, List

# ── Environments ──────────────────────────────────────────────────────────────
from benchmarks.snake.snake_env import SnakeEnv
from benchmarks.maze.maze_env import MazeEnv
from benchmarks.gridworld.gridworld_env import GridworldEnv

# ── Pragma run_episode functions (priors=None → no episodic memory) ───────────
from benchmarks.snake.run import run_episode as snake_pragma
from benchmarks.maze.run import run_episode as maze_pragma
from benchmarks.gridworld.run import run_episode as gw_pragma

N = 50  # episodes per agent per benchmark

# ══════════════════════════════════════════════════════════════════════════════
# Baseline runners — random policy, no DIC
# ══════════════════════════════════════════════════════════════════════════════

def run_snake_baseline(seed: int) -> Dict[str, Any]:
    rng = random.Random(seed)
    env = SnakeEnv(width=10, height=10, seed=seed)
    env.reset()
    total_reward = 0.0
    t = 0
    for t in range(300):
        safe = env.safe_actions()
        action = rng.choice(safe) if safe else rng.choice(["U", "D", "L", "R"])
        res = env.step(action)
        total_reward += res.reward
        if not res.alive:
            break
    return {
        "seed":         seed,
        "steps":        t + 1,
        "score":        env.score,
        "total_reward": total_reward,
    }


def run_maze_baseline(seed: int) -> Dict[str, Any]:
    rng = random.Random(seed)
    env = MazeEnv(seed=seed)
    env.reset()
    total_reward = 0.0
    t = 0
    while env.alive:
        safe = env.safe_actions()
        action = rng.choice(safe) if safe else rng.choice(["U", "D", "L", "R"])
        res = env.step(action)
        total_reward += res.reward
        t += 1
        if not res.alive:
            break
    return {
        "seed":         seed,
        "steps":        env.steps,
        "score":        env.score,
        "reached_goal": env.reached_goal,
        "total_reward": total_reward,
    }


def run_gridworld_baseline(seed: int) -> Dict[str, Any]:
    rng = random.Random(seed)
    env = GridworldEnv(seed=seed)
    env.reset()
    total_reward = 0.0
    while env.alive:
        safe = env.safe_actions()
        action = rng.choice(safe) if safe else rng.choice(["U", "D", "L", "R", "WAIT"])
        res = env.step(action)
        total_reward += res.reward
        if not res.alive:
            break
    return {
        "seed":         seed,
        "steps":        env.steps,
        "score":        env.score,
        "reached_goal": env.reached_goal,
        "total_reward": total_reward,
    }


# ══════════════════════════════════════════════════════════════════════════════
# Table printing
# ══════════════════════════════════════════════════════════════════════════════

def _delta(pragma_val: float, base_val: float, higher_is_better: bool = True) -> str:
    if base_val == 0:
        return "n/a"
    diff = pragma_val - base_val
    pct  = diff / abs(base_val) * 100
    sign = "+" if diff >= 0 else ""
    better = (diff > 0) == higher_is_better
    marker = " ✓" if better else " ✗"
    return f"{sign}{pct:.0f}%{marker}"


def _fmt(val: float, decimals: int = 1) -> str:
    return f"{val:.{decimals}f}"


def print_table(
    title:   str,
    rows:    List[tuple],   # (metric, baseline_str, pragma_str, delta_str)
    width:   int = 62,
) -> None:
    bar = "─" * width
    print(f"\n{'═' * width}")
    print(f"  {title}")
    print(f"{'═' * width}")
    print(f"  {'Metric':<28} {'Baseline':>9}  {'Pragma':>9}  {'Δ':>8}")
    print(f"  {bar}")
    for metric, base, pragma, delta in rows:
        print(f"  {metric:<28} {base:>9}  {pragma:>9}  {delta:>8}")
    print(f"  {bar}")


# ══════════════════════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":

    print(f"\nRunning {N} episodes per agent per benchmark …")
    print("(Pragma agents use full rollouts=200; baseline is instant)\n")

    # ── SNAKE ─────────────────────────────────────────────────────────────────
    print("Snake baseline …", end=" ", flush=True)
    snake_base = [run_snake_baseline(i) for i in range(N)]
    print("done.")

    print("Snake pragma  …", end=" ", flush=True)
    snake_prag = [snake_pragma(seed=i, priors=None) for i in range(N)]
    print("done.")

    sb_scores  = [r["score"]        for r in snake_base]
    sb_steps   = [r["steps"]        for r in snake_base]
    sb_rewards = [r["total_reward"] for r in snake_base]
    sp_scores  = [r["score"]        for r in snake_prag]
    sp_steps   = [r["steps"]        for r in snake_prag]
    sp_rewards = [r["total_reward"] for r in snake_prag]

    print_table("SNAKE — 10×10 grid (50 episodes each)", [
        ("Avg score",
         _fmt(statistics.mean(sb_scores)),
         _fmt(statistics.mean(sp_scores)),
         _delta(statistics.mean(sp_scores), statistics.mean(sb_scores))),
        ("Min score",
         str(min(sb_scores)),
         str(min(sp_scores)),
         _delta(min(sp_scores), min(sb_scores))),
        ("Max score",
         str(max(sb_scores)),
         str(max(sp_scores)),
         _delta(max(sp_scores), max(sb_scores))),
        ("Avg steps",
         _fmt(statistics.mean(sb_steps)),
         _fmt(statistics.mean(sp_steps)),
         _delta(statistics.mean(sp_steps), statistics.mean(sb_steps), higher_is_better=False)),
        ("Avg reward",
         _fmt(statistics.mean(sb_rewards)),
         _fmt(statistics.mean(sp_rewards)),
         _delta(statistics.mean(sp_rewards), statistics.mean(sb_rewards))),
    ])

    # ── MAZE ──────────────────────────────────────────────────────────────────
    print("\nMaze baseline …", end=" ", flush=True)
    maze_base = [run_maze_baseline(i) for i in range(N)]
    print("done.")

    print("Maze pragma   …", end=" ", flush=True)
    maze_prag = [maze_pragma(seed=i, priors=None) for i in range(N)]
    print("done.")

    mb_solved  = sum(1 for r in maze_base if r["reached_goal"])
    mp_solved  = sum(1 for r in maze_prag if r["reached_goal"])
    mb_steps   = [r["steps"] for r in maze_base]
    mp_steps   = [r["steps"] for r in maze_prag]
    mb_rewards = [r["total_reward"] for r in maze_base]
    mp_rewards = [r["total_reward"] for r in maze_prag]

    mb_steps_solved = [r["steps"] for r in maze_base if r["reached_goal"]] or [0]
    mp_steps_solved = [r["steps"] for r in maze_prag if r["reached_goal"]] or [0]

    print_table("MAZE — 15×15 recursive backtracker (50 episodes each)", [
        ("Solved",
         f"{mb_solved}/{N}",
         f"{mp_solved}/{N}",
         _delta(mp_solved, mb_solved)),
        ("Avg steps (all episodes)",
         _fmt(statistics.mean(mb_steps)),
         _fmt(statistics.mean(mp_steps)),
         _delta(statistics.mean(mp_steps), statistics.mean(mb_steps), higher_is_better=False)),
        ("Avg steps (solved only)",
         _fmt(statistics.mean(mb_steps_solved)),
         _fmt(statistics.mean(mp_steps_solved)),
         _delta(statistics.mean(mp_steps_solved), statistics.mean(mb_steps_solved), higher_is_better=False)),
        ("Avg reward",
         _fmt(statistics.mean(mb_rewards)),
         _fmt(statistics.mean(mp_rewards)),
         _delta(statistics.mean(mp_rewards), statistics.mean(mb_rewards))),
    ])

    # ── GRIDWORLD ─────────────────────────────────────────────────────────────
    print("\nGridworld baseline …", end=" ", flush=True)
    gw_base = [run_gridworld_baseline(i) for i in range(N)]
    print("done.")

    print("Gridworld pragma   …", end=" ", flush=True)
    gw_prag = [gw_pragma(seed=i, priors=None) for i in range(N)]
    print("done.")

    gb_solved  = sum(1 for r in gw_base if r["reached_goal"])
    gp_solved  = sum(1 for r in gw_prag if r["reached_goal"])
    gb_killed  = sum(1 for r in gw_base if not r["reached_goal"] and r["steps"] < 300)
    gp_killed  = sum(1 for r in gw_prag if not r["reached_goal"] and r["steps"] < 300)
    gb_timeout = sum(1 for r in gw_base if not r["reached_goal"] and r["steps"] >= 300)
    gp_timeout = sum(1 for r in gw_prag if not r["reached_goal"] and r["steps"] >= 300)
    gb_steps   = [r["steps"] for r in gw_base]
    gp_steps   = [r["steps"] for r in gw_prag]
    gb_rewards = [r["total_reward"] for r in gw_base]
    gp_rewards = [r["total_reward"] for r in gw_prag]

    print_table("GRIDWORLD — 15×15, 5 wandering hazards (50 episodes each)", [
        ("Solved",
         f"{gb_solved}/{N}",
         f"{gp_solved}/{N}",
         _delta(gp_solved, max(gb_solved, 1))),
        ("Killed by hazard",
         f"{gb_killed}/{N}",
         f"{gp_killed}/{N}",
         _delta(gp_killed, max(gb_killed, 1), higher_is_better=False)),
        ("Timed out",
         f"{gb_timeout}/{N}",
         f"{gp_timeout}/{N}",
         _delta(gp_timeout, max(gb_timeout, 1), higher_is_better=False)),
        ("Avg steps",
         _fmt(statistics.mean(gb_steps)),
         _fmt(statistics.mean(gp_steps)),
         _delta(statistics.mean(gp_steps), statistics.mean(gb_steps), higher_is_better=False)),
        ("Avg reward",
         _fmt(statistics.mean(gb_rewards)),
         _fmt(statistics.mean(gp_rewards)),
         _delta(statistics.mean(gp_rewards), statistics.mean(gb_rewards))),
    ])

    print(f"\n{'═' * 62}")
    print("  Notes")
    print(f"{'═' * 62}")
    print("  Baseline: random choice from safe_actions() — no DIC.")
    print("  safe_actions() filters immediate wall hits / hazard contacts,")
    print("  matching Pragma's branching stage. The Δ column measures the")
    print("  value of the full DIC pipeline above that shared filter.")
    print(f"  ✓ = Pragma better   ✗ = Pragma worse or no improvement")
    print(f"{'═' * 62}\n")
