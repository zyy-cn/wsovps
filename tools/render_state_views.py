#!/usr/bin/env python3
"""Generate low-token derived views from canonical mainline docs.

Outputs:
- docs/mainline/CURRENT_LOOP_BRIEF.md
- docs/mainline/loop_state_latest.json
- docs/mainline/CURRENT_GATE_PACK.md
- docs/mainline/WEB_SESSION_BRIEF.md
- docs/mainline/state/CONTROL_PLANE_STATE.json

Anti-drift rule:
- Derived views never override canonical docs.
- If contracts are not machine-extractable, gate pack is emitted in degraded mode and points back to canonical docs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def sha256_file(path: Path) -> str:
    if not path.exists():
        return "missing"
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def compact(text: str, limit: int = 800) -> str:
    text = re.sub(r"\s+", " ", text.strip())
    return text[:limit] if text else "not-yet-declared"


def parse_status(status_md: str) -> dict[str, str]:
    out: dict[str, str] = {}
    patterns = {
        "active_gate": r"^- Active gate:\s*`?([^`\n]+)`?\s*$",
        "active_scientific_gate": r"^- Active scientific gate:\s*`?([^`\n]+)`?\s*$",
        "evidence_tier": r"^- Current evidence tier:\s*`?([^`\n]+)`?\s*$",
        "scientific_status": r"^- Scientific status:\s*`?([^`\n]+)`?\s*$",
        "engineering_status": r"^- Engineering support status:\s*`?([^`\n]+)`?\s*$",
        "overall_status": r"^- Overall progression eligibility:\s*`?([^`\n]+)`?\s*$",
        "listener_status": r"^- Local latest-doc listener status:\s*`?([^`\n]+)`?\s*$",
        "web_cold_start_ready": r"^- Web-session cold-start readiness:\s*`?([^`\n]+)`?\s*$",
    }
    for key, pat in patterns.items():
        m = re.search(pat, status_md, flags=re.MULTILINE)
        if m:
            out[key] = m.group(1).strip()

    section_patterns = [
        ("next_step", r"## Next smallest valid step\n(.*?)\n\n## Latest evidence"),
        ("reentry_condition", r"## Re-entry condition\n(.*?)\n\n## Latest evidence artifact pointers"),
        ("blocker_summary", r"## Current blockers\n(.*?)\n\n## Canonical environment evidence tracker"),
        ("latest_evidence", r"## Latest evidence\n(.*?)\n\n## Re-entry condition"),
    ]
    for key, pat in section_patterns:
        m = re.search(pat, status_md, flags=re.DOTALL)
        if m:
            out[key] = compact(m.group(1), 1000 if key == "latest_evidence" else 700)
    return out


def gate_id_from_label(label: str) -> str:
    label = label.strip()
    if not label:
        return "not-yet-declared"
    parts = re.split(r"\s+—\s+|\s+-\s+|\s+", label, maxsplit=1)
    return parts[0].strip() if parts else label


def extract_block(text: str, kind: str, gate: str) -> str | None:
    start = rf"<!--\s*{kind}_START:{re.escape(gate)}\s*-->"
    end = rf"<!--\s*{kind}_END:{re.escape(gate)}\s*-->"
    m = re.search(start + r"(.*?)" + end, text, flags=re.DOTALL)
    return m.group(1).strip() if m else None


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def extract_sections_numbered(md: str) -> dict[str, str]:
    parts: dict[str, str] = {}
    matches = list(re.finditer(r"^##\s+(\d+)\.\s+(.+?)\s*$", md, flags=re.MULTILINE))
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(md)
        parts[m.group(1)] = md[start:end].strip()
    return parts


def extract_section(md: str, heading: str) -> str:
    pat = rf"^##\s+{re.escape(heading)}\s*$"
    m = re.search(pat, md, flags=re.MULTILINE)
    if not m:
        return ""
    start = m.end()
    next_h = re.search(r"^##\s+", md[start:], flags=re.MULTILINE)
    end = start + next_h.start() if next_h else len(md)
    return md[start:end].strip()


def extract_subsection(md: str, heading: str) -> str:
    pat = rf"^###\s+{re.escape(heading)}\s*$"
    m = re.search(pat, md, flags=re.MULTILINE)
    if not m:
        return ""
    start = m.end()
    next_h = re.search(r"^###\s+|^##\s+", md[start:], flags=re.MULTILINE)
    end = start + next_h.start() if next_h else len(md)
    return md[start:end].strip()


def parse_decision_log(md: str) -> dict[str, str]:
    latest = extract_section(md, "Latest approved decision")
    if not latest:
        return {
            "summary": "not-yet-declared",
            "formal_pass": "not-yet-declared",
            "allowed_scope": "not-yet-declared",
            "not_allowed": "not-yet-declared",
        }
    return {
        "summary": compact(extract_subsection(latest, "Summary"), 600),
        "formal_pass": compact(extract_subsection(latest, "Formal PASS requires"), 600),
        "allowed_scope": compact(extract_subsection(latest, "Allowed execution scope"), 600),
        "not_allowed": compact(extract_subsection(latest, "Not allowed"), 400),
    }


def parse_execution_ticket(md: str) -> dict[str, str]:
    return {
        "objective": compact(extract_section(md, "Objective"), 500),
        "formal_pass": compact(extract_section(md, "Formal PASS requires"), 600),
        "allowed_scope": compact(extract_section(md, "Allowed execution scope"), 600),
        "not_allowed": compact(extract_section(md, "Not allowed this round"), 400),
        "resume_note": compact(extract_section(md, "Resume / re-entry note"), 400),
    }


def extract_formal_standard(metrics_md: str, gate_md: str = "") -> str:
    if gate_md:
        parts = extract_sections_numbered(gate_md)
        sec = parts.get("5")
        if sec:
            return compact(sec, 800)
    m = re.search(r"##\s+2\.\s+Mainline metric priority(.*?)(?:\n##\s+3\.|\Z)", metrics_md, flags=re.S)
    if m:
        return compact(m.group(1), 800)
    return "Read the active gate document and canonical metrics/evidence files."


def required_outputs_list() -> list[str]:
    return [
        "docs/mainline/reports/phase_gate_latest.txt",
        "docs/mainline/reports/acceptance_latest.txt",
        "docs/mainline/reports/evidence_latest.txt",
        "docs/mainline/reports/worked_example_verification_latest.md (if required)",
        "docs/mainline/reports/worked_example_verification_latest.json (if required)",
        "docs/mainline/reports/training_watch_latest.txt (if wait-state/watcher used)",
        "docs/mainline/CURRENT_LOOP_BRIEF.md (regenerate)",
        "docs/mainline/loop_state_latest.json (regenerate)",
        "docs/mainline/CURRENT_GATE_PACK.md (regenerate on gate change)",
        "docs/mainline/WEB_SESSION_BRIEF.md (regenerate)",
        "docs/mainline/state/CONTROL_PLANE_STATE.json (regenerate)",
    ]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", default=".")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    mainline = repo / "docs/mainline"
    reports = mainline / "reports"
    state_dir = mainline / "state"
    state_dir.mkdir(parents=True, exist_ok=True)

    reg_path = mainline / "gates/REGISTRY.json"
    active_gate_path = mainline / "gates/active_gate.json"
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
    recovery_summary_path = mainline / "recovery/RECOVERY_SUMMARY.md"
    prompt_used_latest_path = reports / "prompt_used_latest.md"
    phase_path = reports / "phase_gate_latest.txt"
    acc_path = reports / "acceptance_latest.txt"
    ev_path = reports / "evidence_latest.txt"

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

    gate_def_path: Path | None = None
    reg: dict | None = None
    active_gate_id_registry: str | None = None
    active_gate_ver_registry: str | None = None
    if reg_path.exists():
        try:
            reg = load_json(reg_path)
            active_gate_id_registry = reg.get("active_scientific_gate")
            if isinstance(reg.get("gates"), dict) and active_gate_id_registry in reg.get("gates", {}):
                ent = reg["gates"][active_gate_id_registry]
                gate_def_path = repo / ent.get("definition_file", "")
                active_gate_ver_registry = ent.get("version")
        except Exception:
            reg = None
    if reg_path.exists():
        sources.append(reg_path)
    if active_gate_path.exists():
        sources.append(active_gate_path)
    if gate_def_path and gate_def_path.exists():
        sources.append(gate_def_path)
    src_digest = digest_sources(sources)

    status_md = read_text(status_path)
    metrics_md = read_text(metrics_path)
    st = parse_status(status_md)
    decision = parse_decision_log(read_text(decision_log_path))
    ticket = parse_execution_ticket(read_text(execution_ticket_path))

    gate_label = st.get("active_scientific_gate") or st.get("active_gate", "not-yet-declared")
    gate_id_status = gate_id_from_label(gate_label)
    gate_id = active_gate_id_registry or gate_id_status

    pack_quality = "degraded"
    pack_body = ""
    gate_md = ""
    if gate_def_path and gate_def_path.exists():
        gate_md = read_text(gate_def_path)
        secs = extract_sections_numbered(gate_md)
        key_nums = ["1", "2", "4", "5", "6", "7", "8", "9", "10", "11"]
        names = {
            "1": "Purpose",
            "2": "Claim / Control Goal",
            "4": "Smoke Standard",
            "5": "Formal Standard",
            "6": "Required Metrics",
            "7": "Judgment Rule",
            "8": "Evidence Requirements",
            "9": "Out of Scope",
            "10": "Fallback / Next Step Rule",
            "11": "Re-entry Condition",
        }
        parts = []
        for n in key_nums:
            if n in secs and secs[n].strip():
                parts.append(f"## {n}. {names[n]}\n\n{secs[n].strip()}")
        pack_quality = "full" if len(parts) >= 6 else "degraded"
        pack_body = "\n\n".join(parts) if parts else ""
        if not pack_body:
            pack_body = (
                "This pack is in **degraded** mode because the active gate document does not contain expected numbered sections.\n\n"
                f"Gate doc: `{gate_def_path}`\n"
            )
    else:
        contract = extract_block(metrics_md, "GATE_CONTRACT", gate_id)
        evid = extract_block(read_text(evidence_path), "GATE_EVIDENCE", gate_id)
        pack_quality = "full" if (contract and evid) else "degraded"
        if pack_quality == "full":
            pack_body = "## Gate goal and acceptance contract\n\n" + contract + "\n\n## Evidence requirements\n\n" + evid
        else:
            pack_body = (
                "This pack is in **degraded** mode because a registry-backed gate doc was not found and machine-extractable blocks were not found.\n\n"
                "Preferred mode: use gate registry + gate docs.\n\n"
                "Canonical pointers:\n"
                f"- {metrics_path}\n- {evidence_path}\n- {failure_path}\n"
            )

    gate_pack_path = mainline / "CURRENT_GATE_PACK.md"
    header = (
        "# Current Gate Pack (Derived View)\n\n"
        "**Derived view / anti-drift notice:** canonical docs outrank this pack.\n\n"
        f"- generated_at: `{now()}`\n"
        f"- source_digest: `{src_digest}`\n"
        f"- active_gate_id: `{gate_id}`\n"
        f"- active_gate_label: `{gate_label}`\n"
    )
    if gate_def_path and gate_def_path.exists():
        header += f"- active_gate_file: `{str(gate_def_path.relative_to(repo))}`\n"
    if active_gate_ver_registry:
        header += f"- active_gate_version: `{active_gate_ver_registry}`\n"
    header += f"- pack_quality: `{pack_quality}`\n\n"
    gate_pack_path.write_text(header + pack_body + "\n", encoding="utf-8")

    formal_standard = extract_formal_standard(metrics_md, gate_md)
    state_version = sha256_file(status_path)[:12]
    loop_state = {
        "generated_at": now(),
        "source_digest": src_digest,
        "state_version": state_version,
        "active_gate": gate_label,
        "active_gate_id": gate_id,
        "active_gate_file": str(gate_def_path.relative_to(repo)) if gate_def_path and gate_def_path.exists() else "not-yet-declared",
        "active_gate_version": active_gate_ver_registry or "not-yet-declared",
        "gate_registry_version": reg.get("version") if reg else "absent",
        "active_scientific_gate": st.get("active_scientific_gate", "not-yet-declared"),
        "evidence_tier": st.get("evidence_tier", "not-yet-declared"),
        "scientific_status": st.get("scientific_status", "not-yet-declared"),
        "engineering_status": st.get("engineering_status", "not-yet-declared"),
        "overall_status": st.get("overall_status", "not-yet-declared"),
        "blocker_summary": st.get("blocker_summary", "not-yet-generated"),
        "next_step": st.get("next_step", "not-yet-declared"),
        "formal_standard_reminder": formal_standard,
        "reentry_condition": st.get("reentry_condition", "not-yet-declared"),
        "listener_status": st.get("listener_status", "not-yet-declared"),
        "current_gate_pack": "docs/mainline/CURRENT_GATE_PACK.md",
        "pack_quality": pack_quality,
        "recovery_mode": "present" if recovery_summary_path.exists() else "absent",
        "prompt_archive_status": "present" if prompt_used_latest_path.exists() else "absent",
    }
    (mainline / "loop_state_latest.json").write_text(json.dumps(loop_state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    required_outputs = "".join(f"- `{x}`\n" for x in required_outputs_list())
    brief_text = (
        "# Current Loop Brief (Derived View)\n\n"
        "**Derived view / anti-drift notice:** validate before use; canonical docs outrank this view.\n\n"
        f"- generated_at: `{now()}`\n"
        f"- source_digest: `{src_digest}`\n"
        f"- state_version: `{state_version}`\n\n"
        "## Read protocol (default)\n"
        "1) Validate state views: `python tools/validate_state_views.py`\n"
        "2) If OK, read only: `CURRENT_LOOP_BRIEF.md`, `loop_state_latest.json`, `CURRENT_GATE_PACK.md`, `CURRENT_EXECUTION_TICKET.md`, plus latest reports.\n"
        "3) If STALE/CONFLICTED, read canonical control plane and regenerate: `python tools/render_state_views.py`.\n\n"
        "## Current gate & tier\n"
        f"- active_gate: `{loop_state['active_gate']}`\n"
        f"- active_scientific_gate: `{loop_state['active_scientific_gate']}`\n"
        f"- evidence_tier: `{loop_state['evidence_tier']}`\n\n"
        "## Current blocker summary\n"
        f"{loop_state['blocker_summary']}\n\n"
        "## Next smallest valid step\n"
        f"{loop_state['next_step']}\n\n"
        "## Formal standard reminder\n"
        f"{formal_standard}\n\n"
        "## Re-entry condition\n"
        f"{loop_state['reentry_condition']}\n\n"
        "## Current execution scope objective\n"
        f"{ticket['objective']}\n\n"
        "## Required outputs this iteration\n"
        f"{required_outputs}\n"
        "## Pointers\n"
        "- constitution: `docs/mainline/OPERATING_CONSTITUTION.md`\n"
        "- canonical status: `docs/mainline/STATUS.md`\n"
        "- decision log: `docs/mainline/DECISION_LOG.md`\n"
        "- gate registry (if enabled): `docs/mainline/gates/REGISTRY.json`\n"
        "- current gate pack: `docs/mainline/CURRENT_GATE_PACK.md`\n"
        "- current execution ticket: `docs/mainline/CURRENT_EXECUTION_TICKET.md`\n"
        "- web session brief: `docs/mainline/WEB_SESSION_BRIEF.md`\n"
        "- machine-readable control state: `docs/mainline/state/CONTROL_PLANE_STATE.json`\n"
        "- latest reports: `docs/mainline/reports/*latest*`\n"
        "- recovery summary (if any): `docs/mainline/recovery/RECOVERY_SUMMARY.md`\n"
        "- prompt archive (if any): `docs/mainline/reports/prompt_used_latest.md`\n"
    )
    (mainline / "CURRENT_LOOP_BRIEF.md").write_text(brief_text, encoding="utf-8")

    control_state = {
        "generated_at": now(),
        "source_digest": src_digest,
        "state_version": state_version,
        "active_gate": loop_state["active_gate"],
        "active_gate_id": gate_id,
        "active_gate_file": loop_state["active_gate_file"],
        "active_gate_version": loop_state["active_gate_version"],
        "gate_registry_version": loop_state["gate_registry_version"],
        "active_scientific_gate": loop_state["active_scientific_gate"],
        "evidence_tier": loop_state["evidence_tier"],
        "scientific_status": loop_state["scientific_status"],
        "engineering_status": loop_state["engineering_status"],
        "overall_status": loop_state["overall_status"],
        "blocker_summary": loop_state["blocker_summary"],
        "next_step": loop_state["next_step"],
        "reentry_condition": loop_state["reentry_condition"],
        "formal_standard_reminder": formal_standard,
        "listener_status": loop_state["listener_status"],
        "web_cold_start_ready": st.get("web_cold_start_ready", "not-yet-declared"),
        "decision_log": "docs/mainline/DECISION_LOG.md",
        "latest_decision_summary": decision["summary"],
        "current_execution_ticket": "docs/mainline/CURRENT_EXECUTION_TICKET.md",
        "ticket_objective": ticket["objective"],
        "ticket_scope_summary": ticket["allowed_scope"],
        "current_gate_pack": "docs/mainline/CURRENT_GATE_PACK.md",
        "web_session_brief": "docs/mainline/WEB_SESSION_BRIEF.md",
        "latest_reports": {
            "phase_gate": "docs/mainline/reports/phase_gate_latest.txt",
            "acceptance": "docs/mainline/reports/acceptance_latest.txt",
            "evidence": "docs/mainline/reports/evidence_latest.txt",
            "worked_example_md": "docs/mainline/reports/worked_example_verification_latest.md",
            "worked_example_json": "docs/mainline/reports/worked_example_verification_latest.json",
            "training_watch": "docs/mainline/reports/training_watch_latest.txt",
            "prompt_used": "docs/mainline/reports/prompt_used_latest.md",
        },
    }
    (state_dir / "CONTROL_PLANE_STATE.json").write_text(json.dumps(control_state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    web_brief = (
        "# Web Session Brief (Derived View)\n\n"
        "**Derived view / anti-drift notice:** this file is for fresh web-side decision sessions. Validate state views before relying on it. Canonical docs and executable truth outrank this brief.\n\n"
        f"- generated_at: `{now()}`\n"
        f"- source_digest: `{src_digest}`\n"
        f"- state_version: `{state_version}`\n\n"
        "## Current control-plane snapshot\n"
        f"- active_gate: `{loop_state['active_gate']}`\n"
        f"- active_scientific_gate: `{loop_state['active_scientific_gate']}`\n"
        f"- evidence_tier: `{loop_state['evidence_tier']}`\n"
        f"- scientific_status: `{loop_state['scientific_status']}`\n"
        f"- engineering_status: `{loop_state['engineering_status']}`\n"
        f"- overall_status: `{loop_state['overall_status']}`\n\n"
        "## Latest approved decision summary\n"
        f"{decision['summary']}\n\n"
        "## Current execution scope summary\n"
        f"Objective: {ticket['objective']}\n\n"
        f"Allowed scope: {ticket['allowed_scope']}\n\n"
        f"Formal PASS requires: {ticket['formal_pass']}\n\n"
        f"Not allowed: {ticket['not_allowed']}\n\n"
        "## Current blocker and next step\n"
        f"Blocker: {loop_state['blocker_summary']}\n\n"
        f"Next valid step: {loop_state['next_step']}\n\n"
        "## Read next only if needed\n"
        "- canonical status: `docs/mainline/STATUS.md`\n"
        "- decision log: `docs/mainline/DECISION_LOG.md`\n"
        "- current execution ticket: `docs/mainline/CURRENT_EXECUTION_TICKET.md`\n"
        "- gate registry: `docs/mainline/gates/REGISTRY.json`\n"
        "- active gate file: `docs/mainline/gates/*/<ACTIVE_GATE>.md`\n"
        "- latest reports: `docs/mainline/reports/*latest*`\n"
    )
    (mainline / "WEB_SESSION_BRIEF.md").write_text(web_brief, encoding="utf-8")

    print(f"Rendered derived state views for gate_id={gate_id} digest={src_digest[:12]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
