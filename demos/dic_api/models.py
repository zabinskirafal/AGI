from typing import Any, Dict, List, Optional
from pydantic import BaseModel, field_validator


# ── Request ──────────────────────────────────────────────────────────── #

class EvaluateRequest(BaseModel):
    """
    A proposed file operation from an LLM or calling system.
    DIC will evaluate it through the full 7-stage pipeline.
    """
    op:      str            # "read" | "write" | "delete" | "done"
    path:    str
    content: Optional[str] = None   # required for write; null for read/delete
    reason:  str

    @field_validator("op")
    @classmethod
    def op_must_be_valid(cls, v: str) -> str:
        allowed = {"read", "write", "delete", "done"}
        if v.lower() not in allowed:
            raise ValueError(f"op must be one of {allowed}, got {v!r}")
        return v.lower()

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "op": "write",
                    "path": "notes.txt",
                    "content": "# Notes\n\n- Item 1\n- Item 2\n",
                    "reason": "Create a notes file for the project",
                },
                {
                    "op": "delete",
                    "path": "temp.txt",
                    "content": None,
                    "reason": "Clean up temporary file",
                },
            ]
        }
    }


# ── Response sub-models ───────────────────────────────────────────────── #

class FMEAItemOut(BaseModel):
    failure_mode:  str
    severity:      int
    occurrence:    int
    detection:     int
    reversibility: int
    rpn:           int


class CriticalPathOut(BaseModel):
    reversibility:  str
    file_exists:    bool
    path_depth:     int
    content_size:   int
    side_effects:   List[str]
    p_irreversible: float


class CircuitBreakerOut(BaseModel):
    state:  str   # "ok" | "warn" | "slow" | "stop"
    reason: str


# ── Response ──────────────────────────────────────────────────────────── #

class EvaluateResponse(BaseModel):
    """Full DIC decision with audit trace for every stage."""
    approved:        bool
    block_reason:    Optional[str]
    max_rpn:         int
    utility:         float
    critical_path:   CriticalPathOut
    fmea:            Dict[str, FMEAItemOut]
    circuit_breaker: CircuitBreakerOut
    bayes:           Dict[str, float]
    stage_log:       List[Dict[str, Any]]


class GovernorState(BaseModel):
    """Current session state of the DIC governor."""
    rpn_threshold:        int
    llm_risk_mean:        float
    llm_risk_beta:        str
    circuit_breaker_warn: int
    circuit_breaker_slow: int
    circuit_breaker_stop: int
    consecutive_warn:     int
    consecutive_slow:     int
    steps_evaluated:      int


class ResetResponse(BaseModel):
    message: str
    state:   GovernorState
