"""
agi_pragma.integrations.llamaindex
====================================
Wraps DICGovernor as a LlamaIndex tool guard.

Every file-related tool call is intercepted at ``acall()`` / ``call()``
and evaluated through the full 7-stage DIC pipeline before the underlying
function executes.  Blocked calls return a ``ToolOutput`` whose content is
a plain-text block message — the agent sees it as a tool result and re-plans
without any additional wiring.

Requires:
    pip install "agi-pragma[llamaindex]"   # or: pip install llama-index

Usage
-----
from llama_index.core.tools import FunctionTool
from agi_pragma.integrations.llamaindex import dic_wrap_tools

write_tool  = FunctionTool.from_defaults(fn=write_file,  name="write_file")
delete_tool = FunctionTool.from_defaults(fn=delete_file, name="delete_file")

safe_tools = dic_wrap_tools([write_tool, delete_tool])

agent = ReActAgent(tools=safe_tools, llm=llm)
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

# ── lazy imports ──────────────────────────────────────────────────────────── #
try:
    from llama_index.core.tools import AsyncBaseTool, ToolOutput
    from llama_index.core.tools.types import BaseTool, ToolMetadata
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "llama-index-core is required for the LlamaIndex integration.\n"
        "Install it with:  pip install llama-index-core"
    ) from exc

# ── internal imports ─────────────────────────────────────────────────────── #
from demos.dic_llm.dic_governor import DICGovernor
from demos.dic_llm.file_action import FileAction, FileOp


# --------------------------------------------------------------------------- #
#  Tool-name → FileOp mapping                                                  #
# --------------------------------------------------------------------------- #

_TOOL_NAME_MAP: Dict[str, FileOp] = {
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


def _extract_path(kwargs: Dict[str, Any]) -> str:
    for key in _PATH_KEYS:
        if key in kwargs:
            return str(kwargs[key])
    return "unknown"


def _extract_content(kwargs: Dict[str, Any]) -> Optional[str]:
    for key in _CONTENT_KEYS:
        if key in kwargs:
            return str(kwargs[key])
    return None


def _kwargs_to_action(tool_name: str, kwargs: Dict[str, Any]) -> Optional[FileAction]:
    """Map tool name + kwargs to a FileAction. Returns None for non-file tools."""
    op = _TOOL_NAME_MAP.get(tool_name.lower())
    if op is None:
        return None
    return FileAction(
        op=op,
        path=_extract_path(kwargs),
        content=_extract_content(kwargs),
        reason=str(kwargs.get("reason", f"llama-index tool call: {tool_name}")),
    )


# --------------------------------------------------------------------------- #
#  DICDecision serialisation                                                    #
# --------------------------------------------------------------------------- #

def _decision_summary(decision) -> Dict[str, Any]:
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


def _block_output(tool_name: str, decision, kwargs: Dict[str, Any]) -> ToolOutput:
    """Build a ToolOutput that signals a DIC block to the agent."""
    msg = (
        f"[DIC BLOCKED] {decision.block_reason}  "
        f"(RPN={decision.max_rpn}, "
        f"threshold={decision.circuit_breaker.reason.split('≥')[-1].strip() if '≥' in (decision.block_reason or '') else 'see stage_log'}, "
        f"reversibility={decision.critical_path.reversibility.value})"
    )
    return ToolOutput(
        content=msg,
        tool_name=tool_name,
        raw_input={"kwargs": kwargs},
        raw_output=msg,
        is_error=False,   # not a code error — the agent should re-plan, not crash
    )


# --------------------------------------------------------------------------- #
#  DICWrappedTool                                                               #
# --------------------------------------------------------------------------- #

class DICWrappedTool(AsyncBaseTool):
    """
    LlamaIndex ``AsyncBaseTool`` that guards any existing tool with DIC.

    Passes ``isinstance(tool, AsyncBaseTool)`` and ``isinstance(tool, BaseTool)``
    checks.  Exposes the identical ``.metadata`` (name, description, fn_schema)
    so the LLM receives the same function schema as the original tool.

    Parameters
    ----------
    tool : BaseTool
        The original tool to wrap.
    governor : DICGovernor | None
        Shared governor instance.  A fresh one is created when None.
    """

    def __init__(
        self,
        tool: BaseTool,
        governor: Optional[DICGovernor] = None,
    ) -> None:
        self._wrapped  = tool
        self._governor = governor or DICGovernor()
        self._last_decision: Optional[Dict[str, Any]] = None

    # ------------------------------------------------------------------ #
    #  BaseTool interface                                                   #
    # ------------------------------------------------------------------ #

    @property
    def metadata(self) -> ToolMetadata:
        """Proxy — identical schema presented to the LLM."""
        return self._wrapped.metadata

    # ------------------------------------------------------------------ #
    #  Sync call — DIC check then delegate                                 #
    # ------------------------------------------------------------------ #

    def call(self, *args: Any, **kwargs: Any) -> ToolOutput:
        """Sync interception point."""
        tool_name = self.metadata.get_name()
        action    = _kwargs_to_action(tool_name, kwargs)

        if action is not None:
            decision = self._governor.evaluate(action)
            self._last_decision = _decision_summary(decision)
            if not decision.approved:
                return _block_output(tool_name, decision, kwargs)

        # Approved or non-file tool
        return self._wrapped.call(*args, **kwargs)  # type: ignore[arg-type]

    # ------------------------------------------------------------------ #
    #  Async call — DIC check then delegate                                #
    # ------------------------------------------------------------------ #

    async def acall(self, *args: Any, **kwargs: Any) -> ToolOutput:
        """Async interception point — called by LlamaIndex agents."""
        tool_name = self.metadata.get_name()
        action    = _kwargs_to_action(tool_name, kwargs)

        if action is not None:
            decision = self._governor.evaluate(action)
            self._last_decision = _decision_summary(decision)
            if not decision.approved:
                return _block_output(tool_name, decision, kwargs)

        # Approved or non-file tool
        return await self._wrapped.acall(*args, **kwargs)  # type: ignore[arg-type]

    # ------------------------------------------------------------------ #
    #  Convenience                                                         #
    # ------------------------------------------------------------------ #

    @property
    def last_decision(self) -> Optional[Dict[str, Any]]:
        """Full DIC audit trace for the most recent call, or None."""
        return self._last_decision


# --------------------------------------------------------------------------- #
#  Factory helpers                                                              #
# --------------------------------------------------------------------------- #

def dic_wrap_tool(
    tool: BaseTool,
    governor: Optional[DICGovernor] = None,
) -> DICWrappedTool:
    """
    Wrap a single LlamaIndex tool with DIC evaluation.

    Parameters
    ----------
    tool : BaseTool
        The original tool.
    governor : DICGovernor | None
        Pass an existing governor to share circuit-breaker state.
        A fresh governor is created when None.

    Returns
    -------
    DICWrappedTool
        Drop-in replacement for the original tool.
    """
    return DICWrappedTool(tool, governor)


def dic_wrap_tools(
    tools: Sequence[BaseTool],
    governor: Optional[DICGovernor] = None,
) -> List[DICWrappedTool]:
    """
    Wrap a list of LlamaIndex tools, sharing a single DICGovernor.

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
    >>> agent = ReActAgent(tools=safe_tools, llm=llm)
    """
    shared = governor or DICGovernor()
    return [DICWrappedTool(t, shared) for t in tools]
