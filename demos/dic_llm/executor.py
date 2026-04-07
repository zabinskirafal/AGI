from pathlib import Path
from typing import Optional

from .file_action import FileAction, FileOp

SANDBOX_ROOT = Path(__file__).parent / "sandbox"


class Executor:
    """
    Executes DIC-approved file operations, strictly within sandbox_root.
    Raises if called for a path outside the sandbox — this is a hard guard,
    separate from DIC's scope check, so defence is layered.
    """

    def __init__(self, sandbox_root: Path = SANDBOX_ROOT):
        self.sandbox_root = sandbox_root.resolve()
        self.sandbox_root.mkdir(parents=True, exist_ok=True)

    def execute(self, action: FileAction) -> Optional[str]:
        """
        Execute the action. Returns file contents for READ; None otherwise.
        Raises ValueError if path escapes sandbox (should never reach here
        after DIC approval, but belt-and-suspenders).
        """
        if action.op == FileOp.DONE:
            return None

        resolved = self._safe_resolve(action.path)

        if action.op == FileOp.READ:
            return self._read(resolved)
        elif action.op == FileOp.WRITE:
            return self._write(resolved, action.content or "")
        elif action.op == FileOp.DELETE:
            return self._delete(resolved)

        raise ValueError(f"Unknown op: {action.op}")

    # ------------------------------------------------------------------ #
    #  File operations                                                     #
    # ------------------------------------------------------------------ #

    def _read(self, path: Path) -> str:
        if not path.exists():
            return "(file does not exist)"
        return path.read_text(encoding="utf-8")

    def _write(self, path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def _delete(self, path: Path) -> None:
        if path.exists():
            path.unlink()

    # ------------------------------------------------------------------ #
    #  Safety                                                              #
    # ------------------------------------------------------------------ #

    def _safe_resolve(self, raw_path: str) -> Path:
        p = Path(raw_path)
        resolved = (self.sandbox_root / p).resolve() if not p.is_absolute() else p.resolve()
        try:
            resolved.relative_to(self.sandbox_root)
        except ValueError:
            raise ValueError(
                f"Executor hard-stop: '{raw_path}' resolves outside sandbox "
                f"({self.sandbox_root}). This should have been caught by DIC."
            )
        return resolved
