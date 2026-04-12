"""
RAG Indexer
===========
Builds and persists domain-partitioned Chroma collections.

Each policy document belongs to exactly one domain.  Documents are indexed
into separate collections so the retriever can query only the collection
relevant to the action being evaluated.

Domain → Collection name mapping:
    file_ops  →  dic_file_ops    (file_ops_policy.md)
    database  →  dic_database    (database_policy.md)
    network   →  dic_network     (network_policy.md)

Usage:
    python -m demos.dic_rag.rag_indexer            # build all (skip if current)
    python -m demos.dic_rag.rag_indexer --rebuild  # force full rebuild
    python -m demos.dic_rag.rag_indexer --domain file_ops  # rebuild one domain
"""

import re
from pathlib import Path

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

# ── Paths ────────────────────────────────────────────────────────────────── #

_HERE       = Path(__file__).parent
DOCS_DIR    = _HERE / "docs"
CHROMA_DIR  = _HERE / ".chroma"
EMBED_MODEL = "all-MiniLM-L6-v2"

# doc stem → domain name
DOMAIN_MAP: dict[str, str] = {
    "file_ops_policy": "file_ops",
    "database_policy": "database",
    "network_policy":  "network",
}

# All known domains (for iteration; may include domains with no doc yet)
ALL_DOMAINS: list[str] = ["file_ops", "database", "network"]


def _collection_name(domain: str) -> str:
    return f"dic_{domain}"


def _chroma_client() -> chromadb.PersistentClient:
    return chromadb.PersistentClient(
        path=str(CHROMA_DIR),
        settings=Settings(anonymized_telemetry=False),
    )


# ── Section splitter ─────────────────────────────────────────────────────── #

def _split_sections(text: str, source: str) -> list[dict]:
    """
    Split a markdown document into chunks at heading boundaries (##, ###).
    Returns list of {"id", "text", "source", "section"}.
    """
    parts = re.split(r"(?m)^(#{2,3} .+)$", text)

    chunks: list[dict] = []
    current_heading = "Introduction"
    buffer: list[str] = []

    for part in parts:
        if re.match(r"^#{2,3} ", part):
            body = "\n".join(buffer).strip()
            if body:
                chunks.append({
                    "id":      f"{source}::{current_heading}",
                    "text":    f"{current_heading}\n\n{body}",
                    "source":  source,
                    "section": current_heading,
                })
            current_heading = part.strip()
            buffer = []
        else:
            buffer.append(part)

    body = "\n".join(buffer).strip()
    if body:
        chunks.append({
            "id":      f"{source}::{current_heading}",
            "text":    f"{current_heading}\n\n{body}",
            "source":  source,
            "section": current_heading,
        })

    return chunks


# ── Per-domain builder ────────────────────────────────────────────────────── #

def _build_domain(
    domain:  str,
    client:  chromadb.PersistentClient,
    model:   SentenceTransformer,
    rebuild: bool,
) -> chromadb.Collection:
    """
    Build (or reuse) the Chroma collection for a single domain.
    Indexes all docs whose stem maps to *domain* in DOMAIN_MAP.
    """
    col_name = _collection_name(domain)

    if rebuild:
        try:
            client.delete_collection(col_name)
            print(f"[indexer] Deleted '{col_name}'")
        except Exception:
            pass

    # Check if already populated
    try:
        col = client.get_collection(col_name)
        if col.count() > 0 and not rebuild:
            print(f"[indexer] '{col_name}' already has {col.count()} chunks — skipping")
            return col
    except Exception:
        pass

    col = client.get_or_create_collection(
        name=col_name,
        metadata={"hnsw:space": "cosine", "domain": domain},
    )

    # Find docs that belong to this domain
    doc_files = [
        p for p in sorted(DOCS_DIR.glob("*.md"))
        if DOMAIN_MAP.get(p.stem) == domain
    ]

    if not doc_files:
        print(f"[indexer] '{col_name}' — no docs mapped to domain '{domain}', leaving empty")
        return col

    all_ids, all_texts, all_embeddings, all_metas = [], [], [], []

    for doc_path in doc_files:
        text   = doc_path.read_text(encoding="utf-8")
        source = doc_path.stem
        chunks = _split_sections(text, source)
        print(f"[indexer] {doc_path.name} ({domain}) → {len(chunks)} chunks")

        for chunk in chunks:
            embedding = model.encode(chunk["text"]).tolist()
            all_ids.append(chunk["id"])
            all_texts.append(chunk["text"])
            all_embeddings.append(embedding)
            all_metas.append({
                "source":  chunk["source"],
                "section": chunk["section"],
                "domain":  domain,
            })

    col.add(
        ids=all_ids,
        documents=all_texts,
        embeddings=all_embeddings,
        metadatas=all_metas,
    )
    print(f"[indexer] Indexed {len(all_ids)} chunks into '{col_name}'")
    return col


# ── Public API ────────────────────────────────────────────────────────────── #

def build_index(
    rebuild: bool = False,
    domain:  str | None = None,
) -> dict[str, chromadb.Collection]:
    """
    Build domain-partitioned Chroma collections.

    Parameters
    ----------
    rebuild : bool
        Force rebuild of targeted collections even if they already exist.
    domain : str | None
        Build only this domain.  None (default) builds all known domains.

    Returns
    -------
    dict[str, chromadb.Collection]
        Mapping of domain name → Chroma collection.
    """
    client = _chroma_client()
    model  = SentenceTransformer(EMBED_MODEL)

    targets = [domain] if domain else ALL_DOMAINS
    result: dict[str, chromadb.Collection] = {}

    for d in targets:
        result[d] = _build_domain(d, client, model, rebuild)

    return result


def get_collection(domain: str) -> chromadb.Collection:
    """
    Return the Chroma collection for *domain*, building it if missing.

    Parameters
    ----------
    domain : str
        One of: "file_ops", "database", "network".
    """
    client   = _chroma_client()
    col_name = _collection_name(domain)

    try:
        col = client.get_collection(col_name)
        if col.count() > 0:
            return col
    except Exception:
        pass

    # Build on demand
    model = SentenceTransformer(EMBED_MODEL)
    return _build_domain(domain, client, model, rebuild=False)


def get_all_collections() -> dict[str, chromadb.Collection]:
    """
    Return all domain collections, building any that are missing.
    Only returns collections for domains that have at least one indexed chunk.
    """
    client = _chroma_client()
    model  = SentenceTransformer(EMBED_MODEL)
    result: dict[str, chromadb.Collection] = {}

    for domain in ALL_DOMAINS:
        col = _build_domain(domain, client, model, rebuild=False)
        if col.count() > 0:
            result[domain] = col

    return result


# ── CLI ───────────────────────────────────────────────────────────────────── #

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Build domain-partitioned DIC policy index")
    parser.add_argument("--rebuild", action="store_true", help="Force rebuild")
    parser.add_argument("--domain", choices=ALL_DOMAINS, default=None,
                        help="Build only this domain (default: all)")
    args = parser.parse_args()
    cols = build_index(rebuild=args.rebuild, domain=args.domain)
    for d, c in cols.items():
        print(f"  {d}: {c.count()} chunks in '{_collection_name(d)}'")
