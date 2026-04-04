from core.critical_path_analyzer import CriticalPathAnalyzer

class FMEAEngine:
    """
    Enhanced FMEA Engine for AGI Pragma.
    Integrates Critical Path Analysis (CPA) to determine decision severity.
    """
    def __init__(self):
        self.cpa = CriticalPathAnalyzer()

    def calculate_rpn(self, action_node, execution_graph):
        """
        Calculates the Risk Priority Number (RPN) based on:
        S (Severity) x O (Occurrence) x D (Detection)
        """
        # 1. SEVERITY (S) - Dynamic assessment based on Critical Path
        # Get node ID whether action_node is a dict or an object
        node_id = action_node.get('id') if isinstance(action_node, dict) else getattr(action_node, 'id', None)
        
        if self.cpa.is_on_critical_path(node_id, execution_graph):
            severity = 10  # Maximum impact if failed
        else:
            severity = 4   # Lower impact on non-critical paths

        # 2. OCCURRENCE (O) - Likelihood of failure (1-10)
        # Defaults to 5 if not provided
        occurrence = action_node.get('failure_probability', 5) if isinstance(action_node, dict) else 5

        # 3. DETECTION (D) - Difficulty of detecting error (1-10)
        # High score means it's a silent failure
        detection = action_node.get('detection_difficulty', 5) if isinstance(action_node, dict) else 5

        rpn = severity * occurrence * detection
        
        return {
            "rpn": rpn,
            "is_critical_path": severity == 10,
            "metrics": {
                "S": severity,
                "O": occurrence,
                "D": detection
            }
        }
