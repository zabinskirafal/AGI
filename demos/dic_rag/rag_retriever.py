"""
RAG Retriever
=============
Converts a FileAction (or a plain text query) into a natural-language
query, selects the appropriate domain collection, and retrieves the
top-k most relevant policy chunks.

Domain selection
----------------
When the input is a FileAction the domain is derived from the action type:
    FileOp.*          → "file_ops"   (all current file operations)
    DBAction.*        → "database"   (future)
    NetworkAction.*   → "network"    (future)

When the input is a plain string the retriever fans out across all non-empty
collections, deduplicates by chunk id, and returns the global top-k by score.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from sentence_transformers import SentenceTransformer

from .rag_indexer import get_collection, get_all_collections, EMBED_MODEL

try:
    from ..dic_llm.file_action import FileAction, FileOp
    _HAS_FILE_ACTION = True
except ImportError:
    FileAction = None   # type: ignore
    FileOp     = None   # type: ignore
    _HAS_FILE_ACTION = False


@dataclass
class RetrievedChunk:
    text:    str
    source:  str    # doc stem, e.g. "file_ops_policy"
    section: str    # section heading from the policy doc
    score:   float  # cosine similarity (higher = more relevant)
    domain:  str    # "file_ops", "database", or "network"


# ── Domain detection ──────────────────────────────────────────────────────── #

def _action_to_domain(action) -> str:
    """
    Derive the policy domain from the action type.

    All current FileAction ops (READ, WRITE, DELETE, DONE) map to "file_ops".
    Future action types are detected by class name convention.
    """
    if _HAS_FILE_ACTION and isinstance(action, FileAction):
        return "file_ops"

    # Convention-based fallback for future action types
    cls = type(action).__name__.lower()
    if any(kw in cls for kw in ("db", "database", "sql", "query")):
        return "database"
    if any(kw in cls for kw in ("network", "http", "request", "api", "webhook")):
        return "network"

    return "file_ops"   # safe default


# ── Query builder ─────────────────────────────────────────────────────────── #

def _action_to_query(action) -> str:
    """
    Build a short natural-language retrieval query from an action.
    Example: DELETE file users.csv cleanup
    """
    parts = [action.op.value.upper(), "file", Path(action.path).name]
    if getattr(action, "reason", None):
        parts.append(action.reason)
    return " ".join(parts)


# ── Retriever ─────────────────────────────────────────────────────────────── #

class RAGRetriever:
    """
    Retrieves the most relevant policy chunks for a proposed action.

    On first use the retriever loads all domain collections from Chroma
    (building any that are missing) and caches them.

    Parameters
    ----------
    top_k : int
        Number of chunks to return per query (default 3).
    min_score : float
        Minimum cosine similarity required to include a chunk (default 0.0).
    """

    def __init__(self, top_k: int = 3, min_score: float = 0.0) -> None:
        self.top_k     = top_k
        self.min_score = min_score
        self._model    = SentenceTransformer(EMBED_MODEL)
        # Loaded lazily by _ensure_collections()
        self._collections: dict | None = None

    # ── Collection access ─────────────────────────────────────────────── #

    def _ensure_collections(self) -> dict:
        if self._collections is None:
            self._collections = get_all_collections()
        return self._collections

    @property
    def domains(self) -> list[str]:
        """Domains with at least one indexed chunk."""
        return list(self._ensure_collections().keys())

    # ── Query ─────────────────────────────────────────────────────────── #

    def query(
        self,
        action_or_text,
        domain: str | None = None,
    ) -> list[RetrievedChunk]:
        """
        Retrieve relevant policy chunks.

        Parameters
        ----------
        action_or_text : FileAction | str
            A FileAction (domain auto-detected, query built from op+path+reason)
            or a plain string query (all domains searched, merged by score).
        domain : str | None
            Override the auto-detected domain.  "all" fans out across every
            collection regardless of action type.

        Returns
        -------
        list[RetrievedChunk]
            Ordered by descending cosine similarity, length ≤ top_k.
        """
        cols = self._ensure_collections()

        if isinstance(action_or_text, str):
            query_text      = action_or_text
            selected_domain = domain or "all"
        else:
            query_text      = _action_to_query(action_or_text)
            selected_domain = domain or _action_to_domain(action_or_text)

        embedding = self._model.encode(query_text).tolist()

        if selected_domain == "all":
            return self._query_all(cols, embedding)
        else:
            col = cols.get(selected_domain)
            if col is None:
                # Domain collection missing — fall back to all
                return self._query_all(cols, embedding)
            return self._query_one(col, embedding, selected_domain)

    # ── Internal helpers ──────────────────────────────────────────────── #

    def _query_one(
        self,
        col,
        embedding: list,
        domain: str,
    ) -> list[RetrievedChunk]:
        n = min(self.top_k, col.count())
        if n == 0:
            return []

        results   = col.query(
            query_embeddings=[embedding],
            n_results=n,
            include=["documents", "metadatas", "distances"],
        )
        return self._parse(results, domain)

    def _query_all(
        self,
        cols: dict,
        embedding: list,
    ) -> list[RetrievedChunk]:
        """Fan out to all collections, merge by score, deduplicate, return top-k."""
        seen_ids: set[str] = set()
        all_chunks: list[RetrievedChunk] = []

        for domain, col in cols.items():
            # Fetch more per domain then trim after merge
            n = min(self.top_k + 2, col.count())
            if n == 0:
                continue
            results = col.query(
                query_embeddings=[embedding],
                n_results=n,
                include=["documents", "metadatas", "distances"],
            )
            for chunk in self._parse(results, domain):
                key = f"{chunk.source}::{chunk.section}"
                if key not in seen_ids:
                    seen_ids.add(key)
                    all_chunks.append(chunk)

        all_chunks.sort(key=lambda c: c.score, reverse=True)
        return all_chunks[: self.top_k]

    def _parse(self, results: dict, domain: str) -> list[RetrievedChunk]:
        chunks: list[RetrievedChunk] = []
        docs      = results["documents"][0]
        metas     = results["metadatas"][0]
        distances = results["distances"][0]

        for doc, meta, dist in zip(docs, metas, distances):
            score = round(1.0 - dist / 2.0, 4)
            if score >= self.min_score:
                chunks.append(RetrievedChunk(
                    text=doc,
                    source=meta.get("source", ""),
                    section=meta.get("section", ""),
                    score=score,
                    domain=meta.get("domain", domain),
                ))
        return chunks
