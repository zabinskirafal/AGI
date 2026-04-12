"""
RAG Indexer
===========
Loads policy documents from docs/, splits them into sections, embeds
with sentence-transformers, and persists a Chroma collection.

Usage (one-time build):
    python -m demos.dic_rag.rag_indexer

The collection is persisted at demos/dic_rag/.chroma/ and reused on
subsequent runs unless rebuild=True is passed.
"""

import re
from pathlib import Path
from typing import Optional

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

# ── Paths ────────────────────────────────────────────────────────────────── #

_HERE        = Path(__file__).parent
DOCS_DIR     = _HERE / "docs"
CHROMA_DIR   = _HERE / ".chroma"
COLLECTION   = "dic_policy"
EMBED_MODEL  = "all-MiniLM-L6-v2"  # 22 MB, runs locally, no API key


# ── Section splitter ─────────────────────────────────────────────────────── #

def _split_sections(text: str, source: str) -> list[dict]:
    """
    Split a markdown document into chunks at heading boundaries (##, ###).
    Each chunk includes the heading text for retrieval context.
    Returns list of {"id", "text", "source", "section"}.
    """
    # Split on lines that start with ## or ###
    parts = re.split(r"(?m)^(#{2,3} .+)$", text)

    chunks: list[dict] = []
    current_heading = "Introduction"
    buffer = []

    for part in parts:
        if re.match(r"^#{2,3} ", part):
            # Flush previous buffer
            body = "\n".join(buffer).strip()
            if body:
                chunk_id = f"{source}::{current_heading}"
                chunks.append({
                    "id":      chunk_id,
                    "text":    f"{current_heading}\n\n{body}",
                    "source":  source,
                    "section": current_heading,
                })
            current_heading = part.strip()
            buffer = []
        else:
            buffer.append(part)

    # Flush last buffer
    body = "\n".join(buffer).strip()
    if body:
        chunk_id = f"{source}::{current_heading}"
        chunks.append({
            "id":      chunk_id,
            "text":    f"{current_heading}\n\n{body}",
            "source":  source,
            "section": current_heading,
        })

    return chunks


# ── Build index ──────────────────────────────────────────────────────────── #

def build_index(rebuild: bool = False) -> chromadb.Collection:
    """
    Index all .md files in docs/ into a persistent Chroma collection.

    Parameters
    ----------
    rebuild : bool
        If True, delete the existing collection and rebuild from scratch.

    Returns
    -------
    chromadb.Collection
    """
    client = chromadb.PersistentClient(
        path=str(CHROMA_DIR),
        settings=Settings(anonymized_telemetry=False),
    )

    if rebuild:
        try:
            client.delete_collection(COLLECTION)
            print(f"[indexer] Deleted existing collection '{COLLECTION}'")
        except Exception:
            pass

    # Check if collection already populated
    try:
        col = client.get_collection(COLLECTION)
        if col.count() > 0 and not rebuild:
            print(f"[indexer] Collection '{COLLECTION}' already has {col.count()} chunks — skipping rebuild")
            return col
    except Exception:
        pass

    col = client.get_or_create_collection(
        name=COLLECTION,
        metadata={"hnsw:space": "cosine"},
    )

    # Load and embed documents
    model = SentenceTransformer(EMBED_MODEL)
    doc_files = sorted(DOCS_DIR.glob("*.md"))

    if not doc_files:
        raise FileNotFoundError(f"No .md files found in {DOCS_DIR}")

    all_ids, all_texts, all_embeddings, all_metas = [], [], [], []

    for doc_path in doc_files:
        text   = doc_path.read_text(encoding="utf-8")
        source = doc_path.stem          # "file_ops_policy", "database_policy"
        chunks = _split_sections(text, source)

        print(f"[indexer] {doc_path.name} → {len(chunks)} chunks")

        for chunk in chunks:
            embedding = model.encode(chunk["text"]).tolist()
            all_ids.append(chunk["id"])
            all_texts.append(chunk["text"])
            all_embeddings.append(embedding)
            all_metas.append({"source": chunk["source"], "section": chunk["section"]})

    col.add(
        ids=all_ids,
        documents=all_texts,
        embeddings=all_embeddings,
        metadatas=all_metas,
    )

    print(f"[indexer] Indexed {len(all_ids)} chunks into '{COLLECTION}'")
    return col


def get_collection() -> chromadb.Collection:
    """
    Return the existing Chroma collection (build it first if missing).
    """
    client = chromadb.PersistentClient(
        path=str(CHROMA_DIR),
        settings=Settings(anonymized_telemetry=False),
    )
    try:
        col = client.get_collection(COLLECTION)
        if col.count() > 0:
            return col
    except Exception:
        pass

    # Not built yet — build now
    return build_index()


# ── CLI entry point ──────────────────────────────────────────────────────── #

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Build the DIC policy RAG index")
    parser.add_argument("--rebuild", action="store_true", help="Force rebuild")
    args = parser.parse_args()
    build_index(rebuild=args.rebuild)
