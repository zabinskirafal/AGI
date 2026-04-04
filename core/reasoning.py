# pragma/core/reasoning.py

from pragma.safety.fmea_engine import FMEAEngine
from pragma.safety.circuit_breaker import CircuitBreaker

def process_decision(action_plan):
    fmea = FMEAEngine()
    guard = CircuitBreaker(rpn_threshold=120)

    # Calculate RPN BEFORE execution
    risk_profile = fmea.calculate_rpn(action_plan)
    
    # Check "Stop-Loss"
    validation = guard.validate(risk_profile)
    
    if validation["status"] == "HALTED":
        return trigger_safety_protocol(validation["reason"])
    
    return execute_action(action_plan)
