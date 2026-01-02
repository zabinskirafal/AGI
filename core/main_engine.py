from core.decision_tree import DecisionTree
from core.critical_path_analyzer import CriticalPathAnalyzer
from core.fmea_engine import FMEAEngine
from core.circuit_breaker import CircuitBreaker
from core.bayesian_updater import BayesianUpdater

class PragmaMainEngine:
    """
    The central orchestration engine for AGI Pragma.
    Integrates Reasoning, Risk Assessment (FMEA), and Safety Gates.
    """
    def __init__(self):
        self.tree = DecisionTree()
        self.cpa = CriticalPathAnalyzer()
        self.fmea = FMEAEngine()
        self.breaker = CircuitBreaker(rpn_threshold=120)
        self.bayos = BayesianUpdater()

    def run_decision_cycle(self, objective, context):
        print(f"--- Starting Decision Cycle: {objective} ---")

        # 1. Branching: Generate possible action paths
        paths = self.tree.generate_paths(objective, context)
        
        best_action = None
        
        for action in paths:
            # 2. Critical Path Analysis
            # We treat the 'paths' as a temporary execution graph
            is_critical = self.cpa.is_on_critical_path(action['id'], paths)
            
            # 3. FMEA Risk Assessment
            # This calculates S x O x D based on critical path data
            risk_assessment = self.fmea.calculate_rpn(action, paths)
            rpn = risk_assessment['rpn']
            
            print(f"Action: {action['name']} | RPN: {rpn}")

            # 4. Cognitive Circuit Breaker (The Stop-Loss)
            validation = self.breaker.validate(risk_assessment)
            
            if validation['status'] == "HALTED":
                print(f"⚠️ [CIRCUIT BREAKER] {validation['reason']}")
                continue  # Skip this dangerous path

            # 5. Execution & Bayesian Update
            # If the path passed the safety gate, we update our world model
            self.bayos.update_beliefs(action, context)
            best_action = action
            break 

        return best_action

# Example usage
if __name__ == "__main__":
    engine = PragmaMainEngine()
    engine.run_decision_cycle("Optimize supply chain", {"budget": 10000})
