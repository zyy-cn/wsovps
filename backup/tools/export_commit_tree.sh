#!/usr/bin/env bash
set -euo pipefail

COMMIT_SHA=""
OUTPUT=""
REPO_ROOT="$(pwd)"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --commit-sha) COMMIT_SHA="$2"; shift 2 ;;
    --output) OUTPUT="$2"; shift 2 ;;
    --repo-root) REPO_ROOT="$2"; shift 2 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

if [[ -z "$COMMIT_SHA" || -z "$OUTPUT" ]]; then
  echo "missing required args --commit-sha and --output" >&2
  exit 2
fi

mkdir -p "$(dirname "$OUTPUT")"
TREE_SHA="$(git -C "$REPO_ROOT" rev-parse "${COMMIT_SHA}^{tree}")"
git -C "$REPO_ROOT" archive --format=tar "$COMMIT_SHA" > "$OUTPUT"
echo "commit_sha=$COMMIT_SHA"
echo "tree_sha=$TREE_SHA"
