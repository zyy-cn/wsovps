#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def git(repo: Path, *args: str) -> str:
    cp = subprocess.run(['git', '-C', str(repo), *args], capture_output=True, text=True)
    if cp.returncode != 0:
        raise SystemExit(cp.stderr.strip() or 'git command failed')
    return cp.stdout.strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo-root', default='.')
    ap.add_argument('--allow-runtime-override-only', action='store_true')
    ap.add_argument('--ticket-json')
    args = ap.parse_args()
    repo = Path(args.repo_root).resolve()
    ticket = {}
    if args.ticket_json:
        p = Path(args.ticket_json)
        if p.exists():
            ticket = json.loads(p.read_text(encoding='utf-8'))
    commit_sha = git(repo, 'rev-parse', 'HEAD')
    tree_sha = git(repo, 'rev-parse', 'HEAD^{tree}')
    status = git(repo, 'status', '--porcelain')
    clean = status == ''
    runtime_override_only = bool(ticket.get('runtime_override_only', False)) or args.allow_runtime_override_only
    level = ticket.get('level', 'not-yet-declared')
    code_change_expected = bool(ticket.get('code_change_expected', False))
    require_clean = code_change_expected or level in {'formal', 'pilot'} or bool(ticket.get('long_running', False))
    ok = clean if require_clean and not runtime_override_only else (clean or runtime_override_only)
    result = {
        'commit_sha': commit_sha,
        'tree_sha': tree_sha,
        'working_tree_clean': clean,
        'runtime_override_only': runtime_override_only,
        'require_clean_tree': require_clean,
        'ok': ok,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
