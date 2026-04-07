from dataclasses import dataclass, field
from enum import Enum


class CBState(Enum):
    OK   = "ok"
    WARN = "warn"
    SLOW = "slow"
    STOP = "stop"


@dataclass
class CircuitBreakerConfig:
    warn_rpn:          int = 1800
    slow_rpn:          int = 2200
    stop_rpn:          int = 2600
    # Session-level escalation: consecutive high-RPN proposals
    consecutive_warn_for_slow: int = 3   # 3 WARN → SLOW
    consecutive_slow_for_stop: int = 2   # 2 SLOW → STOP


@dataclass
class CircuitBreakerResult:
    state:  CBState
    reason: str


class CircuitBreaker:
    """
    Stateful circuit breaker tracking consecutive risky LLM proposals.

    Per-action: RPN threshold check (same as benchmark pattern).
    Session-level: escalates if LLM repeatedly proposes risky actions,
    even if each individually falls below the stop threshold.
    """
    def __init__(self, config: CircuitBreakerConfig | None = None):
        self.cfg              = config or CircuitBreakerConfig()
        self._consecutive_warn = 0
        self._consecutive_slow = 0

    def evaluate(self, max_rpn: int) -> CircuitBreakerResult:
        # Per-action RPN check
        if max_rpn >= self.cfg.stop_rpn:
            self._reset_counters()
            return CircuitBreakerResult(
                CBState.STOP,
                f"STOP: RPN {max_rpn} ≥ {self.cfg.stop_rpn}",
            )

        if max_rpn >= self.cfg.slow_rpn:
            self._consecutive_warn = 0
            self._consecutive_slow += 1
            if self._consecutive_slow >= self.cfg.consecutive_slow_for_stop:
                return CircuitBreakerResult(
                    CBState.STOP,
                    f"STOP: {self._consecutive_slow} consecutive SLOW proposals",
                )
            return CircuitBreakerResult(
                CBState.SLOW,
                f"SLOW: RPN {max_rpn} ≥ {self.cfg.slow_rpn}",
            )

        if max_rpn >= self.cfg.warn_rpn:
            self._consecutive_slow = 0
            self._consecutive_warn += 1
            if self._consecutive_warn >= self.cfg.consecutive_warn_for_slow:
                return CircuitBreakerResult(
                    CBState.SLOW,
                    f"SLOW: {self._consecutive_warn} consecutive WARN proposals",
                )
            return CircuitBreakerResult(
                CBState.WARN,
                f"WARN: RPN {max_rpn} ≥ {self.cfg.warn_rpn}",
            )

        # Clean proposal — reset consecutive counters
        self._reset_counters()
        return CircuitBreakerResult(CBState.OK, "OK")

    def _reset_counters(self) -> None:
        self._consecutive_warn = 0
        self._consecutive_slow = 0
