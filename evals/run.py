#!/usr/bin/env python3
"""Flox skills eval harness.

Runs each task in tasks.jsonl through `claude` headless with the Flox plugin
loaded, in one of two arms:

  --mode skills       skills only, MCP disabled (--strict-mcp-config, no --mcp-config)
  --mode skills+mcp   skills plus the flox-mcp server (--mcp-config)

Each answer is scored with deterministic hard-checks plus an LLM judge.
Results are written to results/<mode>.json. Pure stdlib (no node/uv needed).
"""
import argparse
import json
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
PLUGIN_DIR = HERE.parent / "flox-plugin"

ANSWER_SUFFIX = (
    "\n\nProvide the COMPLETE solution as your written answer: the manifest "
    "(in a ```toml code block) and the exact flox commands, with a brief "
    "explanation. Do not execute commands — just give the answer."
)

# Neutral suffix for trigger tests: must NOT mention flox/manifest, so the run
# genuinely tests whether the skill fires on its own (implicit triggering).
NEUTRAL_SUFFIX = (
    "\n\nProvide the complete solution as your written answer (setup steps and "
    "any config). Do not execute commands — just give the answer."
)

# ---- deterministic hard-checks ---------------------------------------------
# Flags hallucinated *Flox* install methods (the ai-13 bug). Only a curl|sh that
# mentions flox counts — a legit `curl … | sh` for some other tool is fine.
FAKE_INSTALL = re.compile(
    r"install\.flox\.dev|flox\.dev/install|curl[^\n]*flox[^\n]*\|\s*(ba)?sh", re.I
)
ABS_PATH = re.compile(r'=\s*"(/home/|/Users/|/usr/local/|/opt/|/root/)', re.I)
# --- hardcoded-secret detection --------------------------------------------
# The flox-environments skill rule is "Never store secrets in manifest" (use env
# vars / ~/.config/<env>/ / existing credential files). We flag a secret-named
# key assigned a *literal* value anywhere in a manifest block, while allowing env
# references ($VAR / ${VAR}) and obvious placeholders. Detection is name-based
# and covers bare or quoted keys, inline tables ({ ... }), and arrays ([ ... ]).
# Known limits (name-based detection can't help it): a secret hidden in a
# NON-secret-named key's value is not caught, and a real value that happens to
# begin with a placeholder token (e.g. "example...") is treated as a placeholder.
_SECRET_NAME = (
    r"(?:SECRET|TOKEN|PASSWORD|PASSWD|API[_-]?KEY|ACCESS[_-]?KEY|PRIVATE[_-]?KEY)"
)
# A secret-named key (optionally quoted, with any prefix/suffix), at a line start
# or inside an inline table / after a comma, consumed up to and including its `=`.
SECRET_KEY = re.compile(
    r"(?im)(?:^|[{,])[ \t]*(?:export[ \t]+)?"
    r"[\"']?[\w.-]*" + _SECRET_NAME + r"[\w.-]*[\"']?[ \t]*=[ \t]*"
)
# A value is an allowed placeholder / non-literal if it begins (after stripping
# surrounding quotes) with any of these.
PLACEHOLDER_VALUE = re.compile(
    r"(?i)^\s*(?:\$|<|\{\{|\*{3,}|x{3,}|changeme|change_me|placeholder|your[_-]|"
    r"example|dummy|redact|todo|fixme|replace|sample|fake|none|null)"
)
# Matches the string literal at the start of a value: basic/literal, single- or
# triple-quoted; the backreference lets a value contain the *other* quote char.
_QUOTED = re.compile(r"(\"\"\"|'''|[\"'])(.*?)\1", re.S)


def toml_blocks(text):
    # ```toml and bare ``` fences only (not ```bash/```python). \r? so CRLF
    # answers aren't silently skipped, which would disable every manifest check.
    return "\n".join(re.findall(r"```(?:toml)?\r?\n(.*?)```", text, re.S))


def _string_values(rhs):
    """Yield the literal string value(s) at the start of a manifest RHS: a single
    quoted value, a triple-quoted value, or the elements of an array. Bare
    (non-string) values yield nothing."""
    rhs = rhs.lstrip()
    if rhs[:1] == "[":
        inner = re.match(r"\[(.*?)\]", rhs, re.S)
        if inner:
            for m in _QUOTED.finditer(inner.group(1)):
                yield m.group(2)
        return
    m = _QUOTED.match(rhs)
    if m:
        yield m.group(2)


