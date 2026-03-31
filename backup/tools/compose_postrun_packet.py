#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
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


def hash_file(path: Path) -> str:
    if not path.exists():
        return 'not-yet-declared'
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo-root', default='.')
    ap.add_argument('--experiment-id', required=True)
    ap.add_argument('--run-id', required=True)
    ap.add_argument('--gate-id', required=True)
    ap.add_argument('--job-id', required=True)
    ap.add_argument('--status', default='completed')
    ap.add_argument('--metrics-json')
    ap.add_argument('--comparison-json')
    ap.add_argument('--diagnostics-json')
    ap.add_argument('--summary-md')
    ap.add_argument('--config-snapshot-path', default='not-yet-declared')
    ap.add_argument('--runtime-override-summary', default='not-yet-declared')
    ap.add_argument('--remote-tree-verified', default='not-yet-declared')
    args = ap.parse_args()
    repo = Path(args.repo_root).resolve()
    reg = load_json(repo / 'docs/mainline/experiments/REGISTRY.json', {'experiments': []})
    exp = next((e for e in reg.get('experiments', []) if e.get('experiment_id') == args.experiment_id), None)
    if not exp:
        raise SystemExit(f'unknown experiment_id: {args.experiment_id}')
    exp_dir = repo / exp['current_dir']
    run_dir = exp_dir / 'runs' / args.run_id / 'postrun'
    run_dir.mkdir(parents=True, exist_ok=True)
    snapshot = load_json(repo / 'docs/mainline/state/SNAPSHOT_STATE.json', {})
    metrics = load_json(Path(args.metrics_json), {'metrics_available': False}) if args.metrics_json else {'metrics_available': False}
    comparison = load_json(Path(args.comparison_json), {'comparison_applicable': False}) if args.comparison_json else {'comparison_applicable': False}
    diagnostics = load_json(Path(args.diagnostics_json), {'stage': 'not-yet-declared', 'suspected_category': 'unknown', 'notes': ''}) if args.diagnostics_json else {'stage': 'not-yet-declared', 'suspected_category': 'unknown', 'notes': ''}
    terminal = {
        'job_id': args.job_id,
        'final_state': args.status,
        'generated_at': datetime.now().isoformat(timespec='seconds'),
        'host': 'not-yet-declared',
        'remote_workdir': 'not-yet-declared',
    }
    binding = {
        'gate_id': args.gate_id,
        'experiment_id': args.experiment_id,
        'run_id': args.run_id,
        'ticket_id': 'not-yet-declared',
        'local_snapshot_id': snapshot.get('local_snapshot_id', 'not-yet-declared'),
        'remote_snapshot_id': snapshot.get('remote_snapshot_id', 'not-yet-declared'),
        'commit_sha': snapshot.get('commit_sha', 'not-yet-declared'),
        'tree_sha': snapshot.get('tree_sha', 'not-yet-declared'),
        'job_id': args.job_id,
        'sync_mode': snapshot.get('sync_mode', 'not-yet-declared'),
        'config_snapshot_path': args.config_snapshot_path,
    }
    artifact_index = {
        'remote_log_path': 'not-yet-declared',
        'remote_run_dir': 'not-yet-declared',
        'remote_checkpoint_dir': 'not-yet-declared',
        'remote_metrics_path': str(Path(args.metrics_json).resolve()) if args.metrics_json else 'not-yet-declared',
        'remote_summary_path': str(Path(args.summary_md).resolve()) if args.summary_md else 'not-yet-declared',
        'local_synced_files': [],
    }
    code_manifest = {
        'commit_sha': binding['commit_sha'],
        'tree_sha': binding['tree_sha'],
        'working_tree_clean': snapshot.get('working_tree_clean', 'not-yet-declared'),
        'runtime_override_present': args.runtime_override_summary != 'not-yet-declared',
        'runtime_override_summary': args.runtime_override_summary,
        'config_snapshot_path': args.config_snapshot_path,
        'remote_tree_verified': args.remote_tree_verified,
    }
    cfg_hash = {
        'config_snapshot_path': args.config_snapshot_path,
        'config_snapshot_hash': hash_file(Path(args.config_snapshot_path)) if args.config_snapshot_path != 'not-yet-declared' else 'not-yet-declared',
    }
    for name, obj in {
        'terminal_state.json': terminal,
        'run_binding.json': binding,
        'metrics_summary.json': metrics,
        'comparison_packet.json': comparison,
        'diagnostics.json': diagnostics,
        'artifact_index.json': artifact_index,
        'code_snapshot_manifest.json': code_manifest,
        'config_snapshot_hash.json': cfg_hash,
    }.items():
        dump(run_dir / name, obj)
    summary_md = Path(args.summary_md).read_text(encoding='utf-8') if args.summary_md and Path(args.summary_md).exists() else ''
    packet_md = f"""# Post-run Evidence Packet

- gate_id: `{args.gate_id}`
- experiment_id: `{args.experiment_id}`
- run_id: `{args.run_id}`
- job_id: `{args.job_id}`
- final_state: `{args.status}`
- commit_sha: `{binding['commit_sha']}`
- tree_sha: `{binding['tree_sha']}`
- config_snapshot_path: `{args.config_snapshot_path}`

## Metrics
```json
{json.dumps(metrics, ensure_ascii=False, indent=2)}
```

## Comparator Facts
```json
{json.dumps(comparison, ensure_ascii=False, indent=2)}
```

## Diagnostics
```json
{json.dumps(diagnostics, ensure_ascii=False, indent=2)}
```

## Provenance
```json
{json.dumps(code_manifest, ensure_ascii=False, indent=2)}
```

## Remote summary excerpt
{summary_md[:4000] if summary_md else 'not-yet-declared'}
"""
    (run_dir / 'postrun_evidence_packet_latest.md').write_text(packet_md, encoding='utf-8')
    manifest = {
        'packet_id': f"{args.experiment_id}-{args.run_id}-{args.job_id}",
        'generated_at': datetime.now().isoformat(timespec='seconds'),
        'project': repo.name,
        'gate_id': args.gate_id,
        'experiment_id': args.experiment_id,
        'run_id': args.run_id,
        'job_id': args.job_id,
        'status': args.status,
        'packet_version': 'v2',
        'files': sorted([p.name for p in run_dir.iterdir() if p.is_file()]),
    }
    dump(run_dir / 'packet_manifest.json', manifest)
    latest = repo / 'docs/mainline/postrun/latest'
    latest.mkdir(parents=True, exist_ok=True)
    dump(latest / 'latest_packet_manifest.json', {
        'path': str((run_dir / 'packet_manifest.json').relative_to(repo)).replace('\\', '/'),
        'experiment_id': args.experiment_id,
        'run_id': args.run_id,
        'gate_id': args.gate_id,
        'job_id': args.job_id,
        'status': args.status,
        'generated_at': manifest['generated_at'],
    })
    shutil.copy2(run_dir / 'postrun_evidence_packet_latest.md', latest / 'latest_postrun_evidence_packet.md')
    # Compose a non-decision review packet.
    review_json = {
        'generated_at': datetime.now().isoformat(timespec='seconds'),
        'packet_manifest_path': str((run_dir / 'packet_manifest.json').relative_to(repo)).replace('\\', '/'),
        'gate_id': args.gate_id,
        'experiment_id': args.experiment_id,
        'run_id': args.run_id,
        'job_id': args.job_id,
        'final_state': args.status,
        'metrics': metrics,
        'comparison_facts': comparison,
        'diagnostics': diagnostics,
        'artifact_paths': artifact_index,
        'provenance': {
            'commit_sha': binding['commit_sha'],
            'tree_sha': binding['tree_sha'],
            'working_tree_clean': code_manifest['working_tree_clean'],
            'runtime_override_present': code_manifest['runtime_override_present'],
            'runtime_override_summary': code_manifest['runtime_override_summary'],
            'config_snapshot_path': code_manifest['config_snapshot_path'],
            'config_snapshot_hash': cfg_hash['config_snapshot_hash'],
            'remote_tree_verified': code_manifest['remote_tree_verified'],
        },
    }
    dump(run_dir / 'review_packet_latest.json', review_json)
    review_md = f"""# Review Packet

## Identity
- gate_id: `{args.gate_id}`
- experiment_id: `{args.experiment_id}`
- run_id: `{args.run_id}`
- job_id: `{args.job_id}`
- packet_manifest_path: `{str((run_dir / 'packet_manifest.json').relative_to(repo)).replace('\\', '/')}`

## Final State
- final_state: `{args.status}`

## Metrics
```json
{json.dumps(metrics, ensure_ascii=False, indent=2)}
```

## Comparator Raw Diff
```json
{json.dumps(comparison, ensure_ascii=False, indent=2)}
```

## Diagnostics
```json
{json.dumps(diagnostics, ensure_ascii=False, indent=2)}
```

## Artifact Paths
```json
{json.dumps(artifact_index, ensure_ascii=False, indent=2)}
```

## Provenance Summary
```json
{json.dumps(review_json['provenance'], ensure_ascii=False, indent=2)}
```
"""
    (run_dir / 'review_packet_latest.md').write_text(review_md, encoding='utf-8')
    dump(latest / 'latest_review_packet.json', {
        'path': str((run_dir / 'review_packet_latest.json').relative_to(repo)).replace('\\', '/'),
        'md_path': str((run_dir / 'review_packet_latest.md').relative_to(repo)).replace('\\', '/'),
        'experiment_id': args.experiment_id,
        'run_id': args.run_id,
        'gate_id': args.gate_id,
        'job_id': args.job_id,
        'final_state': args.status,
        'generated_at': manifest['generated_at'],
    })
    shutil.copy2(run_dir / 'review_packet_latest.md', latest / 'latest_review_packet.md')
    print(json.dumps({'packet_manifest': str((run_dir / 'packet_manifest.json').relative_to(repo)).replace('\\', '/')}, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
