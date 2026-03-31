#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path


def load_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_text(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", default=".")
    args = ap.parse_args()
    repo = Path(args.repo_root).resolve()
    exp_root = repo / "docs/mainline/experiments"
    reg = load_json(exp_root / "REGISTRY.json", {"experiments": []})
    exps = reg.get("experiments", [])
    by_gate = defaultdict(list)
    active = []
    prepared_placeholders = []
    for e in exps:
        by_gate[e.get("gate_id", "UNGATED")].append(e)
        status = e.get("status")
        placeholder = bool(e.get("placeholder", False))
        if status in {"approved", "prepared", "running", "summarized", "reviewed", "interrupted", "failed"} and not placeholder:
            active.append(e)
        if status == "prepared" and placeholder:
            prepared_placeholders.append(e)

    idx_lines = ["# Experiments Index", "", "This index is tool-rendered. Do not hand-edit.", ""]
    for gate in sorted(by_gate):
        idx_lines.append(f"- {gate}: `docs/mainline/experiments/gates/{gate}/INDEX.md`")
    write_text(exp_root / "INDEX.md", "\n".join(idx_lines) + "\n")

    active_lines = ["# Active Experiments", "", "This file is tool-rendered. Do not hand-edit.", ""]
    for e in sorted(active, key=lambda x: x.get("experiment_id", "")):
        active_lines.append(
            f"- `{e.get('experiment_id')}` | gate `{e.get('gate_id')}` | level `{e.get('level')}` | status `{e.get('status')}` | run `{e.get('active_run_id', 'not-yet-declared')}`"
        )
    if len(active_lines) == 4:
        active_lines.append("- none")
    active_lines.extend(["", "## Prepared Placeholders", ""])
    for e in sorted(prepared_placeholders, key=lambda x: x.get("experiment_id", "")):
        active_lines.append(
            f"- `{e.get('experiment_id')}` | gate `{e.get('gate_id')}` | level `{e.get('level')}` | status `{e.get('status')}` | run `{e.get('active_run_id', 'not-yet-declared')}`"
        )
    if active_lines[-1] == "":
        active_lines.append("- none")
    write_text(exp_root / "ACTIVE_EXPERIMENTS.md", "\n".join(active_lines) + "\n")

    for gate, items in by_gate.items():
        lines = [f"# {gate} Experiment Index", "", "This file is tool-rendered. Do not hand-edit.", ""]
        for e in sorted(items, key=lambda x: x.get("experiment_id", "")):
            lines.append(
                f"- `{e.get('experiment_id')}` | level `{e.get('level')}` | status `{e.get('status')}` | dir `{e.get('current_dir')}`"
            )
        write_text(exp_root / "gates" / gate / "INDEX.md", "\n".join(lines) + "\n")
    print(f"rendered experiment indexes for {len(exps)} experiment(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
