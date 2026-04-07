from dataclasses import dataclass
from enum import Enum
from typing import Optional


class FileOp(str, Enum):
    READ   = "read"
    WRITE  = "write"
    DELETE = "delete"
    DONE   = "done"   # LLM signals task complete — no file op


@dataclass
class FileAction:
    op:      FileOp
    path:    str            # relative or absolute path proposed by LLM
    content: Optional[str]  # payload for WRITE; None for READ/DELETE
    reason:  str            # LLM's stated justification

    def __str__(self) -> str:
        extra = f"  ({len(self.content)} chars)" if self.content else ""
        return f"{self.op.value.upper():6s}  {self.path}{extra}  — {self.reason}"
