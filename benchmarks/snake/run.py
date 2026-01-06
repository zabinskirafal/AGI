from snake_env import SnakeEnv
from pragma_agent import PragmaSnakeAgent

def run_episode(seed=0, steps=500, mc_rollouts=50):
    env = SnakeEnv(width=10, height=10, seed=seed)
    agent = PragmaSnakeAgent(seed=seed, mc_rollouts=mc_rollouts, mc_depth=15)

    env.reset()
    total_reward = 0.0
    for t in range(steps):
        a = agent.choose_action(env)
        res = env.step(a)
        total_reward += res.reward
        if not res.alive:
            break

    return {
        "seed": seed,
        "steps": t + 1,
        "score": env.score,
        "alive": env.alive,
        "total_reward": total_reward
    }

if __name__ == "__main__":
    results = [run_episode(seed=i) for i in range(10)]
    for r in results:
        print(r)
