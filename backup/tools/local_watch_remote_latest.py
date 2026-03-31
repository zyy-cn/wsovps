#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any


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


def path_from_manifest(raw: str | None, manifest_dir: Path) -> Path | None:
    if not raw:
        return None
    p = Path(raw)
    return p if p.is_absolute() else (manifest_dir / p)


def remote_exists(host: str, remote_path: str) -> bool:
    return subprocess.run(["ssh", host, "test", "-e", remote_path]).returncode == 0


def remote_read_text(host: str, remote_path: str) -> tuple[bool, str]:
    py = "from pathlib import Path; p=Path(%r); print(p.read_text(encoding='utf-8', errors='ignore') if p.exists() else '', end='')" % remote_path
    cp = subprocess.run(["ssh", host, "python3", "-c", py], capture_output=True, text=True)
    return cp.returncode == 0, cp.stdout


def normalize_state_value(value: Any) -> str:
    return str(value).strip().lower().replace("-", "_").replace(" ", "_")


def evaluate_terminal_status(host: str, spec: dict[str, Any]) -> tuple[str, str] | None:
    status_json_path = spec.get("status_json_path")
    if status_json_path:
        ok, text = remote_read_text(host, str(status_json_path))
        if not ok or not text.strip():
            return "running", f"waiting for terminal status file {status_json_path}"
        try:
            payload = json.loads(text)
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
        remote_path = spec.get(key)
        if remote_path and remote_exists(host, str(remote_path)):
            return state_name, f"{key} observed: {remote_path}"
    return None


def rsync_or_scp(host: str, remote_path: str, local_path: Path) -> tuple[bool, str]:
    local_path.parent.mkdir(parents=True, exist_ok=True)
    rsync = shutil.which("rsync")
    if rsync:
        cp = subprocess.run([rsync, "-az", f"{host}:{remote_path}", str(local_path)], capture_output=True, text=True)
        if cp.returncode == 0:
            return True, "rsync"
    cp = subprocess.run(["scp", f"{host}:{remote_path}", str(local_path)], capture_output=True, text=True)
    return cp.returncode == 0, "scp"


def update_listener_registry(path: Path | None, listener_id: str, job_id: str, experiment_id: str, run_id: str, state: str, reason: str, synced_count: int) -> None:
    if path is None:
        return
    data = read_json(path, {"listeners": []})
    listeners = data.get("listeners", []) if isinstance(data, dict) else []
    cur = {
        "listener_id": listener_id,
        "job_id": job_id,
        "experiment_id": experiment_id,
        "run_id": run_id,
        "listener_pid": os.getpid(),
        "last_poll_time": now(),
        "state": state,
        "reason": reason,
        "last_success_sync_time": now() if synced_count else "not-yet-declared",
        "synced_count": synced_count,
    }
    replaced = False
    for i, item in enumerate(listeners):
        if isinstance(item, dict) and item.get("listener_id") == listener_id:
            listeners[i] = {**item, **cur}
            replaced = True
            break
    if not replaced:
        listeners.append(cur)
    write_text(path, json.dumps({"listeners": listeners}, ensure_ascii=False, indent=2) + "\n")


def maybe_refresh_takeover(manifest: dict[str, Any], manifest_dir: Path) -> None:
    if not manifest.get("refresh_takeover_after_sync", False):
        return
    repo_root = path_from_manifest(manifest.get("repo_root"), manifest_dir)
    if not repo_root:
        return
    subprocess.run([sys.executable, str((repo_root / "tools/render_takeover.py").resolve()), "--repo-root", str(repo_root)], check=False)


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
    report_path = path_from_manifest(manifest.get("report_path"), manifest_dir) or (manifest_dir / "local_listener_latest.txt")
    state_json_path = path_from_manifest(manifest.get("state_json_path"), manifest_dir)
    registry_path = path_from_manifest(manifest.get("listener_registry_path"), manifest_dir)
    listener_id = manifest.get("listener_id", manifest.get("name", manifest_path.stem))
    job_id = manifest.get("job_id", "not-yet-declared")
    experiment_id = manifest.get("experiment_id", "not-yet-declared")
    run_id = manifest.get("run_id", "not-yet-declared")

    while True:
        manifest = read_json(manifest_path)
        state, reason = evaluate_terminal_status(manifest["remote_host"], manifest.get("watch", {}).get("terminal_status", {})) if manifest.get("watch", {}).get("terminal_status") else ("completed", "all remote completion conditions satisfied")
        synced = []
        if state in {"completed", "failed"} or manifest.get("sync_while_running", False):
            for item in manifest.get("sync_files", []):
                local_path = path_from_manifest(item["local"], manifest_dir)
                if local_path is None:
                    continue
                ok, method = rsync_or_scp(manifest["remote_host"], item["remote"], local_path)
                if ok:
                    synced.append({"remote": item["remote"], "local": str(local_path), "method": method})
            if synced:
                maybe_refresh_takeover(manifest, manifest_dir)
        report = "\n".join([
            f"timestamp: {now()}",
            f"manifest: {manifest_path}",
            f"listener_id: {listener_id}",
            f"job_id: {job_id}",
            f"state: {state}",
            f"reason: {reason}",
            f"synced_count: {len(synced)}",
            "",
        ])
        write_text(report_path, report)
        update_listener_registry(registry_path, listener_id, job_id, experiment_id, run_id, state, reason, len(synced))
        if state_json_path:
            write_text(state_json_path, json.dumps({
                "timestamp": now(),
                "state": state,
                "reason": reason,
                "synced_count": len(synced),
                "listener_id": listener_id,
                "job_id": job_id,
            }, ensure_ascii=False, indent=2) + "\n")
        if args.once or state in {"completed", "failed"}:
            return 0 if state == "completed" else 1
        time.sleep(max(5, poll_seconds))


if __name__ == "__main__":
    sys.exit(main())
