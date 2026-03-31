#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else "missing"


def read_head(path: Path, max_lines: int = 60) -> str:
    if not path.exists():
        return ""
    return "\n".join(path.read_text(encoding="utf-8", errors="ignore").splitlines()[:max_lines]).strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--max-archive-lines", type=int, default=60)
    args = ap.parse_args()
    repo = Path(args.repo_root).resolve()
    mainline = repo / "docs/mainline"
    reports = mainline / "reports"
    recovery = mainline / "recovery"
    recovery.mkdir(parents=True, exist_ok=True)
    latest_files = {
        "status": mainline / "STATUS.md",
        "decision_log": mainline / "DECISION_LOG.md",
        "execution_ticket": mainline / "CURRENT_EXECUTION_TICKET.md",
        "web_session_brief": mainline / "WEB_SESSION_BRIEF.md",
        "takeover_latest": mainline / "takeover/TAKEOVER_LATEST.md",
        "control_plane_state": mainline / "state/CONTROL_PLANE_STATE.json",
        "active_jobs": mainline / "state/ACTIVE_JOBS.json",
        "listener_registry": mainline / "state/LISTENER_REGISTRY.json",
        "snapshot_state": mainline / "state/SNAPSHOT_STATE.json",
        "phase_gate_latest": reports / "phase_gate_latest.txt",
        "acceptance_latest": reports / "acceptance_latest.txt",
        "evidence_latest": reports / "evidence_latest.txt",
        "remote_job_summary_latest": reports / "remote_job_summary_latest.md",
        "prompt_used_latest": reports / "prompt_used_latest.md",
    }
    state = {
        "generated_at": now(),
        "repo_root": str(repo),
        "latest": {k: str(v) for k, v in latest_files.items()},
        "digests": {k: sha256_file(v) for k, v in latest_files.items()},
    }
    lines = [f"# Recovery Summary\n\n- generated_at: `{state['generated_at']}`\n- repo_root: `{repo}`\n", "## Latest control-plane files"]
    for k, p in latest_files.items():
        lines.append(f"- {k}: `{p}` (exists: {'yes' if p.exists() else 'no'})")
    for key, path in latest_files.items():
        snippet = read_head(path, args.max_archive_lines)
        if snippet:
            lines += [f"\n## Snippet: {key} ({path.name})", "```text", snippet, "```"]
    lines.append("\n## Anti-drift note")
    lines.append("This recovery summary restores context only. It does not override canonical docs or executable truth.")
    (recovery / "RECOVERY_STATE.json").write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (recovery / "RECOVERY_SUMMARY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote recovery artifacts to: {recovery}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
