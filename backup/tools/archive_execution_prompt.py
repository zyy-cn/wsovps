#!/usr/bin/env python3
"""Archive the execution prompt used for a Codex iteration.

Writes:
- docs/mainline/reports/prompt_used_latest.md
- docs/mainline/reports/archive/prompt_used_<timestamp>.md
- docs/mainline/reports/prompt_provenance_latest.json (optional metadata)

This tool does not change gates. It records provenance for recovery.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path


def ts() -> str:
    return datetime.now().strftime("%Y%m%dT%H%M%S")


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--prompt-file", required=True)
    ap.add_argument("--prompt-type", default="execution", help="execution|supervisor|user")
    ap.add_argument("--gate", default="not-yet-declared")
    ap.add_argument("--loop-id", default="not-yet-declared")
    ap.add_argument("--note", default="")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    prompt_path = Path(args.prompt_file).resolve()
    if not prompt_path.exists():
        raise SystemExit(f"prompt file not found: {prompt_path}")

    mainline = repo / "docs/mainline"
    reports = mainline / "reports"
    archive = reports / "archive"
    reports.mkdir(parents=True, exist_ok=True)
    archive.mkdir(parents=True, exist_ok=True)

    content = read_text(prompt_path)

    header = [
        "# Prompt Used (Provenance)",
        "",
        f"- archived_at: `{now_iso()}`",
        f"- prompt_type: `{args.prompt_type}`",
        f"- gate: `{args.gate}`",
        f"- loop_id: `{args.loop_id}`",
        f"- source_file: `{prompt_path}`",
    ]
    if args.note.strip():
        header.append(f"- note: {args.note.strip()}")
    header.append("")
    header.append("## Prompt")
    header.append("```text")
    body = "\n".join(header) + "\n" + content.rstrip() + "\n```\n"

    latest = reports / "prompt_used_latest.md"
    latest.write_text(body + "\n", encoding="utf-8")

    arch = archive / f"prompt_used_{ts()}.md"
    arch.write_text(body + "\n", encoding="utf-8")

    meta = {
        "archived_at": now_iso(),
        "prompt_type": args.prompt_type,
        "gate": args.gate,
        "loop_id": args.loop_id,
        "source_file": str(prompt_path),
        "latest_path": str(latest),
        "archive_path": str(arch),
        "note": args.note,
    }
    (reports / "prompt_provenance_latest.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Wrote prompt provenance: {latest} and {arch}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
