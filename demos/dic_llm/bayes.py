class BetaTracker:
    """
    Beta(a, b) posterior for a binary event probability.
    Used to track how often the LLM proposes high-risk actions.
    mean = a / (a + b)
    """
    def __init__(self, a: float = 1.0, b: float = 1.0):
        self.a = float(a)
        self.b = float(b)

    @property
    def mean(self) -> float:
        return self.a / (self.a + self.b)

    def update(self, risky: bool) -> None:
        if risky:
            self.a += 1.0
        else:
            self.b += 1.0

    def __repr__(self) -> str:
        return f"Beta(a={self.a:.1f}, b={self.b:.1f}, mean={self.mean:.3f})"
