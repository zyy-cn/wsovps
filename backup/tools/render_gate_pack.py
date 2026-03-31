#!/usr/bin/env python3
"""Render CURRENT_GATE_PACK.md from gate registry + active gate document.

This tool is used for low-token iterations and hot-updated gate semantics.
It fails closed when registry is missing.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def extract_sections(md: str) -> dict[str, str]:
    # Extract numbered top-level sections "## 1. ..." into a dict keyed by section number.
    parts = {}
    matches = list(re.finditer(r"^##\s+(\d+)\.\s+(.+?)\s*$", md, flags=re.MULTILINE))
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(md)
        sec_num = m.group(1)
        body = md[start:end].strip()
        parts[sec_num] = body
    return parts


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", default=".")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    mainline = repo / "docs/mainline"
    reg_path = mainline / "gates/REGISTRY.json"

    if not reg_path.exists():
        raise SystemExit("gate registry not found")

    reg = load_json(reg_path)
    gates = reg.get("gates", {})
    active = reg.get("active_scientific_gate")
    if active not in gates:
        raise SystemExit("active_scientific_gate not found in registry")

    entry = gates[active]
    gate_file = repo / entry.get("definition_file")
    if not gate_file.exists():
        raise SystemExit(f"active gate definition_file missing: {gate_file}")

    md = read_text(gate_file)
    secs = extract_sections(md)

    # Build a compact pack from key sections.
    key_nums = ["1", "2", "4", "5", "6", "7", "8", "9", "10", "11"]
    body_parts = []
    for n in key_nums:
        if n in secs and secs[n]:
            body_parts.append(f"## {n}. {['Purpose','Claim / Control Goal','Smoke Standard','Formal Standard','Required Metrics','Judgment Rule','Evidence Requirements','Out of Scope','Fallback / Next Step Rule','Re-entry Condition'][key_nums.index(n)]}\n\n{secs[n]}")

    pack_quality = "full" if len(body_parts) >= 6 else "degraded"

    out = (
        "# Current Gate Pack (Derived View)\n\n"
        "**Derived view / anti-drift notice:** canonical docs and executable truth outrank this pack.\n\n"
        f"- generated_at: `{now()}`\n"
        f"- registry_version: `{reg.get('version','not-yet-declared')}`\n"
        f"- active_gate_id: `{active}`\n"
        f"- active_gate_version: `{entry.get('version','not-yet-declared')}`\n"
        f"- active_gate_file: `{entry.get('definition_file')}`\n"
        f"- pack_quality: `{pack_quality}`\n\n"
        + "\n\n".join(body_parts)
        + "\n\n## Canonical pointers\n"
        f"- gate doc: `{entry.get('definition_file')}`\n"
        "- registry: `docs/mainline/gates/REGISTRY.json`\n"
        "- status: `docs/mainline/STATUS.md`\n"
    )

    (mainline / "CURRENT_GATE_PACK.md").write_text(out + "\n", encoding="utf-8")
    print(f"Rendered CURRENT_GATE_PACK.md for active gate {active}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
