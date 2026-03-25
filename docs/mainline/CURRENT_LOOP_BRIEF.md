# Current Loop Brief (Derived View)

**Derived view / anti-drift notice:** validate before use; canonical docs outrank this view.

- generated_at: `2026-03-25T09:13:45`
- source_digest: `319780e89b7c9d7a3409c2bc91cd1339691ccf7f481ae006a9325e72af02ba54`
- state_version: `371ddd8c9078`

## Read protocol (default)
1) Validate state views: `python tools/validate_state_views.py`
2) If OK, read only: `CURRENT_LOOP_BRIEF.md`, `loop_state_latest.json`, `CURRENT_GATE_PACK.md`, `CURRENT_EXECUTION_TICKET.md`, plus latest reports.
3) If STALE/CONFLICTED, read canonical control plane and regenerate: `python tools/render_state_views.py`.

## Current gate & tier
- active_gate: `S1 — Talk2DINO faithful reproduction`
- active_scientific_gate: `S1 — Talk2DINO faithful reproduction`
- evidence_tier: `smoke`

## Current blocker summary
### Scientific blockers - No formal S1 benchmark report exists yet. - Faithful training/evaluation protocol alignment has not been recorded in reports. - Canonical reusable Φ_o has not yet been evidenced under this control plane. ### Engineering-support blockers - Pre-extracted COCO feature `.pth` artifacts are absent under the canonical path `../coco2014_b14`. - The faithful training path now points at the canonical extraction location, but the files themselves still need to be materialized.

## Next smallest valid step
- Materialize the canonical COCO feature `.pth` files under `../coco2014_b14` using the repo extraction path. - Re-run the faithful Stage-1 smoke on the remote repo after the feature files exist. - Sync the resulting commit to GitHub, then record the commit hash in this file and `CURRENT_EXECUTION_TICKET.md`.

## Formal standard reminder
Formal S1 acceptance requires all of the following: - the faithful Stage-1 protocol is documented and bound to concrete entrypoints, configs, and paths; - benchmark evaluation is executed on the declared object-level OVS validation set, centered on Pascal VOC 20, Pascal Context 59, and COCO Object; - no critical integrity bug remains in dataset selection, metric aggregation, checkpoint loading, evaluator invocation, or config binding; - the resulting projector Φ_o is judged reusable for Stage 2; - the full evidence pack is present and reviewable. Until a later hot update tightens numeric thresholds, the default formal interpretation is: protocol-complete benchmark evidence plus explicit judgment on reuse, not a smoke-only floor.

## Re-entry condition
After deployment, bootstrap verification, or any long-job completion, re-read `STATUS.md`, `CURRENT_EXECUTION_TICKET.md`, the active gate docs, and latest reports before the next bounded step.

## Current execution scope objective
Complete the first bounded iteration after privatization: 1. verify the control plane and canonical environment assumptions, 2. close the minimum E0 and E1 evidence gaps, 3. if unblocked, execute the smallest S1-serving smoke verification of the faithful Talk2DINO path.

## Required outputs this iteration
- `docs/mainline/reports/phase_gate_latest.txt`
- `docs/mainline/reports/acceptance_latest.txt`
- `docs/mainline/reports/evidence_latest.txt`
- `docs/mainline/reports/worked_example_verification_latest.md (if required)`
- `docs/mainline/reports/worked_example_verification_latest.json (if required)`
- `docs/mainline/reports/training_watch_latest.txt (if wait-state/watcher used)`
- `docs/mainline/CURRENT_LOOP_BRIEF.md (regenerate)`
- `docs/mainline/loop_state_latest.json (regenerate)`
- `docs/mainline/CURRENT_GATE_PACK.md (regenerate on gate change)`
- `docs/mainline/WEB_SESSION_BRIEF.md (regenerate)`
- `docs/mainline/state/CONTROL_PLANE_STATE.json (regenerate)`

## Pointers
- constitution: `docs/mainline/OPERATING_CONSTITUTION.md`
- canonical status: `docs/mainline/STATUS.md`
- decision log: `docs/mainline/DECISION_LOG.md`
- gate registry (if enabled): `docs/mainline/gates/REGISTRY.json`
- current gate pack: `docs/mainline/CURRENT_GATE_PACK.md`
- current execution ticket: `docs/mainline/CURRENT_EXECUTION_TICKET.md`
- web session brief: `docs/mainline/WEB_SESSION_BRIEF.md`
- machine-readable control state: `docs/mainline/state/CONTROL_PLANE_STATE.json`
- latest reports: `docs/mainline/reports/*latest*`
- recovery summary (if any): `docs/mainline/recovery/RECOVERY_SUMMARY.md`
- prompt archive (if any): `docs/mainline/reports/prompt_used_latest.md`
