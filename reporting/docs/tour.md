# Reading Tour

A 10-minute guided read of Health Agent Infra for someone who is not you right now — including future-you coming back cold. Different from [flagship_walkthrough.md](flagship_walkthrough.md) (which explains the loop mechanics) and the README 3-minute path (which is a link list). This doc explains *why* each piece exists.

The aim is to rebuild the mental model, not to browse the code.

---

## 1. What you're looking at

Health Agent Infra (internal name: Health Lab) is not a health app. It is a governed runtime and contract layer. Its job is to turn your own health evidence — passive wearables, typed readiness notes — into **structured state**, then let a bounded agent act on that state with an audit trail and a review mechanism.

The wedge is narrow by design: everything between "raw personal evidence" and "bounded agent action." Not the wearable API. Not the chatbot. Not the medical device. The governed middle.

The proof lives in one flagship loop, `recovery_readiness_v1`, which runs end-to-end over both synthetic fixtures and a real Garmin CSV export. That loop is the whole current claim.

---

## 2. How to orient the repo

Read the repo through the **eight canonical buckets**, nothing else:

```
pull                passive / machine-readable input acquisition
clean               deterministic normalization + validation + bundle assembly
merge_human_inputs  human notes, voice notes, manual logs
research            notebooks and bounded exploratory work
interpretation      model-oriented code and experiments
reporting           docs, proofs, operator-facing demos
writeback           explicit persisted-state update surfaces
safety              tests, compatibility wrappers, fail-closed checks
```

Namespaces inside buckets (like `clean/health_model/`) are current implementation locations, not separate canonical categories. If you see something that looks like a ninth bucket, it's a compatibility surface or legacy content.

Why this shape matters: it forces every new slice to answer "which bucket does this belong in?" before it lands. That question kills most feature creep before it starts.

---

## 3. Where the thesis is controlling

Two docs own the thesis:

- [`reporting/docs/canonical_doctrine.md`](canonical_doctrine.md) — the controlling statement of what the project is and is not. Wins any conflict with other docs until explicitly retired.
- [`reporting/docs/explicit_non_goals.md`](explicit_non_goals.md) — 12 hard + 2 soft non-goals. Read this before proposing any new direction.

The non-goals doc is load-bearing. Most of the project's discipline comes from what it refuses to build: no second connector, no UI, no hosted runtime, no clinical claims, no ML learning loop. When you feel the pull to expand scope, this doc is the counterweight.

---

## 4. Where the runtime lives

The flagship runtime path is:

```
PULL → CLEAN → STATE → POLICY → RECOMMEND → ACTION → REVIEW
```

