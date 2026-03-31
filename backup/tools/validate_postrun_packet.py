#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

REQUIRED = [
    'packet_manifest.json',
    'terminal_state.json',
    'run_binding.json',
    'metrics_summary.json',
    'artifact_index.json',
    'postrun_evidence_packet_latest.md',
    'code_snapshot_manifest.json',
    'config_snapshot_hash.json',
    'review_packet_latest.json',
    'review_packet_latest.md',
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--postrun-dir', required=True)
    args = ap.parse_args()
    base = Path(args.postrun_dir).resolve()
    errs: list[str] = []
    for name in REQUIRED:
        if not (base / name).exists():
            errs.append(f'missing {name}')
    if (base / 'packet_manifest.json').exists():
        manifest = json.loads((base / 'packet_manifest.json').read_text(encoding='utf-8'))
        for key in ['packet_id', 'gate_id', 'experiment_id', 'run_id', 'job_id', 'status']:
            if key not in manifest:
                errs.append(f'manifest missing {key}')
    if (base / 'code_snapshot_manifest.json').exists():
        prov = json.loads((base / 'code_snapshot_manifest.json').read_text(encoding='utf-8'))
        for key in ['commit_sha', 'tree_sha', 'working_tree_clean', 'config_snapshot_path']:
            if key not in prov:
                errs.append(f'code_snapshot_manifest missing {key}')
    if errs:
        print('CONFLICTED: post-run packet invalid')
        for e in errs:
            print('-', e)
        return 1
    print('OK: post-run packet is valid')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
