#!/usr/bin/env python3
"""Poll remote completion markers and sync only small latest docs / summary files.

This helper is intentionally conservative:
- it polls remote state over ssh,
- it synchronizes only explicitly listed small files,
- it writes a local listener report and optional state json,
- it exits when the remote state is completed or failed,
- it does not pull checkpoints or other large artifacts by default.

Backward-compatible completion modes:
- legacy marker/pattern checks via watch.fail_if_any_exist / watch.all_exist / watch.all_contains,
- preferred structured terminal-state checks via watch.terminal_status.
"""
from __future__ import annotations

import argparse
import json
import shlex
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def read_json(path: Path) -> dict[str, Any]:
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
    cp = subprocess.run(["ssh", host, f"test -e {shlex.quote(remote_path)}"], capture_output=True, text=True)
    return cp.returncode == 0


def remote_read_text(host: str, remote_path: str) -> tuple[bool, str]:
    py = (
        "from pathlib import Path; "
        f"p = Path({remote_path!r}); "
        "print(p.read_text(encoding='utf-8', errors='ignore') if p.exists() else '', end='')"
    )
    cp = subprocess.run(["ssh", host, "python", "-c", py], capture_output=True, text=True)
    return cp.returncode == 0, cp.stdout


def remote_contains(host: str, remote_path: str, pattern: str) -> bool:
    ok, text = remote_read_text(host, remote_path)
    return ok and pattern in text


