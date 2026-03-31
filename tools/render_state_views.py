#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


def compact(text: str, limit: int = 600) -> str:
    text = re.sub(r"\s+", " ", text.strip())
    return text[:limit] if text else "not-yet-declared"


def digest_sources(paths: list[Path]) -> str:
    h = hashlib.sha256()
    for p in paths:
        h.update(str(p).encode())
        if p.exists():
            h.update(p.read_bytes())
        else:
            h.update(b"MISSING")
    return h.hexdigest()


def extract_section(md: str, heading: str) -> str:
    m = re.search(rf"^##\s+{re.escape(heading)}\s*$", md, flags=re.M)
    if not m:
        return ""
    start = m.end()
    m2 = re.search(r"^##\s+", md[start:], flags=re.M)
    end = start + m2.start() if m2 else len(md)
    return md[start:end].strip()


def parse_status(status_md: str) -> dict[str, str]:
    mapping = {
        "active_gate": r"^- Active gate:\s*`?([^`\n]+)`?\s*$",
        "active_scientific_gate": r"^- Active scientific gate:\s*`?([^`\n]+)`?\s*$",
        "evidence_tier": r"^- Current evidence tier:\s*`?([^`\n]+)`?\s*$",
        "scientific_status": r"^- Scientific status:\s*`?([^`\n]+)`?\s*$",
        "engineering_status": r"^- Engineering support status:\s*`?([^`\n]+)`?\s*$",
        "overall_status": r"^- Overall progression eligibility:\s*`?([^`\n]+)`?\s*$",
        "sync_mode": r"^- Current sync mode:\s*`?([^`\n]+)`?\s*$",
        "local_snapshot_id": r"^- Local snapshot id:\s*`?([^`\n]+)`?\s*$",
        "remote_snapshot_id": r"^- Remote snapshot id:\s*`?([^`\n]+)`?\s*$",
        "takeover_refreshed_at": r"^- Takeover refreshed at:\s*`?([^`\n]+)`?\s*$",
        "listener_status": r"^- Local latest-doc listener status:\s*`?([^`\n]+)`?\s*$",
    }
    out = {}
    for key, pat in mapping.items():
        m = re.search(pat, status_md, flags=re.M)
        out[key] = m.group(1).strip() if m else "not-yet-declared"
    out["blocker_summary"] = compact(extract_section(status_md, "Current blockers"), 1200)
    out["next_step"] = compact(extract_section(status_md, "Next smallest valid step"), 400)
    out["active_experiments"] = compact(extract_section(status_md, "Active experiments"), 800)
    return out


