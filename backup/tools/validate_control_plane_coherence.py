#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
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
    args = ap.parse_args()
    repo = Path(args.repo_root).resolve()
    errs: list[str] = []
    ticket = load_json(repo / 'docs/mainline/state/CURRENT_EXECUTION_TICKET.json', {})
    state = load_json(repo / 'docs/mainline/state/SNAPSHOT_STATE.json', {})
    exp_reg = load_json(repo / 'docs/mainline/experiments/REGISTRY.json', {'experiments': []})
    latest_packet_ptr = load_json(repo / 'docs/mainline/postrun/latest/latest_packet_manifest.json', {})
    latest_review_ptr = load_json(repo / 'docs/mainline/postrun/latest/latest_review_packet.json', {})
    control = load_json(repo / 'docs/mainline/state/CONTROL_PLANE_STATE.json', {})
    if ticket.get('experiment_id', 'not-yet-declared') != 'not-yet-declared':
        known = {e.get('experiment_id') for e in exp_reg.get('experiments', [])}
        if ticket['experiment_id'] not in known:
            errs.append('ticket experiment_id not found in experiment registry')
    if ticket.get('commit_sha', 'not-yet-declared') != 'not-yet-declared' and state.get('commit_sha', 'not-yet-declared') not in {'not-yet-declared', ticket.get('commit_sha')}:
        errs.append('ticket commit_sha disagrees with snapshot state')
    if latest_packet_ptr.get('path') and not (repo / latest_packet_ptr['path']).exists():
        errs.append('latest packet pointer path missing')
    if latest_review_ptr.get('path') and not (repo / latest_review_ptr['path']).exists():
        errs.append('latest review packet pointer path missing')
    if latest_packet_ptr.get('experiment_id') and latest_review_ptr.get('experiment_id') and latest_packet_ptr.get('experiment_id') != latest_review_ptr.get('experiment_id'):
        errs.append('latest packet pointer and latest review pointer disagree on experiment_id')
    if latest_packet_ptr.get('run_id') and latest_review_ptr.get('run_id') and latest_packet_ptr.get('run_id') != latest_review_ptr.get('run_id'):
        errs.append('latest packet pointer and latest review pointer disagree on run_id')
    if control.get('takeover_latest_path') and not (repo / control['takeover_latest_path']).exists():
        errs.append('control plane takeover path missing')
    if errs:
        print('CONFLICTED: control plane coherence failed')
        for e in errs:
            print('-', e)
        return 1
    print('OK: control plane coherence holds')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
