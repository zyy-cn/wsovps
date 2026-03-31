#!/usr/bin/env bash
set -euo pipefail

REMOTE=""
REMOTE_DIR=""
LOCAL_DIR="$(pwd)"
EXCLUDE_FILE=""
REPO_ROOT="$(pwd)"
COMMIT_SHA=""
ALLOW_DIR_SYNC="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --remote) REMOTE="$2"; shift 2 ;;
    --remote-dir) REMOTE_DIR="$2"; shift 2 ;;
    --local-dir) LOCAL_DIR="$2"; shift 2 ;;
    --exclude-file) EXCLUDE_FILE="$2"; shift 2 ;;
    --repo-root) REPO_ROOT="$2"; shift 2 ;;
    --commit-sha) COMMIT_SHA="$2"; shift 2 ;;
    --allow-dir-sync) ALLOW_DIR_SYNC="$2"; shift 2 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

if [[ -z "$REMOTE" || -z "$REMOTE_DIR" ]]; then
  echo "missing required args --remote and --remote-dir" >&2
  exit 2
fi

mkdir -p "$REPO_ROOT/docs/mainline/state"
if [[ -z "$COMMIT_SHA" && "$ALLOW_DIR_SYNC" != "true" ]]; then
  echo "commit-bound sync requires --commit-sha unless --allow-dir-sync true is explicitly set" >&2
  exit 2
fi

SNAPSHOT_ID="snap_$(date +%Y%m%d_%H%M%S)"
MODE="ssh_snapshot"
TREE_SHA="not-yet-declared"
WORKING_TREE_CLEAN="not-yet-declared"
ARCHIVE_TMP=""

if [[ -n "$COMMIT_SHA" ]]; then
  MODE="commit_tree"
  TREE_SHA="$(git -C "$REPO_ROOT" rev-parse "${COMMIT_SHA}^{tree}")"
  if [[ -z "$(git -C "$REPO_ROOT" status --porcelain)" ]]; then
    WORKING_TREE_CLEAN="true"
  else
    WORKING_TREE_CLEAN="false"
  fi
  ARCHIVE_TMP="$(mktemp --suffix .tar)"
  git -C "$REPO_ROOT" archive --format=tar "$COMMIT_SHA" > "$ARCHIVE_TMP"
  ssh "$REMOTE" "mkdir -p '$REMOTE_DIR' '$REMOTE_DIR/.codex_sync' && rm -rf '$REMOTE_DIR'/*"
  scp "$ARCHIVE_TMP" "$REMOTE:$REMOTE_DIR/.codex_sync/source_tree.tar" >/dev/null
  ssh "$REMOTE" "tar -xf '$REMOTE_DIR/.codex_sync/source_tree.tar' -C '$REMOTE_DIR' && rm -f '$REMOTE_DIR/.codex_sync/source_tree.tar'"
else
  RSYNC_ARGS=(-az --delete)
  if [[ -n "$EXCLUDE_FILE" ]]; then
    RSYNC_ARGS+=(--exclude-from "$EXCLUDE_FILE")
  fi
  ssh "$REMOTE" "mkdir -p '$REMOTE_DIR/.codex_sync'"
  rsync "${RSYNC_ARGS[@]}" "$LOCAL_DIR/" "$REMOTE:$REMOTE_DIR/"
fi

TMP_JSON="$(mktemp)"
python3 - <<PY > "$TMP_JSON"
import json, datetime
print(json.dumps({
  'local_snapshot_id': '$SNAPSHOT_ID',
  'remote_snapshot_id': '$SNAPSHOT_ID',
  'generated_at': datetime.datetime.now().isoformat(timespec='seconds'),
  'commit_sha': '$COMMIT_SHA' if '$COMMIT_SHA' else 'not-yet-declared',
  'tree_sha': '$TREE_SHA',
  'working_tree_clean': '$WORKING_TREE_CLEAN',
  'sync_mode': '$MODE',
  'remote_tree_verified': 'false'
}, ensure_ascii=False, indent=2))
PY
scp "$TMP_JSON" "$REMOTE:$REMOTE_DIR/.codex_sync/remote_snapshot.json" >/dev/null
python3 - <<PY
import json, pathlib, datetime
p = pathlib.Path(r"$REPO_ROOT/docs/mainline/state/SNAPSHOT_STATE.json")
obj = {}
if p.exists():
    try:
        obj = json.loads(p.read_text(encoding='utf-8'))
    except Exception:
        obj = {}
obj.update({
  'local_workspace_root': str(pathlib.Path(r"$LOCAL_DIR").resolve()),
  'local_snapshot_id': r"$SNAPSHOT_ID",
  'local_snapshot_created_at': datetime.datetime.now().isoformat(timespec='seconds'),
  'remote_runner_root': r"$REMOTE_DIR",
  'remote_snapshot_id': r"$SNAPSHOT_ID",
  'synced_at': datetime.datetime.now().isoformat(timespec='seconds'),
  'sync_mode': '$MODE',
  'commit_sha': '$COMMIT_SHA' if '$COMMIT_SHA' else 'not-yet-declared',
  'tree_sha': '$TREE_SHA',
  'working_tree_clean': '$WORKING_TREE_CLEAN',
  'remote_tree_verified': 'false'
})
p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
PY
rm -f "$TMP_JSON"
if [[ -n "$ARCHIVE_TMP" ]]; then rm -f "$ARCHIVE_TMP"; fi
echo "synced snapshot $SNAPSHOT_ID to $REMOTE:$REMOTE_DIR using $MODE"
