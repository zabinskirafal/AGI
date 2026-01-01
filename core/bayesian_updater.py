class BayesianUpdate:
    """
    Incremental learning module. Updates internal priors based on 
    observed outcomes to refine the model's world-view.
    """
    def update_beliefs(self, prior, likelihood, evidence):
        # P(H|E) = (P(E|H) * P(H)) / P(E)
        posterior = (likelihood * prior) / evidence
        return posterior
