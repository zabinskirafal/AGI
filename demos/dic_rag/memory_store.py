"""
Memory Store
============
Persists blocked decisions to a JSON file and retrieves similar past
failures to inject into the RAG evaluation pipeline.

Each blocked action is recorded as a MemoryEntry.  On subsequent
evaluations, retrieve_similar() finds entries whose op type and path
pattern match the current action and returns them ordered by relevance.

The memory file is written atomically (write-to-temp then rename) so a
crash during save never produces a corrupt file.

File location: demos/dic_rag/memory.json  (excluded from git)
"""

import json
import os
import tempfile
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


MEMORY_FILE = Path(__file__).parent / "memory.json"

# Maximum entries to keep in the file (oldest pruned first)
MAX_ENTRIES = 200

# Similarity score thresholds for retrieval
_MIN_SCORE = 3   # must reach this to be returned at all
_TOP_K     = 3   # maximum entries returned per query


# ── Data model ───────────────────────────────────────────────────────────── #

@dataclass
class MemoryEntry:
    """
    A record of one blocked decision, stored in memory.json.

    Fields
    ------
    timestamp        : ISO-8601 UTC string
    op               : file operation string ("read", "write", "delete")
    path             : original path string as proposed by the agent
    path_stem        : filename without extension, lower-cased
    path_ext         : file extension including dot, lower-cased (".csv", "")
    block_reason     : the block_reason string from DICDecision
    justification    : list of "Blocked per …" lines from block_justification
    rpn              : max_rpn at the time of blocking
    occurrence_bump  : how much to add to o_base for similar future actions
                       (1 if rpn < 4000, 2 if rpn ≥ 4000)
    """
    timestamp:       str
    op:              str
    path:            str
    path_stem:       str
    path_ext:        str
    block_reason:    str
    justification:   list[str]
    rpn:             int
    occurrence_bump: int


# ── Similarity scoring ────────────────────────────────────────────────────── #

def _similarity(entry: MemoryEntry, op: str, stem: str, ext: str) -> int:
    """
    Rule-based similarity score between a MemoryEntry and a candidate action.

    Points
    ------
    +4  same op type
    +3  same filename stem (exact, lower-cased)
    +2  same file extension
    +1  stem contains one of the other's words (partial)
    """
    score = 0
    if entry.op == op:
        score += 4
    if entry.path_stem == stem:
        score += 3
    elif stem and entry.path_stem and (stem in entry.path_stem or entry.path_stem in stem):
        score += 1
    if entry.path_ext == ext:
        score += 2
    return score


# ── MemoryStore ───────────────────────────────────────────────────────────── #

class MemoryStore:
    """
    Read/write interface for the persistent memory file.

    Parameters
    ----------
    path : Path
        Location of the JSON memory file (default: MEMORY_FILE).
    """

    def __init__(self, path: Path = MEMORY_FILE) -> None:
        self._path = path
        self._entries: list[MemoryEntry] = self._load()

    # ── Public API ─────────────────────────────────────────────────────── #

    def record(
        self,
        op:            str,
        path:          str,
        block_reason:  str,
        justification: list[str],
        rpn:           int,
    ) -> None:
        """
        Save a blocked decision to persistent memory.

        Duplicate suppression: if an identical (op, path, block_reason)
        entry was recorded in the last 10 entries it is not duplicated.
        """
        p = Path(path)
        stem = p.stem.lower()
        ext  = p.suffix.lower()

        # Dedup: skip if the last 10 entries contain the same (op, stem, block_reason)
        for recent in self._entries[-10:]:
            if recent.op == op and recent.path_stem == stem and recent.block_reason == block_reason:
                return

        bump = 2 if rpn >= 4000 else 1
        entry = MemoryEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            op=op,
            path=path,
            path_stem=stem,
            path_ext=ext,
            block_reason=block_reason,
            justification=justification,
            rpn=rpn,
            occurrence_bump=bump,
        )
        self._entries.append(entry)

        # Prune if over limit
        if len(self._entries) > MAX_ENTRIES:
            self._entries = self._entries[-MAX_ENTRIES:]

        self._save()

    def retrieve_similar(self, op: str, path: str, top_k: int = _TOP_K) -> list[MemoryEntry]:
        """
        Return the most similar past failures for the given action,
        ordered by descending similarity score.

        Only entries scoring ≥ _MIN_SCORE are returned.
        """
        p    = Path(path)
        stem = p.stem.lower()
        ext  = p.suffix.lower()

        scored = [
            (e, _similarity(e, op, stem, ext))
            for e in self._entries
        ]
        scored.sort(key=lambda x: x[1], reverse=True)

        return [e for e, s in scored[:top_k] if s >= _MIN_SCORE]

    def count(self) -> int:
        return len(self._entries)

    # ── Persistence ────────────────────────────────────────────────────── #

    def _load(self) -> list[MemoryEntry]:
        if not self._path.exists():
            return []
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
            return [MemoryEntry(**item) for item in raw]
        except Exception:
            # Corrupt file — start fresh rather than crash
            return []

    def _save(self) -> None:
        data = json.dumps([asdict(e) for e in self._entries], indent=2, ensure_ascii=False)
        # Atomic write: write to temp file in same directory, then rename
        fd, tmp = tempfile.mkstemp(dir=self._path.parent, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(data)
            os.replace(tmp, self._path)
        except Exception:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise
