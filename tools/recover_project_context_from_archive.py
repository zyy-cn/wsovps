#!/usr/bin/env python3
"""Recover mid-project context from latest + archive reports.

This tool is intentionally conservative:
- it scans only small docs/reports (not checkpoints),
- it produces a recovery summary and machine-readable recovery state,
- it does not declare gates passed; it restores context for a new session.

Outputs:
- docs/mainline/recovery/RECOVERY_SUMMARY.md
- docs/mainline/recovery/RECOVERY_STATE.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def sha256_file(path: Path) -> str:
    if not path.exists():
        return "missing"
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pick_latest_by_prefix(archive_dir: Path, prefix: str) -> Path | None:
    candidates = [p for p in archive_dir.glob(f"{prefix}*") if p.is_file()]
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def collect_extra_sources(repo: Path) -> dict[str, Path]:
    out: dict[str, Path] = {}
    patterns = [
        ("session_handoff", "docs/SESSION_HANDOFF*"),
        ("handoff_docs", "docs/*handoff*"),
        ("archive_docs", "docs/archive/*"),
        ("comparison_summary", "outputs/*/comparison_summary.json"),
        ("horizontal_comparison", "outputs/*/horizontal_comparison.md"),
        ("codex_task_dir", "codex/*"),
    ]
    for key, pat in patterns:
        matches = sorted(repo.glob(pat), key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True)
        if matches:
            out[key] = matches[0]
    return out


def read_head(path: Path, max_lines: int = 80) -> str:
    if not path.exists():
        return ""
    return "\n".join(path.read_text(encoding="utf-8", errors="ignore").splitlines()[:max_lines]).strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--max-archive-lines", type=int, default=80)
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    mainline = repo / "docs/mainline"
    reports = mainline / "reports"
    archive = reports / "archive"
    recovery_dir = mainline / "recovery"
    recovery_dir.mkdir(parents=True, exist_ok=True)

    latest_files = {
        "status": mainline / "STATUS.md",
        "decision_log": mainline / "DECISION_LOG.md",
        "execution_ticket": mainline / "CURRENT_EXECUTION_TICKET.md",
        "web_session_brief": mainline / "WEB_SESSION_BRIEF.md",
        "control_plane_state": mainline / "state/CONTROL_PLANE_STATE.json",
        "gate_registry": mainline / "gates/REGISTRY.json",
        "active_gate": mainline / "gates/active_gate.json",
        "gate_change_log": mainline / "gates/history/gate_change_log.md",
        "phase_gate_latest": reports / "phase_gate_latest.txt",
        "acceptance_latest": reports / "acceptance_latest.txt",
        "evidence_latest": reports / "evidence_latest.txt",
        "worked_example_md": reports / "worked_example_verification_latest.md",
        "worked_example_json": reports / "worked_example_verification_latest.json",
        "training_watch_latest": reports / "training_watch_latest.txt",
        "prompt_used_latest": reports / "prompt_used_latest.md",
        "state_brief": mainline / "CURRENT_LOOP_BRIEF.md",
        "state_json": mainline / "loop_state_latest.json",
        "gate_pack": mainline / "CURRENT_GATE_PACK.md",
    }
    latest_files.update(collect_extra_sources(repo))

    try:
        regp = latest_files["gate_registry"]
        if regp.exists():
            reg = json.loads(regp.read_text(encoding="utf-8"))
            ag = reg.get("active_scientific_gate")
            if isinstance(reg.get("gates"), dict) and ag in reg.get("gates", {}):
                df = reg["gates"][ag].get("definition_file")
                if df:
                    latest_files["active_gate_definition"] = repo / df
    except Exception:
        pass

    archive_picks = {}
    if archive.exists():
        for key, prefix in [
            ("phase_gate_archive", "phase_gate_latest"),
            ("acceptance_archive", "acceptance_latest"),
            ("evidence_archive", "evidence_latest"),
            ("training_watch_archive", "training_watch_latest"),
            ("worked_example_md_archive", "worked_example_verification_latest"),
            ("prompt_used_archive", "prompt_used"),
        ]:
            p = pick_latest_by_prefix(archive, prefix)
            if p:
                archive_picks[key] = p

    state: dict[str, Any] = {
        "generated_at": now(),
        "repo_root": str(repo),
        "latest": {k: str(v) for k, v in latest_files.items()},
        "archive_picks": {k: str(v) for k, v in archive_picks.items()},
        "digests": {k: sha256_file(v) for k, v in latest_files.items()},
        "archive_digests": {k: sha256_file(v) for k, v in archive_picks.items()},
    }

    lines = [f"# Recovery Summary\n\n- generated_at: `{state['generated_at']}`\n- repo_root: `{repo}`\n"]
    lines.append("## Latest control-plane files")
    for k, p in latest_files.items():
        exists = "yes" if p.exists() else "no"
        lines.append(f"- {k}: `{p}` (exists: {exists})")

    lines.append("\n## Archive picks (most recent matching files)")
    if not archive_picks:
        lines.append("- none")
    else:
        for k, p in archive_picks.items():
            lines.append(f"- {k}: `{p}`")

    def add_snippet(title: str, path: Path):
        if not path.exists():
            return
        snippet = read_head(path, max_lines=args.max_archive_lines)
        if not snippet:
            return
        lines.append(f"\n## Snippet: {title} ({path.name})")
        lines.append("```text")
        lines.append(snippet)
        lines.append("```")

    for key in [
        "status",
        "decision_log",
        "execution_ticket",
        "web_session_brief",
        "phase_gate_latest",
        "acceptance_latest",
        "evidence_latest",
        "training_watch_latest",
        "prompt_used_latest",
        "session_handoff",
        "handoff_docs",
        "comparison_summary",
        "horizontal_comparison",
        "gate_change_log",
    ]:
        if key in latest_files:
            add_snippet(key, latest_files[key])

    lines.append("\n## Anti-drift note")
    lines.append(
        "This recovery summary restores context only. It does not override canonical docs or executable truth. "
        "If conflicts exist, fall back to canonical sources and re-validate."
    )

    (recovery_dir / "RECOVERY_STATE.json").write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (recovery_dir / "RECOVERY_SUMMARY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote recovery artifacts to: {recovery_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
