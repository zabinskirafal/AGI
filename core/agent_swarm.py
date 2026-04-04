import numpy as np
from .main_engine import PragmaEngine

class SwarmController:
    """
    Manages coordination and strategic isolation of AGI agents.
    Forces agents to solve problems independently during high-chaos events.
    """
    def __init__(self, agent_count=5):
        self.agents = [PragmaEngine() for _ in range(agent_count)]
        self.is_connected = True

    def evaluate_chaos_threshold(self, chaos_level):
        """
        If chaos in the sandbox is too high (>0.8), force strategic decoupling.
        """
        if chaos_level > 0.8:
            self.trigger_decoupling()
        else:
            self.synchronize_swarm()

    def trigger_decoupling(self):
        """Forces agents into isolation to develop unique local solutions."""
        self.is_connected = False
        print("[Swarm] Strategic Decoupling Active: Agents operating in independent silos.")

    def synchronize_swarm(self):
        """Merges isolated findings back using Bayesian Consensus."""
        if not self.is_connected:
            print("[Swarm] Re-integration: Merging isolated world-models via Bayesian Consensus.")
            self.is_connected = True
