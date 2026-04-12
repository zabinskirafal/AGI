"""
Scenario-Weighted Monte Carlo for DIC
======================================
Defines four operational scenarios (normal, stress, extreme, catastrophic)
that modulate Monte Carlo rollout interpretation of proposed agent actions.

Each ScenarioConfig carries:
  p_death        — probability weight for catastrophic / fatal-class outcomes
                   (irreversible data destruction, system compromise)
  p_trap         — probability weight for cascade / trap failures
                   (one bad action unlocks further irreversible harm)
  time_pressure  — urgency factor 0..1; reduces effective detection quality
                   (high time_pressure ≈ rushed operator, less careful review)
  rpn_threshold  — scenario-specific RPN ceiling; stricter under stress
  n_trials       — Monte Carlo sample count; more trials under higher stress
                   for tighter confidence intervals

Monte Carlo rollout
-------------------
``monte_carlo_rollout(action, cp, scenario)`` simulates *n_trials* independent
outcomes for the proposed action given the scenario context.  Each trial draws:

  1. base_fail     ~ Bernoulli(cp.p_irreversible)
  2. catastrophic  ~ Bernoulli(scenario.p_death)   [only if base_fail]
  3. cascade       ~ Bernoulli(scenario.p_trap)     [independent]
  4. undetected    ~ Bernoulli(time_pressure)       [applies to any failure]

Per-trial damage:
  catastrophic escalation → 1.0
  cascade / trap          → 0.7
  base failure only       → 0.4
  undetected modifier     → damage * 1.5, capped at 1.0
  no failure              → 0.0

Aggregate metrics feed an RPN multiplier that is applied on top of the FMEA
base RPN before the Decision Gate comparison.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Optional


# ── ScenarioConfig ────────────────────────────────────────────────────────── #

@dataclass(frozen=True)
class ScenarioConfig:
    """
    Immutable configuration for one operational scenario.

    Parameters
    ----------
    name : str
        Scenario identifier — one of "normal", "stress", "extreme",
        "catastrophic".
    p_death : float
        Probability weight (0..1) for catastrophic-class outcomes given a base
        failure has occurred.  Scales the chance that a bad action causes
        irreversible, high-severity damage.
    p_trap : float
        Probability weight (0..1) for cascade / trap failures.  Independent of
        base failure — models the risk that this action opens a door to further
        irreversible harm even when the action itself seems benign.
    time_pressure : float
        Urgency factor (0..1).  Reduces detection effectiveness — a rushed
        operator or tight deadline increases the chance that harm goes
        undetected until after execution.
    rpn_threshold : int
        Maximum acceptable RPN *after* Monte Carlo adjustment.  Actions whose
        adjusted_rpn meets or exceeds this value are blocked.
    n_trials : int
        Number of Monte Carlo trials to run per evaluation.  Higher values
        give tighter confidence intervals at the cost of computation time.
    description : str
        Human-readable description shown in the DIC audit trace.
    """
    name:          str
    p_death:       float
    p_trap:        float
    time_pressure: float
    rpn_threshold: int
    n_trials:      int
    description:   str


# ── Built-in scenario registry ────────────────────────────────────────────── #

SCENARIOS: dict[str, ScenarioConfig] = {
    "normal": ScenarioConfig(
        name          = "normal",
        p_death       = 0.01,
        p_trap        = 0.05,
        time_pressure = 0.10,
        rpn_threshold = 2400,
        n_trials      = 500,
        description   = "Standard operating conditions — low ambient risk",
    ),
    "stress": ScenarioConfig(
        name          = "stress",
        p_death       = 0.05,
        p_trap        = 0.15,
        time_pressure = 0.40,
        rpn_threshold = 1800,
        n_trials      = 1000,
        description   = "Elevated load or partial system degradation",
    ),
    "extreme": ScenarioConfig(
        name          = "extreme",
        p_death       = 0.15,
        p_trap        = 0.30,
        time_pressure = 0.70,
        rpn_threshold = 1200,
        n_trials      = 2000,
        description   = "High-stakes environment — failure consequences amplified",
    ),
    "catastrophic": ScenarioConfig(
        name          = "catastrophic",
        p_death       = 0.35,
        p_trap        = 0.50,
        time_pressure = 0.90,
        rpn_threshold = 800,
        n_trials      = 5000,
        description   = "Critical / life-safety context — near-zero tolerance",
    ),
}

ALL_SCENARIO_NAMES = list(SCENARIOS.keys())


def get_scenario(name: str) -> ScenarioConfig:
    """Return the ScenarioConfig for *name*, raising ValueError if unknown."""
    try:
        return SCENARIOS[name]
    except KeyError:
        raise ValueError(
            f"Unknown scenario {name!r}. "
            f"Choose from: {ALL_SCENARIO_NAMES}"
        )


# ── Monte Carlo result ────────────────────────────────────────────────────── #

@dataclass
class MonteCarloResult:
    """
    Aggregate output from a Monte Carlo rollout for one proposed action.

    Attributes
    ----------
    scenario : str
        Name of the scenario used.
    n_trials : int
        Number of trials simulated.
    p_catastrophic : float
        Fraction of trials that produced a catastrophic outcome.
    p_cascade : float
        Fraction of trials that triggered a cascade / trap failure.
    p_undetected : float
        Fraction of failure trials where harm went undetected.
    expected_damage : float
        Mean damage score across all trials (0.0 = none, 1.0 = total).
    detection_effectiveness : float
        1 − time_pressure — the fraction of failures the system can detect.
    rpn_multiplier : float
        Multiplier derived from expected_damage, applied to the FMEA base RPN.
    base_rpn : int
        FMEA max RPN before scenario adjustment.
    adjusted_rpn : int
        base_rpn × rpn_multiplier (rounded to nearest int).
    """
    scenario:                str
    n_trials:                int
    p_catastrophic:          float
    p_cascade:               float
    p_undetected:            float
    expected_damage:         float
    detection_effectiveness: float
    rpn_multiplier:          float
    base_rpn:                int
    adjusted_rpn:            int


# ── RPN multiplier lookup ─────────────────────────────────────────────────── #

def _damage_to_multiplier(expected_damage: float) -> float:
    """Map expected_damage (0..1) to an RPN multiplier."""
    if expected_damage < 0.10:  return 1.0
    if expected_damage < 0.25:  return 1.2
    if expected_damage < 0.40:  return 1.5
    if expected_damage < 0.60:  return 2.0
    if expected_damage < 0.80:  return 2.5
    return 3.0


# ── Core rollout function ─────────────────────────────────────────────────── #

def monte_carlo_rollout(
    p_irreversible: float,
    scenario:       ScenarioConfig,
    n_trials:       Optional[int] = None,
    seed:           Optional[int] = None,
) -> MonteCarloResult:
    """
    Run a Monte Carlo simulation for one proposed action.

    Parameters
    ----------
    p_irreversible : float
        Base probability of an irreversible outcome (from CriticalPathResult).
    scenario : ScenarioConfig
        Operational scenario to apply.
    n_trials : int | None
        Override the scenario's default trial count.
    seed : int | None
        RNG seed for reproducibility (None = non-deterministic).

    Returns
    -------
    MonteCarloResult
        Aggregate metrics and adjusted RPN multiplier.

    Notes
    -----
    This function intentionally uses ``random`` (not ``numpy``) so there are
    no heavy dependencies.  For n_trials ≤ 5000 the overhead is negligible.
    """
    rng = random.Random(seed)
    trials = n_trials or scenario.n_trials

    n_catastrophic = 0
    n_cascade      = 0
    n_undetected   = 0
    total_damage   = 0.0
    failure_count  = 0

    for _ in range(trials):
        damage = 0.0
        failed = False

        # 1. Base irreversible outcome
        if rng.random() < p_irreversible:
            failed = True
            damage = 0.4

            # 2. Catastrophic escalation (conditional on base failure)
            if rng.random() < scenario.p_death:
                damage = 1.0
                n_catastrophic += 1

        # 3. Independent cascade / trap failure
        if rng.random() < scenario.p_trap:
            n_cascade += 1
            if damage < 0.7:
                damage = 0.7
                failed = True

        # 4. Detection failure amplifies any damage
        if failed and rng.random() < scenario.time_pressure:
            n_undetected += 1
            damage = min(1.0, damage * 1.5)

        if failed:
            failure_count += 1

        total_damage += damage

    expected_damage         = total_damage / trials
    p_catastrophic          = n_catastrophic / trials
    p_cascade               = n_cascade / trials
    p_undetected            = n_undetected / failure_count if failure_count else 0.0
    detection_effectiveness = 1.0 - scenario.time_pressure
    multiplier              = _damage_to_multiplier(expected_damage)

    return MonteCarloResult(
        scenario                = scenario.name,
        n_trials                = trials,
        p_catastrophic          = round(p_catastrophic, 4),
        p_cascade               = round(p_cascade, 4),
        p_undetected            = round(p_undetected, 4),
        expected_damage         = round(expected_damage, 4),
        detection_effectiveness = round(detection_effectiveness, 3),
        rpn_multiplier          = multiplier,
        base_rpn                = 0,   # filled in by caller
        adjusted_rpn            = 0,   # filled in by caller
    )
