#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ALLOWED = {
    "proposed": {"approved"},
    "approved": {"prepared"},
    "prepared": {"running"},
    "running": {"interrupted", "failed", "summarized"},
    "summarized": {"reviewed"},
    "reviewed": {"accepted", "rejected", "inconclusive"},
    "interrupted": {"superseded"},
    "failed": {"superseded"},
    "accepted": {"archived"},
    "rejected": {"archived"},
    "inconclusive": {"archived"},
    "superseded": {"archived"},
}


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
    ap.add_argument("--to-status", required=True)
    ap.add_argument("--closure-note", default="")
    args = ap.parse_args()
    repo = Path(args.repo_root).resolve()
    reg_path = repo / "docs/mainline/experiments/REGISTRY.json"
    reg = load_json(reg_path, {"experiments": []})
    matches = [e for e in reg.get("experiments", []) if e.get("experiment_id") == args.experiment_id]
    if not matches:
        raise SystemExit(f"unknown experiment_id: {args.experiment_id}")
    entry = matches[0]
    cur = entry.get("status", "approved")
    nxt = args.to_status
    if nxt not in ALLOWED.get(cur, set()):
        raise SystemExit(f"illegal status transition: {cur} -> {nxt}")
    cur_dir = repo / entry["current_dir"]
    status_path = cur_dir / "STATUS.md"
    text = status_path.read_text(encoding="utf-8", errors="ignore") if status_path.exists() else "# Experiment Status\n\n"
    if "- status:" in text:
        text = re.sub(r"- status:\s*`?[^`\n]+`?", f"- status: `{nxt}`", text)
    else:
        text += f"- status: `{nxt}`\n"
    note = args.closure_note or "not-yet-declared"
    if "- closure_note:" in text:
        text = re.sub(r"- closure_note:\s*`?[^`\n]+`?", f"- closure_note: `{note}`", text)
    else:
        text += f"- closure_note: `{note}`\n"
    status_path.write_text(text, encoding="utf-8")
    entry["status"] = nxt

    base_gate = repo / "docs/mainline/experiments/gates" / entry["gate_id"]
    if nxt == "archived":
        dest_parent = base_gate / "archived"
    elif nxt in {"accepted", "rejected", "inconclusive", "superseded"}:
        dest_parent = base_gate / "completed"
    else:
        dest_parent = base_gate / "active"
    dest = dest_parent / cur_dir.name
    if cur_dir.exists() and cur_dir != dest:
        dest_parent.mkdir(parents=True, exist_ok=True)
        cur_dir.replace(dest)
        entry["current_dir"] = str(dest.relative_to(repo)).replace("\\", "/")
    write_json(reg_path, reg)
    print(json.dumps(entry, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
