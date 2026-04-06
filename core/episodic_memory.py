import json
import os
from typing import Dict, Tuple

# Prior state: maps tracker key → (a, b) Beta parameters
PriorState = Dict[str, Tuple[float, float]]


class EpisodicMemory:
    """
    Persistent episodic memory for AGI Pragma agents.

    Saves and loads Beta(a, b) tracker parameters between benchmark runs.
    The terminal posterior of run N becomes the initial prior for run N+1,
    so the agent accumulates calibrated risk estimates across sessions rather
    than starting from maximum uncertainty (Beta(1,1)) every time.

    Storage format (JSON):
        {
            "trap_rate":  {"a": 12.5, "b": 3.1},
            "death_rate": {"a": 8.4,  "b": 21.0}
        }

    Usage:
        memory = EpisodicMemory("artifacts/snake/memory.json")
        priors = memory.load()                     # Beta(1,1) if no file yet

        for seed in range(50):
            summary = run_episode(seed=seed, priors=priors)
            priors = memory.extract(summary["bayes_state"])  # carry forward

        memory.save(priors)                        # persist for next run
    """

    def __init__(self, path: str, decay: float = 1.0):
        """
        path  : path to memory.json for this benchmark.
        decay : shrink accumulated pseudo-counts by this factor on load,
                keeping the agent sensitive to environmental change.
                1.0 = full persistence (default), 0.5 = halve pseudo-counts.
        """
        self.path  = path
        self.decay = decay

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def load(self) -> PriorState:
        """
        Load Beta(a, b) parameters from memory file.
        Returns empty dict (callers fall back to Beta(1,1)) if file absent.
        Applies decay factor to accumulated pseudo-counts on load.
        """
        if not os.path.exists(self.path):
            return {}

        with open(self.path, encoding="utf-8") as f:
            raw = json.load(f)

        state: PriorState = {}
        for key, entry in raw.items():
            a = 1.0 + (entry["a"] - 1.0) * self.decay
            b = 1.0 + (entry["b"] - 1.0) * self.decay
            state[key] = (max(1.0, a), max(1.0, b))

        return state

    def save(self, state: PriorState) -> None:
        """Persist Beta(a, b) parameters to memory file."""
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        payload = {k: {"a": a, "b": b} for k, (a, b) in state.items()}
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

    def get_ab(self, state: PriorState, key: str) -> Tuple[float, float]:
        """Return (a, b) for key, defaulting to uniform Beta(1,1)."""
        return state.get(key, (1.0, 1.0))

    def extract(self, bayes_state: Dict[str, Dict[str, float]]) -> PriorState:
        """
        Convert a summary's bayes_state dict into a PriorState.
        bayes_state format: {"trap_rate": {"a": ..., "b": ...}, ...}
        """
        return {k: (v["a"], v["b"]) for k, v in bayes_state.items()}

    def describe(self, state: PriorState) -> str:
        """Human-readable summary of loaded priors."""
        if not state:
            return "no prior (first run — starting from Beta(1,1))"
        parts = [
            f"{k}: Beta({a:.2f}, {b:.2f}) → mean={a/(a+b):.3f}"
            for k, (a, b) in sorted(state.items())
        ]
        return " | ".join(parts)
