from core.critical_path_analyzer import CriticalPathAnalyzer

class FMEAEngine:
    """
    Enhanced FMEA Engine for AGI Pragma.
    Integrates Critical Path Analysis to determine Severity.
    """
    def __init__(self):
        self.cpa = CriticalPathAnalyzer()

    def calculate_rpn(self, action_node, execution_graph):
        # 1. SEVERITY (S) - Dynamic assessment based on Critical Path
        # If the action is on the critical path, severity is maximum.
        if self.cpa.is_on_critical_path(action_node, execution_graph):
            severity = 10 
        else:
            severity = 4 # Non-critical path failure has lower impact

        # 2. OCCURRENCE (O) - Likelihood of failure
        occurrence = action_node.get('failure_probability', 5)

        # 3. DETECTION (D) - How likely we are to miss the error
        # High detection score (e.g., 9) means the error is "invisible".
        detection = action_node.get('detection_difficulty', 5)

        rpn = severity * occurrence * detection
        
        return {
            "rpn": rpn,
            "is_critical": severity == 10,
            "breakdown": {"S": severity, "O": occurrence, "D": detection}
        }
