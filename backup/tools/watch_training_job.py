#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def read_json(path: Path, default=None):
    if default is None:
        default = {}
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def append_archive(base_report: Path, text: str) -> None:
    archive_dir = base_report.parent / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    write_text(archive_dir / f"{base_report.stem}_{ts}{base_report.suffix or '.txt'}", text)


def path_from_manifest(raw: str | None, manifest_dir: Path) -> Path | None:
    if not raw:
        return None
    p = Path(raw)
    return p if p.is_absolute() else (manifest_dir / p)


def normalize_state_value(value: Any) -> str:
    return str(value).strip().lower().replace("-", "_").replace(" ", "_")


def evaluate_terminal_status_local(spec: dict[str, Any], manifest_dir: Path) -> tuple[str, str] | None:
    status_json_path = path_from_manifest(spec.get("status_json_path"), manifest_dir)
    if status_json_path:
        if not status_json_path.exists():
            return "running", f"waiting for terminal status file {status_json_path}"
        try:
            payload = json.loads(status_json_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            return "failed", f"terminal status json unreadable: {exc}"
        status_key = str(spec.get("status_key", "status"))
        exit_key = str(spec.get("exit_code_key", "exit_code"))
        success_values = {normalize_state_value(v) for v in spec.get("success_values", ["success", "completed", "done"])}
        failure_values = {normalize_state_value(v) for v in spec.get("failure_values", ["failed", "error", "cancelled", "interrupted"])}
        state_value = normalize_state_value(payload.get(status_key, ""))
        if state_value in success_values:
            exit_code = payload.get(exit_key)
            if spec.get("treat_nonzero_exit_as_failure", True) and exit_code not in (None, 0, "0", ""):
                return "failed", "terminal status marked success but exit code was nonzero"
            return "completed", f"terminal status success in {status_json_path}"
        if state_value in failure_values:
            return "failed", f"terminal status failure in {status_json_path}: {payload.get(status_key)}"
        return "running", f"waiting for terminal state in {status_json_path}"
    for key, state_name in [("failure_marker_path", "failed"), ("success_marker_path", "completed")]:
        p = path_from_manifest(spec.get(key), manifest_dir)
        if p and p.exists():
            return state_name, f"{key} observed: {p}"
    return None


def run_shell_commands(commands: list[str], cwd: Path) -> list[dict[str, Any]]:
    results = []
    for cmd in commands:
        cp = subprocess.run(cmd, cwd=str(cwd), shell=True, text=True, capture_output=True)
        results.append({
            "command": cmd,
            "returncode": cp.returncode,
            "stdout": cp.stdout[-2000:],
            "stderr": cp.stderr[-2000:],
        })
        if cp.returncode != 0:
            break
    return results


def update_jobs_registry(path: Path | None, manifest: dict[str, Any], state: str, reason: str) -> None:
    if path is None:
        return
    data = read_json(path, {"jobs": []})
    jobs = data.get("jobs", []) if isinstance(data, dict) else []
    job_id = manifest.get("job_id", manifest.get("name", "unnamed-job"))
    current = {
        "job_id": job_id,
        "ticket_id": manifest.get("ticket_id", "not-yet-declared"),
        "gate_id": manifest.get("scientific_gate", "not-yet-declared"),
        "experiment_id": manifest.get("experiment_id", "not-yet-declared"),
        "run_id": manifest.get("run_id", "not-yet-declared"),
        "job_type": manifest.get("job_type", "long-running"),
        "watcher_pid": os.getpid(),
        "status": state,
        "terminal_state": state if state in {"completed", "failed", "stale", "post_complete_failed"} else "running",
        "summary_ready": state in {"completed", "post_complete_failed"},
        "started_at": manifest.get("started_at", now()),
        "updated_at": now(),
        "reason": reason,
        "terminal_state_path": manifest.get("watch", {}).get("terminal_status", {}).get("status_json_path"),
        "remote_summary_path": manifest.get("remote_summary_path", "not-yet-declared"),
    }
    replaced = False
    for idx, job in enumerate(jobs):
        if isinstance(job, dict) and job.get("job_id") == job_id:
            jobs[idx] = {**job, **current}
            replaced = True
            break
    if not replaced:
        jobs.append(current)
    write_text(path, json.dumps({"jobs": jobs}, ensure_ascii=False, indent=2) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--poll-seconds", type=int, default=None)
    ap.add_argument("--once", action="store_true")
    args = ap.parse_args()
    manifest_path = Path(args.manifest).resolve()
    manifest_dir = manifest_path.parent
    manifest = read_json(manifest_path)
    poll_seconds = args.poll_seconds or int(manifest.get("poll_seconds", 120))
    report_path = path_from_manifest(manifest.get("report_path"), manifest_dir) or (ROOT / "docs/mainline/reports/training_watch_latest.txt")
    state_json_path = path_from_manifest(manifest.get("state_json_path"), manifest_dir)
    registry_path = path_from_manifest(manifest.get("active_jobs_registry_path"), manifest_dir)
    cwd = path_from_manifest(manifest.get("working_dir"), manifest_dir) or ROOT
    completed_once = False
    manifest.setdefault("started_at", now())

    while True:
        manifest = read_json(manifest_path)
        terminal_spec = manifest.get("watch", {}).get("terminal_status", {})
        decision = evaluate_terminal_status_local(terminal_spec, manifest_dir) if terminal_spec else ("completed", "all completion conditions satisfied")
        state, reason = decision if decision is not None else ("completed", "all completion conditions satisfied")
        post_actions = []
        if state == "completed" and not completed_once:
            post_actions = run_shell_commands(list(manifest.get("on_complete_commands", [])), cwd)
            if any(item["returncode"] != 0 for item in post_actions):
                state = "post_complete_failed"
                reason = "a post-completion command failed"
            completed_once = True
        elif state in {"stale", "failed"}:
            post_actions = run_shell_commands(list(manifest.get("on_fail_commands", [])), cwd)
        report = "\n".join([
            f"timestamp: {now()}",
            f"manifest: {manifest_path}",
            f"job_id: {manifest.get('job_id', manifest.get('name', manifest_path.stem))}",
            f"state: {state}",
            f"reason: {reason}",
            "",
        ])
        write_text(report_path, report)
        append_archive(report_path, report)
        update_jobs_registry(registry_path, manifest, state, reason)
        if state_json_path:
            write_text(state_json_path, json.dumps({
                "timestamp": now(),
                "state": state,
                "reason": reason,
                "job_id": manifest.get("job_id", manifest.get("name", "unnamed-job")),
            }, ensure_ascii=False, indent=2) + "\n")
        if args.once or state in {"completed", "post_complete_failed", "stale", "failed"}:
            return 0 if state == "completed" else 1
        time.sleep(max(5, poll_seconds))


if __name__ == "__main__":
    sys.exit(main())
