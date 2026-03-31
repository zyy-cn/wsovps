#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

REQUIRED = [
    'design_pack_id', 'gate_id', 'changed_files', 'allowed_paths', 'forbidden_paths',
    'outside_allowed', 'touched_forbidden', 'compatibility_note', 'compatibility_smoke'
]


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception as exc:
        raise SystemExit(f'FAILED: could not parse {path}: {exc}')


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('packet')
    args = ap.parse_args()
    path = Path(args.packet)
    obj = load_json(path)
    missing = [k for k in REQUIRED if k not in obj]
    if missing:
        raise SystemExit('FAILED: missing keys: ' + ', '.join(missing))
    print('OK: delta review packet validated')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
