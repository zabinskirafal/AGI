"""
RAG Retriever
=============
Converts a FileAction (or a plain text query) into a natural-language
query, embeds it, and retrieves the top-k most relevant policy chunks
from the Chroma collection.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from sentence_transformers import SentenceTransformer

from .rag_indexer import get_collection, EMBED_MODEL

# Import FileAction lazily to avoid circular deps when used standalone
try:
    from ..dic_llm.file_action import FileAction
except ImportError:
    FileAction = None  # type: ignore


@dataclass
class RetrievedChunk:
    text:     str
    source:   str    # "file_ops_policy" or "database_policy"
    section:  str    # section heading from the policy doc
    score:    float  # cosine similarity (higher = more relevant)


# ── Query builder ─────────────────────────────────────────────────────────── #

def _action_to_query(action) -> str:
    """
    Convert a FileAction to a short natural-language retrieval query.
    Example: FileAction(DELETE, "users.csv", reason="cleanup")
             → "DELETE file users.csv cleanup"
    """
    parts = [action.op.value.upper(), "file", Path(action.path).name]
    if action.reason:
        parts.append(action.reason)
    return " ".join(parts)


# ── Retriever ─────────────────────────────────────────────────────────────── #

class RAGRetriever:
    """
    Retrieves the most relevant policy chunks for a proposed action.

    Parameters
    ----------
    top_k : int
        Number of chunks to return per query (default 3).
    min_score : float
        Minimum cosine similarity to include a chunk (default 0.0 — return
        all top_k even if weakly relevant; caller can filter further).
    """

    def __init__(self, top_k: int = 3, min_score: float = 0.0) -> None:
        self.top_k     = top_k
        self.min_score = min_score
        self._model    = SentenceTransformer(EMBED_MODEL)
        self._col      = get_collection()

    def query(self, action_or_text) -> list[RetrievedChunk]:
        """
        Retrieve relevant policy chunks.

        Parameters
        ----------
        action_or_text : FileAction | str
            Either a FileAction (converted to a query string automatically)
            or a plain string query.

        Returns
        -------
        list[RetrievedChunk]
            Ordered by descending cosine similarity.
        """
        if isinstance(action_or_text, str):
            query_text = action_or_text
        else:
            query_text = _action_to_query(action_or_text)

        embedding = self._model.encode(query_text).tolist()

        results = self._col.query(
            query_embeddings=[embedding],
            n_results=min(self.top_k, self._col.count()),
            include=["documents", "metadatas", "distances"],
        )

        chunks: list[RetrievedChunk] = []
        docs      = results["documents"][0]
        metas     = results["metadatas"][0]
        distances = results["distances"][0]   # cosine distance (0=identical, 2=opposite)

        for doc, meta, dist in zip(docs, metas, distances):
            # Chroma cosine distance → similarity: sim = 1 - dist/2
            score = round(1.0 - dist / 2.0, 4)
            if score >= self.min_score:
                chunks.append(RetrievedChunk(
                    text=doc,
                    source=meta.get("source", ""),
                    section=meta.get("section", ""),
                    score=score,
                ))

        return chunks
