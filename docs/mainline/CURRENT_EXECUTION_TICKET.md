# Current Execution Ticket (Canonical Current-Round Scope)

This file is the canonical current-round scope for Codex.

## Objective
Implement the minimum E4A Oracle-Obj loss-attribution surface from the approved implementation pack, run the bounded E4A smoke only, preserve the settled S2 PASS evidence, and refresh the authoritative latest/takeover surfaces.

## Active gate binding
- active_gate: `E4A`
- active_scientific_gate: `S2A`
- evidence_tier: `design`
- formal_standard_version: `wsovps-e4a-s2a-design-intake-v1`

## Role / execution binding
- role_boundary_ack: `required`
- execution_location: `remote_first`
- remote_execution_required: `true`
- long_running: `false`
- watcher_required: `false`
- listener_required: `false`
- requires_takeover_refresh: `true`
- git_boundary: `false`
- delivery_mode: `design_pack`
- design_pack_required: `true`
- design_pack_id: `DP-E4A-ORACLEOBJ-LOSS-ATTRIBUTION-IMPLEMENTATION-R2`
- design_pack_status: `approved`
- allowed_design_deviation: `false`
- milestone_id: `e4a-implementation-r2`
- code_change_expected: `true`
- runtime_override_only: `false`
- working_tree_clean: `true`
- local_snapshot_id: `not-yet-declared`
- remote_snapshot_id: `not-yet-declared`
- remote_tree_verified: `true`
- config_snapshot_path: `not-yet-declared`
- governance_ingestion_note: `pre-flight code-truth check passed; implementation pack assumptions still match the current residual runtime`
- archive_sync_note: `remote alignment verified; bounded commit and smoke will be mirrored after code landing`

## Experiment binding
- experiment_id: `EXP-E4A-ORACLEOBJ-LOSS-ATTRIBUTION-INSTRUMENTATION`
- run_id: `not-yet-declared`
- question_type: `implementation_smoke`
- level: `implementation`
- eligible_for_gate_judgment: `false`
- expected_next_status: `bounded_smoke_ready`

## Bound design packs
- `DP-E4A-ORACLEOBJ-LOSS-ATTRIBUTION-INSTRUMENTATION-R1`
- `DP-S2A-ORACLEOBJ-LOSS-MECHANISM-VALIDATION-R1`

## Round constraints
- Preserve S2 PASS evidence and provenance.
- Use remote authoritative runtime only (`/mnt/sda/zyy/code/wsovps`) for execution truth.
- No S2A formal execution in this round.
- No training or benchmark matrix beyond the bounded E4A smoke.
- Keep PP116 asset discovery compatibility (`data/pascal_part116`) intact.

## Allowed execution scope
- Implement the minimum E4A loss-attribution surface in the approved residual-layer files.
- Run the bounded E4A smoke only.
- Preserve the settled S2 PASS evidence and provenance.
- Refresh canonical latest/takeover surfaces and sync the implementation result back to local.

## Required deliverables
- refreshed `STATUS.md`, `CURRENT_LOOP_BRIEF.md`, `CURRENT_GATE_PACK.md`, `WEB_SESSION_BRIEF.md`, `loop_state_latest.json`, `CONTROL_PLANE_STATE.json`
- refreshed `TAKEOVER_LATEST.md` and `TAKEOVER_LATEST.json`
- E4A implementation reports, smoke summary, compatibility note, and delta review packet

## Not allowed this round
- any S2A formal experiment execution
- any training / benchmark matrix beyond the bounded E4A smoke
- any shared-path touch
- scope widening outside the approved E4A implementation pack boundary

## Resume note
S2 PASS evidence is preserved; the remaining action is bounded E4A implementation, smoke, and handoff refresh.
