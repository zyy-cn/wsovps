#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo-root', default='.')
    args = ap.parse_args()
    repo = Path(args.repo_root).resolve()
    base = repo / 'docs/mainline/designs'
    entries = []
    for manifest in base.glob('GATE_*/**/DESIGN_MANIFEST.json'):
        data = json.loads(manifest.read_text(encoding='utf-8'))
        entries.append({
            'design_pack_id': data.get('design_pack_id','not-yet-declared'),
            'gate_id': data.get('gate_id','not-yet-declared'),
            'status': data.get('status','not-yet-declared'),
            'path': str(manifest.parent.relative_to(repo)).replace('\\','/')
        })
    entries.sort(key=lambda x: (x['gate_id'], x['design_pack_id']))
    lines = ['# Design Packs', '', '```json', json.dumps(entries, ensure_ascii=False, indent=2), '```', '']
    (base / 'INDEX.md').write_text('\n'.join(lines), encoding='utf-8')
    print(json.dumps({'count': len(entries)}, ensure_ascii=False, indent=2))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
