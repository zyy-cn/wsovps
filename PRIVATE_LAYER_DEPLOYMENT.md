# WSOVPS Private Layer Deployment

## What this overlay contains
- project-private control-plane docs under `docs/mainline/*`
- normalized gate registry and active-gate state aligned to the uploaded new gate pack
- experiment registry with archived historical prerequisite entry plus active/prepared placeholders for the new chain
- takeover/state/report placeholders compatible with the shipped mainline tools
- root `AGENTS.md`, `START_AUTOMATION.md`, and the project-specific Prompt 2
- copied `.agents/skills/*` and `.codex/config.toml`

## How to deploy
1. Make a backup or branch in the target repo.
2. Extract this overlay at the repository root of `wsovps`.
3. Allow overwrite for `AGENTS.md`, `START_AUTOMATION.md`, `.agents/*`, `.codex/*`, and `docs/mainline/*` if those paths already exist.
4. From repo root, run:
   - `python tools/render_experiment_index.py`
   - `python tools/render_state_views.py`
   - `python tools/render_code_provenance_report.py`
   - `python tools/render_takeover.py`
   - `python tools/validate_gate_registry.py`
   - `python tools/validate_experiment_registry.py`
   - `python tools/validate_state_views.py`
   - `python tools/validate_control_plane_coherence.py`
5. Start Codex from repo root and paste `PROMPT_2_WSOVPS_GATE_DRIVEN.md`.

## Intended first execution scope after deployment
The first Codex round is still `E2`, not `E3`. It should reconcile any legacy control-plane residue in the real repo, populate missing archive/manifests, validate the normalized control plane, and refresh takeover. It must not claim new scientific progress.
