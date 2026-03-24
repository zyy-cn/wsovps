#!/usr/bin/env python3
"""Validate the gate registry for consistency.

Exit codes:
- 0: OK
- 1: STALE/CONFLICTED

This tool is conservative: if anything is ambiguous, it fails closed.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", default=".")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reg_path = repo / "docs/mainline/gates/REGISTRY.json"
    if not reg_path.exists():
        print("STALE: gate registry not found")
        return 1

    try:
        reg = load_json(reg_path)
    except Exception as e:
        print(f"CONFLICTED: cannot parse REGISTRY.json: {e}")
        return 1

    gates = reg.get("gates")
    if not isinstance(gates, dict) or not gates:
        print("CONFLICTED: REGISTRY.json missing non-empty 'gates' map")
        return 1

    active_sci = reg.get("active_scientific_gate")
    if not active_sci or active_sci not in gates:
        print("CONFLICTED: active_scientific_gate missing or not present in gates")
        return 1

    # Validate each gate entry
    for gid, entry in gates.items():
        if not isinstance(entry, dict):
            print(f"CONFLICTED: gate entry not object: {gid}")
            return 1
        df = entry.get("definition_file")
        if not df:
            print(f"CONFLICTED: gate missing definition_file: {gid}")
            return 1
        dfp = repo / df
        if not dfp.exists():
            print(f"STALE: definition_file missing for gate {gid}: {df}")
            return 1
        deps = entry.get("depends_on", [])
        if not isinstance(deps, list):
            print(f"CONFLICTED: depends_on must be list: {gid}")
            return 1
        for d in deps:
            if d not in gates:
                print(f"CONFLICTED: gate {gid} depends_on unknown gate: {d}")
                return 1

    # Detect trivial dependency cycles (DFS)
    visiting: set[str] = set()
    visited: set[str] = set()

    def dfs(n: str) -> bool:
        if n in visiting:
            return True
        if n in visited:
            return False
        visiting.add(n)
        for d in gates[n].get("depends_on", []):
            if dfs(d):
                return True
        visiting.remove(n)
        visited.add(n)
        return False

    for gid in gates:
        if dfs(gid):
            print(f"CONFLICTED: dependency cycle detected at gate: {gid}")
            return 1

    print("OK: gate registry validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
