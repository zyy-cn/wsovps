# WSOVPS Deployment Instructions

## What is included
This package renders a **project-private workflow layer** for the current WSOVPS / Talk2DINO-derived repository, preserving the kit deployment flow and enabling science-first dual-gate control.

## Current running gate semantics
- Active scientific gate: `S1 — Talk2DINO faithful reproduction`
- Supporting engineering gates: `E0 — bootstrap and environment alignment`, `E1 — data/weights/features readiness`
- Current evidence tier: `smoke`
- Smoke evidence does **not** count as formal PASS

## Recommended deployment path
Overlay the generated private layer onto the canonical repo root of your existing `wsovps` checkout.

Expected canonical repo facts:
- host: `gpu4090d`
- repo dir: `/home/zyy/code/wsovps`
- clone URL: `https://github.com/zyy-cn/wsovps`
- branch: `main`
- conda env: `wsovps`

## Overlay steps
1. Back up the current repo or commit/stash local changes.
2. Overlay the generated package contents into the repo root.
3. Verify these paths exist:
   - `AGENTS.md`
   - `START_AUTOMATION.md`
   - `.codex/config.toml`
   - `.agents/skills/*`
   - `docs/mainline/*`
   - `docs/outline/wsovps_outline_v5.tex`
   - `docs/runbooks/mainline_phase_gate_runbook.md`
   - `tools/remote_verify_project.sh`
   - `tools/watch_training_job.py`
   - `tools/local_watch_remote_latest.py`
4. From repo root, run:
   - `python tools/validate_gate_registry.py`
   - `python tools/render_state_views.py`
   - `python tools/validate_state_views.py`
5. Start Codex from repo root and paste `wsovps_prompt2_first_run.txt`.

## First bounded iteration goal
The first iteration should:
- complete E0 bootstrap/environment evidence,
- complete E1 data/weights/features readiness evidence,
- and, if unblocked, run the smallest S1-serving smoke verification.

## Long-running jobs
If the first iteration needs a long train/eval run:
- use durable wait-state,
- optionally launch `tools/watch_training_job.py`,
- and prepare `tools/local_watch_remote_latest.py` when later review depends on synchronized local latest docs.

## Notes
This intake intentionally keeps Stage 2 (`Oracle-Obj residual-part`) and Stage 3 (`Pred-Obj / non-oracle instance source`) default-off until S1 is reviewed.
