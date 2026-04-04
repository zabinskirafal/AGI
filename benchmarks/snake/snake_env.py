from dataclasses import dataclass
from typing import List, Tuple, Dict
import random

Point = Tuple[int, int]

ACTIONS: Dict[str, Tuple[int, int]] = {
    "U": (0, -1),
    "D": (0, 1),
    "L": (-1, 0),
    "R": (1, 0),
}

OPPOSITE = {"U": "D", "D": "U", "L": "R", "R": "L"}

@dataclass
class StepResult:
    alive: bool
    ate: bool
    reward: float

class SnakeEnv:
    """
    Minimal Snake environment.
    - Wall collision or self-collision => death (catastrophic loss).
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
        self.steps = 0
        self.food = self._spawn_food()
        return self.obs()

    def clone(self, seed=0) -> "SnakeEnv":
        sim = SnakeEnv(self.width, self.height, seed=seed)
        sim.snake = list(self.snake)
        sim.dir = self.dir
        sim.score = self.score
        sim.alive = self.alive
        sim.steps = self.steps
        sim.food = self.food
        return sim

    def _spawn_food(self) -> Point:
        free = {(x, y) for x in range(self.width) for y in range(self.height)} - set(self.snake)
        return self.rng.choice(list(free))

    def obs(self):
        return {
            "head": self.snake[0],
            "snake": list(self.snake),
            "food": self.food,
            "dir": self.dir,
            "width": self.width,
            "height": self.height,
            "score": self.score,
            "steps": self.steps,
            "alive": self.alive,
        }

    def next_head(self, action: str) -> Point:
        dx, dy = ACTIONS[action]
        hx, hy = self.snake[0]
        return (hx + dx, hy + dy)

    def is_wall(self, p: Point) -> bool:
        x, y = p
        return (x < 0 or x >= self.width or y < 0 or y >= self.height)

    def is_self_collision(self, p: Point, will_grow: bool) -> bool:
        # if will grow, tail doesn't move => collision check includes tail
        body = set(self.snake if will_grow else self.snake[:-1])
        return p in body

    def is_dead_move(self, action: str) -> bool:
        # do not allow immediate reversal (optional rule)
        if action == OPPOSITE.get(self.dir):
            action = self.dir

        nh = self.next_head(action)
        if self.is_wall(nh):
            return True

        will_grow = (nh == self.food)
        return self.is_self_collision(nh, will_grow=will_grow)

    def safe_actions(self) -> List[str]:
        return [a for a in ACTIONS.keys() if not self.is_dead_move(a)]

    def step(self, action: str) -> StepResult:
        if not self.alive:
            return StepResult(alive=False, ate=False, reward=0.0)

        # prevent instant reverse
        if action == OPPOSITE.get(self.dir):
            action = self.dir

        nh = self.next_head(action)

        # death
        if self.is_wall(nh):
            self.alive = False
            return StepResult(alive=False, ate=False, reward=-10.0)

        ate = (nh == self.food)
        if self.is_self_collision(nh, will_grow=ate):
            self.alive = False
            return StepResult(alive=False, ate=False, reward=-10.0)

        # move
        self.dir = action
        self.snake.insert(0, nh)
        if ate:
            self.score += 1
            self.food = self._spawn_food()
            reward = 5.0
        else:
            self.snake.pop()
            reward = -0.01

        self.steps += 1
        return StepResult(alive=True, ate=ate, reward=reward)
