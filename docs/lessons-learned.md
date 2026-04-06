# Lessons Learned — AGI Pragma Benchmark Suite

Three benchmarks. Three different failure modes. One consistent finding about
where the DIC pipeline is strong and where it depends on external design choices.

---

## Snake — the utility weight problem

### What failed

The initial Snake agent used `dist_weight = 0.2` in its utility function —
a low weight on food distance that made the agent effectively passive.
It avoided risk successfully but rarely pursued the goal.

| Config | Avg score | Avg reward |
|---|---|---|
| dist_weight = 0.2 (passive) | 0.4 | ~0 |
| dist_weight = 1.5 (active) | 22.8 | 102.4 |

**One parameter change produced a 57× improvement in score.**

### What it taught

The FMEA, circuit breaker, and decision gate all operated correctly from the start.
The failure was entirely in the utility function's balance between risk avoidance
and goal pursuit.

This established the first core lesson: **the DIC safety pipeline is not the bottleneck.**
The pipeline constrains what the agent *can* do; the utility function determines
what the agent *wants* to do. A miscalibrated utility produces a safe but useless agent.

Safety ≠ passivity. An agent that never takes risks never achieves goals.
The circuit breaker's role is to constrain *how much* risk is taken, not to
eliminate risk-taking entirely.

---

## Maze — two failures, one fix

### What failed first: critical path calibration

In v1.0, `p_death` in the Monte Carlo rollouts was only set when the environment's
`alive` flag went `False` — which requires accumulating 300 total steps.
Since each rollout runs for only `depth=25` steps, the clone could never timeout
within the rollout window unless the episode was already near step 275.

Result: `p_death ≈ 0` throughout every episode. RPN stayed low. The circuit
breaker never engaged. The agent navigated on manhattan distance alone.

**Fix:** a rollout that exhausts its depth without reaching the goal counts as
a timeout signal. One line changed. `p_death` immediately reflected ~1.0 for
a 25-step random walk in a maze that requires ≥24 directed steps.

Solve rate: unchanged at 4/50.

### What failed second: saturated signal

The fix was correct but revealed a deeper problem. With `depth=25` and a maze
requiring many more steps under a random policy, `p_death ≈ 1.0` for **all**
candidate actions at every step. The signal was accurate but uninformative —
it could not differentiate between directions.

The circuit breaker correctly fired STOP for all actions (RPN = 270 ≥ 260).
The fallback selected by least RPN (all equal). The final decision reduced back
to the utility function's manhattan distance term — identical to v1.0 behaviour.

### What fixed it: BFS distance

Replacing manhattan distance with exact BFS path distance — precomputed once
per maze via reverse-BFS from the goal, O(1) per lookup — gave the utility
function accurate topological information.

| Change | Solve rate | Avg steps |
|---|---|---|
| Manhattan distance (v1.1) | 4/50 (8%) | 277.9 |
| BFS path distance (v2.0) | 50/50 (100%) | 46.1 |

Revisit penalty and deeper rollouts (depth 25→50) added afterward produced
no measurable change. BFS was the decisive fix.

### What it taught

Three lessons from Maze:

**1. Calibration bugs are silent.** The v1.0 rollouts produced plausible-looking
numbers (`p_death = 0`) that were simply wrong. The pipeline accepted them without
error. Correctness of the critical path estimate must be verified against the
domain's known minimum solution length.

**2. A correct signal can be uninformative.** After the fix, `p_death = 1.0`
was accurate — a random walk almost never solves a maze in 25 steps. But accuracy
without variance is useless for action selection. Signal quality requires both
correctness and differentiation across the action space.

**3. The safety pipeline and the utility function fail independently.**
In every Maze version, the FMEA and circuit breaker operated correctly.
The pipeline was not the problem in v1.0 or v1.1. The failure was in the
goal-progress signal the utility function relied on. This independence is a
structural property of the DIC: a broken utility function produces poor
decisions but does not break safety gating.

---

## Gridworld — the first benchmark where risk is real

### What worked

The Dynamic Threat Gridworld is the first benchmark where the Monte Carlo
`p_death` signal varies meaningfully across candidate actions at each step.
Moving toward a hazard cluster has genuinely higher `p_death` than WAIT or
evasion. The FMEA and Critical Path stages drive decisions, not just gate them.

| Metric | Value |
|---|---|
| Solved | 39/50 (78%) |
| Killed | 11/50 (22%) |
| Timed out | 0/50 |
| Circuit breaker state | WARN / SLOW throughout |

### What it taught

**1. Proportional autonomy constraint works in practice.**
The circuit breaker operated in WARN/SLOW range (RPN 180–200) across most steps —
flagging risk and restricting decision depth without collapsing into STOP.
The four-state design (OK/WARN/SLOW/STOP) is not theoretical; it produces
qualitatively different behaviour at each level.

**2. Some failure is irreducible.**
The 11 killed episodes represent hazard configurations that cross the direct path
regardless of decision quality. Zero timeouts confirms the agent always made
decisive forward progress. The 22% failure rate is the floor for a direct-path
strategy against 5 random wanderers — not a pipeline failure.

**3. WAIT is correctly evaluated but rarely selected.**
The utility function correctly considers WAIT as a first-class action.
In practice, the direct-path utility dominates when the path appears clear.
Whether WAIT could prevent some kills is an open question for future analysis.

