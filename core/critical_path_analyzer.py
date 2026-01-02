# core/critical_path_analyzer.py

class CriticalPathAnalyzer:
    """
    Identifies mission-critical nodes in the decision tree.
    """
    def is_on_critical_path(self, node_id, execution_graph):
        # Logic to determine if a failure at this node 
        # stops the entire objective.
        pass

# core/fmea_risk_engine.py (Updated logic)

from core.critical_path_analyzer import CriticalPathAnalyzer

class FMEARiskEngine:
    def calculate_severity(self, action, graph):
        cpa = CriticalPathAnalyzer()
        
        if cpa.is_on_critical_path(action.id, graph):
            return 10  # Maximum Severity: Critical Path Failure
        return 3       # Low Severity: Non-critical delay
