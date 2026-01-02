class CircuitBreaker:
    """
    Decision-level Stop-Loss mechanism.
    Prevents autonomous execution if the risk profile exceeds the threshold.
    """
    def __init__(self, rpn_threshold=120):
        self.threshold = rpn_threshold

    def validate(self, rpn_result):
        rpn = rpn_result['rpn']
        
        if rpn >= self.threshold:
            return {
                "status": "HALTED",
                "reason": f"RPN {rpn} exceeds safety threshold {self.threshold}",
                "action": "Trigger Deep Reasoning / Request Human Intervention"
            }
        
        return {"status": "PROCEED", "rpn": rpn}