Each stage does one thing. Each arrow increases commitment: evidence → claim → proposal → write → outcome. See the [README](../../README.md#runtime-at-a-glance) for the annotated diagram.

The spec and walkthrough:

- [`reporting/docs/flagship_loop_spec.md`](flagship_loop_spec.md) — what each stage is contractually required to do.
- [`reporting/docs/flagship_walkthrough.md`](flagship_walkthrough.md) — narrative walkthrough of one run, stage by stage.

The implementation is a single module: `clean/health_model/recovery_readiness_v1/`. Eight files, no cross-cutting abstractions, no framework. Each file maps to one stage of the loop plus shared schemas:

- `schemas.py` — typed dataclasses: `RecoveryState`, `TrainingRecommendation`, `ReviewEvent`, `ReviewOutcome`, `PolicyDecision`, `SignalQuality`. No implicit state anywhere.
- `clean.py` — deterministic CLEAN: validates, computes baselines, assembles `CleanedEvidence`.
- `state.py` — builds `RecoveryState` with `signal_quality`, `uncertainties`, `recovery_status`, `readiness_score`.
- `policy.py` — six executable rules (R1 block, R2 soften, R3 escalate-on-diagnosis-language, R4 RHR-spike, R5 no-unknown-action, R6 writeback-locality). Each rule returns a `PolicyDecision`.
- `recommend.py` — builds the `TrainingRecommendation`; this is where goal-conditioned tailoring (`_goal_conditioned_detail`) lives.
- `action.py` — idempotent local writeback. Enforces writeback-locality at the I/O boundary.
- `review.py` — schedules review events, records outcomes, computes confidence adjustment from outcome history.
- `cli.py` — end-to-end CLI runner with `--scenario` (synthetic) and `--source real` (Garmin CSV export).

If a stage grows unwieldy, split it inside its file rather than introducing helper modules. The shape of the loop is the shape of the code.

---

## 5. Where the proof lives

Two sibling captured bundles demonstrate the loop end-to-end:

- `reporting/artifacts/flagship_loop_proof/2026-04-16-recovery-readiness-v1/` — eight synthetic scenarios covering: green path, bounded downgrade, stronger downgrade, RHR-spike escalation, policy block on insufficient signal, confidence soften on sparse signal, and a paired tailoring demonstration (same evidence, different `active_goal`, different `action_detail`).
- `reporting/artifacts/flagship_loop_proof/2026-04-16-garmin-real-slice/` — the same loop running against a committed real Garmin CSV export. Same CLEAN→REVIEW code; only the PULL source differs.

Each captured bundle contains:

- `captured/*.json` — full run artifacts (cleaned evidence + state + recommendation + action record + review event + review outcome).
- `summary/*.txt` — human-readable summaries.
- `writeback/recovery_readiness_v1/` — actual written JSONL logs and daily plan notes, as the ACTION layer produced them.

The captures are **inspectable**: open any JSON and read the full reasoning chain. The policy decisions are in `policy_decisions[]` with rule IDs and notes. The state's uncertainties are in `state.uncertainties[]`. The recommendation's confidence is in `training_recommendation.confidence`. Nothing is implicit.

---

## 6. How to run it yourself

From repo root:

```bash
PYTHONPATH=clean:safety python -m health_model.recovery_readiness_v1.cli run \
  --scenario mildly_impaired_with_hard_plan \
  --base-dir /tmp/recovery_readiness_v1 \
  --date 2026-04-16 \
  --now 2026-04-16T07:15:00+00:00 \
  --record-review-outcome followed_and_improved
```

Swap `--scenario` for any of the eight. Swap `--source real` to run against the committed Garmin CSV.

Full test suite:

```bash
PYTHONPATH=clean:safety uv run --with pytest pytest safety/tests/test_recovery_readiness_v1.py -v
```

28 passing at current commit.

---

## 7. What's intentionally not done

Two `TODO(founder)` markers are live in the codebase:

- `_goal_conditioned_detail` in `recommend.py` — first-pass periodization heuristic (RPE caps for strength_block, Zone 2 caps for endurance_taper). The wiring is permanent; the heuristic values are placeholder.
- `derive_confidence_adjustment` in `review.py` — first-pass asymmetric calibration (+0.05 per followed+improved, −0.02 per followed+no-improvement, clamp ±0.25). Same framing.

These are explicit founder-authoring slots, not bugs. The loop is structurally complete; the judgment layer is where the next real investment belongs.

Other intentional not-dones:

- Phase 3 (adapter / connector-truth reconciliation) is queued. See `STATUS.md` L46 for the specific lane.
- No second connector, no Apple Health / Oura / Whoop. The brief's §15 non-goal.
- No hosted service, no multi-user, no UI.
- No ML / learning loop. Calibration stays a pure deterministic function over outcome history.

---

## 8. Reading paths by question

If you come in with a specific question, start here:

| Question | Start at |
|---|---|
| "What is this project?" | [`canonical_doctrine.md`](canonical_doctrine.md) §Thesis |
| "Why isn't this a chatbot / app / wearable API?" | [`explicit_non_goals.md`](explicit_non_goals.md) |
| "What does the runtime actually do?" | [`flagship_walkthrough.md`](flagship_walkthrough.md) |
| "Does it actually run?" | `reporting/artifacts/flagship_loop_proof/2026-04-16-recovery-readiness-v1/captured/recovered_with_easy_plan.json` |
| "Does it run on real data?" | `reporting/artifacts/flagship_loop_proof/2026-04-16-garmin-real-slice/captured/real_garmin_slice_2026-04-08.json` |
| "What's the policy layer?" | `clean/health_model/recovery_readiness_v1/policy.py` + [`minimal_policy_rules.md`](minimal_policy_rules.md) |
| "What's tailoring?" | Diff the two `tailoring_*.json` captures — identical evidence, different `action_detail`. |
| "How did we get here?" | [`phase_timeline.md`](phase_timeline.md) |
| "What's next?" | `STATUS.md` + the current plan file in `reporting/docs/plan_*.md` |

---

## 9. One honest caveat

This is a personal-use proof, not a product. It is not hosted, not multi-user, not clinical, not polished, not monetized. The audience for the repo is primarily the author's own clarity. Public legibility is a side effect of making the repo narrate itself coherently — it is not the goal.

If the tour stops making sense, the likely cause is that the repo has evolved faster than this doc. Doctrine wins; come back to `canonical_doctrine.md` and work outward from there.
