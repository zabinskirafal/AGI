class BetaTracker:
    """
    Beta(a,b) for probability of a binary event.
    mean = a/(a+b)
    """
    def __init__(self, a=1.0, b=1.0):
        self.a = float(a)
        self.b = float(b)

    @property
    def mean(self) -> float:
        return self.a / (self.a + self.b)

    def update(self, event: bool):
        if event:
            self.a += 1.0
        else:
            self.b += 1.0