def parse_kv_text(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for ln in text.splitlines():
        ln = ln.strip()
        if not ln or ln.startswith("#") or "=" not in ln:
            continue
        k, v = ln.split("=", 1)
        out[k.strip()] = v.strip()
    return out


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
            return "failed", f"terminal status json unreadable: {status_json_path}: {exc}"
        status_key = str(spec.get("status_key", "status"))
        exit_key = str(spec.get("exit_code_key", "exit_code"))
        success_values = {normalize_state_value(v) for v in spec.get("success_values", ["success", "completed", "done"])}
        failure_values = {normalize_state_value(v) for v in spec.get("failure_values", ["failed", "error", "cancelled", "interrupted"])}
        state_value = normalize_state_value(payload.get(status_key, ""))
        if state_value in success_values:
            exit_code = payload.get(exit_key)
            if spec.get("treat_nonzero_exit_as_failure", True) and exit_code not in (None, 0, "0", ""):
                return "failed", f"terminal status marked success but exit code was nonzero in {status_json_path}"
            return "completed", f"terminal status success in {status_json_path}"
        if state_value in failure_values:
            return "failed", f"terminal status failure in {status_json_path}: {payload.get(status_key)}"
        return "running", f"waiting for terminal state in {status_json_path}"

    status_kv_path = spec.get("status_kv_path")
    if status_kv_path:
        ok, text = remote_read_text(host, str(status_kv_path))
        if not ok or not text.strip():
            return "running", f"waiting for terminal status file {status_kv_path}"
        payload = parse_kv_text(text)
        status_key = str(spec.get("status_key", "status"))
        exit_key = str(spec.get("exit_code_key", "exit_code"))
        success_values = {normalize_state_value(v) for v in spec.get("success_values", ["success", "completed", "done"])}
        failure_values = {normalize_state_value(v) for v in spec.get("failure_values", ["failed", "error", "cancelled", "interrupted"])}
        state_value = normalize_state_value(payload.get(status_key, ""))
        if state_value in success_values:
            exit_code = payload.get(exit_key)
            if spec.get("treat_nonzero_exit_as_failure", True) and exit_code not in (None, "0", ""):
                return "failed", f"terminal status marked success but exit code was nonzero in {status_kv_path}"
            return "completed", f"terminal status success in {status_kv_path}"
        if state_value in failure_values:
            return "failed", f"terminal status failure in {status_kv_path}: {payload.get(status_key)}"
        return "running", f"waiting for terminal state in {status_kv_path}"

    failure_marker_path = spec.get("failure_marker_path")
    if failure_marker_path and remote_exists(host, str(failure_marker_path)):
        return "failed", f"failure marker exists: {failure_marker_path}"

    success_marker_path = spec.get("success_marker_path")
    exit_code_path = spec.get("exit_code_path")
    require_success_marker = bool(spec.get("require_success_marker", False))

    if success_marker_path and remote_exists(host, str(success_marker_path)):
        if exit_code_path:
            ok, text = remote_read_text(host, str(exit_code_path))
            if not ok or not text.strip():
                return "running", f"waiting for exit code in {exit_code_path}"
            raw = text.strip().splitlines()[0].strip()
            try:
                code = int(raw)
            except ValueError:
                return "failed", f"unreadable exit code in {exit_code_path}: {raw!r}"
            if code == 0:
                return "completed", f"success marker + zero exit code observed ({success_marker_path}, {exit_code_path})"
            return "failed", f"success marker present but exit code was nonzero in {exit_code_path}"
        return "completed", f"success marker exists: {success_marker_path}"

    if exit_code_path and not require_success_marker:
        ok, text = remote_read_text(host, str(exit_code_path))
        if ok and text.strip():
            raw = text.strip().splitlines()[0].strip()
            try:
                code = int(raw)
            except ValueError:
                return "failed", f"unreadable exit code in {exit_code_path}: {raw!r}"
            if code == 0:
                return "completed", f"zero exit code observed in {exit_code_path}"
            return "failed", f"nonzero exit code observed in {exit_code_path}: {code}"
        return "running", f"waiting for exit code in {exit_code_path}"

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


def render_report(manifest_path: Path, state: str, reason: str, synced: list[dict[str, str]]) -> str:
    lines = [
        f"timestamp: {now()}",
        f"manifest: {manifest_path}",
        f"state: {state}",
        f"reason: {reason}",
        "",
        "synced_files:",
    ]
    if not synced:
        lines.append("- none")
    else:
        for item in synced:
            lines.append(f"- remote: {item['remote']}")
            lines.append(f"  local: {item['local']}")
            lines.append(f"  method: {item['method']}")
    return "\n".join(lines) + "\n"


def evaluate_remote(manifest: dict[str, Any]) -> tuple[str, str]:
    host = manifest["remote_host"]
    watch = manifest.get("watch", {})
    terminal_spec = watch.get("terminal_status")
    if isinstance(terminal_spec, dict) and terminal_spec:
        decision = evaluate_terminal_status(host, terminal_spec)
        if decision is not None:
            return decision
    for rp in watch.get("fail_if_any_exist", []):
        if remote_exists(host, rp):
            return "failed", f"failure marker exists: {rp}"
    for rp in watch.get("all_exist", []):
        if not remote_exists(host, rp):
            return "running", "waiting for required remote artifact paths"
    for spec in watch.get("all_contains", []):
        if not remote_contains(host, spec["path"], spec["pattern"]):
            return "running", f"waiting for pattern in {spec['path']}"
    return "completed", "all remote completion conditions satisfied"


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

    while True:
        manifest = read_json(manifest_path)
        state, reason = evaluate_remote(manifest)
        synced: list[dict[str, str]] = []
        if state in {"completed", "failed"} or manifest.get("sync_while_running", False):
            for item in manifest.get("sync_files", []):
                remote_path = item["remote"]
                local_path = path_from_manifest(item["local"], manifest_dir)
                if local_path is None:
                    continue
                ok, method = rsync_or_scp(manifest["remote_host"], remote_path, local_path)
                if ok:
                    synced.append({"remote": remote_path, "local": str(local_path), "method": method})
        report = render_report(manifest_path, state, reason, synced)
        write_text(report_path, report)
        if state_json_path:
            write_text(
                state_json_path,
                json.dumps(
                    {
                        "timestamp": now(),
                        "state": state,
                        "reason": reason,
                        "synced_count": len(synced),
                        "manifest": str(manifest_path),
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
            )
        if args.once or state in {"completed", "failed"}:
            return 0 if state == "completed" else 1
        time.sleep(max(5, poll_seconds))


if __name__ == "__main__":
    sys.exit(main())
