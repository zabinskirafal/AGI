from dataclasses import dataclass
from typing import Dict, Any, List, Tuple

from .snake_env import SnakeEnv, ACTIONS
from .critical_path import critical_path_estimate
from .risk_fmea import fmea_table, max_rpn
from .tornado import tornado_rank
from .bayes import BetaTracker
from .circuit_breaker import CircuitBreaker, CircuitBreakerConfig


@dataclass
class DecisionReport:
    action: str
    blocked_actions: Dict[str, str]
    per_action: Dict[str, Dict[str, Any]]
    tornado: List[Dict[str, Any]]
    bayes: Dict[str, float]


class PragmaSnakeAgent:
    def __init__(
        self,
        fmea_rpn_threshold: int = 240,
        rollouts: int = 200,
        depth: int = 25,
        seed: int = 0,
        circuit_breaker_config: CircuitBreakerConfig | None = None,
    ):
        self.fmea_rpn_threshold = fmea_rpn_threshold
        self.rollouts = rollouts
        self.depth = depth
        self.seed = seed

        self.trap_tracker = BetaTracker(1, 1)
        self.death_tracker = BetaTracker(1, 1)

        self.circuit_breaker = CircuitBreaker(
            circuit_breaker_config or CircuitBreakerConfig()
        )

    def choose_action(self, env: SnakeEnv) -> Tuple[str, DecisionReport]:
        candidates = list(ACTIONS.keys())
        per_action: Dict[str, Dict[str, Any]] = {}
        blocked: Dict[str, str] = {}

        for a in candidates:
            immediate_collision = env.is_dead_move(a)

            if immediate_collision:
                table = fmea_table(1.0, 0.0, immediate_collision=True)
                per_action[a] = {
                    "immediate_collision": True,
                    "critical_path": {
                        "p_death": 1.0,
                        "p_trap": 0.0,
                        "expected_steps_to_death": 1.0,
                    },
                    "fmea": {k: vars(v) for k, v in table.items()},
                    "max_rpn": max_rpn(table),
                    "circuit_breaker": {
                        "state": "stop",
                        "reason": "STOP: immediate self-harm",
                    },
                    "utility": -1e9,
                }
                blocked[a] = "Blocked: immediate self-harm."
                continue

            cp = critical_path_estimate(
                env, a, rollouts=self.rollouts, depth=self.depth, seed_base=self.seed
            )
            table = fmea_table(cp.p_death, cp.p_trap, immediate_collision=False)
            m_rpn = max_rpn(table)

            cb = self.circuit_breaker.evaluate(m_rpn)

            dist = self._food_distance_after(env, a)
            utility = (
                (1.0 - cp.p_death) * 10.0
                + (1.0 - cp.p_trap) * 3.0
                - dist * 0.2
                - (m_rpn / 1000.0)
            )

            per_action[a] = {
                "critical_path": vars(cp),
                "fmea": {k: vars(v) for k, v in table.items()},
                "max_rpn": m_rpn,
                "circuit_breaker": {
                    "state": cb.state.value,
                    "reason": cb.reason,
                },
                "utility": utility,
            }

            if m_rpn >= self.fmea_rpn_threshold or cb.state.value == "stop":
                blocked[a] = cb.reason

        allowed = [a for a in candidates if a not in blocked]
        if not allowed:
            allowed = sorted(candidates, key=lambda x: per_action[x]["max_rpn"])

        best = max(allowed, key=lambda x: per_action[x]["utility"])

        factors = {
            "p_death": -per_action[best]["critical_path"]["p_death"],
            "p_trap": -per_action[best]["critical_path"]["p_trap"],
            "max_rpn": -per_action[best]["max_rpn"] / 100.0,
        }
        ranked = tornado_rank(factors)

        return best, DecisionReport(
            action=best,
            blocked_actions=blocked,
            per_action=per_action,
            tornado=[{"factor": f.name, "impact": f.impact} for f in ranked],
            bayes={
                "trap_rate_mean": self.trap_tracker.mean,
                "death_rate_mean": self.death_tracker.mean,
            },
        )

    def update_bayes(self, report: DecisionReport):
        cp = report.per_action[report.action]["critical_path"]
        self.trap_tracker.update(cp["p_trap"] > 0.25)
        self.death_tracker.update(cp["p_death"] > 0.25)

    def _food_distance_after(self, env: SnakeEnv, action: str) -> float:
        hx, hy = env.snake[0]
        dx, dy = ACTIONS[action]
        fx, fy = env.food
        return abs(hx + dx - fx) + abs(hy + dy - fy)
