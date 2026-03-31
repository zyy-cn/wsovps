#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def load_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--job-id", required=True)
    ap.add_argument("--remote-host")
    ap.add_argument("--remote-command")
    ap.add_argument("--watch-manifest")
    ap.add_argument("--listener-manifest")
    ap.add_argument("--ticket-path")
    args = ap.parse_args()
    repo = Path(args.repo_root).resolve()
    ticket_state = load_json(repo / "docs/mainline/state/CURRENT_EXECUTION_TICKET.json", {})
    if not ticket_state:
        raise SystemExit("missing ticket machine-state json; run render_state_views first")
    if not bool(ticket_state.get("long_running", False)):
        raise SystemExit("current ticket is not marked long_running: true")
    if ticket_state.get("experiment_id", "not-yet-declared") == "not-yet-declared" or ticket_state.get("run_id", "not-yet-declared") == "not-yet-declared":
        raise SystemExit("long-running jobs must bind experiment_id and run_id")
    if ticket_state.get("delivery_mode") == "design_pack" and ticket_state.get("design_pack_status") != "approved":
        raise SystemExit("design-pack delivery mode requires an approved design pack before launch")
    if bool(ticket_state.get("code_change_expected", False)) and not bool(ticket_state.get("runtime_override_only", False)):
        if ticket_state.get("commit_sha", "not-yet-declared") == "not-yet-declared":
            raise SystemExit("code-changing long-running jobs require commit_sha in the ticket")
        if str(ticket_state.get("working_tree_clean", "not-yet-declared")).lower() != "true":
            raise SystemExit("code-changing long-running jobs require working_tree_clean=true")

    jobs_path = repo / "docs/mainline/state/ACTIVE_JOBS.json"
    data = load_json(jobs_path, {"jobs": []})
    jobs = data.get("jobs", []) if isinstance(data, dict) else []
    job = {
        "job_id": args.job_id,
        "ticket_id": ticket_state.get("objective", "not-yet-declared"),
        "gate_id": ticket_state.get("active_scientific_gate", ticket_state.get("active_gate", "not-yet-declared")),
        "experiment_id": ticket_state.get("experiment_id", "not-yet-declared"),
        "run_id": ticket_state.get("run_id", "not-yet-declared"),
        "status": "prepared",
        "started_at": now(),
        "watcher_pid": None,
        "listener_pid": None,
        "remote_pid": None,
        "remote_host": args.remote_host or "not-yet-declared",
        "terminal_state_path": None,
        "remote_summary_path": None,
        "takeover_refreshed": False,
    }

    if args.remote_host and args.remote_command:
        wrapped = f"nohup bash -lc {json.dumps(args.remote_command)} >/tmp/{args.job_id}.log 2>&1 & echo $!"
        cp = subprocess.run(["ssh", args.remote_host, "bash", "-lc", wrapped], capture_output=True, text=True)
        if cp.returncode == 0:
            job["remote_pid"] = cp.stdout.strip().splitlines()[-1] if cp.stdout.strip() else None
            job["status"] = "launched"
        else:
            job["status"] = "failed"
            job["reason"] = cp.stderr[-500:]

    if args.watch_manifest:
        manifest = load_json(Path(args.watch_manifest).resolve(), {})
        terminal = manifest.get("watch", {}).get("terminal_status", {})
        job["terminal_state_path"] = terminal.get("status_json_path")
        p = subprocess.Popen([sys.executable, str((repo / "tools/watch_training_job.py").resolve()), "--manifest", str(Path(args.watch_manifest).resolve())])
        job["watcher_pid"] = p.pid
        job["status"] = "watching"
    if args.listener_manifest:
        manifest = load_json(Path(args.listener_manifest).resolve(), {})
        for item in manifest.get("sync_files", []):
            if str(item.get("remote", "")).endswith("remote_job_summary_latest.md"):
                job["remote_summary_path"] = item.get("remote")
        p = subprocess.Popen([sys.executable, str((repo / "tools/local_watch_remote_latest.py").resolve()), "--manifest", str(Path(args.listener_manifest).resolve())])
        job["listener_pid"] = p.pid
    jobs = [j for j in jobs if not (isinstance(j, dict) and j.get("job_id") == args.job_id)] + [job]
    write_json(jobs_path, {"jobs": jobs})
    print(json.dumps(job, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
