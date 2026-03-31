#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
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
    ap.add_argument('--postrun-dir', required=True)
    args = ap.parse_args()
    repo = Path(args.repo_root).resolve()
    postrun_dir = Path(args.postrun_dir).resolve()
    manifest = load_json(postrun_dir / 'packet_manifest.json', {})
    terminal = load_json(postrun_dir / 'terminal_state.json', {})
    binding = load_json(postrun_dir / 'run_binding.json', {})
    metrics = load_json(postrun_dir / 'metrics_summary.json', {})
    comparison = load_json(postrun_dir / 'comparison_packet.json', {})
    diagnostics = load_json(postrun_dir / 'diagnostics.json', {})
    artifacts = load_json(postrun_dir / 'artifact_index.json', {})
    provenance = load_json(postrun_dir / 'code_snapshot_manifest.json', {})
    cfg_hash = load_json(postrun_dir / 'config_snapshot_hash.json', {})
    packet = {
        'generated_at': datetime.now().isoformat(timespec='seconds'),
        'packet_manifest_path': str((postrun_dir / 'packet_manifest.json').relative_to(repo)).replace('\\', '/'),
        'gate_id': manifest.get('gate_id', binding.get('gate_id', 'not-yet-declared')),
        'experiment_id': manifest.get('experiment_id', binding.get('experiment_id', 'not-yet-declared')),
        'run_id': manifest.get('run_id', binding.get('run_id', 'not-yet-declared')),
        'job_id': manifest.get('job_id', binding.get('job_id', 'not-yet-declared')),
        'final_state': terminal.get('final_state', manifest.get('status', 'not-yet-declared')),
        'metrics': metrics,
        'comparison_facts': comparison,
        'diagnostics': diagnostics,
        'artifact_paths': artifacts,
        'provenance': {
            'commit_sha': binding.get('commit_sha', provenance.get('commit_sha', 'not-yet-declared')),
            'tree_sha': binding.get('tree_sha', provenance.get('tree_sha', 'not-yet-declared')),
            'working_tree_clean': provenance.get('working_tree_clean', 'not-yet-declared'),
            'runtime_override_present': provenance.get('runtime_override_present', False),
            'runtime_override_summary': provenance.get('runtime_override_summary', 'not-yet-declared'),
            'config_snapshot_path': binding.get('config_snapshot_path', provenance.get('config_snapshot_path', 'not-yet-declared')),
            'config_snapshot_hash': cfg_hash.get('config_snapshot_hash', 'not-yet-declared'),
            'remote_tree_verified': provenance.get('remote_tree_verified', 'not-yet-declared'),
        },
    }
    dump(postrun_dir / 'review_packet_latest.json', packet)
    md = f"""# Review Packet

## Identity
- gate_id: `{packet['gate_id']}`
- experiment_id: `{packet['experiment_id']}`
- run_id: `{packet['run_id']}`
- job_id: `{packet['job_id']}`
- packet_manifest_path: `{packet['packet_manifest_path']}`

## Final State
- final_state: `{packet['final_state']}`

## Metrics
```json
{json.dumps(packet['metrics'], ensure_ascii=False, indent=2)}
```

## Comparator Raw Diff
```json
{json.dumps(packet['comparison_facts'], ensure_ascii=False, indent=2)}
```

## Diagnostics
```json
{json.dumps(packet['diagnostics'], ensure_ascii=False, indent=2)}
```

## Artifact Paths
```json
{json.dumps(packet['artifact_paths'], ensure_ascii=False, indent=2)}
```

## Provenance Summary
```json
{json.dumps(packet['provenance'], ensure_ascii=False, indent=2)}
```
"""
    (postrun_dir / 'review_packet_latest.md').write_text(md, encoding='utf-8')
    latest = repo / 'docs/mainline/postrun/latest'
    latest.mkdir(parents=True, exist_ok=True)
    dump(latest / 'latest_review_packet.json', {
        'path': str((postrun_dir / 'review_packet_latest.json').relative_to(repo)).replace('\\', '/'),
        'md_path': str((postrun_dir / 'review_packet_latest.md').relative_to(repo)).replace('\\', '/'),
        'experiment_id': packet['experiment_id'],
        'run_id': packet['run_id'],
        'gate_id': packet['gate_id'],
        'final_state': packet['final_state'],
        'generated_at': packet['generated_at'],
    })
    shutil.copy2(postrun_dir / 'review_packet_latest.md', latest / 'latest_review_packet.md')
    print(str(postrun_dir / 'review_packet_latest.md'))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
