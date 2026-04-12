"""
Scenario Benchmark
==================
Compares DIC behaviour across all four operational scenarios
(normal, stress, extreme, catastrophic) using MockActor(scenario="default").

Each session replays the same 4-action script (READ, WRITE×2, DELETE) so
differences in block counts are caused purely by scenario parameters, not
by action variance.

Usage
-----
    python -m benchmarks.scenario.run
    python -m benchmarks.scenario.run --sessions 50
    python -m benchmarks.scenario.run --output artifacts/scenario_benchmark.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

from demos.dic_llm.mock_actor   import MockActor
from demos.dic_llm.dic_governor import DICGovernor
from demos.dic_llm.executor     import Executor
from demos.dic_llm.file_action  import FileOp
from core.scenario_weights      import ALL_SCENARIO_NAMES, get_scenario, SCENARIOS

# ── ANSI ──────────────────────────────────────────────────────────────────── #
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"

DEFAULT_SESSIONS = 20
MAX_STEPS        = 20


# ── Per-session result ────────────────────────────────────────────────────── #

@dataclass
class SessionResult:
    scenario:      str
    session_id:    int
    completed:     bool
    total_actions: int       # non-DONE proposals
    blocked:       int
    approved:      int
    blocks_by_op:  dict      # {"READ": n, "WRITE": n, "DELETE": n}
    rpns:          list[int]
    adj_rpns:      list[int]


@dataclass
class ScenarioAggregate:
    scenario:               str
    description:            str
    rpn_threshold:          int
    n_trials:               int
    p_death:                float
    p_trap:                 float
    time_pressure:          float
    sessions:               int
    completion_rate:        float
    total_actions:          int
    total_blocked:          int
    total_approved:         int
    block_rate:             float
    avg_blocks_per_session: float
    blocks_by_op:           dict    # summed across sessions
    avg_base_rpn:           float
    avg_adj_rpn:            float
    avg_rpn_multiplier:     float   # adj / base


# ── Session runner ────────────────────────────────────────────────────────── #

def _run_session(scenario_name: str, session_id: int, sandbox: Path) -> SessionResult:
    actor    = MockActor(scenario="default")
    gov      = DICGovernor(sandbox_root=sandbox, scenario=scenario_name)
    executor = Executor(sandbox_root=sandbox)

    # Suppress MockActor's start_task print
    devnull = open(os.devnull, "w")
    orig    = sys.stdout
    sys.stdout = devnull
    try:
        actor.start_task("benchmark task")
    finally:
        sys.stdout = orig
        devnull.close()

    blocked      = 0
    approved     = 0
    total        = 0
    completed    = False
    blocks_by_op = {"READ": 0, "WRITE": 0, "DELETE": 0, "DONE": 0}
    rpns:     list[int] = []
    adj_rpns: list[int] = []

    for _ in range(MAX_STEPS):
        action = actor.propose_action()
        if action.op == FileOp.DONE:
            completed = True
            break

        total += 1
        op_name = action.op.value.upper()

        decision = gov.evaluate(action)

        # Pull base_rpn and adjusted_rpn from stage_log
        base_rpn = adj_rpn = decision.max_rpn
        for entry in decision.stage_log:
            if entry.get("stage") == "monte_carlo":
                base_rpn = entry["base_rpn"]
                adj_rpn  = entry["adjusted_rpn"]
                break
        rpns.append(base_rpn)
        adj_rpns.append(adj_rpn)

        if decision.approved:
            approved += 1
            try:
                executor.execute(action)
            except Exception:
                pass
            actor.feedback(action, approved=True, result="ok", block_reason=None)
        else:
            blocked += 1
            blocks_by_op[op_name] = blocks_by_op.get(op_name, 0) + 1
            actor.feedback(action, approved=False, result=None,
                           block_reason=decision.block_reason)

    return SessionResult(
        scenario      = scenario_name,
        session_id    = session_id,
        completed     = completed,
        total_actions = total,
        blocked       = blocked,
        approved      = approved,
        blocks_by_op  = blocks_by_op,
        rpns          = rpns,
        adj_rpns      = adj_rpns,
    )


def _aggregate(results: list[SessionResult], scenario_name: str) -> ScenarioAggregate:
    cfg     = get_scenario(scenario_name)
    subset  = [r for r in results if r.scenario == scenario_name]
    n       = len(subset)

    total_actions  = sum(r.total_actions for r in subset)
    total_blocked  = sum(r.blocked       for r in subset)
    total_approved = sum(r.approved      for r in subset)
    completed      = sum(1 for r in subset if r.completed)

    # Sum blocks per op
    blocks_by_op: dict[str, int] = {}
    for r in subset:
        for op, cnt in r.blocks_by_op.items():
            blocks_by_op[op] = blocks_by_op.get(op, 0) + cnt

    all_base = [v for r in subset for v in r.rpns]
    all_adj  = [v for r in subset for v in r.adj_rpns]
    avg_base = sum(all_base) / len(all_base) if all_base else 0.0
    avg_adj  = sum(all_adj)  / len(all_adj)  if all_adj  else 0.0
    avg_mult = avg_adj / avg_base if avg_base else 1.0

    return ScenarioAggregate(
        scenario               = scenario_name,
        description            = cfg.description,
        rpn_threshold          = cfg.rpn_threshold,
        n_trials               = cfg.n_trials,
        p_death                = cfg.p_death,
        p_trap                 = cfg.p_trap,
        time_pressure          = cfg.time_pressure,
        sessions               = n,
        completion_rate        = completed / n if n else 0.0,
        total_actions          = total_actions,
        total_blocked          = total_blocked,
        total_approved         = total_approved,
        block_rate             = total_blocked / total_actions if total_actions else 0.0,
        avg_blocks_per_session = total_blocked / n if n else 0.0,
        blocks_by_op           = blocks_by_op,
        avg_base_rpn           = round(avg_base, 1),
        avg_adj_rpn            = round(avg_adj,  1),
        avg_rpn_multiplier     = round(avg_mult, 3),
    )


# ── Printing ──────────────────────────────────────────────────────────────── #

def _bar(rate: float, width: int = 20) -> str:
    filled = int(rate * width)
    return "█" * filled + "░" * (width - filled)


def _print_table(aggs: list[ScenarioAggregate]) -> None:
    print(f"\n{BOLD}{CYAN}{'═'*80}{RESET}")
    print(f"{BOLD}{CYAN}  Scenario Benchmark — DIC Block Rate by Operational Scenario{RESET}")
    print(f"{BOLD}{CYAN}{'═'*80}{RESET}")

    hdr = (
        f"  {'Scenario':<14}  {'Threshold':>9}  {'Blk/sess':>8}  "
        f"{'Block%':>7}  {'Blocked':>7}  {'READ':>5}  {'WRITE':>5}  {'DELETE':>6}  "
        f"{'AvgRPN':>7}  {'×mult':>6}"
    )
    print(hdr)
    print(f"  {'─'*14}  {'─'*9}  {'─'*8}  {'─'*7}  {'─'*7}  {'─'*5}  {'─'*5}  {'─'*6}  {'─'*7}  {'─'*6}")

    colours = {
        "normal":       GREEN,
        "stress":       CYAN,
        "extreme":      YELLOW,
        "catastrophic": RED,
    }

    for a in aggs:
        col      = colours.get(a.scenario, RESET)
        blk_pct  = a.block_rate * 100
        bar      = _bar(a.block_rate, 10)
        r_blk    = a.blocks_by_op.get("READ",   0)
        w_blk    = a.blocks_by_op.get("WRITE",  0)
        d_blk    = a.blocks_by_op.get("DELETE", 0)

        print(
            f"  {col}{BOLD}{a.scenario:<14}{RESET}  "
            f"{a.rpn_threshold:>9}  "
            f"{a.avg_blocks_per_session:>8.2f}  "
            f"{col}{blk_pct:>5.1f}% {bar}{RESET}  "
            f"{a.total_blocked:>7}  "
            f"{r_blk:>5}  {w_blk:>5}  {d_blk:>6}  "
            f"{a.avg_adj_rpn:>7.0f}  "
            f"{a.avg_rpn_multiplier:>6.2f}×"
        )

    print(f"\n  {DIM}Sessions per scenario: {aggs[0].sessions if aggs else 0}{RESET}")
    print(f"  {DIM}Actor: MockActor(scenario='default') — READ + WRITE×2 + DELETE per session{RESET}")
    print(f"  {DIM}RPN shown is scenario-adjusted (base × Monte Carlo multiplier){RESET}")
    print()

    # Per-op breakdown
    print(f"  {BOLD}Action breakdown (blocked / total across all sessions):{RESET}")
    ops = ["READ", "WRITE", "DELETE"]
    for op in ops:
        print(f"  {op:<8}", end="")
        for a in aggs:
            col    = colours.get(a.scenario, RESET)
            total  = a.sessions  # each session has 1 READ, 2 WRITE, 1 DELETE
            blk    = a.blocks_by_op.get(op, 0)
            rate   = blk / (a.sessions * (2 if op == "WRITE" else 1))
            bar    = _bar(rate, 8)
            print(f"  {col}{a.scenario:<14} {blk:>3}/{a.sessions * (2 if op=='WRITE' else 1):<3} {bar}{RESET}", end="")
        print()
    print()


# ── Main ──────────────────────────────────────────────────────────────────── #

def run_benchmark(
    n_sessions:  int = DEFAULT_SESSIONS,
    output_path: Optional[str] = None,
) -> list[ScenarioAggregate]:

    total = len(ALL_SCENARIO_NAMES) * n_sessions
    done  = 0

    print(f"\n{BOLD}{CYAN}{'═'*64}{RESET}")
    print(f"{BOLD}{CYAN}  DIC Scenario Benchmark{RESET}")
    print(f"{BOLD}{CYAN}{'═'*64}{RESET}")
    print(f"  Scenarios: {', '.join(ALL_SCENARIO_NAMES)}")
    print(f"  Sessions:  {n_sessions} per scenario  ({total} total)")
    print(f"  Actor:     MockActor(scenario='default')\n")

    all_results: list[SessionResult] = []

    for scenario_name in ALL_SCENARIO_NAMES:
        for sid in range(1, n_sessions + 1):
            done += 1
            w     = 30
            filled = int(w * done / total)
            bar    = "█" * filled + "░" * (w - filled)
            print(
                f"\r  [{bar}] {100*done/total:5.1f}%  "
                f"{scenario_name} #{sid:<3}",
                end="", flush=True,
            )
            with tempfile.TemporaryDirectory() as tmpdir:
                sandbox = Path(tmpdir) / "sandbox"
                sandbox.mkdir()
                result = _run_session(scenario_name, sid, sandbox)
                all_results.append(result)

    print()  # newline after progress

    aggs = [_aggregate(all_results, s) for s in ALL_SCENARIO_NAMES]
    _print_table(aggs)

    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "meta": {
                "sessions_per_scenario": n_sessions,
                "scenarios":             ALL_SCENARIO_NAMES,
                "actor":                 "MockActor(scenario='default')",
                "script":                ["READ", "WRITE", "WRITE", "DELETE", "DONE"],
            },
            "aggregates": [asdict(a) for a in aggs],
            "sessions":   [asdict(r) for r in all_results],
        }
        Path(output_path).write_text(json.dumps(payload, indent=2))
        print(f"  {DIM}Saved → {output_path}{RESET}\n")

    return aggs


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DIC scenario benchmark")
    parser.add_argument("--sessions", type=int, default=DEFAULT_SESSIONS)
    parser.add_argument("--output",   default="artifacts/scenario_benchmark.json")
    args = parser.parse_args()
    run_benchmark(n_sessions=args.sessions, output_path=args.output)
