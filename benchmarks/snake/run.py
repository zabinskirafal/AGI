import json
from typing import Any, Dict, List, Optional

from snake_env import SnakeEnv
from pragma_agent import PragmaSnakeAgent
from artifacts import ArtifactWriter


def run_episode(
    seed: int = 0,
    steps: int = 300,
    rollouts: int = 200,
    depth: int = 25,
    rpn_threshold: int = 240,
    log: bool = False,
) -> Dict[str, Any]:
    env = SnakeEnv(width=10, height=10, seed=seed)
    agent = PragmaSnakeAgent(
        fmea_rpn_threshold=rpn_threshold,
        rollouts=rollouts,
        depth=depth,
        seed=seed,
    )
    env.reset()

    writer = ArtifactWriter()  # artifacts/snake/...
    total_reward = 0.0

    # Optional: store minimal run header as first decision entry (useful for reproducibility)
    if log:
        writer.write_decision({
            "type": "run_header",
            "seed": seed,
            "steps_limit": steps,
            "rollouts": rollouts,
            "depth": depth,
            "rpn_threshold": rpn_threshold,
            "env": {"width": env.width, "height": env.height},
        })

    for t in range(steps):
        action, report = agent.choose_action(env)
        res = env.step(action)
        total_reward += res.reward

        agent.update_bayes(report)

        if log:
            writer.write_decision({
                "type": "decision",
                "t": t,
                "action": action,
                "alive": res.alive,
                "ate": res.ate,
                "reward": res.reward,
                "score": env.score,
                "report": {
                    "blocked_actions": report.blocked_actions,
                    "tornado": report.tornado,
                    "bayes": report.bayes,
                    # If you want full per_action detail, uncomment:
                    # "per_action": report.per_action,
                }
            })

        if not res.alive:
            break

    summary = {
        "seed": seed,
        "steps": t + 1,
        "score": env.score,
        "alive": env.alive,
        "total_reward": total_reward,
        "final_bayes": {
            "trap_rate_mean": agent.trap_tracker.mean,
            "death_rate_mean": agent.death_tracker.mean,
        },
        "config": {
            "steps_limit": steps,
            "rollouts": rollouts,
            "depth": depth,
            "rpn_threshold": rpn_threshold,
            "env": {"width": env.width, "height": env.height},
        }
    }

    # Always write summary (even if log=False) for reproducible runs
    writer.write_summary(summary)
    return summary


if __name__ == "__main__":
    results: List[Dict[str, Any]] = [run_episode(seed=i, log=False) for i in range(10)]
    print(json.dumps(results, indent=2))
