# WSOVPS Mainline Status

This file tracks the authoritative state for document-driven automation.

## Current state
- Current code snapshot status: `takeover protocol active; structured takeover required; local-edit / remote-run-only enforced; support snapshot at ebe55a2`
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
- Local latest sync status: `synced-ebe55a2`
- Mandatory handoff artifact: `docs/mainline/reports/takeover_latest.md`
- Takeover schema: `docs/mainline/TAKEOVER_SCHEMA.md`
- Git sync cadence: commit/push at gate completion by default; earlier sync only when operationally necessary
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
- The canonical COCO 2014 data root `data/coco2014` on `gpu4090d` is now audited and readable.
- The README paths `../coco/captions_train2014.json` and `../coco/captions_val2014.json` are now materialized through symlink/path alignment to that canonical root.
- `dino_extraction_v2.py` previously treated the annotation path as a `torch.load`-able `.pth`; that mismatch has now been patched locally so JSON inputs can be consumed in the faithful path.
- Pre-extracted COCO feature `.pth` artifacts remain absent until the patched extractor is redeployed and the official extraction order is rerun.

## Canonical environment evidence tracker
- remote host alias: `gpu4090d`
- canonical remote repo dir: `/home/zyy/code/wsovps`
- conda env: `wsovps`
- canonical wrapper: `tools/remote_verify_project.sh`
- remote HEAD consistency evidence: `synced-ebe55a2`
- bootstrap preflight evidence: `recorded-smoke`

## Running / pending jobs
- none

## Next allowed action type
`deploy-and-replay`

## Next smallest valid step
- Deploy the local-only JSON-compatibility patch for `dino_extraction_v2.py` to the remote repo, then rerun the README-ordered feature extraction.
- After the feature files exist, rerun the faithful Stage-1 smoke on the remote repo.
- Sync the resulting commit to GitHub, then record the commit hash in this file and `CURRENT_EXECUTION_TICKET.md`.

## Latest evidence
- remote environment and wrapper verified on `gpu4090d`
- CUDA 12.8 driver visible; `torch 2.1.0+cu118` works on the remote env
- `mmcv-full 1.7.2`, `mmengine 0.10.7`, `mmsegmentation 0.30.0`, `openai-clip 1.0.1` installed
- remote smoke forward-step passed on `ProjectionLayer`
- dataset/path bindings patched to canonical repo-local symlink roots
- workflow correction recorded: local edits only; remote run only
- takeover protocol: canonical handoff document required at end of each meaningful cycle, and it must be decision-sufficient when inspection/diagnosis occurs
- authoritative commit truth: `ebe55a2` on local, GitHub, and remote deployed clone
- takeover refresh does not itself force a Git commit or push
- E1 remains blocked by the extractor/input-format mismatch, which prevents feature materialization from starting

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