def has_hardcoded_secret(text):
    """True if a manifest block assigns a real literal to a secret-named key."""
    for key in SECRET_KEY.finditer(text):
        for value in _string_values(text[key.end():]):
            if value.strip() and not PLACEHOLDER_VALUE.match(value):
                return True
    return False


CHECKS = {
    "no_fake_install_url": lambda a: not FAKE_INSTALL.search(a),
    "no_abs_paths": lambda a: not ABS_PATH.search(toml_blocks(a)),
    # No secret hardcoded into the manifest (secrets belong in env vars /
    # ~/.config/<env>/ / existing credential files, not the committed manifest).
    "no_hardcoded_secret": lambda a: not has_hardcoded_secret(toml_blocks(a)),
    "has_install_section": lambda a: "[install]" in a,
    "has_services_section": lambda a: "[services" in a,
    "has_build_section": lambda a: "[build" in a,
    "mentions_containerize": lambda a: "flox containerize" in a,
    "uses_flox_publish": lambda a: "flox publish" in a,
    "uses_include_or_layer": lambda a: "[include]" in a or "flox activate -r" in a,
    "uses_search_show": lambda a: "flox search" in a or "flox show" in a,
    # Implicit-trigger check: did the skill fire and produce Flox guidance even
    # though the prompt never said "flox"?
    "invokes_flox": lambda a: bool(re.search(r"\bflox\b", a, re.I))
    and ("flox init" in a or "[install]" in a or "manifest.toml" in a
         or "flox search" in a or "flox show" in a or "flox install" in a),
}


def run_claude(prompt, mode, allow_tools, timeout=420, retries=3):
    cmd = ["claude", "-p", prompt, "--output-format", "json"]
    if allow_tools:
        cmd += ["--allowedTools", *allow_tools]
    if mode == "skills":
        cmd += ["--plugin-dir", str(PLUGIN_DIR), "--strict-mcp-config"]
    elif mode == "skills+mcp":
        mcp_cfg = HERE / "flox-mcp.json"
        cmd += ["--plugin-dir", str(PLUGIN_DIR), "--mcp-config", str(mcp_cfg)]
    elif mode == "judge":
        cmd += ["--strict-mcp-config"]
    last = "unknown"
    for attempt in range(retries):
        try:
            out = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            last = "TIMEOUT"
        else:
            if out.returncode != 0:
                last = f"EXIT {out.returncode}: {out.stderr[:300]}"
            else:
                try:
                    return json.loads(out.stdout).get("result", ""), None
                except json.JSONDecodeError:
                    last = f"BAD JSON: {out.stdout[:300]}"
        # transient (rate limit / overload / blip) -> backoff and retry
        if attempt < retries - 1:
            time.sleep(2 + attempt * attempt * 3)
    return None, last


def judge(task, answer):
    prompt = (
        "You are grading an AI assistant's answer about the Flox package "
        "manager. Be strict and concrete.\n\n"
        f"TASK: {task['prompt']}\n\nRUBRIC: {task['rubric']}\n\n"
        f"ANSWER:\n{answer}\n\n"
        'Return ONLY a JSON object: {"score": <int 1-5>, "correct": <true|false>, '
        '"issues": [<short strings>]}'
    )
    result, err = run_claude(prompt, "judge", allow_tools=None)
    if err:
        return {"score": 0, "correct": False, "issues": [f"judge error: {err}"]}
    raw, m = {}, re.search(r"\{.*\}", result, re.S)
    if m:
        try:
            raw = json.loads(m.group(0))
        except json.JSONDecodeError:
            raw = {"issues": ["judge json parse fail"]}
    else:
        raw = {"issues": ["no json"]}
    # Normalize — the model occasionally omits a key; never let that KeyError later.
    try:
        score = int(raw.get("score", 0) or 0)
    except (TypeError, ValueError):
        score = 0
    return {"score": score, "correct": bool(raw.get("correct", False)),
            "issues": raw.get("issues", [])}


