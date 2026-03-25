# WSOVPS Mainline Status

This file tracks the authoritative state for document-driven automation.

## Current state
- Current code snapshot status: `local-first workflow correction recorded; remote run-only target; support snapshot at e278f9d`
- Gate mode: `science-first-dual-gate`
- Active gate: `S1 — Talk2DINO faithful reproduction`
- Active scientific gate: `S1 — Talk2DINO faithful reproduction`
- Supporting engineering gate(s): `E0 — bootstrap and environment alignment`, `E1 — data/weights/features readiness`
- Gate registry mode: `enabled`
- Gate registry: `docs/mainline/gates/REGISTRY.json`
- Gate registry version: `v1`
- Active gate definition file (from registry): `docs/mainline/gates/scientific/S1.md`
- Active gate version (from registry): `v1`
- Terminal mainline mode: `inactive`
- Mainline authority: `docs/mainline/*`
- Default-off modules: `Oracle-Obj residual-part stage`, `Pred-Obj / instance-source exploration`, `non-faithful projector variants`, `evaluation shortcuts`
- Scientific status: `INCONCLUSIVE`
- Engineering support status: `BLOCKED`
- Overall progression eligibility: `INCONCLUSIVE`
- Evidence bundle reviewed: `yes`
- Current evidence tier: `smoke`
- Local latest-doc listener status: `required-if-long-job-launched`
- Local latest sync status: `workflow-correction-recorded`
- Mandatory handoff artifact: `docs/mainline/reports/takeover_latest.md`
- Cold-start recovery mode: `active`
- Web-session cold-start readiness: `ready-after-derived-views`
- Prompt provenance status: `initialized`

## Why the current gate is active
- The uploaded outline makes faithful Talk2DINO reproduction the first scientific prerequisite.
- The current repository is still a Talk2DINO-derived baseline and does not yet contain a reviewable private control-plane evidence pack.
- Oracle-Obj residual-part work is explicitly downstream of a trusted object projector Φ_o.

## Why the current scientific gate is active
- `S1` is the first claim-bearing scientific gate after privatization.
- Residual-part validation is not allowed to count until S1 yields a reusable projector and a trusted benchmark path.
- The required supporting engineering work is limited to E0 and E1.

## Current blockers
### Scientific blockers
- No formal S1 benchmark report exists yet.
- Faithful training/evaluation protocol alignment has not been recorded in reports.
- Canonical reusable Φ_o has not yet been evidenced under this control plane.

### Engineering-support blockers
- Pre-extracted COCO feature `.pth` artifacts are absent under the canonical path `../coco2014_b14`.
- The faithful training path now points at the canonical extraction location, but the files themselves still need to be materialized.

## Canonical environment evidence tracker
- remote host alias: `gpu4090d`
- canonical remote repo dir: `/home/zyy/code/wsovps`
- conda env: `wsovps`
- canonical wrapper: `tools/remote_verify_project.sh`
- remote HEAD consistency evidence: `run-only-target-4e1ae2c`
- bootstrap preflight evidence: `recorded-smoke`

## Running / pending jobs
- none

## Next allowed action type
`feature-materialization-and-replay`

## Next smallest valid step
- Materialize the canonical COCO feature `.pth` files under `../coco2014_b14` using the repo extraction path.
- Re-run the faithful Stage-1 smoke on the remote repo after the feature files exist.
- Sync the resulting commit to GitHub, then record the commit hash in this file and `CURRENT_EXECUTION_TICKET.md`.

## Latest evidence
- remote environment and wrapper verified on `gpu4090d`
- CUDA 12.8 driver visible; `torch 2.1.0+cu118` works on the remote env
- `mmcv-full 1.7.2`, `mmengine 0.10.7`, `mmsegmentation 0.30.0`, `openai-clip 1.0.1` installed
- remote smoke forward-step passed on `ProjectionLayer`
- dataset/path bindings patched to canonical repo-local symlink roots
- workflow correction recorded: local edits only; remote run only
- takeover protocol: canonical handoff document required at end of each meaningful cycle
- E1 remains blocked by missing pre-extracted feature artifacts

## Re-entry condition
After deployment, bootstrap verification, or any long-job completion, re-read `STATUS.md`, `CURRENT_EXECUTION_TICKET.md`, the active gate docs, and latest reports before the next bounded step.

## Latest evidence artifact pointers
- Phase/gate report: `docs/mainline/reports/phase_gate_latest.txt`
- Acceptance report: `docs/mainline/reports/acceptance_latest.txt`
- Evidence report: `docs/mainline/reports/evidence_latest.txt`
- Takeover report: `docs/mainline/reports/takeover_latest.md`
- Worked example (md): `docs/mainline/reports/worked_example_verification_latest.md`
- Worked example (json): `docs/mainline/reports/worked_example_verification_latest.json`
- Watcher report (if used): `docs/mainline/reports/training_watch_latest.txt`

## Derived state views
- Brief: `docs/mainline/CURRENT_LOOP_BRIEF.md`
- State JSON: `docs/mainline/loop_state_latest.json`
- Current gate pack: `docs/mainline/CURRENT_GATE_PACK.md`
- Web session brief: `docs/mainline/WEB_SESSION_BRIEF.md`
- Machine-readable control state: `docs/mainline/state/CONTROL_PLANE_STATE.json`

## Current-round control files
- Decision log: `docs/mainline/DECISION_LOG.md`
- Current execution ticket: `docs/mainline/CURRENT_EXECUTION_TICKET.md`

## Prompt provenance artifacts
- Prompt used (latest): `docs/mainline/reports/prompt_used_latest.md`

## Recovery artifacts
- Recovery summary: `docs/mainline/recovery/RECOVERY_SUMMARY.md`