---

## Cross-cutting lessons

### Lesson 1 — the safety pipeline is domain-agnostic and consistently correct

Across all three benchmarks, the FMEA, decision gate, and circuit breaker
operated without failure. Every calibration bug and every poor solve rate
was traceable to the utility function or the critical path estimate — not
to the safety gating itself. The pipeline is a reliable layer.

### Lesson 2 — the utility function is the primary design variable

Each benchmark's improvement came from fixing the utility function:

| Benchmark | Fix | Impact |
|---|---|---|
| Snake | Increase dist_weight 0.2 → 1.5 | 57× score improvement |
| Maze | Replace manhattan with BFS distance | 8% → 100% solve rate |
| Gridworld | manhattan is correct (open grid) | 78% baseline, p_death differentiating |

The safety pipeline stays fixed. The utility function is tuned to the domain.
This is the right separation: invariant safety, domain-specific progress signal.

### Lesson 3 — the Monte Carlo signal needs domain-appropriate calibration

The critical path estimate must be designed with the domain's solution
characteristics in mind:

- **Snake:** rollout horizon (depth=25) is sufficient relative to the step budget.
  Traps emerge within 25 random steps.
- **Maze:** horizon must account for minimum solution length under the rollout policy.
  A random walk needs far more than 25 steps to reach a goal 24+ directed steps away.
- **Gridworld:** horizon (depth=50) is sufficient because hazard collision risk
  manifests locally and quickly — within a few steps of a hazard.

The lesson: calibrate depth to the domain's *expected time-to-failure under
the rollout policy*, not to the episode step budget.

### Lesson 4 — signal differentiation matters as much as signal accuracy

A correct but uniformly saturated signal (Maze v1.1: `p_death = 1.0` for all
actions) is equivalent to no signal for action selection purposes. Useful risk
estimation requires variance across the candidate action set. Design the rollout
policy and horizon to produce differentiated estimates, not just accurate ones.

---

## Episodic Memory — learning between sessions

### The current state

All three agents start each episode with uniform Bayesian priors:
`BetaTracker(a=1, b=1)` — maximum uncertainty. The agent relearns hazard
rates, trap frequencies, and collision risks from scratch every episode.

Within an episode, the Bayesian update stage (stage 7) works correctly:
the Beta trackers accumulate evidence and sharpen estimates as the episode
progresses. The `final_bayes` field in each episode summary records the
posterior at termination:

```json
"final_bayes": {
  "collision_rate_mean": 0.923,
  "trap_rate_mean": 0.038
}
```

This posterior is written to `artifacts/` and then discarded. The next
episode starts at `Beta(1, 1)` regardless.

### The concept

Episodic memory makes the terminal posterior of episode N the prior for
episode N+1. Instead of discarding accumulated belief, the agent carries
it forward as structured prior knowledge.

For the Beta distribution this is trivial: `Beta(a, b)` from episode N
becomes the initial `(a, b)` for episode N+1. No architectural change is
needed — only the initialisation of BetaTracker changes from `(1, 1)` to
the loaded posterior.

```python
# Without episodic memory (current)
self.collision_tracker = BetaTracker(a=1, b=1)

# With episodic memory
prior = load_prior("collision_rate", session_id)   # reads artifacts/
self.collision_tracker = BetaTracker(a=prior.a, b=prior.b)
```

### What this enables

**Faster adaptation.** An agent that has navigated 50 gridworld episodes
knows that `collision_rate ≈ 0.9` in this environment. A new episode should
start with that prior, not with maximum uncertainty. The agent reaches
calibrated risk estimates in fewer steps.

**Session-level learning.** If the environment changes between sessions
(e.g. hazard count increases from 5 to 8), the prior will initially be
wrong — the agent will underestimate collision risk. But Bayesian updating
will correct this within a few episodes. The agent is sensitive to change
without being blind to accumulated experience.

**Cross-domain transfer.** Priors from one domain (e.g. Gridworld collision
rates) can inform initialisation in a new but related domain (e.g. a larger
gridworld or a maze with moving hazards). The Beta parameters are
interpretable: `a` is pseudo-count of observed events, `b` is
pseudo-count of non-events. Domain similarity can be expressed as a
fraction of the accumulated pseudo-counts transferred.

### What it does not solve

Episodic memory is not a substitute for a better utility function.
A Bayesian prior that accurately estimates `p_death = 0.9` in the maze
does not help if `p_death = 0.9` for all actions and the utility function
cannot differentiate between them. The signal differentiation problem
(Lesson 4) is upstream of belief accuracy.

Episodic memory sharpens the *speed* of calibration. It does not change
the *structure* of what the DIC can and cannot distinguish.

### Implementation path

The artifact system already writes the necessary data. The implementation
requires:

1. A `load_prior(metric, session_path)` function that reads the most recent
   `summary_*.json` from `artifacts/<benchmark>/` and extracts `final_bayes`.
2. Initialising BetaTrackers from the loaded `(a, b)` rather than `(1, 1)`.
3. A decay factor (optional): `a_new = 1 + (a_loaded - 1) × decay` to
   down-weight old evidence and remain sensitive to environmental change.

The existing `ArtifactWriter` and `final_bayes` schema require no changes.
