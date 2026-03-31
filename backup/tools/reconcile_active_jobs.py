#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime
from pathlib import Path


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def pid_alive(pid) -> bool:
    try:
        os.kill(int(pid), 0)
        return True
    except Exception:
        return False


def load_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", default=".")
    args = ap.parse_args()
    repo = Path(args.repo_root).resolve()
    jobs_path = repo / "docs/mainline/state/ACTIVE_JOBS.json"
    listeners_path = repo / "docs/mainline/state/LISTENER_REGISTRY.json"
    reports = repo / "docs/mainline/reports"
    takeover = repo / "docs/mainline/takeover/TAKEOVER_LATEST.md"
    remote_summary = reports / "remote_job_summary_latest.md"
    jobs = load_json(jobs_path, {"jobs": []})
    listeners = load_json(listeners_path, {"listeners": []})
    orphaned = 0
    completion_ready = 0

    for job in jobs.get("jobs", []):
        if not isinstance(job, dict):
            continue
        wp = job.get("watcher_pid")
        lp = job.get("listener_pid")
        state = job.get("status", "unknown")
        if wp and not pid_alive(wp) and state in {"prepared", "launched", "watching"}:
            job["status"] = "orphaned"
            orphaned += 1
        if lp and not pid_alive(lp) and state == "watching":
            job["listener_state"] = "orphaned"
            orphaned += 1
        terminal_path = job.get("terminal_state_path")
        if terminal_path:
            term = Path(terminal_path)
            if not term.is_absolute():
                term = repo / terminal_path
            if term.exists() and state in {"watching", "launched"}:
                job["terminal_state_detected"] = True
        if remote_summary.exists() and job.get("terminal_state_detected"):
            job["summary_ready"] = True
            completion_ready += 1
        if takeover.exists() and job.get("summary_ready"):
            job["takeover_refreshed"] = True
        job["reconciled_at"] = now()

    for listener in listeners.get("listeners", []):
        if isinstance(listener, dict):
            pid = listener.get("listener_pid")
            listener["stale"] = bool(pid and not pid_alive(pid))
            listener["reconciled_at"] = now()

    write_json(jobs_path, jobs)
    write_json(listeners_path, listeners)
    reports.mkdir(parents=True, exist_ok=True)
    report = "\n".join([
        f"timestamp: {now()}",
        f"jobs_count: {len(jobs.get('jobs', []))}",
        f"listeners_count: {len(listeners.get('listeners', []))}",
        f"orphaned_count: {orphaned}",
        f"completion_ready_count: {completion_ready}",
        "",
    ])
    (reports / "job_reconcile_latest.md").write_text(report, encoding="utf-8")
    print("Reconciled active jobs and listeners")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
