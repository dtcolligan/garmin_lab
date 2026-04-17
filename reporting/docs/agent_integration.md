# Agent Integration

How a Claude agent (or open Claude-equivalent) installs and uses Health Agent Infra.

The package ships two things the agent consumes:

1. **A CLI called `hai`** — deterministic subcommands on the user's PATH.
2. **Five markdown skills** under `skills/` — judgment-layer instructions.

The agent reads skills, makes decisions, and invokes CLI subcommands to move structured state. The CLI validates the agent's output at the writeback boundary.

## Install

For local development:

```bash
cd /path/to/health_agent_infra
pip install -e .
hai setup-skills
```

`pip install -e .` exposes the `hai` command on the user's PATH. `hai setup-skills` copies every directory under `skills/` into `~/.claude/skills/` (or a custom path via `--dest`). If a skill of the same name already exists, `hai setup-skills` skips it unless `--force` is passed.

Verify:

```bash
hai --help
ls ~/.claude/skills/   # should list recovery-readiness, reporting, merge-human-inputs, writeback-protocol, safety
```

## Claude Code

After `hai setup-skills`, Claude Code discovers the skills automatically the next time it starts. The skills appear in its available-skills list with descriptions drawn from each `SKILL.md` frontmatter.

The agent invokes CLI subcommands via its `Bash` tool. Each `SKILL.md` scopes `allowed-tools` to the exact CLI patterns it needs — e.g., the writeback-protocol skill allows `Bash(hai writeback *)` and `Bash(hai review *)` but not other commands.

Typical agent loop in Claude Code:

1. User: "Give me today's training recommendation."
2. Agent reads `recovery-readiness` skill (loaded on user prompt or via skill discovery).
3. Agent asks the user for today's manual readiness via the merge-human-inputs skill, then captures it:
   `hai intake readiness --soreness moderate --energy high --planned-session-type hard --active-goal strength_block > /tmp/mr.json`
4. Agent: `hai pull --date $(date +%Y-%m-%d) --user-id u_1 --manual-readiness-json /tmp/mr.json > /tmp/evidence.json`
5. Agent: `hai clean --evidence-json /tmp/evidence.json > /tmp/prep.json`
6. Agent reads `prep.json`, classifies state and applies policy per the skill, writes `TrainingRecommendation` JSON to `/tmp/rec.json`.
7. Agent: `hai writeback --recommendation-json /tmp/rec.json --base-dir ~/.local/share/hai/recovery_readiness_v1`
8. Agent: `hai review schedule --recommendation-json /tmp/rec.json --base-dir ~/.local/share/hai/recovery_readiness_v1`
9. Agent uses the `reporting` skill to narrate the recommendation back to the user.

For offline replays or fixtures, step 3 can be replaced with `--use-default-manual-readiness` in step 4; that produces a neutral default without asking the user. The default is explicitly fabricated, not inferred — use it only for testing.

## Claude Agent SDK

Two options:

1. **CLI subcommand dispatch** — the SDK agent runs `hai` subcommands via shell. This is the same flow as Claude Code. Fully agent-agnostic.
2. **Direct Python imports** — if the SDK is running in the same Python environment where `pip install -e .` happened, the agent can `from health_agent_infra.clean import clean_inputs, build_raw_summary` and call functions directly. This skips subprocess overhead but couples the agent to Python. Use only for performance-sensitive inner loops.

For the SDK, skill discovery is not automatic. Upload skills to the Anthropic Skills API (the SDK has org-level support) or reference them by file path in your agent's system prompt.

## Other Claude surfaces

- **Claude.ai** — skill upload is per-user via the UI. Upload each `skills/<skill>/SKILL.md` manually; supporting files in a skill directory are not currently supported there.
- **Web API** — use the Skills API to register skills by `skill_id` and reference them in conversation turns.

## Open Claude-equivalent agents

Any agent with:

- A shell-exec tool (for `hai` subcommands), AND
- A way to load markdown system-prompt fragments at session start (for the skills)

can drive this package. The contract between agent and runtime is the `TrainingRecommendation` JSON schema at `hai writeback` — open-source agents just need to produce a valid JSON.

## MCP

No MCP server ships yet. A future wrapper could expose the CLI subcommands as MCP tools for agents that prefer MCP over shell. Tracked in `STATUS.md` under "what's next."

## Where tools expect paths

- `hai pull` reads from `pull/data/garmin/export/daily_summary_export.csv` (packaged with the repo; override via `--export-dir` in the adapter call if needed).
- `hai writeback` requires `--base-dir` whose path ends in `recovery_readiness_v1/`. Enforced at the I/O boundary. Suggested default: `~/.local/share/health_agent_infra/recovery_readiness_v1/`.
- `hai setup-skills` defaults to `~/.claude/skills/`. Override via `--dest`.

## Where the determinism boundary is

**`hai writeback` calls `src/health_agent_infra/validate.py::validate_recommendation_dict` before any side effect.** That pure function enforces the following invariants — each with a stable machine-readable `invariant` id that the CLI surfaces in stderr on failure:

- `required_fields_present` — every required key exists in the JSON
- `schema_version` — exact match against the runtime's `RECOMMENDATION_SCHEMA_VERSION`
- `action_enum` — `action` is one of the six-value `ActionKind` set (runtime-enforced; `Literal` types in Python are compile-time hints only)
- `confidence_enum` — `confidence` ∈ {`low`, `moderate`, `high`}
- `bounded_true` — `bounded is True`
- `no_banned_tokens` — R2: none of the ten banned diagnosis-shaped tokens appear in `rationale[]` or `action_detail` values (case-insensitive)
- `follow_up_shape` — `follow_up` is an object carrying `review_at`, `review_question`, `review_event_id`
- `review_at_within_24h` — R4: `review_at` is within 24 hours of `issued_at` and not before
- `policy_decisions_present` — at least one `PolicyDecision` entry is recorded

Violations exit with code 2 and stderr `writeback rejected: invariant=<id>: <message>`. Nothing persists. Callers can pattern-match on the invariant id without parsing prose.

Everything upstream (pull, clean) is deterministic pure functions on evidence. Everything downstream (writeback, review) is idempotent persistence with locality enforcement (`base_dir` must be a path segment named `recovery_readiness_v1`).

## What an agent should NOT do

- Modify JSONL files directly. All state mutation goes through `hai`.
- Claim more than the evidence supports. Rationale in the recommendation must reference raw_summary numbers.
- Use diagnostic / clinical language. R2 in the recovery-readiness skill and the writeback schema check both reject it.
- Call `hai` subcommands outside its `allowed-tools` scope in the relevant skill.
