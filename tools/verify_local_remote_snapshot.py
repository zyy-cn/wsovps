#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def load_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return default


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo-root', default='.')
    ap.add_argument('--remote-host')
    ap.add_argument('--remote-marker-path')
    ap.add_argument('--update-local-state', action='store_true')
    args = ap.parse_args()
    repo = Path(args.repo_root).resolve()
    state_path = repo / 'docs/mainline/state/SNAPSHOT_STATE.json'
    state = load_json(state_path, {})
    local = {
        'local_snapshot_id': state.get('local_snapshot_id', 'not-yet-declared'),
        'commit_sha': state.get('commit_sha', 'not-yet-declared'),
        'tree_sha': state.get('tree_sha', 'not-yet-declared'),
    }
    remote = {
        'remote_snapshot_id': state.get('remote_snapshot_id', 'not-yet-declared'),
        'commit_sha': 'not-yet-declared',
        'tree_sha': 'not-yet-declared',
    }
    if args.remote_host and args.remote_marker_path:
        cp = subprocess.run(['ssh', args.remote_host, 'cat', args.remote_marker_path], capture_output=True, text=True)
        if cp.returncode == 0 and cp.stdout.strip():
            try:
                payload = json.loads(cp.stdout)
                remote.update({
                    'remote_snapshot_id': payload.get('remote_snapshot_id', remote['remote_snapshot_id']),
                    'commit_sha': payload.get('commit_sha', remote['commit_sha']),
                    'tree_sha': payload.get('tree_sha', remote['tree_sha']),
                })
            except Exception:
                pass
    match = local['commit_sha'] == remote['commit_sha'] and local['tree_sha'] == remote['tree_sha']
    out = {**local, **remote, 'match': match, 'remote_tree_verified': match}
    if args.update_local_state:
        state['remote_tree_verified'] = match
        state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding='utf-8')
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if match else 1


if __name__ == '__main__':
    raise SystemExit(main())
