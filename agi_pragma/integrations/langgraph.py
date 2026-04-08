"""
agi_pragma.integrations.langgraph
==================================
Wraps DICGovernor as a LangGraph node.

The node intercepts every ToolCall in the last AIMessage and evaluates it
through the full 7-stage DIC pipeline before any tool executor runs.

Requires:
    pip install langgraph langchain-core

Usage
-----
from agi_pragma.integrations.langgraph import DICGuardNode, dic_conditional_edge

guard = DICGuardNode()                  # uses default DICGovernor
graph.add_node("dic_guard", guard)
graph.add_conditional_edges(
    "agent",
    dic_conditional_edge,
    {"approved": "tools", "blocked": "agent"},
)
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, List, Literal, Optional, Sequence

# ── lazy imports — fail with a clear message ─────────────────────────────── #
try:
    from langchain_core.messages import AIMessage, ToolMessage
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "langchain-core is required for the LangGraph integration.\n"
        "Install it with:  pip install langchain-core"
    ) from exc

try:
    from langgraph.graph import END
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "langgraph is required for the LangGraph integration.\n"
        "Install it with:  pip install langgraph"
    ) from exc

# ── internal imports ─────────────────────────────────────────────────────── #
from demos.dic_llm.dic_governor import DICGovernor
from demos.dic_llm.file_action import FileAction, FileOp


# --------------------------------------------------------------------------- #
#  Tool-name → FileOp mapping                                                  #
# --------------------------------------------------------------------------- #

_TOOL_NAME_MAP: Dict[str, FileOp] = {
    # Common LangChain / LangGraph tool naming conventions
    "read_file":    FileOp.READ,
    "read":         FileOp.READ,
    "write_file":   FileOp.WRITE,
    "write":        FileOp.WRITE,
    "create_file":  FileOp.WRITE,
    "delete_file":  FileOp.DELETE,
    "delete":       FileOp.DELETE,
    "remove_file":  FileOp.DELETE,
    "remove":       FileOp.DELETE,
}

# Argument name aliases for path and content across different tool schemas
_PATH_KEYS   = ("path", "file_path", "filename", "name", "filepath")
_CONTENT_KEYS = ("content", "text", "data", "body")


def _extract_path(args: Dict[str, Any]) -> str:
    for key in _PATH_KEYS:
        if key in args:
            return str(args[key])
    return "unknown"


def _extract_content(args: Dict[str, Any]) -> Optional[str]:
    for key in _CONTENT_KEYS:
        if key in args:
            return str(args[key])
    return None


def _tool_call_to_action(tool_call: Dict[str, Any]) -> Optional[FileAction]:
    """
    Convert a LangChain ToolCall dict to a FileAction.

    Returns None if the tool name is not a recognised file operation
    (non-file tools are not subject to DIC evaluation).
    """
    name = tool_call.get("name", "").lower()
    op   = _TOOL_NAME_MAP.get(name)
    if op is None:
        return None

    args    = tool_call.get("args", {}) or {}
    path    = _extract_path(args)
    content = _extract_content(args)
    reason  = args.get("reason", f"tool call: {name}")

    return FileAction(op=op, path=path, content=content, reason=reason)


# --------------------------------------------------------------------------- #
#  DICDecision serialisation helper                                             #
# --------------------------------------------------------------------------- #

def _decision_to_dict(decision, tool_call_id: str) -> Dict[str, Any]:
    cp = decision.critical_path
    return {
        "tool_call_id": tool_call_id,
        "approved":     decision.approved,
        "block_reason": decision.block_reason,
        "max_rpn":      decision.max_rpn,
        "utility":      decision.utility,
        "critical_path": {
            "reversibility":  cp.reversibility.value,
            "file_exists":    cp.file_exists,
            "p_irreversible": cp.p_irreversible,
            "side_effects":   cp.side_effects,
        },
        "fmea":          decision.fmea,
        "circuit_breaker": {
            "state":  decision.circuit_breaker.state.value,
            "reason": decision.circuit_breaker.reason,
        },
        "bayes":      decision.bayes,
        "stage_log":  decision.stage_log,
    }


# --------------------------------------------------------------------------- #
#  DICGuardNode                                                                 #
# --------------------------------------------------------------------------- #

class DICGuardNode:
    """
    LangGraph node that evaluates every file-related ToolCall through DIC.

    State keys written
    ------------------
    ``dic_decisions``       list[dict] — one entry per evaluated tool call,
                            containing the full audit trace.
    ``blocked_tool_calls``  set[str]  — tool_call_id values that were blocked.

    State keys read
    ---------------
    ``messages``  list — last AIMessage is inspected for tool_calls.

    Parameters
    ----------
    governor : DICGovernor | None
        Reuse an existing governor (useful to share circuit-breaker state
        across nodes).  A fresh governor is created when None.
    """

    def __init__(self, governor: Optional[DICGovernor] = None):
        self.governor = governor or DICGovernor()

    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        messages: Sequence = state.get("messages", [])
        if not messages:
            return {}

        # Find the last AIMessage
        last_ai: Optional[AIMessage] = None
        for msg in reversed(messages):
            if isinstance(msg, AIMessage):
                last_ai = msg
                break

        if last_ai is None or not getattr(last_ai, "tool_calls", None):
            return {}

        decisions: List[Dict[str, Any]] = []
        blocked:   set[str]              = set()
        block_messages: List[ToolMessage] = []

        for tc in last_ai.tool_calls:
            tool_id   = tc.get("id", tc.get("name", "unknown"))
            tool_name = tc.get("name", "")

            action = _tool_call_to_action(tc)

            if action is None:
                # Not a file operation — pass through unmodified
                decisions.append({
                    "tool_call_id": tool_id,
                    "approved":     True,
                    "block_reason": None,
                    "note":         f"Non-file tool '{tool_name}' skipped DIC evaluation",
                })
                continue

            decision = self.governor.evaluate(action)
            d = _decision_to_dict(decision, tool_id)
            decisions.append(d)

            if not decision.approved:
                blocked.add(tool_id)
                # Inject a ToolMessage so the LLM understands why it was blocked
                block_messages.append(
                    ToolMessage(
                        content=(
                            f"[DIC BLOCKED] {decision.block_reason}  "
                            f"(RPN={decision.max_rpn}, threshold={self.governor.rpn_threshold})"
                        ),
                        tool_call_id=tool_id,
                    )
                )

        update: Dict[str, Any] = {
            "dic_decisions":      decisions,
            "blocked_tool_calls": blocked,
        }

        if block_messages:
            # Prepend block messages so the LLM can see them before re-planning
            update["messages"] = block_messages

        return update


# --------------------------------------------------------------------------- #
#  Conditional edge helper                                                      #
# --------------------------------------------------------------------------- #

def dic_conditional_edge(
    state: Dict[str, Any],
) -> Literal["approved", "blocked"]:
    """
    Route after the dic_guard node.

    Returns ``"approved"`` when all tool calls passed DIC evaluation,
    ``"blocked"`` when one or more were blocked (so the agent can re-plan).

    Typical usage::

        graph.add_conditional_edges(
            "agent",
            dic_conditional_edge,
            {"approved": "tools", "blocked": "agent"},
        )
    """
    blocked = state.get("blocked_tool_calls", set())
    return "blocked" if blocked else "approved"
