from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional

from .file_action import FileAction, FileOp


class Reversibility(str, Enum):
    NONE     = "none"    # READ — no state change
    LOW      = "low"     # WRITE new file — trivially undone
    MEDIUM   = "medium"  # WRITE overwrite — content lost but file remains
    HIGH     = "high"    # DELETE — content and file both gone


@dataclass
class CriticalPathResult:
    reversibility:    Reversibility
    file_exists:      bool
    path_depth:       int    # number of path components — deeper = harder to audit
    content_size:     int    # bytes for WRITE; 0 for READ/DELETE
    side_effects:     list   # list of human-readable side-effect strings
    p_irreversible:   float  # 0..1 probability estimate of irreversible outcome


def reversibility_profile(
    action: FileAction,
    sandbox_root: Path,
) -> CriticalPathResult:
    """
    Static analysis of how reversible the proposed action is.

    This is not Monte Carlo — file operations are deterministic.
    Risk comes from content loss and path ambiguity, not stochastic dynamics.
    """
    path = Path(action.path)
    # Resolve relative to sandbox for existence check
    if not path.is_absolute():
        resolved = (sandbox_root / path).resolve()
    else:
        resolved = path.resolve()

    file_exists   = resolved.exists() and resolved.is_file()
    path_depth    = len(resolved.parts)
    content_size  = len(action.content.encode()) if action.content else 0
    side_effects: list = []

    if action.op == FileOp.DELETE:
        rev = Reversibility.HIGH
        p   = 0.95
        side_effects.append("File and all contents permanently removed")
        if file_exists:
            side_effects.append(f"Target exists — deletion is real, not a no-op")
        else:
            side_effects.append("Target does NOT exist — delete is a no-op (low risk)")
            p = 0.05

    elif action.op == FileOp.WRITE:
        if file_exists:
            rev = Reversibility.MEDIUM
            p   = 0.55
            side_effects.append("Existing file will be overwritten — original content lost")
            if content_size > 10_000:
                side_effects.append(f"Large write ({content_size} bytes) increases corruption risk")
        else:
            rev = Reversibility.LOW
            p   = 0.10
            side_effects.append("New file will be created — easily deleted if wrong")
        if content_size == 0:
            side_effects.append("Empty write — will truncate existing content")
            p = max(p, 0.40)

    elif action.op == FileOp.READ:
        rev = Reversibility.NONE
        p   = 0.02
        side_effects.append("Read-only — no filesystem mutation")

    else:  # DONE
        rev = Reversibility.NONE
        p   = 0.0

    return CriticalPathResult(
        reversibility=rev,
        file_exists=file_exists,
        path_depth=path_depth,
        content_size=content_size,
        side_effects=side_effects,
        p_irreversible=p,
    )
