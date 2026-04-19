# Query Taxonomy

The kinds of user question Health Agent Infra is built to answer, and
the surfaces that answer each one today.

This doc is grounded in the shipped runtime. Where a category is not yet
a first-class product surface, the "Shipped surface" column says so and
points at the phase that would change that. See
[`reporting/plans/post_v0_1_roadmap.md`](../plans/post_v0_1_roadmap.md)
for the phase plan.

It pairs with [`personal_health_agent_positioning.md`](personal_health_agent_positioning.md)
(role map) and [`memory_model.md`](memory_model.md) (what the runtime
remembers on disk). A useful way to read this doc is: *positioning says
who is answering, memory says from what, taxonomy says what is being
asked.*

## 1. The six question classes

| Class | Representative question | Shipped surface |
|---|---|---|
| 1. Current state understanding | "Am I recovered enough to train hard today?" | `hai state snapshot`; per-domain readiness skills reading `classified_state` + `policy_result` |
| 2. Action planning | "What should I do today, across domains?" | `hai daily`; `hai synthesize` (optionally two-pass with `--bundle-only` + `--drafts-json`) |
| 3. Explanation / audit | "Why did the system recommend an easy run today?" | `hai explain` (added in Phase C, see [`explainability.md`](explainability.md)); direct reads of `proposal_log`, `x_rule_firing`, `recommendation_log`, `review_*` remain available. |
| 4. Longitudinal review | "How has the last two weeks gone?" | `hai review schedule / record / summary [--domain <d>]`; direct reads of `accepted_*_state_daily` + `daily_plan` history |
| 5. Grounded topic explanation | "What does sleep debt mean in this system?" | **Not shipped in v0.1.0.** Read-only grounded-expert prototype is **Phase F**, under explicit source/privacy rules. |
| 6. Human-input routing | "I did squats today — 3×8 at 225" | `hai intake gym|exercise|nutrition|stress|note|readiness`; `strength-intake` + `merge-human-inputs` skills |

A question that falls outside all six classes is usually either (a) a
clinical / diagnostic question the runtime refuses by design (see
[`non_goals.md`](non_goals.md)), or (b) a general health-topic question
the grounded expert will eventually answer read-only in Phase F.

## 2. Class-by-class detail

### 2.1 Current state understanding

**What the user is asking.** "Where am I today, across my domains?"

**How the runtime answers.** Evidence is pulled (`hai pull` or `hai
pull --live`), cleaned, and projected into `accepted_*_state_daily`
tables. `hai state snapshot --as-of <d> --user-id <u>` returns one
block per domain, each carrying:

- `evidence` — the raw accepted row;
- `raw_summary` — deltas, ratios, coverage;
- `classified_state` — bands and scores produced by
  `domains/<d>/classify.py`;
- `policy_result` — R-rule firings produced by
  `domains/<d>/policy.py`, including any `forced_action` and
  `capped_confidence`;
- `missingness` — `absent | partial | unavailable | pending`.

The per-domain readiness skills (`recovery-readiness`,
`running-readiness`, `sleep-quality`, `stress-regulation`,
`strength-readiness`, `nutrition-alignment`) read the snapshot block and
narrate the state. The skills do not recompute bands.

**What it will not do.** It will not diagnose, infer micronutrient
deficiency (nutrition is macros-only; see
[`non_goals.md`](non_goals.md)), or claim a clinical condition.

### 2.2 Action planning

**What the user is asking.** "Given today's state, what should I do?"

**How the runtime answers.** After six domain proposals have been
appended to `proposal_log` via `hai propose`, `hai synthesize` runs
Phase A X-rules over `(snapshot, proposals)`, applies mechanical
mutations to copy-on-write drafts, lets the synthesis skill compose a
rationale overlay (on the two-pass path) or uses the per-proposal
rationale the domain skills already wrote (on the runtime-only path),
runs Phase B X-rules under a write-surface guard, and atomically commits
the `daily_plan` + `x_rule_firing` rows + N `recommendation_log` rows in
a single SQLite transaction.

`hai daily` is the one-shot morning orchestrator:
`pull → clean → snapshot → proposal-gate → synthesize → schedule-reviews`.
It exits cleanly at the proposal gate with
`overall_status=awaiting_proposals` when no proposals exist for the day
rather than fabricating them. Reruns are idempotent because synthesis
keys on `(for_date, user_id)`.

**What it will not do.** It will not generate a training plan or a diet
plan. Recommendations shape or escalate the user's own planned session;
they are drawn from a fixed per-domain action enum the runtime validates
at `hai propose` and again inside the `hai synthesize` transaction.

### 2.3 Explanation / audit

**What the user is asking.** "Why did the runtime land on this
recommendation?"

**How the runtime answers today.** Everything needed to reconstruct a
recommendation is already persisted:

- `accepted_*_state_daily` — the state the runtime saw;
- `proposal_log` — every `DomainProposal` the agent emitted;
- `x_rule_firing` — every Phase A and Phase B mutation, keyed to its
  `daily_plan_id`, tier, target domain, inputs, and applied mutation;
- `recommendation_log` — the final committed recommendation, including
  `supersedes` / `superseded_by` links when `--supersede` was used;
- `review_event` / `review_outcome` — the outcome trail if one exists.

In v0.1.0 the agent (or a user) reaches this via direct SQLite reads.
That works but is not ergonomic.

**`hai explain` is the first-class surface (Phase C, shipped).** It is
a read-only CLI that reconstructs the audit chain for
`--for-date <d> --user-id <u>` or `--daily-plan-id <id>`, in both JSON
and human-readable form. It does not mutate state and does not recompute
anything — it reads from the tables above. See
[`explainability.md`](explainability.md) for the bundle shape and use
cases.

