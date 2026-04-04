from dataclasses import dataclass
from typing import Dict

@dataclass
class FMEAItem:
    failure_mode: str
    severity: int   # 1..10 (10 = catastrophic)
    occurrence: int # 1..10 (10 = frequent)
    detection: int  # 1..10 (10 = hard to detect)
    rpn: int

def clamp10(x: float) -> int:
    x = int(round(x))
    return max(1, min(10, x))

def occ_from_prob(p: float) -> int:
    """
    Convert probability (0..1) to Occurrence 1..10.
    """
    # heuristic mapping
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
    p_death_horizon: float,
    p_trap_horizon: float,
    immediate_collision: bool
) -> Dict[str, FMEAItem]:
    """
    Build a minimal FMEA table for a candidate action.
    - Death = wall/self collision or high-prob death within horizon
    - Trap = leads to states with no safe actions soon (dead-end)
    Detection meaning:
      1 = easy to detect, 10 = hard to detect
    """
    table: Dict[str, FMEAItem] = {}

    # Immediate collision is fully detectable (D=1) and catastrophic (S=10)
    if immediate_collision:
        s, o, d = 10, 10, 1
        table["immediate_death"] = FMEAItem("Immediate collision", s, o, d, s*o*d)
        # if immediate collision exists, that should already block decision
        return table

    # Probabilistic death within horizon
    s = 10
    o = occ_from_prob(p_death_horizon)
    d = 3  # easy-ish: agent can estimate via rollout, but not perfect
    table["prob_death"] = FMEAItem("Death within horizon", s, o, d, s*o*d)

    # Trap risk (no safe moves soon / funnel)
    s = 8
    o = occ_from_prob(p_trap_horizon)
    d = 6  # harder to detect than immediate collision
    table["trap"] = FMEAItem("Trapped / dead-end", s, o, d, s*o*d)

    return table

def max_rpn(table: Dict[str, FMEAItem]) -> int:
    return max(item.rpn for item in table.values()) if table else 0