def process_task(t, mode, allow):
    """Run + score one task (agent call, hard-checks, judge). Thread-safe."""
    suffix = NEUTRAL_SUFFIX if t.get("trigger_test") else ANSWER_SUFFIX
    tier = t.get("tier", "should")
    base = {"id": t["id"], "area": t["area"], "tier": tier,
            "trigger_test": bool(t.get("trigger_test"))}
    answer, err = run_claude(t["prompt"] + suffix, mode, allow)
    if err:
        print(f"    [{tier}] {t['id']}: run error: {err}", flush=True)
        return {**base, "error": err}
    hard = {c: CHECKS[c](answer) for c in t["checks"]}
    hard_pass = all(hard.values())
    verdict = judge(t, answer)
    print(f"    [{tier}] {t['id']}: hard={'PASS' if hard_pass else 'FAIL'} "
          f"judge={verdict.get('score')}/5", flush=True)
    return {**base, "hard_checks": hard, "hard_pass": hard_pass,
            "judge": verdict, "answer_excerpt": answer[:1200]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["skills", "skills+mcp"], default="skills")
    ap.add_argument("--tasks", default=str(HERE / "tasks.jsonl"))
    ap.add_argument("--only", help="run a single task id")
    ap.add_argument("--gate", action="store_true",
                    help="exit non-zero if binding gates fail (functional should-tier < 100%)")
    ap.add_argument("--plugin-dir", help="override the plugin dir (e.g. a pre-consolidation checkout)")
    ap.add_argument("--out", help="output filename under results/ (default: <mode>.json)")
    ap.add_argument("--concurrency", type=int, default=6,
                    help="parallel claude calls (default 6; lower if you hit rate limits)")
    args = ap.parse_args()

    if args.plugin_dir:
        global PLUGIN_DIR
        PLUGIN_DIR = Path(args.plugin_dir).resolve()

    allow = ["Skill", "Read"]
    if args.mode == "skills+mcp":
        allow += ["mcp__flox-mcp"]

    tasks = [json.loads(l) for l in Path(args.tasks).read_text().splitlines() if l.strip()]
    if args.only:
        tasks = [t for t in tasks if t["id"] == args.only]

    n = min(args.concurrency, len(tasks)) or 1
    print(f"running {len(tasks)} tasks at concurrency {n} ({args.mode}) ...", flush=True)
    with ThreadPoolExecutor(max_workers=n) as ex:
        results = list(ex.map(lambda t: process_task(t, args.mode, allow), tasks))

    scored = [r for r in results if "judge" in r]

    def stats(rs):
        n = max(len(rs), 1)
        return {
            "n": len(rs),
            "hard_pass_rate": round(sum(r["hard_pass"] for r in rs) / n, 3),
            "avg_judge_score": round(sum(r["judge"]["score"] for r in rs) / n, 2),
            "judge_correct_rate": round(sum(bool(r["judge"]["correct"]) for r in rs) / n, 3),
        }

    triggers = [r for r in scored if r["trigger_test"]]
    should_triggers = [r for r in triggers if r["tier"] == "should"]
    summary = {
        "mode": args.mode,
        "n_tasks": len(results),
        "n_errors": sum(1 for r in results if "error" in r),
        **stats(scored),
        "by_tier": {tier: stats([r for r in scored if r["tier"] == tier])
                    for tier in ("should", "may", "stretch") if any(r["tier"] == tier for r in scored)},
        # triggering is probabilistic — measured, not gated
        "n_trigger_tasks": len(triggers),
        "trigger_invokes_flox_rate": round(
            sum(r["hard_checks"].get("invokes_flox", False) for r in triggers) / max(len(triggers), 1), 3),
        "should_trigger_rate": round(
            sum(r["hard_checks"].get("invokes_flox", False) for r in should_triggers) / max(len(should_triggers), 1), 3),
    }
    out = {"summary": summary, "results": results}
    out_path = HERE / "results" / (args.out or f"{args.mode.replace('+', '_')}.json")
    out_path.write_text(json.dumps(out, indent=2))
    print("\n=== SUMMARY ===")
    print(json.dumps(summary, indent=2))
    print(f"written: {out_path}")

    if args.gate:
        # Binding gate = DETERMINISTIC hard-checks on functional should-tier tasks.
        # The LLM judge's correctness/score is noisy run-to-run, and triggering is
        # probabilistic, so both are *reported* (avg_judge_score, judge_correct_rate,
        # should_trigger_rate) but never fail the build — only the deterministic
        # structural checks do.
        binding = [r for r in scored if r["tier"] == "should" and not r["trigger_test"]]
        bad = [r for r in binding if not r["hard_pass"]]
        errs = [r for r in results if "error" in r and r.get("tier", "should") == "should"]
        if bad or errs:
            print(f"\nGATE FAILED: {len(bad)} functional should-tier task(s) failed hard-checks: "
                  f"{[(r['id'], [k for k, v in r['hard_checks'].items() if not v]) for r in bad]}; errors: {[r['id'] for r in errs]}")
            sys.exit(1)
        print(f"\nGATE PASSED: all {len(binding)} functional should-tier tasks pass hard-checks. "
              f"(advisory: judge correct {summary['judge_correct_rate']}, avg {summary['avg_judge_score']}, "
              f"should-trigger {summary['should_trigger_rate']}).")


if __name__ == "__main__":
    main()