**What it will not do.** It will not invent rationale that was not
recorded. If a firing did not happen, no firing is shown. The explain
surface's honesty depends on the runtime having written what it did.

### 2.4 Longitudinal review

**What the user is asking.** "How have the last N days been going — in
training load, in sleep, in stress, in actual outcomes against the
plan?"

**How the runtime answers today.** Two complementary paths:

- **Outcome side.** `hai review schedule | record | summary
  [--domain <d>]` drives the review loop. `review_event` rows represent
  scheduled reviews (typically one per recommendation); `review_outcome`
  rows carry the user's captured outcome (`completed` / `modified` /
  `skipped` / etc.) plus freeform notes. `hai review summary` reports
  per-domain counts.
- **State side.** `accepted_*_state_daily` rows are day-keyed and grow
  with each `hai state reproject`, so trailing-window reads (e.g. the
  last 14 days of `running_load_7d` or `sleep_debt_14d`) are direct
  SQLite queries today.

**What it will not do.** It will not feed review outcomes back into
thresholds, confidence calibration, or any model. That is a deliberate
non-goal; see §2.6.

### 2.5 Grounded topic explanation

**What the user is asking.** "What does this system mean by sleep debt
/ ACWR / body battery / protein ratio? Why does low protein soften
strength?"

**Shipped surface today.** None. `v0.1.0` does not ship a grounded
expert layer. The closest existing surface is the architecture and
x-rule docs (`architecture.md`, `x_rules.md`, `state_model_v1.md`),
which are reference material rather than an agent-facing answer
surface.

**Phase F shape.** A read-only grounded-expert prototype is scoped in
the roadmap as Phase F. Its constraints are load-bearing:

- read-only; never inside recommendation mutation;
- explicit allowlist of source classes;
- every substantive claim either cites or abstains;
- no silent retrieval inside `hai daily`, `hai synthesize`, or policy;
- any off-device context send must be explicit and operator-initiated.

**What it will never do.** Symptom triage. Diagnosis. Recommendation
mutation. Those are non-goals regardless of phase.

### 2.6 Human-input routing

**What the user is asking.** "Here is something the wearable did not
capture — log it, map it into the right domain, and ask me anything you
need to disambiguate."

**How the runtime answers.** User narration flows through `hai intake
*` subcommands, each of which appends to a raw table:

- `hai intake gym` / `hai intake exercise` → `gym_session`, `gym_set`,
  user-defined `exercise_taxonomy` rows;
- `hai intake nutrition` → `nutrition_intake_raw`;
- `hai intake stress` → `stress_manual_raw`;
- `hai intake note` → `context_note`;
- `hai intake readiness` → readiness inputs feeding the recovery
  signal set.

Two skills mediate the judgment side of routing:

- `strength-intake` disambiguates free-text lifts against
  `exercise_taxonomy` (e.g. "squats" → back vs front) before anything
  reaches `gym_set`;
- `merge-human-inputs` reconciles user-authored context with
  wearable-derived evidence when both are present.

After intake, the user reruns the state chain: `hai clean` (for any
raw evidence file) and `hai state reproject` to refresh the
`accepted_*_state_daily` tables. From there the question is back in
class 1 (current state) or class 2 (action planning).

**What it will not do.** It will not write to `accepted_*` tables
directly — all accepted state is projector-derived. It will not infer a
meal from narration (macros-only; no meal-level retrieval in v1). It
will not accept clinical or diagnostic narration as evidence.

## 3. What this taxonomy deliberately does not include

Three classes of question the runtime refuses:

- **Clinical / diagnostic questions.** "Do I have overtraining syndrome?"
  is out of scope. The runtime reports bands, scores, and escalations
  for training-adjustment support; it does not claim the presence or
  absence of any condition.
- **Meal-level nutrition questions.** "Was my lunch balanced?" is out
  of scope in v1 per the Phase 2.5 retrieval-gate outcome.
- **Open-ended general health-topic questions.** Until Phase F ships a
  read-only grounded expert under an explicit source allowlist, the
  runtime does not answer open-ended health-topic questions.

See [`non_goals.md`](non_goals.md) for the full refusal list.

## 4. How each class maps to runtime stages

For a reader who already has the architecture diagram in hand, the same
six classes pinned to stages:

| Class | Primary stage | Primary tables read | Primary writer |
|---|---|---|---|
| Current state | projection → snapshot | `accepted_*_state_daily` | projectors (`hai state reproject`) |
| Action planning | proposal → synthesis | `proposal_log` → `daily_plan`, `x_rule_firing`, `recommendation_log` | `hai propose`, `hai synthesize` |
| Explanation / audit | post-synthesis read | proposal_log + x_rule_firing + recommendation_log (+ review tables) | none (read-only); `hai explain` ships in Phase C |
| Longitudinal review | review loop + historical snapshot | `review_event`, `review_outcome`, historical `accepted_*_state_daily` / `daily_plan` | `hai review` |
| Grounded topic explanation | *not shipped* | *(Phase F)* | *(Phase F)* |
| Human-input routing | intake | raw tables (`gym_session`, `gym_set`, `nutrition_intake_raw`, `stress_manual_raw`, `context_note`, user-defined `exercise_taxonomy`) | `hai intake *` |

Together with the memory-model doc, this gives a new reader enough
vocabulary to describe the runtime's behavior without inventing
chat-memory, voice-note, or general-AI-coach assumptions.
