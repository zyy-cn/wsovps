#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path

REQUIRED = ['DESIGN.md','INTERFACES.md','PSEUDOCODE.md','ACCEPTANCE.md','IMPLEMENT_PLAN.md','DESIGN_MANIFEST.json']

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--design-pack-path', required=True)
    args = ap.parse_args()
    base = Path(args.design_pack_path).resolve()
    errs = []
    for name in REQUIRED:
        if not (base / name).exists():
            errs.append(f'missing {name}')
    if (base / 'DESIGN_MANIFEST.json').exists():
        data = json.loads((base / 'DESIGN_MANIFEST.json').read_text(encoding='utf-8'))
        if data.get('status') not in {'draft','approved','superseded'}:
            errs.append('invalid manifest status')
        if not isinstance(data.get('required_read_order', []), list):
            errs.append('required_read_order must be a list')
    if errs:
        print('CONFLICTED: design pack invalid')
        for e in errs:
            print('-', e)
        return 1
    print('OK: design pack is valid')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
