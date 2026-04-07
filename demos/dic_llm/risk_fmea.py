from dataclasses import dataclass
from typing import Dict, Optional

from .file_action import FileAction, FileOp


@dataclass
class FMEAItem:
    failure_mode:  str
    severity:      int  # 1..10
    occurrence:    int  # 1..10  — driven by LLM risk tracker mean
    detection:     int  # 1..10
    reversibility: int  # 0=fully reversible … 10=fully irreversible
    rpn:           int  # S × O × D × R


def occ_from_prob(p: float) -> int:
    """Convert probability (0..1) to Occurrence score 1..10."""
    if p <= 0.01: return 1
    if p <= 0.03: return 2
    if p <= 0.07: return 3
    if p <= 0.12: return 4
    if p <= 0.20: return 5
    if p <= 0.32: return 6
    if p <= 0.45: return 7
    if p <= 0.60: return 8
    if p <= 0.80: return 9
    return 10


def fmea_table(
    action:          FileAction,
    file_exists:     bool,
    llm_risk_mean:   float,   # Beta tracker mean for LLM proposing risky actions
) -> Dict[str, FMEAItem]:
    """
    Build FMEA table for a candidate file operation.

    Occurrence is driven by llm_risk_mean — how often this LLM session
    has proposed high-risk actions. Higher tracker mean → higher O for all modes.

    Reversibility reflects how easily the action can be undone:
      DELETE : R=10 — permanent unless external backup exists
      WRITE overwrite : R=8 — original content lost
      WRITE new file  : R=3 — can simply delete the created file
      READ   : R=1  — read-only, no mutation
    """
    o_base = occ_from_prob(llm_risk_mean)
    table: Dict[str, FMEAItem] = {}

    if action.op == FileOp.DELETE:
        # Permanent data loss — catastrophic, irreversible
        s, o, d, r = 10, min(10, o_base + 2), 2, 10
        table["permanent_data_loss"] = FMEAItem(
            "File permanently deleted — unrecoverable without backup",
            s, o, d, r, s * o * d * r,
        )
        # Deleting wrong file — hard to detect before execution
        s2, o2, d2, r2 = 9, o_base, 7, 10
        table["wrong_file_deleted"] = FMEAItem(
            "Wrong file targeted — path confusion or LLM hallucination",
            s2, o2, d2, r2, s2 * o2 * d2 * r2,
        )

    elif action.op == FileOp.WRITE:
        if file_exists:
            # Overwrite — original content lost
            s, o, d, r = 8, o_base, 3, 8
            table["overwrite_data_loss"] = FMEAItem(
                "Existing file overwritten — original content lost",
                s, o, d, r, s * o * d * r,
            )
        # Unintended file created / corrupted content
        s2, o2, d2, r2 = 4, max(1, o_base - 2), 7, 3
        table["unintended_write"] = FMEAItem(
            "File created/modified with incorrect content",
            s2, o2, d2, r2, s2 * o2 * d2 * r2,
        )

    elif action.op == FileOp.READ:
        # Sensitive data exposure — low severity in sandbox context
        s, o, d, r = 5, max(1, o_base - 3), 5, 1
        table["sensitive_read"] = FMEAItem(
            "Sensitive file contents exposed to LLM context",
            s, o, d, r, s * o * d * r,
        )

    return table


def max_rpn(table: Dict[str, FMEAItem]) -> int:
    return max(item.rpn for item in table.values()) if table else 0
