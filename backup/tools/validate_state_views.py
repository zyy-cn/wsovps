#!/usr/bin/env python3
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


def parse_field(status_md: str, pattern: str, default: str = "not-yet-declared") -> str:
    m = re.search(pattern, status_md, flags=re.M)
    return m.group(1).strip() if m else default


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", default=".")
    args = ap.parse_args()
    repo = Path(args.repo_root).resolve()
    mainline = repo / "docs/mainline"
    reports = mainline / "reports"
    state_dir = mainline / "state"
    views = {
        "brief": mainline / "CURRENT_LOOP_BRIEF.md",
        "state": mainline / "loop_state_latest.json",
        "pack": mainline / "CURRENT_GATE_PACK.md",
        "web_brief": mainline / "WEB_SESSION_BRIEF.md",
        "control_state": state_dir / "CONTROL_PLANE_STATE.json",
        "ticket_state": state_dir / "CURRENT_EXECUTION_TICKET.json",
    }
    missing = [k for k, p in views.items() if not p.exists()]
    if missing:
        print(f"STALE: missing derived views: {missing}")
        return 1
    try:
        state = json.loads(views["state"].read_text(encoding="utf-8"))
        control = json.loads(views["control_state"].read_text(encoding="utf-8"))
        ticket = json.loads(views["ticket_state"].read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"STALE: cannot parse derived state json: {exc}")
        return 1

    sources = [
        mainline / "STATUS.md",
        mainline / "METRICS_ACCEPTANCE.md",
        mainline / "EVIDENCE_REQUIREMENTS.md",
        mainline / "FAILURE_PLAYBOOK.md",
        mainline / "OPERATING_CONSTITUTION.md",
        mainline / "PLAN.md",
        mainline / "IMPLEMENT.md",
        mainline / "ENVIRONMENT_AND_VALIDATION.md",
        mainline / "CODEBASE_MAP.md",
        mainline / "SUPERVISOR_STATE_MACHINE.md",
        mainline / "DECISION_LOG.md",
        mainline / "CURRENT_EXECUTION_TICKET.md",
        mainline / "ROLE_CHARTER.md",
        mainline / "SYNC_AND_EXECUTION_POLICY.md",
        mainline / "LISTENER_WATCHER_POLICY.md",
        mainline / "REMOTE_SUMMARY_PROTOCOL.md",
        mainline / "TAKEOVER_PROTOCOL.md",
        mainline / "EXPERIMENT_MANAGEMENT_POLICY.md",
        mainline / "experiments/AGENTS.md",
        mainline / "experiments/STATE_TRANSITIONS.md",
        mainline / "experiments/REGISTRY.json",
        reports / "phase_gate_latest.txt",
        reports / "acceptance_latest.txt",
        reports / "evidence_latest.txt",
        reports / "remote_job_summary_latest.md",
        reports / "code_provenance_report_latest.json",
        reports / "code_provenance_report_latest.md",
        mainline / "gates/REGISTRY.json",
        mainline / "postrun/latest/latest_review_packet.json",
        mainline / "postrun/latest/latest_review_packet.md",
        mainline / "gates/active_gate.json",
        state_dir / "ACTIVE_JOBS.json",
        state_dir / "LISTENER_REGISTRY.json",
        state_dir / "SNAPSHOT_STATE.json",
    ]
    current_digest = digest_sources(sources)
    if state.get("source_digest") != current_digest or control.get("source_digest") != current_digest:
        print("CONFLICTED: source_digest mismatch; regenerate derived views")
        return 1
    status_md = (mainline / "STATUS.md").read_text(encoding="utf-8", errors="ignore")
    gate_now = parse_field(status_md, r"^- Active gate:\s*`?([^`\n]+)`?\s*$")
    if gate_now != state.get("active_gate"):
        print("CONFLICTED: active gate mismatch; regenerate derived views")
        return 1
    if control.get("takeover_latest_path") != "docs/mainline/takeover/TAKEOVER_LATEST.md":
        print("CONFLICTED: CONTROL_PLANE_STATE takeover pointer unexpected")
        return 1
    if "experiment_id" not in ticket or "question_type" not in ticket:
        print("CONFLICTED: ticket machine-state missing experiment keys")
        return 1
    print("OK: derived state views match canonical sources")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
