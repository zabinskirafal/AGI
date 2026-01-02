class FMEAEngine:
    """
    Failure Mode and Effects Analysis (FMEA) Engine for AGI Pragma.
    Calculates the Risk Priority Number (RPN) for proposed agent actions.
    """
    def __init__(self):
        self.severity_map = {
            "financial": 9,
            "data_integrity": 8,
            "system_access": 7,
            "general_query": 2
        }

    def calculate_rpn(self, action_plan):
        # S = Severity (How bad is the failure?)
        s = self._estimate_severity(action_plan)
        
        # O = Occurrence (How likely is the error?)
        o = self._estimate_occurrence(action_plan)
        
        # D = Detection (How hard is it to catch the error before impact?)
        d = self._estimate_detection(action_plan)
        
        rpn = s * o * d
        return {
            "rpn": rpn,
            "metrics": {"severity": s, "occurrence": o, "detection": d}
        }

    def _estimate_severity(self, plan):
        # Logic to map action type to impact level
        return self.severity_map.get(plan.category, 5)

    def _estimate_occurrence(self, plan):
        # Logic based on LLM confidence or historical error rates
        return plan.uncertainty_score * 10 

    def _estimate_detection(self, plan):
        # High score means the error is INVISIBLE (Hidden Failure)
        if not plan.has_monitoring_hook:
            return 9  # Dangerous: Silent failure
        return 3      # Safe: Highly observable
