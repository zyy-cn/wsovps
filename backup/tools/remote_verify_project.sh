#!/usr/bin/env bash
set -euo pipefail

MODE="git-boundary"
REMOTE=""
REPO_DIR=""
BRANCH=""
CLONE_URL=""
ENV_CMD=""
CMD=""
KEEP_UNTRACKED=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode) MODE="$2"; shift 2 ;;
    --remote) REMOTE="$2"; shift 2 ;;
    --repo-dir) REPO_DIR="$2"; shift 2 ;;
    --branch) BRANCH="$2"; shift 2 ;;
    --clone-url) CLONE_URL="$2"; shift 2 ;;
    --env-cmd) ENV_CMD="$2"; shift 2 ;;
    --cmd) CMD="$2"; shift 2 ;;
    --keep-untracked) KEEP_UNTRACKED=1; shift ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

if [[ -z "$REMOTE" || -z "$REPO_DIR" || -z "$CMD" ]]; then
  echo "missing required args" >&2
  exit 2
fi

CLEAN_CMD="git reset --hard && git clean -fdx"
if [[ "$KEEP_UNTRACKED" == "1" ]]; then
  CLEAN_CMD="git reset --hard"
fi

if [[ "$MODE" == "git-boundary" ]]; then
  if [[ -z "$BRANCH" || -z "$CLONE_URL" ]]; then
    echo "git-boundary mode requires --branch and --clone-url" >&2
    exit 2
  fi
  read -r -d '' REMOTE_SCRIPT <<EOS || true
set -euo pipefail
mkdir -p "$(dirname "$REPO_DIR")"
if [[ ! -d "$REPO_DIR/.git" ]]; then
  git clone "$CLONE_URL" "$REPO_DIR"
fi
cd "$REPO_DIR"
git fetch --all --prune
if git show-ref --verify --quiet "refs/heads/$BRANCH"; then
  git checkout "$BRANCH"
else
  git checkout -B "$BRANCH" "origin/$BRANCH" || git checkout -B "$BRANCH"
fi
$CLEAN_CMD
git pull --ff-only || true
if [[ -n "$ENV_CMD" ]]; then
  eval "$ENV_CMD"
fi
$CMD
EOS
else
  read -r -d '' REMOTE_SCRIPT <<EOS || true
set -euo pipefail
cd "$REPO_DIR"
if [[ -n "$ENV_CMD" ]]; then
  eval "$ENV_CMD"
fi
$CMD
EOS
fi

ssh "$REMOTE" "bash -lc $(printf '%q' "$REMOTE_SCRIPT")"
