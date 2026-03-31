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
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def render_text(text: str, values: dict[str, str]) -> str:
    for k, v in values.items():
        text = text.replace("{{" + k + "}}", str(v))
    return text


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--gate-id", required=True)
    ap.add_argument("--level", choices=["formal", "pilot"], required=True)
    ap.add_argument("--seq", required=True)
    ap.add_argument("--slug", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--question", required=True)
    ap.add_argument("--eligible-for-gate-judgment", default="false")
    ap.add_argument("--long-running", default="false")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    exp_root = repo / "docs/mainline/experiments"
    reg_path = exp_root / "REGISTRY.json"
    reg = load_json(reg_path, {"version": "v5p4-lite", "experiments": []})
    level_code = {"formal": "F", "pilot": "P"}[args.level]
    experiment_id = f"{args.gate_id}-{level_code}{args.seq}"
    dirname = f"{experiment_id}-{args.slug}"
    target = exp_root / "gates" / args.gate_id / "active" / dirname
    if target.exists():
        raise SystemExit(f"experiment already exists: {target}")
    template_root = exp_root / "_templates" / args.level
    if not template_root.exists():
        raise SystemExit(f"missing experiment template: {template_root}")

    values = {
        "EXPERIMENT_ID": experiment_id,
        "GATE_ID": args.gate_id,
        "TITLE": args.title,
        "QUESTION": args.question,
        "ELIGIBLE_FOR_GATE_JUDGMENT": str(args.eligible_for_gate_judgment).lower(),
        "LONG_RUNNING": str(args.long_running).lower(),
    }
    for src in template_root.rglob("*"):
        if src.is_dir():
            continue
        rel = src.relative_to(template_root)
        out_name = rel.name.replace(".template", "")
        out = target / rel.parent / out_name
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render_text(src.read_text(encoding="utf-8"), values), encoding="utf-8")

    entry = {
        "experiment_id": experiment_id,
        "gate_id": args.gate_id,
        "level": args.level,
        "title": args.title,
        "status": "approved",
        "main_question": args.question,
        "current_dir": str(target.relative_to(repo)).replace("\\", "/"),
        "bound_ticket": "not-yet-declared",
        "long_running": str(args.long_running).lower() == "true",
        "watcher_required": False,
        "listener_required": False,
        "eligible_for_gate_judgment": str(args.eligible_for_gate_judgment).lower() == "true",
        "active_run_id": "not-yet-declared",
    }
    reg["experiments"] = [e for e in reg.get("experiments", []) if e.get("experiment_id") != experiment_id] + [entry]
    write_json(reg_path, reg)
    print(json.dumps(entry, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
