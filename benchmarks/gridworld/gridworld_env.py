from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple
import random

Point = Tuple[int, int]

# Five actions: four directions plus WAIT (agent stays, hazards still move)
ACTIONS: Dict[str, Tuple[int, int]] = {
    "U":    (-1,  0),
    "D":    ( 1,  0),
    "L":    ( 0, -1),
    "R":    ( 0,  1),
    "WAIT": ( 0,  0),
}

SIZE     = 15
MAX_STEPS = 300
N_HAZARDS = 5

# Directions used for hazard random walks (no WAIT — hazards always move)
_MOVE_DIRS: List[Tuple[int, int]] = [(-1, 0), (1, 0), (0, -1), (0, 1)]


@dataclass
class StepResult:
    alive:        bool
    reached_goal: bool
    reward:       float


@dataclass
class Hazard:
    pos: Point
    rng: random.Random

    def move(self) -> None:
        """Take one random step, staying in place if all moves go out of bounds."""
        r, c = self.pos
        options = [
            (r + dr, c + dc)
            for dr, dc in _MOVE_DIRS
            if 0 <= r + dr < SIZE and 0 <= c + dc < SIZE
        ]
        if options:
            self.pos = self.rng.choice(options)


class GridworldEnv:
    """
    15×15 open grid with N_HAZARDS moving threats.

    Step order each turn:
      1. Agent acts (moves or waits).
      2. Check: agent now on a hazard? → death.
      3. Hazards move.
      4. Check: any hazard moved onto agent? → death.
      5. Check: agent on goal? → solved.
      6. Check: steps >= MAX_STEPS? → timeout.

    Both collision directions are checked so the agent cannot safely
    step into a cell that a hazard is vacating — the hazard may not vacate it.

    - score = MAX_STEPS − steps_taken when goal reached; 0 otherwise.
    - WAIT is a valid action: agent stays, hazards move. Useful for
      letting a hazard pass rather than dodging into its future path.
    """

    SIZE      = SIZE
    MAX_STEPS = MAX_STEPS

    def __init__(self, seed: int = 0):
        self.seed = seed
        self.rng  = random.Random(seed)
        self.start: Point = (1, 1)
        self.goal:  Point = (SIZE - 2, SIZE - 2)
        self.reset()

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def reset(self) -> dict:
        self.steps:        int   = 0
        self.alive:        bool  = True
        self.reached_goal: bool  = False
        self.score:        int   = 0
        self.agent_pos:    Point = self.start
        self.visit_counts: Dict[Point, int] = {self.start: 1}

        # Spawn hazards at random open cells (not start, not goal)
        self.rng = random.Random(self.seed)  # reset RNG for reproducibility
        self.hazards: List[Hazard] = self._spawn_hazards()
        return self.obs()

    def clone(self, seed: int = 0) -> "GridworldEnv":
        """Deep copy with independent per-hazard RNGs for Monte Carlo rollouts."""
        sim = GridworldEnv.__new__(GridworldEnv)
        sim.seed          = seed
        sim.rng           = random.Random(seed)
        sim.start         = self.start
        sim.goal          = self.goal
        sim.steps         = self.steps
        sim.alive         = self.alive
        sim.reached_goal  = self.reached_goal
        sim.score         = self.score
        sim.agent_pos     = self.agent_pos
        sim.visit_counts  = dict(self.visit_counts)
        # Each hazard gets its own seeded RNG so rollouts diverge correctly
        sim.hazards = [
            Hazard(pos=h.pos, rng=random.Random(seed + i))
            for i, h in enumerate(self.hazards)
        ]
        return sim

    def step(self, action: str) -> StepResult:
        if not self.alive:
            return StepResult(alive=False, reached_goal=self.reached_goal, reward=0.0)

        # 1. Agent moves (WAIT keeps same position)
        dr, dc = ACTIONS[action]
        r, c   = self.agent_pos
        nr, nc = r + dr, c + dc

        # Boundary check — out-of-bounds moves are no-ops (same as maze walls)
        if not self._in_bounds((nr, nc)):
            return StepResult(alive=True, reached_goal=False, reward=0.0)

        self.agent_pos = (nr, nc)
        if action != "WAIT":
            self.steps += 1
            self.visit_counts[self.agent_pos] = (
                self.visit_counts.get(self.agent_pos, 0) + 1
            )

        # 2. Agent walked into a hazard
        if self.agent_pos in self.hazard_positions():
            self.alive = False
            self.score = 0
            return StepResult(alive=False, reached_goal=False, reward=-10.0)

        # 3. Hazards move
        for h in self.hazards:
            h.move()

        # 4. A hazard moved onto the agent
        if self.agent_pos in self.hazard_positions():
            self.alive = False
            self.score = 0
            return StepResult(alive=False, reached_goal=False, reward=-10.0)

        # 5. Goal check
        if self.agent_pos == self.goal:
            self.reached_goal = True
            self.alive        = False
            self.score        = MAX_STEPS - self.steps
            return StepResult(alive=False, reached_goal=True, reward=10.0)

        # 6. Timeout
        if self.steps >= MAX_STEPS:
            self.alive = False
            self.score = 0
            return StepResult(alive=False, reached_goal=False, reward=-10.0)

        return StepResult(alive=True, reached_goal=False, reward=-0.1)

    def hazard_positions(self) -> Set[Point]:
        return {h.pos for h in self.hazards}

    def is_dead_move(self, action: str) -> bool:
        """True if the action lands on a current hazard position or out of bounds."""
        dr, dc = ACTIONS[action]
        r, c   = self.agent_pos
        nxt    = (r + dr, c + dc)
        if not self._in_bounds(nxt):
            return True
        return nxt in self.hazard_positions()

    def safe_actions(self) -> List[str]:
        return [a for a in ACTIONS if not self.is_dead_move(a)]

    def proximity_score(self, pos: Point) -> int:
        """Number of hazard cells within Manhattan distance 2 of pos."""
        r, c = pos
        return sum(
            1 for h in self.hazards
            if abs(h.pos[0] - r) + abs(h.pos[1] - c) <= 2
        )

    def manhattan_to_goal(self, pos: Point) -> int:
        return abs(pos[0] - self.goal[0]) + abs(pos[1] - self.goal[1])

    def obs(self) -> dict:
        return {
            "agent_pos":    self.agent_pos,
            "goal":         self.goal,
            "hazards":      list(self.hazard_positions()),
            "steps":        self.steps,
            "alive":        self.alive,
            "reached_goal": self.reached_goal,
            "score":        self.score,
            "manhattan":    self.manhattan_to_goal(self.agent_pos),
            "proximity":    self.proximity_score(self.agent_pos),
        }

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _spawn_hazards(self) -> List[Hazard]:
        forbidden = {self.start, self.goal}
        # Also keep a buffer of 1 cell around start so agent isn't immediately killed
        r0, c0 = self.start
        for dr in range(-1, 2):
            for dc in range(-1, 2):
                forbidden.add((r0 + dr, c0 + dc))

        candidates = [
            (r, c)
            for r in range(SIZE)
            for c in range(SIZE)
            if (r, c) not in forbidden
        ]
        chosen = self.rng.sample(candidates, N_HAZARDS)
        return [
            Hazard(pos=p, rng=random.Random(self.seed + i))
            for i, p in enumerate(chosen)
        ]

    def _in_bounds(self, pos: Point) -> bool:
        r, c = pos
        return 0 <= r < SIZE and 0 <= c < SIZE
