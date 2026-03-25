# Codex Approval Reduction Guide

This repo-scoped guide documents the low-interruption Codex defaults for `wsovps`.
It is guidance for trusted-repo operation and does not change the gate contracts.

## Project-scoped config
The repo includes `.codex/config.toml` with the following defaults:
- `sandbox_mode = "workspace-write"`
- `approval_policy = "never"`

## Scope note
- These settings apply only when the repo is trusted by the local Codex environment.
- Admin-managed or host-managed policy may still override `approval_policy = "never"`.
- This file does not grant broader filesystem access than the current workspace.

## Behavioral defaults for this project
Prefer the following execution pattern:
- local edits only
- remote run only
- no direct remote code patching
- latest-doc pullback required after remote runs

## Recommended allowlist prefixes
Use these prefixes for repeated safe commands in this project:
- `git add -f docs/mainline/`
- `git commit -m`
- `git push`
- `rsync -av`
- `ssh gpu4090d`
- `git fetch`
- `git checkout`
- `git reset --hard`

## Suggested user-level rules text
If a user-level allowlist or approval rule file is available in the current environment, use wording equivalent to:

```text
wsovps project rules:
- prefer local edits only
- treat gpu4090d as run-only
- require takeover_latest.md at the end of every meaningful execution cycle
- allow the safe prefixes listed in docs/runbooks/codex_approval_reduction.md
```

Do not auto-apply home-directory rules unless the current environment explicitly supports that operation.
