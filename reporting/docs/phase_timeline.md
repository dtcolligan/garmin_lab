# Phase Timeline

A one-glance record of how Health Agent Infra (internal name: Health Lab) got to its current shape. Grouped by logical phase, not per commit. Each entry names the transition, not just the work.

This doc is for future-self. Its job is to make the path legible when you come back cold.

---

## 2026-02-21 → 2026-03-04 — Garmin pipeline origin

First working Garmin pull + clean + feature pipeline. Exploratory notebooks. The repo was a Garmin-focused data project, not yet a governed runtime.

- Key commits: `34f6c2a` (pipeline origin), `ad5698b` (restructure into modules, first README).

**Why it mattered:** Established that raw Garmin evidence could be deterministically ingested and shaped. This is the factual substrate the rest of the project sits on top of.

---

## 2026-03-27 — Readiness scoring + UI experiments

Daily readiness scoring, nutrition/training context, web UI dashboard, coaching summary endpoint. An attempt to ship the loop as a consumer-facing product.

- Key commits: `0d82cea` (readiness scoring), `7af7591` (dashboard), `2b2270c` (coaching UI).

**Why it mattered:** Surfaced the limits of the consumer-app framing. The scoring + UI path proved the shape of the data but not a defensible thesis. Became the entry point for the thesis pivot a few weeks later.

---

## 2026-04-09 — Thesis pivot to Health Lab

The project is reframed as Health Lab — a governed runtime and contract layer, not a consumer app. Schema plan, transformation plan, execution spec all land on the same day.

- Key commits: `6a82955` (schema plan), `66211ed` (transformation plan), `1c6c487` (execution spec), `77c9952` (daily snapshot core), `13c9cb3` (offline Garmin export adapter).

**Why it mattered:** The product-to-infrastructure pivot. The thesis stops being "a health app that scores your day" and becomes "the governed layer between personal evidence and bounded agent action." Everything after this is building that claim.

---

## 2026-04-10 — Agent interface v1 and canonical public demo

Agent-facing CLI surface comes online: contract, bundle, voice-note, context, recommendation. Canonical public demo bundle lands. This is the first public-legibility proof path.

- Key commits: `6d9bd7b` (agent interface v1), `e89c744` (roundtrip proof), `e4b4d51` (contract CLI), `e08592c` (bundle CLI), `c21cf6a` (voice note CLI), `cb192e8` (context CLI), `6d3b2e4` (recommendation CLI), `a16e08d` (canonical public demo), `34c3816` (flagship loop proof audit bundle).

**Why it mattered:** Shifted the repo from "code that processes data" to "a CLI-first proof path an outsider can run end-to-end." Set the legibility standard every later phase had to keep.

---

## 2026-04-11 — Retrieval contract v1 and writeback surfaces

Retrieval contract freezes. Multiple retrieval slices (sleep review, day nutrition brief, weekly pattern, recommendation, feedback, resolution). Recommendation-judgment writeback contract lands with proof bundles.

- Key commits: `9be3a31` (retrieval contract v1), `14d34bb` (recommendation-judgment writeback contract), `32108e0` (canonical definition freeze).

**Why it mattered:** Formalized how the runtime reads and writes. The retrieval contract is what later phases audit against; the writeback contract is what keeps ACTION bounded.

---

## 2026-04-12 — Canonical framing and 8-bucket restructure

Repo restructures into the approved top-level buckets (`pull`, `clean`, `merge_human_inputs`, `research`, `interpretation`, `reporting`, `writeback`, `safety`). Legacy product surfaces archived. Namespace renames (`health_agent_infra`). v1 platform contracts freeze: Garmin, Cronometer, supplements, daily snapshot merge. wger reframed as bounded exploratory, not flagship.

- Key commits: `fdba78e` (repo restructure), `2855b96` (archive legacy), `51a9c66` (freeze v1 contracts), `273ae9a` (wger reframe), `e6297f7` (canonical package namespace), `a4c78da` (Cronometer adapter).

**Why it mattered:** The repo's shape stopped being accidental. The 8-bucket model is the controlling layout from here on. wger's demotion is what keeps Phase 3 disciplined later.

---

## 2026-04-14 — Manual gym phase 4 prototype and connector cleanup

First bounded manual-gym prototype on the tree. Connector drift removed from root docs. Hevy surface pruned. Legacy trio gate demoted. Manual gym becomes canonical in the snapshot contract.

- Key commits: `0e2a507` (manual gym canonical), `30d0863` (phase 4 prototype), `a148176` (remove Hevy), `9cade67` (remove connector drift).

**Why it mattered:** Phase 4 gets a single honest deliverable without expanding the flagship. The cleanup enforces "no connector sprawl" at the doc layer.

---

## 2026-04-15 — Rename to Health Agent Infra

Public-facing name becomes Health Agent Infra; "Health Lab" retained as internal codename.

- Key commit: `e093c32`.

**Why it mattered:** Names the wedge more precisely — it's agent infrastructure, not a lab. Internal codename preserved so commit history and tribal memory still parse.

---

## 2026-04-16 — Phase 1 doctrine, Phase 2 flagship, and DoS closure (same day)

Chief Operational Brief's Phase 1 doctrine pass lands. The flagship `recovery_readiness_v1` loop lands end-to-end with 19 passing tests and a 6-scenario proof bundle. External-review tightening pass. Finally: Phase 2 closure — real Garmin slice, tailoring substance (action-parameter variance on identical evidence), review-loop calibration, and doc currency — meets the Definition-of-Success brief's §10 non-negotiables and §11 strong-success criteria.

- Key commits: `ce838e9` (Phase 1 doctrine), `adfca63` (Phase 2 flagship), `c98c921` (external-review tightening), `f3a73e6` (Phase 2 closure).

**Why it mattered:** The thesis goes from "well-framed repo" to "running, inspectable, domain-credible proof." The user's `active_goal` is now surfaced in the recommendation payload so downstream LLM consumers can act on it. Review-loop calibration returns bounded deltas over real outcomes. One real-day Garmin slice runs through the unchanged CLEAN→REVIEW pipeline. Everything the brief asks for at this horizon is in the tree.

---

## Current state (2026-04-16)

- 28 passing tests; 8 synthetic scenarios + 1 real Garmin slice in the captured proof bundles.
- Phase 1 doctrine is controlling (`reporting/docs/canonical_doctrine.md`).
- Phase 2 flagship is shipped and inspectable.
- Phase 3 (adapter/connector reframing) is queued but not started — see `STATUS.md` for the specific lane.
- No `TODO(founder)` markers remain in code. `_goal_conditioned_detail` now surfaces `active_goal` as pass-through; `derive_confidence_adjustment` was reshaped into `summarize_review_history` returning structured counts. The runtime does not invent judgment; that work belongs to a downstream LLM consumer.

## Reading this timeline

If you're coming back cold, the three loadbearing commits to re-read first are:

1. `1c6c487` (2026-04-09, Health Lab execution spec) — where the thesis locks.
2. `fdba78e` (2026-04-12, repo restructure) — where the shape locks.
3. `f3a73e6` (2026-04-16, Phase 2 closure) — where the current proof locks.
