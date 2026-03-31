#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

VALID_STATUSES = {
    "proposed", "approved", "prepared", "running", "interrupted", "failed",
    "summarized", "reviewed", "accepted", "rejected", "inconclusive",
    "superseded", "archived"
}


def load_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", default=".")
    args = ap.parse_args()
    repo = Path(args.repo_root).resolve()
    reg_path = repo / "docs/mainline/experiments/REGISTRY.json"
    reg = load_json(reg_path, {"experiments": []})
    errs = []
    for e in reg.get("experiments", []):
        exp_id = e.get("experiment_id", "UNKNOWN")
        level = e.get("level")
        status = e.get("status")
        cur_dir = repo / e.get("current_dir", "")
        if level not in {"formal", "pilot"}:
            errs.append(f"{exp_id}: invalid level {level!r}")
        if status not in VALID_STATUSES:
            errs.append(f"{exp_id}: invalid status {status!r}")
        if not cur_dir.exists():
            errs.append(f"{exp_id}: current_dir missing: {cur_dir}")
            continue
        if status in {"approved", "prepared", "running", "summarized", "reviewed", "interrupted", "failed"} and "active" not in cur_dir.parts:
            errs.append(f"{exp_id}: active-like status but not under active/: {cur_dir}")
        if status in {"accepted", "rejected", "inconclusive", "superseded"} and "completed" not in cur_dir.parts:
            errs.append(f"{exp_id}: completed-like status but not under completed/: {cur_dir}")
        if status == "archived" and "archived" not in cur_dir.parts:
            errs.append(f"{exp_id}: archived status but not under archived/: {cur_dir}")
        if level == "formal":
            for req in ["RESULT_SUMMARY.md", "ACCEPTANCE.md"]:
                if not (cur_dir / req).exists():
                    errs.append(f"{exp_id}: formal experiment missing {req}")
    if errs:
        print("CONFLICTED: experiment registry validation failed")
        for err in errs:
            print("-", err)
        return 1
    print("OK: experiment registry is consistent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
