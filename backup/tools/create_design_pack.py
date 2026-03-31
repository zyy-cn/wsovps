#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path

def render(text: str, values: dict[str, str]) -> str:
    for k, v in values.items():
        text = text.replace('{{' + k + '}}', str(v))
    return text

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo-root', default='.')
    ap.add_argument('--gate-id', required=True)
    ap.add_argument('--design-pack-id', required=True)
    ap.add_argument('--goal', required=True)
    ap.add_argument('--scope', required=True)
    ap.add_argument('--status', default='draft', choices=['draft','approved','superseded'])
    args = ap.parse_args()
    repo = Path(args.repo_root).resolve()
    base = repo / 'docs/mainline/designs' / f'GATE_{args.gate_id}' / args.design_pack_id
    if base.exists():
        raise SystemExit(f'design pack already exists: {base}')
    tpl_root = repo / 'docs/mainline/designs/_templates'
    values = {'DESIGN_PACK_ID': args.design_pack_id, 'GATE_ID': args.gate_id, 'STATUS': args.status, 'GOAL': args.goal, 'SCOPE': args.scope}
    for src in tpl_root.iterdir():
        if src.is_dir():
            continue
        out = base / src.name.replace('.template', '')
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render(src.read_text(encoding='utf-8'), values), encoding='utf-8')
    print(json.dumps({'design_pack_id': args.design_pack_id, 'path': str(base.relative_to(repo)).replace('\\','/')}, ensure_ascii=False, indent=2))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
