import random
from typing import Dict, List
from snake_env import ACTIONS, SnakeEnv

class PragmaSnakeAgent:
    """
    Decision-gated agent:
    1) Branching: consider actions
    2) Safety gate: remove self-harm moves
    3) Simple scoring: prefer closer to food + less trapped
    4) Optional Monte Carlo rollouts: estimate survival probability
    """
    def __init__(self, seed=0, mc_rollouts=0, mc_depth=10):
        self.rng = random.Random(seed)
        self.mc_rollouts = mc_rollouts
        self.mc_depth = mc_depth

    def choose_action(self, env: SnakeEnv) -> str:
        # 1) enumerate
        candidates = list(ACTIONS.keys())

        # 2) safety gate (self-harm = forbidden)
        safe = [a for a in candidates if not env.is_dead_move(a)]
        if not safe:
            # no safe moves => choose anything (death unavoidable)
            return self.rng.choice(candidates)

        # 3) score heuristics
        scored = [(self._score(env, a), a) for a in safe]
        scored.sort(reverse=True)

        # 4) optional Monte Carlo
        if self.mc_rollouts > 0:
            best = None
            best_val = -1e9
            for _, a in scored[:2]:  # test top-2
                val = self._mc_value(env, a)
                if val > best_val:
                    best_val = val
                    best = a
            return best

        return scored[0][1]

    def _score(self, env: SnakeEnv, action: str) -> float:
        # simple: move toward food
        hx, hy = env.snake[0]
        fx, fy = env.food
        dx = abs((hx + ACTIONS[action][0]) - fx)
        dy = abs((hy + ACTIONS[action][1]) - fy)
        dist = dx + dy
        return -dist

    def _mc_value(self, env: SnakeEnv, first_action: str) -> float:
        # Monte Carlo rollout: how often do we survive and eat?
        wins = 0
        eats = 0
        for i in range(self.mc_rollouts):
            sim = self._clone_env(env, seed=i)
            r = sim.step(first_action)
            if not r.alive:
                continue
            for _ in range(self.mc_depth):
                a = self.rng.choice(list(ACTIONS.keys()))
                rr = sim.step(a)
                if not rr.alive:
                    break
                if rr.ate:
                    eats += 1
            else:
                wins += 1
        # value: survival + eating
        return wins + 0.2 * eats

    def _clone_env(self, env: SnakeEnv, seed=0) -> SnakeEnv:
        sim = SnakeEnv(env.width, env.height, seed=seed)
        # copy state
        sim.snake = list(env.snake)
        sim.dir = env.dir
        sim.food = env.food
        sim.score = env.score
        sim.alive = env.alive
        return sim