def parse_ticket_fields(ticket_md: str) -> dict:
    fields: dict[str, str] = {}
    for line in ticket_md.splitlines():
        m = re.match(r"^-\s+([a-zA-Z0-9_]+):\s*`?([^`]+?)`?\s*$", line.strip())
        if m:
            fields[m.group(1)] = m.group(2).strip()

    def sec(name: str, limit: int = 500):
        return compact(extract_section(ticket_md, name), limit)

    def as_bool(key: str) -> bool:
        return str(fields.get(key, "false")).strip().lower() == "true"

    allowed_tools_raw = fields.get("allowed_tools", "not-yet-declared")
    allowed_tools = [] if allowed_tools_raw in {"not-yet-declared", ""} else [x.strip() for x in allowed_tools_raw.split(",") if x.strip()]
    must_not_raw = fields.get("must_not_edit_manually", "experiment_registry,indexes,takeover_ledger")
    must_not = [x.strip() for x in must_not_raw.split(",") if x.strip()]

    return {
        "objective": sec("Objective", 400),
        "active_gate": fields.get("active_gate", "not-yet-declared"),
        "active_scientific_gate": fields.get("active_scientific_gate", "not-yet-declared"),
        "evidence_tier": fields.get("evidence_tier", "not-yet-declared"),
        "formal_standard_version": fields.get("formal_standard_version", "not-yet-declared"),
        "role_boundary_ack": fields.get("role_boundary_ack", "required"),
        "execution_location": fields.get("execution_location", "local_first"),
        "remote_execution_required": as_bool("remote_execution_required"),
        "long_running": as_bool("long_running"),
        "watcher_required": as_bool("watcher_required"),
        "listener_required": as_bool("listener_required"),
        "requires_takeover_refresh": as_bool("requires_takeover_refresh"),
        "git_boundary": as_bool("git_boundary"),
        "experiment_id": fields.get("experiment_id", "not-yet-declared"),
        "run_id": fields.get("run_id", "not-yet-declared"),
        "question_type": fields.get("question_type", "not-yet-declared"),
        "level": fields.get("level", "not-yet-declared"),
        "eligible_for_gate_judgment": as_bool("eligible_for_gate_judgment"),
        "expected_next_status": fields.get("expected_next_status", "not-yet-declared"),
        "allowed_tools": allowed_tools,
        "must_not_edit_manually": must_not,
        "delivery_mode": fields.get("delivery_mode", "prompt"),
        "design_pack_required": as_bool("design_pack_required"),
        "design_pack_id": fields.get("design_pack_id", "not-yet-declared"),
        "design_pack_status": fields.get("design_pack_status", "not-yet-declared"),
        "allowed_design_deviation": as_bool("allowed_design_deviation"),
        "branch_role": fields.get("branch_role", "not-yet-declared"),
        "writeback_scope": fields.get("writeback_scope", "not-yet-declared"),
        "parallel_group_id": fields.get("parallel_group_id", "not-yet-declared"),
        "branch_summary_path": fields.get("branch_summary_path", "not-yet-declared"),
        "branch_artifact_root": fields.get("branch_artifact_root", "not-yet-declared"),
        "milestone_id": fields.get("milestone_id", "not-yet-declared"),
        "code_change_expected": as_bool("code_change_expected"),
        "runtime_override_only": as_bool("runtime_override_only"),
        "commit_sha": fields.get("commit_sha", "not-yet-declared"),
        "tree_sha": fields.get("tree_sha", "not-yet-declared"),
        "working_tree_clean": fields.get("working_tree_clean", "not-yet-declared"),
        "local_snapshot_id": fields.get("local_snapshot_id", "not-yet-declared"),
        "remote_snapshot_id": fields.get("remote_snapshot_id", "not-yet-declared"),
        "remote_tree_verified": fields.get("remote_tree_verified", "not-yet-declared"),
        "config_snapshot_path": fields.get("config_snapshot_path", "not-yet-declared"),
        "governance_ingestion_note": fields.get("governance_ingestion_note", "not-yet-declared"),
        "archive_sync_note": fields.get("archive_sync_note", "not-yet-declared"),
        "formal_pass": sec("Formal PASS requires", 500),
        "allowed_scope": sec("Allowed execution scope", 500),
        "resume_note": sec("Resume / re-entry note", 300),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", default=".")
    args = ap.parse_args()
    repo = Path(args.repo_root).resolve()
    mainline = repo / "docs/mainline"
    reports = mainline / "reports"
    state_dir = mainline / "state"
    state_dir.mkdir(parents=True, exist_ok=True)

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
    src_digest = digest_sources(sources)

    status = parse_status(read_text(mainline / "STATUS.md"))
    try:
        gate_reg = json.loads(read_text(mainline / "gates/REGISTRY.json")) if (mainline / "gates/REGISTRY.json").exists() else {}
    except Exception:
        gate_reg = {}
    try:
        exp_reg = json.loads(read_text(mainline / "experiments/REGISTRY.json")) if (mainline / "experiments/REGISTRY.json").exists() else {"experiments": []}
    except Exception:
        exp_reg = {"experiments": []}

    ticket_md = read_text(mainline / "CURRENT_EXECUTION_TICKET.md")
    ticket = parse_ticket_fields(ticket_md)
    (state_dir / "CURRENT_EXECUTION_TICKET.json").write_text(json.dumps(ticket, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    state_version = hashlib.sha256(read_text(mainline / "STATUS.md").encode()).hexdigest()[:12]
    active_statuses = {"approved", "prepared", "running", "summarized", "reviewed", "interrupted", "failed"}
    active_experiments = [
        e for e in exp_reg.get("experiments", [])
        if e.get("status") in active_statuses and not bool(e.get("placeholder", False))
    ]
    prepared_placeholders = [
        e for e in exp_reg.get("experiments", [])
        if e.get("status") == "prepared" and bool(e.get("placeholder", False))
    ]

    loop_state = {
        "generated_at": now(),
        "source_digest": src_digest,
        "state_version": state_version,
        "active_gate": status.get("active_gate", "not-yet-declared"),
        "active_gate_id": status.get("active_gate", "not-yet-declared"),
        "active_scientific_gate": status.get("active_scientific_gate", "not-yet-declared"),
        "evidence_tier": status.get("evidence_tier", "not-yet-declared"),
        "scientific_status": status.get("scientific_status", "not-yet-declared"),
        "engineering_status": status.get("engineering_status", "not-yet-declared"),
        "overall_status": status.get("overall_status", "not-yet-declared"),
        "blocker_summary": status.get("blocker_summary", "not-yet-generated"),
        "next_step": status.get("next_step", "not-yet-declared"),
        "listener_status": status.get("listener_status", "not-yet-declared"),
        "current_sync_mode": status.get("sync_mode", "not-yet-declared"),
        "local_snapshot_id": status.get("local_snapshot_id", "not-yet-declared"),
        "remote_snapshot_id": status.get("remote_snapshot_id", "not-yet-declared"),
        "takeover_path": "docs/mainline/takeover/TAKEOVER_LATEST.md",
        "ticket_machine_state_path": "docs/mainline/state/CURRENT_EXECUTION_TICKET.json",
        "experiment_registry_path": "docs/mainline/experiments/REGISTRY.json",
        "active_experiment_count": len(active_experiments),
        "prepared_placeholder_count": len(prepared_placeholders),
        "pack_quality": "full" if gate_reg else "degraded",
    }
    (mainline / "loop_state_latest.json").write_text(json.dumps(loop_state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    brief = f"""# Current Loop Brief (Derived View)

- generated_at: `{loop_state['generated_at']}`
- source_digest: `{src_digest}`
- state_version: `{state_version}`

## Current gate & tier
- active_gate: `{loop_state['active_gate']}`
- active_scientific_gate: `{loop_state['active_scientific_gate']}`
- evidence_tier: `{loop_state['evidence_tier']}`

## Current blocker summary
{loop_state['blocker_summary']}

## Next smallest valid step
{loop_state['next_step']}

## Current execution scope objective
{ticket['objective']}

## Active experiments
- count: `{len(active_experiments)}`
- registry: `docs/mainline/experiments/REGISTRY.json`

## Prepared placeholders
- count: `{len(prepared_placeholders)}`

## Primary handoff artifact
- `docs/mainline/takeover/TAKEOVER_LATEST.md`
"""
    (mainline / "CURRENT_LOOP_BRIEF.md").write_text(brief + "\n", encoding="utf-8")

    gate_pack = f"""# Current Gate Pack (Derived View)

- generated_at: `{now()}`
- source_digest: `{src_digest}`
- active_gate: `{loop_state['active_gate']}`
- active_scientific_gate: `{loop_state['active_scientific_gate']}`
- pack_quality: `{loop_state['pack_quality']}`

Read the active gate doc, current ticket machine-state, experiment rules, and latest reports for the formal contract.
"""
    (mainline / "CURRENT_GATE_PACK.md").write_text(gate_pack + "\n", encoding="utf-8")

    control_state = {
        "generated_at": now(),
        "source_digest": src_digest,
        "state_version": state_version,
        "active_gate": loop_state["active_gate"],
        "active_gate_id": loop_state["active_gate_id"],
        "active_gate_file": "not-yet-declared",
        "active_gate_version": "not-yet-declared",
        "gate_registry_version": gate_reg.get("version", "absent") if isinstance(gate_reg, dict) else "absent",
        "active_scientific_gate": loop_state["active_scientific_gate"],
        "evidence_tier": loop_state["evidence_tier"],
        "scientific_status": loop_state["scientific_status"],
        "engineering_status": loop_state["engineering_status"],
        "overall_status": loop_state["overall_status"],
        "decision_log": "docs/mainline/DECISION_LOG.md",
        "latest_review_packet": "docs/mainline/postrun/latest/latest_review_packet.json",
        "latest_code_provenance_report": "docs/mainline/reports/code_provenance_report_latest.json",
        "current_execution_ticket": "docs/mainline/CURRENT_EXECUTION_TICKET.md",
        "current_execution_ticket_machine_state": "docs/mainline/state/CURRENT_EXECUTION_TICKET.json",
        "takeover_latest_path": "docs/mainline/takeover/TAKEOVER_LATEST.md",
        "takeover_last_updated": status.get("takeover_refreshed_at", "not-yet-declared"),
        "active_jobs_registry_path": "docs/mainline/state/ACTIVE_JOBS.json",
        "listener_registry_path": "docs/mainline/state/LISTENER_REGISTRY.json",
        "snapshot_state_path": "docs/mainline/state/SNAPSHOT_STATE.json",
        "experiment_registry_path": "docs/mainline/experiments/REGISTRY.json",
        "default_sync_mode": "ssh_snapshot",
        "role_model_version": "v5p4-lite",
        "watcher_policy_version": "v5p4-lite",
        "experiment_policy_version": "v5p4-lite",
    }
    (state_dir / "CONTROL_PLANE_STATE.json").write_text(json.dumps(control_state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    web = f"""# Web Session Brief (Derived View)

- generated_at: `{now()}`
- source_digest: `{src_digest}`
- state_version: `{state_version}`

## Current control-plane snapshot
- active_gate: `{loop_state['active_gate']}`
- active_scientific_gate: `{loop_state['active_scientific_gate']}`
- evidence_tier: `{loop_state['evidence_tier']}`
- scientific_status: `{loop_state['scientific_status']}`
- engineering_status: `{loop_state['engineering_status']}`
- overall_status: `{loop_state['overall_status']}`
- active_experiments: `{len(active_experiments)}`

## Primary handoff artifact
- `docs/mainline/takeover/TAKEOVER_LATEST.md`
"""
    (mainline / "WEB_SESSION_BRIEF.md").write_text(web + "\n", encoding="utf-8")
    print(f"Rendered derived state views for {repo.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
