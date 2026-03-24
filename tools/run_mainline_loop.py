#!/usr/bin/env python3
"""Prepare a bounded supervisor prompt for one iteration.

This script does not invoke Codex directly. It writes a durable prompt file that can be
used in either interactive Codex or `codex exec`.
"""
from __future__ import annotations
from pathlib import Path
from datetime import datetime
import argparse

ROOT = Path(__file__).resolve().parents[1]
STATUS = ROOT / "docs/mainline/STATUS.md"
REPORTS = ROOT / "docs/mainline/reports"

READ_ORDER_TIER_A = [
    "AGENTS.md",
    "docs/mainline/CURRENT_LOOP_BRIEF.md",
    "docs/mainline/loop_state_latest.json",
    "docs/mainline/CURRENT_GATE_PACK.md",
    "docs/mainline/reports/*latest*",
]

READ_ORDER_TIER_B = [
    "AGENTS.md",
    "START_AUTOMATION.md",
    "docs/mainline/INDEX.md",
    "docs/mainline/PLAN.md",
    "docs/mainline/IMPLEMENT.md",
    "docs/mainline/STATUS.md",
    "docs/mainline/METRICS_ACCEPTANCE.md",
    "docs/mainline/EVIDENCE_REQUIREMENTS.md",
    "docs/mainline/FAILURE_PLAYBOOK.md",
    "docs/mainline/ENVIRONMENT_AND_VALIDATION.md",
    "docs/mainline/CODEBASE_MAP.md",
    "docs/mainline/SUPERVISOR_STATE_MACHINE.md",
    "docs/runbooks/mainline_phase_gate_runbook.md",
    "docs/mainline/gates/REGISTRY.json (if present)",
    "the active gate definition file from the registry (if present)",
]

def status_text() -> str:
    return STATUS.read_text(encoding="utf-8", errors="ignore") if STATUS.exists() else ""


def read_field(label: str) -> str:
    text = status_text()
    for line in text.splitlines():
        if line.startswith(f"- {label}:"):
            return line.split(":", 1)[1].strip()
    return "UNKNOWN"


def read_gate_summary() -> str:
    gate_mode = read_field("Gate mode")
    active_scientific = read_field("Active scientific gate")
    supporting = read_field("Supporting engineering gate(s)")
    active_gate = read_field("Active gate")
    if gate_mode.strip("`") == "science-first-dual-gate":
        return f"gate mode: {gate_mode}; active scientific gate: {active_scientific}; supporting engineering gate(s): {supporting}; compatibility active gate: {active_gate}"
    return f"gate mode: {gate_mode}; active gate: {active_gate}"


def terminal_active() -> bool:
    text = status_text()
    return "Terminal mainline mode: `active`" in text or "Terminal mainline mode: active" in text


def running_jobs_present() -> bool:
    text = status_text()
    marker = "## Running / pending jobs"
    if marker not in text:
        return False
    after = text.split(marker, 1)[1]
    lines = [ln.strip() for ln in after.splitlines()[1:8] if ln.strip()]
    if not lines:
        return False
    joined = " ".join(lines).lower()
    return not any(tok in joined for tok in ["none", "no active jobs", "n/a", "not in use", "replace with"])


def build_prompt(revalidate: bool = False) -> str:
    gate_summary = read_gate_summary()
    ro_a = "\n".join(f"- {x}" for x in READ_ORDER_TIER_A)
    ro_b = "\n".join(f"- {x}" for x in READ_ORDER_TIER_B)
    if terminal_active() or revalidate:
        return f"""$mainline-supervisor

First run `python tools/validate_state_views.py`.\n\nIf validation is OK, read only:
{ro_a}\n\nIf validation is STALE or CONFLICTED, fall back to canonical reads:
{ro_b}\n
authoritative current state from STATUS.md: {gate_summary}
terminal-mainline mode is active or requested.

Task:
1. Do not activate a new gate.
2. Run only bounded terminal revalidation.
3. Refresh STATUS.md and terminal report files if evidence changes.
4. Write/update docs/mainline/reports/mainline_terminal_summary.txt
5. Keep evidence artifacts current if the terminal judgment depends on them.
6. Stop after this bounded revalidation loop.
"""
    wait_note = ""
    if running_jobs_present():
        wait_note = "\n8. If running or pending jobs are still in progress, keep the result in documented wait-state and do not treat the gate as passed."
    return f"""$mainline-supervisor

First run `python tools/validate_state_views.py`.\n\nIf validation is OK, read only:
{ro_a}\n\nIf validation is STALE or CONFLICTED, fall back to canonical reads:
{ro_b}\n
authoritative current state from STATUS.md: {gate_summary}

Run exactly one bounded supervisor iteration:
1. determine gate mode, the current active gate or active scientific gate, and the current blocker,
2. identify any required supporting engineering gates,
3. identify the smallest next valid step,
4. if a scoped implementation step is needed, perform only that step,
5. if the required step is long-running, convert it into durable wait-state and optionally prepare watcher support instead of waiting indefinitely,
6. run scientific acceptance evaluation, engineering-support evaluation, and overall progression evaluation as applicable,
7. update docs/mainline/STATUS.md,
8. write/update docs/mainline/reports/phase_gate_latest.txt, acceptance_latest.txt, evidence_latest.txt, and any required worked-example outputs,{wait_note}
9. stop.
"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--terminal-revalidate", action="store_true")
    args = ap.parse_args()
    REPORTS.mkdir(parents=True, exist_ok=True)
    prompt = build_prompt(revalidate=args.terminal_revalidate)
    out = REPORTS / "supervisor_prompt_latest.txt"
    out.write_text(prompt, encoding="utf-8")
    print(f"saved: {out}")
    print(prompt)
    if not args.dry_run:
        print("\nNo direct Codex invocation is performed by this script.")
        print(f"timestamp: {datetime.now().isoformat(timespec='seconds')}")


if __name__ == "__main__":
    main()
