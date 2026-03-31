# Deployment Instructions — WSOVPS v5p4-lite Private Layer Overlay

This package is an in-place overlay for the uploaded `wsovps` project package.
It is not a clean-room rebootstrap and it should not reset the existing project history or reports.

## What this overlay does
- upgrades the project control plane to the v5p4-lite runtime model,
- preserves the existing deployment flow,
- preserves the researcher + web-side GPT planning role split,
- preserves the local-first / remote-mirror execution model,
- adds takeover-first handoff files and v5p4-lite policy docs,
- initializes experiment / design / post-run / state registries required by the newer runtime.

## Assumptions preserved from the uploaded project
- project name: `WSOVPS`
- canonical remote host alias: `gpu4090d`
- canonical remote repo dir: `/home/zyy/code/wsovps`
- canonical wrapper: `tools/remote_verify_project.sh`
- current archived gate state: `S1 PASS frozen and archived`

## Deployment steps
1. Unzip this overlay at the root of the existing WSOVPS repository.
2. Allow overwrite for files inside:
   - `AGENTS.md`
   - `START_AUTOMATION.md`
   - `.agents/`
   - `.codex/`
   - `tools/`
   - `docs/mainline/`
   - `docs/runbooks/`
3. Do **not** delete the existing project source tree, datasets, weights, logs, or historical reports.
4. Start Codex from the repository root.
5. Paste the file `project_specific_prompt2_wsovps_v5p4_lite.md` as Prompt 2.

## Optional sanity checks after overlay deployment
Run from repo root:
```bash
python tools/validate_gate_registry.py --repo-root .
python tools/validate_state_views.py --repo-root .
python tools/render_takeover.py --repo-root .
```

## Expected result
After deployment, the primary web-side handoff path should be:
- `docs/mainline/takeover/TAKEOVER_LATEST.md`

The current scope should remain archive-only unless a later approved ticket explicitly opens a new gate.
