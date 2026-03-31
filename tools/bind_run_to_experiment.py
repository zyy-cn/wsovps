#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--experiment-id", required=True)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--purpose", required=True)
    ap.add_argument("--status", default="prepared")
    ap.add_argument("--local-snapshot-id", default="not-yet-declared")
    ap.add_argument("--remote-snapshot-id", default="not-yet-declared")
    ap.add_argument("--summary-path", default="not-yet-declared")
    ap.add_argument("--job-id", default="not-yet-declared")
    ap.add_argument("--run-dir", default="not-yet-declared")
    ap.add_argument("--commit-sha", default="not-yet-declared")
    ap.add_argument("--tree-sha", default="not-yet-declared")
    ap.add_argument("--config-snapshot-path", default="not-yet-declared")
    args = ap.parse_args()
    repo = Path(args.repo_root).resolve()
    reg = load_json(repo / "docs/mainline/experiments/REGISTRY.json", {"experiments": []})
    entry = next((e for e in reg.get("experiments", []) if e.get("experiment_id") == args.experiment_id), None)
    if entry is None:
        raise SystemExit(f"unknown experiment_id: {args.experiment_id}")
    exp_dir = repo / entry["current_dir"]
    ledger_path = exp_dir / "RUN_LEDGER.json"
    ledger = load_json(ledger_path, {"runs": []})
    run = {
        "run_id": args.run_id,
        "parent_experiment_id": args.experiment_id,
        "purpose": args.purpose,
        "changed_params": {},
        "local_snapshot_id": args.local_snapshot_id,
        "remote_snapshot_id": args.remote_snapshot_id,
        "status": args.status,
        "summary_path": args.summary_path,
        "commit_sha": args.commit_sha,
        "tree_sha": args.tree_sha,
        "config_snapshot_path": args.config_snapshot_path,
        "best_so_far": False,
        "notes": "",
    }
    ledger["runs"] = [r for r in ledger.get("runs", []) if r.get("run_id") != args.run_id] + [run]
    write_json(ledger_path, ledger)

    bindings_path = exp_dir / "RUN_BINDINGS.json"
    if bindings_path.exists():
        bindings = load_json(bindings_path, {"bindings": []})
        bindings["bindings"] = [b for b in bindings.get("bindings", []) if b.get("run_id") != args.run_id] + [{
            "run_id": args.run_id,
            "job_id": args.job_id,
            "run_dir": args.run_dir,
            "summary_path": args.summary_path,
            "commit_sha": args.commit_sha,
            "tree_sha": args.tree_sha,
            "config_snapshot_path": args.config_snapshot_path,
        }]
        write_json(bindings_path, bindings)
    entry["active_run_id"] = args.run_id
    write_json(repo / "docs/mainline/experiments/REGISTRY.json", reg)
    print(json.dumps(run, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
