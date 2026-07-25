# Flox skills evals

A standalone eval suite for the Flox skill: tasks scored for correctness and
quality, used to catch regressions and to measure whether the skill triggers on
the right requests and supplies the right context. (It also gated the
consolidation work — each merge step had to hold or beat the recorded baseline —
but the suite stands on its own beyond that.)

Tasks are tiered by triggering expectation: **should** (must trigger + be
correct; these bind the gate), **may** (nice if it triggers), and **stretch**
(we'd like it to, but it's fine if not — these never fail the gate). Many
prompts deliberately never mention "flox", to test that the skill fires when a
user just wants "a new project" / "add nodejs 18.4" / "a PyTorch GPU setup".

## What it does

For every task in `tasks.jsonl`, runs `claude` headless with the Flox plugin
loaded and scores the answer two ways:

- **Hard checks** — deterministic regex checks (no hallucinated install URL, no
  absolute paths in manifests, no hardcoded secrets in manifests, required
  manifest sections present, correct commands used).
- **LLM judge** — a separate `claude` call grades the answer 1–5 against the
  task's rubric and returns a pass/fail.

### Trigger tests

Tasks with `"trigger_test": true` check **implicit triggering**: the prompt never
says "flox" (e.g. "create a new Node.js project"), and a neutral instruction is
used so nothing biases the model toward Flox. The `invokes_flox` hard-check then
verifies the skill fired anyway and produced Flox guidance. These guard the
behavior the retired MCP server used to encourage.

Two arms (this is the AI-93 comparison):

| Mode | Flag | Needs |
|------|------|-------|
| `skills` | `--strict-mcp-config` (MCP off) | nothing extra |
| `skills+mcp` | `--mcp-config flox-mcp.json` | nothing extra — `flox-mcp.json` runs the public MCP server via `flox activate -r flox/flox-mcp-server -- flox-mcp` (no FloxHub login required) |

## Run

```bash
python3 run.py --mode skills            # skills-only baseline
python3 run.py --mode skills+mcp        # skills + MCP (needs flox-mcp)
python3 run.py --mode skills --only node-env   # single task
python3 run.py --mode skills --gate     # exit non-zero if binding gates fail (CI)
```

Results land in `results/<mode>.json` with a summary (hard-pass rate, avg judge
score, correct rate). Pure stdlib — no node/uv required.

## Authentication

The harness shells out to `claude`, which needs credentials:

- **Locally** it uses whatever the `claude` CLI is logged in with (an OAuth
  token in `~/.claude/.credentials.json`, e.g. a Claude subscription) — usage
  counts against that account.
- **In CI** there is no local login, so the workflow
  (`.github/workflows/evals.yml`) exports the org-managed
  `MANAGED_SKILLS_ANTHROPIC_API_KEY` secret as `ANTHROPIC_API_KEY`; `claude` uses
  it for both the agent and judge calls. The job runs `run.py --mode skills
  --gate`, which fails the build only if a functional `should`-tier task fails
  its deterministic hard-checks (judge score and triggering are reported, not
  gated — see Gate policy below).

## Baselines

Recorded on the original 7-skill layout (pre-consolidation):

| Arm | Hard-check pass | Avg judge score | Correct rate | File |
|-----|-----------------|-----------------|--------------|------|
| skills-only | 8/8 (100%) | 4.62 / 5 | 8/8 | `results/skills.json` |
| skills + MCP | 8/8 (100%) | 4.25 / 5 | 8/8 | `results/skills_mcp.json` |

**AI-93 finding:** skills-only is at least as good as skills+MCP (the delta is
within LLM-judge run-to-run noise; both arms are 100% correct and 100%
hard-pass). No measurable context gap from removing the MCP.

## Gate policy

Both the LLM judge (integer 1–5, plus a binary "correct") and implicit
triggering are **probabilistic run-to-run** — a single task can flip
correct↔incorrect or trigger↔not-trigger between identical runs. Binding CI on
those would make it flaky (15 functional tasks at ~95% judge reliability ≈ 46%
chance of an all-green run). So `--gate` is split:

- **Binding (deterministic):** every **functional `should`-tier** task must pass
  its **hard-checks** (no hallucinated Flox install, required manifest sections,
  correct commands, etc.). These are regex-deterministic and stable; a failure
  blocks the build.
- **Advisory (reported, never blocks):** `avg_judge_score`, `judge_correct_rate`,
  per-tier breakdown, and `should_trigger_rate`. These are tracked as quality/
  triggering trends (watch for a sustained drop), not pass/fail gates. `may` and
  `stretch` tasks are advisory by definition.
