#!/usr/bin/env bash
set -euo pipefail

REMOTE=""
MANIFEST=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --remote) REMOTE="$2"; shift 2 ;;
    --manifest) MANIFEST="$2"; shift 2 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

if [[ -z "$REMOTE" || -z "$MANIFEST" ]]; then
  echo "missing required args --remote and --manifest" >&2
  exit 2
fi

python3 - <<PY
import json, pathlib, subprocess
manifest = json.loads(pathlib.Path(r"$MANIFEST").read_text(encoding='utf-8'))
for item in manifest.get('sync_files', []):
    local = pathlib.Path(item['local'])
    local.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(['scp', f"$REMOTE:{item['remote']}", str(local)], check=False)
PY
echo "synced small artifacts from $REMOTE using $MANIFEST"
