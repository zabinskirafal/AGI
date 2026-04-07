"""
DIC Governor — REST API (file operations domain)
=================================================
Wraps the DIC pipeline as a stateful HTTP service.
The governor instance persists across requests, so the Beta tracker
and circuit breaker accumulate session state just as they do in the
interactive demo.

Routes:
    POST /evaluate          Evaluate a proposed file action
    GET  /state             Current governor state (belief, circuit breaker)
    POST /reset             Reset governor to fresh state
    GET  /health            Liveness check
    GET  /                  API info + quick reference

Run:
    uvicorn demos.dic_api.main:app --reload --port 8000
    python3 -m demos.dic_api.main
"""

from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from .models import (
    EvaluateRequest, EvaluateResponse,
    FMEAItemOut, CriticalPathOut, CircuitBreakerOut,
    GovernorState, ResetResponse,
)
from demos.dic_llm.file_action  import FileAction, FileOp
from demos.dic_llm.dic_governor import DICGovernor, DICDecision


# ── Governor singleton ────────────────────────────────────────────────── #
# Shared across all requests so tracker state accumulates over the session.

_governor: DICGovernor = DICGovernor()
_steps:    int         = 0


def _fresh_governor() -> DICGovernor:
    return DICGovernor()


# ── App ───────────────────────────────────────────────────────────────── #

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _governor, _steps
    _governor = _fresh_governor()
    _steps    = 0
    yield


app = FastAPI(
    title="DIC Governor API",
    description=(
        "Decision-in-Context (DIC) pipeline as a REST service. "
        "POST a proposed file action; receive an approved/blocked verdict "
        "with a full 7-stage audit trace."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


# ── Helpers ───────────────────────────────────────────────────────────── #

def _to_response(d: DICDecision) -> EvaluateResponse:
    cp = d.critical_path
    cb = d.circuit_breaker
    return EvaluateResponse(
        approved=d.approved,
        block_reason=d.block_reason,
        max_rpn=d.max_rpn,
        utility=d.utility,
        critical_path=CriticalPathOut(
            reversibility=cp.reversibility.value,
            file_exists=cp.file_exists,
            path_depth=cp.path_depth,
            content_size=cp.content_size,
            side_effects=cp.side_effects,
            p_irreversible=cp.p_irreversible,
        ),
        fmea={
            name: FMEAItemOut(**item)
            for name, item in d.fmea.items()
        },
        circuit_breaker=CircuitBreakerOut(
            state=cb.state.value,
            reason=cb.reason,
        ),
        bayes=d.bayes,
        stage_log=d.stage_log,
    )


def _governor_state() -> GovernorState:
    g  = _governor
    cb = g.circuit_breaker
    return GovernorState(
        rpn_threshold=g.rpn_threshold,
        llm_risk_mean=round(g.llm_risk_tracker.mean, 4),
        llm_risk_beta=repr(g.llm_risk_tracker),
        circuit_breaker_warn=cb.cfg.warn_rpn,
        circuit_breaker_slow=cb.cfg.slow_rpn,
        circuit_breaker_stop=cb.cfg.stop_rpn,
        consecutive_warn=cb._consecutive_warn,
        consecutive_slow=cb._consecutive_slow,
        steps_evaluated=_steps,
    )


# ── Routes ────────────────────────────────────────────────────────────── #

@app.get("/", tags=["info"])
def root() -> Dict[str, Any]:
    """API overview and quick reference."""
    return {
        "service": "DIC Governor API — file operations domain",
        "version": "1.0.0",
        "pipeline": [
            "1. Branching      — scope gate (sandbox, path traversal)",
            "2. Critical Path  — reversibility analysis",
            "3. FMEA           — S×O×D×R per failure mode",
            "4. Decision Gate  — block if max_rpn ≥ threshold",
            "5. Circuit Breaker — session escalation on repeated risk",
            "6. Utility        — task progress benefit − risk",
            "7. Belief Update  — Beta tracker for LLM risk rate",
        ],
        "ops":    ["read", "write", "delete", "done"],
        "routes": {
            "POST /evaluate": "Evaluate a proposed file action",
            "GET  /state":    "Current governor session state",
            "POST /reset":    "Reset governor to fresh state",
            "GET  /health":   "Liveness check",
            "GET  /docs":     "Interactive Swagger UI",
        },
        "rpn_threshold": _governor.rpn_threshold,
    }


@app.get("/health", tags=["info"])
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/state", response_model=GovernorState, tags=["governor"])
def get_state() -> GovernorState:
    """Return current session state of the DIC governor."""
    return _governor_state()


@app.post("/reset", response_model=ResetResponse, tags=["governor"])
def reset_governor() -> ResetResponse:
    """
    Reset the governor to a fresh state.
    Clears the Beta tracker and circuit breaker counters.
    """
    global _governor, _steps
    _governor = _fresh_governor()
    _steps    = 0
    return ResetResponse(
        message="Governor reset to initial state.",
        state=_governor_state(),
    )


@app.post("/evaluate", response_model=EvaluateResponse, tags=["evaluate"])
def evaluate(body: EvaluateRequest) -> EvaluateResponse:
    """
    Evaluate a proposed file action through the full 7-stage DIC pipeline.

    Returns an approved/blocked verdict with a complete audit trace
    showing what each stage decided and why.

    The governor is **stateful**: the Beta risk tracker and circuit breaker
    accumulate across calls within a session. Use POST /reset to start fresh.
    """
    global _steps

    try:
        op = FileOp(body.op)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Unknown op: {body.op!r}")

    action   = FileAction(op=op, path=body.path, content=body.content, reason=body.reason)
    decision = _governor.evaluate(action)
    _steps  += 1

    return _to_response(decision)


# ── Error handler ─────────────────────────────────────────────────────── #

@app.exception_handler(Exception)
async def generic_error(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"error": type(exc).__name__, "detail": str(exc)},
    )


# ── Entry point ───────────────────────────────────────────────────────── #

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("demos.dic_api.main:app", host="0.0.0.0", port=8000, reload=True)
