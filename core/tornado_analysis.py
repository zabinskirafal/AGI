class TornadoAnalysis:
    """
    Module for identifying high-impact decision variables.
    Calculates sensitivity of outcomes to individual input changes.
    """
    def __init__(self, baseline_state):
        self.baseline = baseline_state

    def calculate_sensitivity(self, variables):
        # Identifies variables that account for the most variance
        # Returns a sorted list of 'Tornado Drivers'
        pass

    def filter_noise(self, threshold=0.8):
        # Prunes variables with low impact on the final decision
        pass
