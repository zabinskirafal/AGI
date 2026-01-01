from .decision_tree import DecisionTree
from .tornado_analysis import TornadoAnalysis
from .simulation_engine import MonteCarloSimulation
from .bayesian_updater import BayesianUpdate

def pragma_decision_loop(input_data):
    # 1. Budowa drzewa (Decision Tree)
    tree = DecisionTree(input_data)
    
    # 2. Filtracja istotności (Tornado)
    tornado = TornadoAnalysis(input_data)
    key_drivers = tornado.calculate_sensitivity(input_data)
    
    # 3. Weryfikacja ryzyka (Monte Carlo)
    simulation = MonteCarloSimulation(key_drivers)
    confidence = simulation.run_simulation()
    
    # 4. Uczenie (Bayes) po otrzymaniu wyniku
    # Ten krok następuje po "obserwacji" rzeczywistości
    return confidence
