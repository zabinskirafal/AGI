from dataclasses import dataclass
from typing import Dict, Any, List, Tuple
import math

from snake_env import SnakeEnv, ACTIONS
from critical_path import critical_path_estimate
from risk_fmea import fmea_table, max_rpn
from tornado import tornado_rank
from bayes import BetaTracker

@dataclass
class DecisionReport:
    action: str
    blocked_actions: Dict[str, str]
    per_action: Dict[str, Dict[str, Any]]
    tornado: List[Dict[str, Any]]
    bayes: Dict[str, float]

class PragmaSnakeAgent:
    """
    Minimal AGI Pragma loop for Snake:
      1) Branch candidate actions
      2) Critical Path (Monte Carlo rollouts) -> p_death, p_trap, expected steps
      3) FMEA -> RPN gate (block if too risky)
      4) Choose best among allowed based on utility (eat + survival)
      5) Tornado-style ranking of decision drivers for transparency
      6) Bayes trackers update (trap / near-miss rates)
    """
    def __init__(self, fmea_rpn_threshold=240, rollouts=200, depth=25, seed=0):
        self.fmea_rpn_threshold = fmea_rpn_threshold
        self.rollouts = rollouts
        self.depth = depth
        self.seed = seed

        # Bayes trackers: learn "how often trap happens" and "how often death happens within horizon"
        self.trap_tracker = BetaTracker(1, 1)
        self.death_tracker = BetaTracker(1, 1)

    def choose_action(self, env: SnakeEnv) -> Tuple[str, DecisionReport]:
        candidates = list(ACTIONS.keys())
        per_action: Dict[str, Dict[str, Any]] = {}
        blocked: Dict[str, str] = {}

        # Evaluate each action
        for a in candidates:
            immediate_collision = env.is_dead_move(a)

            if immediate_collision:
                table = fmea_table(1.0, 0.0, immediate_collision=True)
                per_action[a] = {
                    "immediate_collision": True,
                    "critical_path": {"p_death": 1.0, "p_trap": 0.0, "expected_steps_to_death": 1.0},
                    "fmea": {k: vars(v) for k, v in table.items()},
                    "max_rpn": max_rpn(table),
                    "utility": -1e9,
                }
                blocked[a] = "Blocked: immediate self-harm (catastrophic collision)."
                continue

            cp = critical_path_estimate(env, a, rollouts=self.rollouts, depth=self.depth, seed_base=self.seed)
            table = fmea_table(cp.p_death, cp.p_trap, immediate_collision=False)
            m_rpn = max_rpn(table)

            if m_rpn >= self.fmea_rpn_threshold:
                blocked[a] = f"Blocked by FMEA gate (max RPN={m_rpn} >= {self.fmea_rpn_threshold})."

            # Utility: prefer survival and eating potential
            # simple scoring: survival (1 - p_death) + trap avoidance + proximity to food
            dist = self._food_distance_after(env, a)
            utility = (
                (1.0 - cp.p_death) * 10.0
                + (1.0 - cp.p_trap) * 3.0
                - dist * 0.2
                - (m_rpn / 1000.0)  # tiny penalty for risk
            )

            per_action[a] = {
                "immediate_collision": False,
                "critical_path": {
                    "p_death": cp.p_death,
                    "p_trap": cp.p_trap,
                    "expected_steps_to_death": cp.expected_steps_to_death
                },
                "fmea": {k: vars(v) for k, v in table.items()},
                "max_rpn": m_rpn,
                "utility": utility,
                "dist_to_food_after": dist,
            }

        # Choose among non-blocked
        allowed = [a for a in candidates if a not in blocked]
        if not allowed:
            # if everything blocked, pick the least bad (min max_rpn)
            allowed = candidates

        best = max(allowed, key=lambda a: per_action[a]["utility"])

        # Tornado factors (explain decision drivers)
        chosen = per_action[best]
        factors = {
            "p_death_horizon": -chosen["critical_path"]["p_death"],
            "p_trap_horizon": -chosen["critical_path"]["p_trap"],
            "expected_steps_to_death": chosen["critical_path"]["expected_steps_to_death"] / max(1.0, self.depth),
            "dist_to_food_after": -chosen["dist_to_food_after"],
            "max_rpn": -chosen["max_rpn"] / 100.0,
        }
        t_rank = tornado_rank(factors)

        report = DecisionReport(
            action=best,
            blocked_actions=blocked,
            per_action=per_action,
            tornado=[{"factor": f.name, "impact": f.impact} for f in t_rank],
            bayes={
                "trap_rate_mean": self.trap_tracker.mean,
                "death_rate_mean": self.death_tracker.mean
            }
        )

        return best, report

    def update_bayes(self, chosen_report: DecisionReport):
        # Update trackers based on chosen action predicted outcomes (simple, consistent)
        cp = chosen_report.per_action[chosen_report.action]["critical_path"]
        self.trap_tracker.update(cp["p_trap"] > 0.25)
        self.death_tracker.update(cp["p_death"] > 0.25)

    def _food_distance_after(self, env: SnakeEnv, action: str) -> float:
        hx, hy = env.snake[0]
        dx, dy = ACTIONS[action]
        nx, ny = hx + dx, hy + dy
        fx, fy = env.food
        return abs(nx - fx) + abs(ny - fy)
