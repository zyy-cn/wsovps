#!/usr/bin/env python3
"""Validate derived state views against canonical sources.

Exit codes:
- 0: OK (safe to use low-token Tier-A read set)
- 1: STALE/CONFLICTED (must fall back to canonical docs and regenerate views)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


def digest_sources(paths: list[Path]) -> str:
    h = hashlib.sha256()
    for p in paths:
        h.update(str(p).encode())
        if p.exists():
            h.update(p.read_bytes())
        else:
            h.update(b"MISSING")
    return h.hexdigest()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


def parse_field(status_md: str, pattern: str, default: str = "not-yet-declared") -> str:
    m = re.search(pattern, status_md, flags=re.MULTILINE)
    return m.group(1).strip() if m else default


def gate_id(label: str) -> str:
    parts = re.split(r"\s+—\s+|\s+-\s+|\s+", label.strip(), maxsplit=1)
    return parts[0].strip() if parts and label.strip() else "not-yet-declared"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", default=".")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    mainline = repo / "docs/mainline"
    reports = mainline / "reports"

    status_path = mainline / "STATUS.md"
    metrics_path = mainline / "METRICS_ACCEPTANCE.md"
    evidence_path = mainline / "EVIDENCE_REQUIREMENTS.md"
    failure_path = mainline / "FAILURE_PLAYBOOK.md"
    constitution_path = mainline / "OPERATING_CONSTITUTION.md"
    plan_path = mainline / "PLAN.md"
    implement_path = mainline / "IMPLEMENT.md"
    env_path = mainline / "ENVIRONMENT_AND_VALIDATION.md"
    codebase_path = mainline / "CODEBASE_MAP.md"
    state_machine_path = mainline / "SUPERVISOR_STATE_MACHINE.md"
    decision_log_path = mainline / "DECISION_LOG.md"
    execution_ticket_path = mainline / "CURRENT_EXECUTION_TICKET.md"
    runbook_path = repo / "docs/runbooks/mainline_phase_gate_runbook.md"
    agents_path = repo / "AGENTS.md"
    start_auto_path = repo / "START_AUTOMATION.md"
    reg_path = mainline / "gates/REGISTRY.json"
    active_gate_path = mainline / "gates/active_gate.json"
    recovery_summary_path = mainline / "recovery/RECOVERY_SUMMARY.md"
    prompt_used_latest_path = reports / "prompt_used_latest.md"
    phase_path = reports / "phase_gate_latest.txt"
    acc_path = reports / "acceptance_latest.txt"
    ev_path = reports / "evidence_latest.txt"

    views = {
        "brief": mainline / "CURRENT_LOOP_BRIEF.md",
        "state": mainline / "loop_state_latest.json",
        "pack": mainline / "CURRENT_GATE_PACK.md",
        "web_brief": mainline / "WEB_SESSION_BRIEF.md",
        "control_state": mainline / "state/CONTROL_PLANE_STATE.json",
    }
    missing = [name for name, path in views.items() if not path.exists()]
    if missing:
        print(f"STALE: missing derived views: {missing}")
        return 1

    try:
        state = json.loads(views["state"].read_text(encoding="utf-8"))
        control_state = json.loads(views["control_state"].read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"STALE: cannot parse derived state json: {exc}")
        return 1

    sources = [
        status_path,
        metrics_path,
        evidence_path,
        failure_path,
        constitution_path,
        plan_path,
        implement_path,
        env_path,
        codebase_path,
        state_machine_path,
        decision_log_path,
        execution_ticket_path,
        runbook_path,
        agents_path,
        start_auto_path,
        recovery_summary_path,
        prompt_used_latest_path,
        phase_path,
        acc_path,
        ev_path,
    ]
    gate_def = None
    active_gate_reg = None
    if reg_path.exists():
        sources.append(reg_path)
        try:
            reg = json.loads(reg_path.read_text(encoding="utf-8"))
            active_gate_reg = reg.get("active_scientific_gate")
            if isinstance(reg.get("gates"), dict) and active_gate_reg in reg.get("gates", {}):
                df = reg["gates"][active_gate_reg].get("definition_file")
                if df:
                    gate_def = repo / df
        except Exception:
            print("CONFLICTED: cannot parse REGISTRY.json")
            return 1
    if active_gate_path.exists():
        sources.append(active_gate_path)
    if gate_def and gate_def.exists():
        sources.append(gate_def)
    current_digest = digest_sources(sources)

    pack_md = views["pack"].read_text(encoding="utf-8", errors="ignore")
    if "pack_quality: `degraded`" in pack_md or state.get("pack_quality") == "degraded":
        print("STALE: CURRENT_GATE_PACK is degraded; fall back to canonical docs and regenerate after gate/rule clarification")
        return 1

    for name, obj in {"loop_state_latest.json": state, "CONTROL_PLANE_STATE.json": control_state}.items():
        if obj.get("source_digest", "") != current_digest:
            print(f"CONFLICTED: {name} source_digest mismatch; regenerate derived views")
            print(f"  recorded: {obj.get('source_digest', '')[:12]}")
            print(f"  current : {current_digest[:12]}")
            return 1

    status_md = read_text(status_path)
    gate_now = parse_field(status_md, r"^- Active gate:\s*`?([^`\n]+)`?\s*$")
    gate_recorded = state.get("active_gate", "")
    if gate_now != gate_recorded:
        print("CONFLICTED: active gate mismatch; regenerate derived views")
        print(f"  status: {gate_now}")
        print(f"  state : {gate_recorded}")
        return 1

    sci_now = parse_field(status_md, r"^- Active scientific gate:\s*`?([^`\n]+)`?\s*$")
    sci_recorded = state.get("active_scientific_gate", "")
    if sci_recorded and sci_now != sci_recorded:
        print("CONFLICTED: active scientific gate mismatch; regenerate derived views")
        print(f"  status: {sci_now}")
        print(f"  state : {sci_recorded}")
        return 1

    if control_state.get("active_gate") != state.get("active_gate"):
        print("CONFLICTED: CONTROL_PLANE_STATE active gate mismatch; regenerate derived views")
        return 1

    if control_state.get("current_execution_ticket") != "docs/mainline/CURRENT_EXECUTION_TICKET.md":
        print("CONFLICTED: CONTROL_PLANE_STATE current_execution_ticket pointer unexpected")
        return 1

    if active_gate_reg and sci_now and sci_now != "not-yet-declared":
        if gate_id(sci_now) != active_gate_reg:
            print("CONFLICTED: STATUS active scientific gate id differs from registry active_scientific_gate")
            print(f"  status sci gate id: {gate_id(sci_now)}")
            print(f"  registry active    : {active_gate_reg}")
            return 1

    print("OK: derived state views match canonical sources")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
