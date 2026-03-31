#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path


def load_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return default


def dump(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding='utf-8')


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo-root', default='.')
    args = ap.parse_args()
    repo = Path(args.repo_root).resolve()
    state = load_json(repo / 'docs/mainline/state/SNAPSHOT_STATE.json', {})
    ticket = load_json(repo / 'docs/mainline/state/CURRENT_EXECUTION_TICKET.json', {})
    latest_ptr = load_json(repo / 'docs/mainline/postrun/latest/latest_packet_manifest.json', {})
    packet_path = repo / latest_ptr['path'] if latest_ptr.get('path') else None
    latest_packet = load_json(packet_path, {}) if packet_path else {}
    packet_dir = packet_path.parent if packet_path else None
    code_manifest = load_json(packet_dir / 'code_snapshot_manifest.json', {}) if packet_dir else {}
    cfg_hash = load_json(packet_dir / 'config_snapshot_hash.json', {}) if packet_dir else {}
    payload = {
        'generated_at': datetime.now().isoformat(timespec='seconds'),
        'commit_sha': ticket.get('commit_sha', state.get('commit_sha', 'not-yet-declared')),
        'tree_sha': ticket.get('tree_sha', state.get('tree_sha', 'not-yet-declared')),
        'working_tree_clean': ticket.get('working_tree_clean', state.get('working_tree_clean', 'not-yet-declared')),
        'runtime_override_present': code_manifest.get('runtime_override_present', False),
        'runtime_override_summary': code_manifest.get('runtime_override_summary', 'not-yet-declared'),
        'config_snapshot_path': ticket.get('config_snapshot_path', code_manifest.get('config_snapshot_path', 'not-yet-declared')),
        'config_snapshot_hash': cfg_hash.get('config_snapshot_hash', 'not-yet-declared'),
        'remote_tree_verified': code_manifest.get('remote_tree_verified', state.get('remote_tree_verified', 'not-yet-declared')),
        'local_snapshot_id': state.get('local_snapshot_id', 'not-yet-declared'),
        'remote_snapshot_id': state.get('remote_snapshot_id', 'not-yet-declared'),
        'experiment_id': latest_packet.get('experiment_id', latest_ptr.get('experiment_id', 'not-yet-declared')),
        'run_id': latest_packet.get('run_id', latest_ptr.get('run_id', 'not-yet-declared')),
        'job_id': latest_packet.get('job_id', latest_ptr.get('job_id', 'not-yet-declared')),
        'packet_path': latest_ptr.get('path', 'not-yet-declared'),
    }
    reports = repo / 'docs/mainline/reports'
    reports.mkdir(parents=True, exist_ok=True)
    dump(reports / 'code_provenance_report_latest.json', payload)
    md = f"""# Code Provenance Report

- generated_at: `{payload['generated_at']}`
- commit_sha: `{payload['commit_sha']}`
- tree_sha: `{payload['tree_sha']}`
- working_tree_clean: `{payload['working_tree_clean']}`
- runtime_override_present: `{payload['runtime_override_present']}`
- runtime_override_summary: {payload['runtime_override_summary']}
- config_snapshot_path: `{payload['config_snapshot_path']}`
- config_snapshot_hash: `{payload['config_snapshot_hash']}`
- remote_tree_verified: `{payload['remote_tree_verified']}`
- local_snapshot_id: `{payload['local_snapshot_id']}`
- remote_snapshot_id: `{payload['remote_snapshot_id']}`
- experiment_id: `{payload['experiment_id']}`
- run_id: `{payload['run_id']}`
- job_id: `{payload['job_id']}`
- packet_path: `{payload['packet_path']}`
"""
    (reports / 'code_provenance_report_latest.md').write_text(md, encoding='utf-8')
    print(str(reports / 'code_provenance_report_latest.md'))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
