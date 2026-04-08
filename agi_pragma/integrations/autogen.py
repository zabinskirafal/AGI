"""
agi_pragma.integrations.autogen
================================
Wraps DICGovernor as an AutoGen tool validator.

Every file-related tool call is intercepted at ``run_json()`` and evaluated
through the full 7-stage DIC pipeline before execution.  Blocked calls return
a plain-text block message instead of executing — the LLM sees it as a tool
result and can re-plan.

Requires:
    pip install "agi-pragma[autogen]"   # or: pip install pyautogen

Usage
-----
from autogen_core.tools import FunctionTool
from agi_pragma.integrations.autogen import dic_wrap_tools

# your original tools
write_tool  = FunctionTool(write_file,  description="Write a file")
delete_tool = FunctionTool(delete_file, description="Delete a file")

# wrap — every call goes through DIC before executing
safe_write, safe_delete = dic_wrap_tools([write_tool, delete_tool])

agent = AssistantAgent(
    name="assistant",
    model_client=model_client,
    tools=[safe_write, safe_delete],
)
"""

from __future__ import annotations

from typing import Any, List, Mapping, Optional, Sequence

# ── lazy imports — fail with a clear message ─────────────────────────────── #
try:
    from autogen_core import CancellationToken
    from autogen_core.tools import BaseTool
    from pydantic import BaseModel
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "pyautogen is required for the AutoGen integration.\n"
        "Install it with:  pip install pyautogen"
    ) from exc

# ── internal imports ─────────────────────────────────────────────────────── #
from demos.dic_llm.dic_governor import DICGovernor
from demos.dic_llm.file_action import FileAction, FileOp


# --------------------------------------------------------------------------- #
#  Tool-name → FileOp mapping (same conventions as LangGraph integration)      #
# --------------------------------------------------------------------------- #

