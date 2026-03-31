#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, os
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest", nargs="?", default="profiles/gpu4090d/bootstrap_links.example.json")
    ap.add_argument("--root", default=".")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--fix", action="store_true")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    manifest = Path(args.manifest).resolve()
    data = json.loads(manifest.read_text(encoding="utf-8"))
    missing = []
    for rel in data.get("required_paths", []):
        p = root / rel
        if not p.exists():
            missing.append(rel)
    if missing and args.fix:
        for rel in missing:
            (root / rel).mkdir(parents=True, exist_ok=True)
    print(json.dumps({"root": str(root), "missing": missing, "fixed": bool(args.fix and missing)}, indent=2))
    return 1 if missing and args.check and not args.fix else 0


if __name__ == "__main__":
    raise SystemExit(main())
