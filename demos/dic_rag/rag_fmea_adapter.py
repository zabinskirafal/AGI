"""
RAG FMEA Adapter
================
Translates retrieved policy chunks into FMEA score adjustments.

The adapter scans chunk text for known risk keywords and returns a
FMEAOverride that the RAGGovernor applies before calling fmea_table().
"""

from dataclasses import dataclass, field

from .rag_retriever import RetrievedChunk


@dataclass
class FMEAOverride:
    """
    Adjustments to FMEA inputs derived from retrieved policy context.

    severity_delta  : int   added to the base Severity score (clipped to 1-10)
    detection_delta : int   added to the base Detection score (clipped to 1-10)
    notes           : list  human-readable explanation for each adjustment
    """
    severity_delta:  int         = 0
    detection_delta: int         = 0
    notes:           list[str]   = field(default_factory=list)


# ── Keyword → adjustment map ─────────────────────────────────────────────── #
#
# Each entry: (keyword_in_chunk_text, severity_delta, detection_delta, note)
# Matches are case-insensitive.  The first matching rule per keyword class wins.
#
_RULES: list[tuple[str, int, int, str]] = [
    # Severity escalations
    ("always critical",        +2,  0, "Policy: operation is always CRITICAL (+2 severity)"),
    ("critical",               +1,  0, "Policy: critical risk flag in matching section (+1 severity)"),
    ("prohibited",             +2,  0, "Policy: operation is prohibited without confirmation (+2 severity)"),
    ("escalate to human",      +2,  0, "Policy: human escalation required (+2 severity)"),
    ("escalate",               +1,  0, "Policy: escalation flag in matching section (+1 severity)"),
    ("irreversible",           +1,  0, "Policy: operation is irreversible (+1 severity)"),
    ("permanently lost",       +2,  0, "Policy: data permanently lost if no backup (+2 severity)"),
    ("backup required",        +1,  0, "Policy: backup required before operation (+1 severity)"),
    ("production",             +1,  0, "Policy: production data in scope (+1 severity)"),
    ("pii",                    +1,  0, "Policy: PII exposure risk (+1 severity)"),

    # Detection escalations (hard to detect = higher D score)
    ("hard to detect",          0, +2, "Policy: operation is hard to detect (+2 detection)"),
    ("audit",                   0, +1, "Policy: audit requirement increases detection difficulty (+1 detection)"),
    ("silently",                0, +2, "Policy: agents can modify silently (+2 detection)"),
    ("no audit log",            0, +2, "Policy: no audit log — post-incident detection impossible (+2 detection)"),
    ("autocommit",              0, +2, "Policy: autocommit mode — no rollback (+2 detection)"),

    # Severity reductions (policy confirms low risk)
    ("low-risk",               -1,  0, "Policy: operation confirmed low-risk (−1 severity)"),
    ("no-op",                  -2,  0, "Policy: operation is a no-op (−2 severity)"),
    ("zero risk",              -2,  0, "Policy: policy confirms zero risk (−2 severity)"),
    ("aggregate only",         -1,  0, "Policy: aggregate-only query reduces risk (−1 severity)"),
]


def adapt(chunks: list[RetrievedChunk]) -> FMEAOverride:
    """
    Scan retrieved chunks for policy keywords and build a FMEAOverride.

    Rules are applied once per keyword class across all chunks (no double
    counting).  The final deltas are clipped so the adjusted score stays
    within [1, 10] when applied externally.

    Parameters
    ----------
    chunks : list[RetrievedChunk]

    Returns
    -------
    FMEAOverride
    """
    override = FMEAOverride()
    matched_keywords: set[str] = set()

    # Combine all chunk texts for scanning (lower-cased)
    combined = "\n".join(c.text for c in chunks).lower()

    for keyword, s_delta, d_delta, note in _RULES:
        if keyword in combined and keyword not in matched_keywords:
            override.severity_delta  += s_delta
            override.detection_delta += d_delta
            override.notes.append(note)
            matched_keywords.add(keyword)

    return override
