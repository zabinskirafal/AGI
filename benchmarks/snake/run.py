import json
from snake_env import SnakeEnv
from pragma_agent import PragmaSnakeAgent

def run_episode(seed=0, steps=300, rollouts=200, depth=25, rpn_threshold=240, log=False):
    env = SnakeEnv(width=10, height=10, seed=seed)
    agent = PragmaSnakeAgent(
        fmea_rpn_threshold=rpn_threshold,
        rollouts=rollouts,
        depth=depth,
        seed=seed
    )
    env.reset()

    total_reward = 0.0
    decision_logs = []

    for t in range(steps):
        a, report = agent.choose_action(env)
        res = env.step(a)
        total_reward += res.reward

        agent.update_bayes(report)

        if log:
            decision_logs.append({
                "t": t,
                "obs": env.obs(),
                "action": a,
                "step_result": {"alive": res.alive, "ate": res.ate, "reward": res.reward},
                "report": {
                    "blocked_actions": report.blocked_actions,
                    "per_action": report.per_action,
                    "tornado": report.tornado,
                    "bayes": report.bayes,
                }
            })

        if not res.alive:
            break

    return {
        "seed": seed,
        "steps": t + 1,
        "score": env.score,
        "alive": env.alive,
        "total_reward": total_reward,
        "final_bayes": {
            "trap_rate_mean": agent.trap_tracker.mean,
            "death_rate_mean": agent.death_tracker.mean
        },
        "decisions": decision_logs if log else None
    }

if __name__ == "__main__":
    results = [run_episode(seed=i, log=False) for i in range(10)]
    print(json.dumps(results, indent=2))