_TOOL_NAME_MAP: dict[str, FileOp] = {
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

_PATH_KEYS    = ("path", "file_path", "filename", "name", "filepath")
_CONTENT_KEYS = ("content", "text", "data", "body")


def _extract_path(args: Mapping[str, Any]) -> str:
    for key in _PATH_KEYS:
        if key in args:
            return str(args[key])
    return "unknown"


def _extract_content(args: Mapping[str, Any]) -> Optional[str]:
    for key in _CONTENT_KEYS:
        if key in args:
            return str(args[key])
    return None


def _args_to_action(tool_name: str, args: Mapping[str, Any]) -> Optional[FileAction]:
    """Map tool name + args dict to a FileAction.  Returns None for non-file tools."""
    op = _TOOL_NAME_MAP.get(tool_name.lower())
    if op is None:
        return None
    return FileAction(
        op=op,
        path=_extract_path(args),
        content=_extract_content(args),
        reason=str(args.get("reason", f"autogen tool call: {tool_name}")),
    )


# --------------------------------------------------------------------------- #
#  DICDecision serialisation helper                                             #
# --------------------------------------------------------------------------- #

def _decision_summary(decision) -> dict[str, Any]:
    cp = decision.critical_path
    return {
        "approved":     decision.approved,
        "block_reason": decision.block_reason,
        "max_rpn":      decision.max_rpn,
        "utility":      decision.utility,
        "critical_path": {
            "reversibility":  cp.reversibility.value,
            "file_exists":    cp.file_exists,
            "p_irreversible": cp.p_irreversible,
        },
        "circuit_breaker": {
            "state":  decision.circuit_breaker.state.value,
            "reason": decision.circuit_breaker.reason,
        },
        "bayes":     decision.bayes,
        "stage_log": decision.stage_log,
    }


# --------------------------------------------------------------------------- #
#  DICWrappedTool                                                               #
# --------------------------------------------------------------------------- #

class DICWrappedTool(BaseTool[BaseModel, Any]):
    """
    AutoGen ``BaseTool`` subclass that guards any existing tool with DIC.

    Drop-in replacement: passes ``isinstance(tool, BaseTool)`` checks,
    exposes identical ``.schema``, ``.name``, and ``.description``.

    Parameters
    ----------
    tool : BaseTool
        The original tool to wrap.
    governor : DICGovernor | None
        Shared governor instance.  A fresh one is created when None.
    """

    def __init__(
        self,
        tool: "BaseTool[Any, Any]",
        governor: Optional[DICGovernor] = None,
    ) -> None:
        super().__init__(
            args_type=tool.args_type(),
            return_type=str,
            name=tool.name,
            description=tool.description,
        )
        self._wrapped  = tool
        self._governor = governor or DICGovernor()

    # ------------------------------------------------------------------ #
    #  Required abstract method — delegates to wrapped tool               #
    # ------------------------------------------------------------------ #

    async def run(
        self,
        args: BaseModel,
        cancellation_token: CancellationToken,
    ) -> Any:
        """Delegate execution to the wrapped tool."""
        return await self._wrapped.run_json(
            args.model_dump(), cancellation_token
        )

    # ------------------------------------------------------------------ #
    #  Interception point                                                  #
    # ------------------------------------------------------------------ #

    async def run_json(
        self,
        args: Mapping[str, Any],
        cancellation_token: CancellationToken,
        call_id: str | None = None,
    ) -> Any:
        """
        Evaluate the tool call through DIC before execution.

        - Non-file tools pass through immediately.
        - Approved file operations are forwarded to the original tool.
        - Blocked operations return a plain-text block message so the
          LLM can see it as a tool result and re-plan accordingly.
        """
        action = _args_to_action(self.name, args)

        if action is None:
            # Not a file operation — pass through without evaluation
            return await self._wrapped.run_json(args, cancellation_token, call_id=call_id)

        decision = self._governor.evaluate(action)
        self._last_decision = _decision_summary(decision)

        if not decision.approved:
            return (
                f"[DIC BLOCKED] {decision.block_reason}  "
                f"(RPN={decision.max_rpn}, "
                f"threshold={self._governor.rpn_threshold}, "
                f"reversibility={decision.critical_path.reversibility.value})"
            )

        return await self._wrapped.run_json(args, cancellation_token, call_id=call_id)

    # ------------------------------------------------------------------ #
    #  Convenience                                                         #
    # ------------------------------------------------------------------ #

    @property
    def last_decision(self) -> Optional[dict[str, Any]]:
        """The DIC audit trace for the most recent call, or None."""
        return getattr(self, "_last_decision", None)


# --------------------------------------------------------------------------- #
#  Factory helpers                                                              #
# --------------------------------------------------------------------------- #

def dic_wrap_tool(
    tool: "BaseTool[Any, Any]",
    governor: Optional[DICGovernor] = None,
) -> DICWrappedTool:
    """
    Wrap a single AutoGen tool with DIC evaluation.

    Parameters
    ----------
    tool : BaseTool
        The original tool.
    governor : DICGovernor | None
        Pass an existing governor to share circuit-breaker state across tools.
        A fresh governor is created when None.

    Returns
    -------
    DICWrappedTool
        Drop-in replacement for the original tool.
    """
    return DICWrappedTool(tool, governor)


def dic_wrap_tools(
    tools: Sequence["BaseTool[Any, Any]"],
    governor: Optional[DICGovernor] = None,
) -> List[DICWrappedTool]:
    """
    Wrap a list of AutoGen tools, sharing a single DICGovernor.

    Sharing the governor is important: the circuit breaker escalates
    across all tool calls in the session, not per-tool.

    Parameters
    ----------
    tools : Sequence[BaseTool]
        Original tools to protect.
    governor : DICGovernor | None
        Shared governor.  One is created if not provided.

    Returns
    -------
    List[DICWrappedTool]
        Same-length list of wrapped tools, same order.

    Example
    -------
    >>> safe_tools = dic_wrap_tools([write_tool, delete_tool, read_tool])
    >>> agent = AssistantAgent("assistant", model_client=client, tools=safe_tools)
    """
    shared = governor or DICGovernor()
    return [DICWrappedTool(t, shared) for t in tools]
