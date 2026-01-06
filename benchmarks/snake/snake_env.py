from dataclasses import dataclass
from typing import List, Tuple, Optional
import random

Point = Tuple[int, int]

ACTIONS = {
    "U": (0, -1),
    "D": (0, 1),
    "L": (-1, 0),
    "R": (1, 0),
}

@dataclass
class StepResult:
    alive: bool
    ate: bool
    reward: float

class SnakeEnv:
    """
    Minimal Snake environment.
    - Wall collision or self collision => death (loss).
    - Eating => grows.
    """
    def __init__(self, width=10, height=10, seed=0):
        self.width = width
        self.height = height
        self.rng = random.Random(seed)
        self.reset()

    def reset(self):
        cx, cy = self.width // 2, self.height // 2
        self.snake: List[Point] = [(cx, cy), (cx-1, cy), (cx-2, cy)]
        self.dir = "R"
        self.score = 0
        self.alive = True
        self.food = self._spawn_food()
        return self._obs()

    def _spawn_food(self) -> Point:
        free = {(x, y) for x in range(self.width) for y in range(self.height)} - set(self.snake)
        return self.rng.choice(list(free))

    def _obs(self):
        # Simple observation structure (you can expand later)
        head = self.snake[0]
        return {
            "head": head,
            "snake": list(self.snake),
            "food": self.food,
            "dir": self.dir,
            "width": self.width,
            "height": self.height,
        }

    def _next_head(self, action: str) -> Point:
        dx, dy = ACTIONS[action]
        hx, hy = self.snake[0]
        return (hx + dx, hy + dy)

    def is_dead_move(self, action: str) -> bool:
        nh = self._next_head(action)
        x, y = nh
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return True
        # self collision (note: tail moves unless we eat)
        body = set(self.snake[:-1])
        return nh in body

    def step(self, action: str) -> StepResult:
        if not self.alive:
            return StepResult(alive=False, ate=False, reward=0.0)

        # prevent reverse into itself (optional rule)
        opposites = {"U": "D", "D": "U", "L": "R", "R": "L"}
        if action == opposites.get(self.dir):
            action = self.dir

        nh = self._next_head(action)
        if self.is_dead_move(action):
            self.alive = False
            return StepResult(alive=False, ate=False, reward=-10.0)

        self.dir = action
        ate = (nh == self.food)

        self.snake.insert(0, nh)
        if ate:
            self.score += 1
            self.food = self._spawn_food()
            reward = 5.0
        else:
            self.snake.pop()
            reward = -0.01  # tiny step cost to prefer efficiency

        return StepResult(alive=True, ate=ate, reward=reward)
