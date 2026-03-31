#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path


def load_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return default


def dump(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "
", encoding='utf-8')


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo-root', default='.')
    ap.add_argument('--design-pack-dir', required=True)
    ap.add_argument('--postrun-dir', required=True)
    ap.add_argument('--changed-files-json')
    ap.add_argument('--compatibility-note', default='not-yet-declared')
    ap.add_argument('--compatibility-smoke', default='not-yet-declared')
    ap.add_argument('--unresolved-risks', default='not-yet-declared')
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    design_dir = Path(args.design_pack_dir).resolve()
    postrun_dir = Path(args.postrun_dir).resolve()
    manifest = load_json(design_dir / 'DESIGN_MANIFEST.json', {})
    review = load_json(postrun_dir / 'review_packet_latest.json', {})
    changed = load_json(Path(args.changed_files_json), []) if args.changed_files_json else []
    changed_files = changed.get('files', []) if isinstance(changed, dict) else changed

    allowed = manifest.get('allowed_paths', []) or manifest.get('scope_files_allowed', [])
    forbidden = manifest.get('forbidden_paths', []) or manifest.get('must_not_change', [])

    def matches(patterns, path):
        return any(path == p or path.startswith(p.rstrip('/') + '/') for p in patterns)

    outside_allowed = [p for p in changed_files if allowed and not matches(allowed, p)]
    touched_forbidden = [p for p in changed_files if forbidden and matches(forbidden, p)]

    payload = {
        'generated_at': datetime.now().isoformat(timespec='seconds'),
        'design_pack_id': manifest.get('design_pack_id', 'not-yet-declared'),
        'gate_id': manifest.get('gate_id', 'not-yet-declared'),
        'postrun_dir': str(postrun_dir.relative_to(repo)).replace('\', '/'),
        'review_packet_path': str((postrun_dir / 'review_packet_latest.json').relative_to(repo)).replace('\', '/') if (postrun_dir / 'review_packet_latest.json').exists() else 'not-yet-declared',
        'changed_files': changed_files,
        'allowed_paths': allowed,
        'forbidden_paths': forbidden,
        'outside_allowed': outside_allowed,
        'touched_forbidden': touched_forbidden,
        'shared_path_touch_policy': manifest.get('shared_path_touch_policy', 'not-yet-declared'),
        'backward_compatibility_required': manifest.get('backward_compatibility_required', False),
        'compatibility_note': args.compatibility_note,
        'compatibility_smoke': args.compatibility_smoke,
        'unresolved_risks': args.unresolved_risks,
        'smoke_summary': review.get('final_state', 'not-yet-declared'),
    }

    out_json = postrun_dir / 'delta_review_packet_latest.json'
    dump(out_json, payload)
    md = f"""# Delta Review Packet

## Identity
- design_pack_id: `{payload['design_pack_id']}`
- gate_id: `{payload['gate_id']}`
- postrun_dir: `{payload['postrun_dir']}`
- review_packet_path: `{payload['review_packet_path']}`

## Changed Files
```json
{json.dumps(payload['changed_files'], ensure_ascii=False, indent=2)}
```

## Path Boundary Check
```json
{{
  "allowed_paths": {json.dumps(payload['allowed_paths'], ensure_ascii=False)},
  "forbidden_paths": {json.dumps(payload['forbidden_paths'], ensure_ascii=False)},
  "outside_allowed": {json.dumps(payload['outside_allowed'], ensure_ascii=False)},
  "touched_forbidden": {json.dumps(payload['touched_forbidden'], ensure_ascii=False)}
}}
```

## Compatibility Guard
```json
{{
  "shared_path_touch_policy": {json.dumps(payload['shared_path_touch_policy'], ensure_ascii=False)},
  "backward_compatibility_required": {json.dumps(payload['backward_compatibility_required'], ensure_ascii=False)},
  "compatibility_note": {json.dumps(payload['compatibility_note'], ensure_ascii=False)},
  "compatibility_smoke": {json.dumps(payload['compatibility_smoke'], ensure_ascii=False)}
}}
```

## Unresolved Risks
{payload['unresolved_risks']}
"""
    (postrun_dir / 'delta_review_packet_latest.md').write_text(md, encoding='utf-8')

    latest = repo / 'docs/mainline/postrun/latest'
    latest.mkdir(parents=True, exist_ok=True)
    dump(latest / 'latest_delta_review_packet.json', {
        'path': str(out_json.relative_to(repo)).replace('\', '/'),
        'md_path': str((postrun_dir / 'delta_review_packet_latest.md').relative_to(repo)).replace('\', '/'),
        'design_pack_id': payload['design_pack_id'],
        'gate_id': payload['gate_id'],
        'generated_at': payload['generated_at'],
    })
    shutil.copy2(postrun_dir / 'delta_review_packet_latest.md', latest / 'latest_delta_review_packet.md')
    print(str(out_json.relative_to(repo)).replace('\', '/'))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
