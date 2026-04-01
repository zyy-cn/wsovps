# Current Execution Ticket (Canonical Current-Round Scope)

This file is the canonical current-round scope for Codex.

## Objective
Run S2A Oracle-Obj loss mechanism formal validation (R2) using the landed E4A attribution surface; GPU1/2 only; no Pred-Obj; preserve S2 PASS; refresh takeover.

## Active gate binding
- active_gate: `S2A`
- active_scientific_gate: `S2A`
- evidence_tier: `formal`
- formal_standard_version: `wsovps-s2a-loss-mechanism-formal-r2`

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
- design_pack_id: `DP-S2A-ORACLEOBJ-LOSS-MECHANISM-FORMAL-R2`
- design_pack_status: `approved`
- allowed_design_deviation: `false`
- milestone_id: `s2a-formal-r2`
- code_change_expected: `true`
- runtime_override_only: `false`
- working_tree_clean: `true`
- local_snapshot_id: `not-yet-declared`
- remote_snapshot_id: `not-yet-declared`
- remote_tree_verified: `true`
- config_snapshot_path: `not-yet-declared`
- governance_ingestion_note: `S2A formal bound to landed E4A attribution surface; E4A smoke evidence is settled and preserved; no Pred-Obj or evaluator drift`
- archive_sync_note: `E4A smoke closeout preserved; S2A formal matrix pending on GPU1/2 only`

## Experiment binding
- experiment_id: `EXP-S2A-ORACLEOBJ-LOSS-MECHANISM-VALIDATION`
- run_id: `RUN-S2A-FORMAL-R2`
- question_type: `formal_scientific_validation`
- level: `formal`
- eligible_for_gate_judgment: `true`
- expected_next_status: `formal_evidence_ready`

## Bound design packs
- `DP-E4A-ORACLEOBJ-LOSS-ATTRIBUTION-IMPLEMENTATION-R1`
- `DP-S2A-ORACLEOBJ-LOSS-MECHANISM-VALIDATION-R1`

## Round constraints
- Preserve S2 PASS evidence and provenance.
- Use remote authoritative runtime only (`/mnt/sda/zyy/code/wsovps`) for execution truth.
- Use GPU1/GPU2 only.
- No Pred-Obj (no E5/S3).
- No evaluator/protocol semantic changes.
- No activation of excluded losses.
- Keep PP116 asset discovery compatibility (`data/pascal_part116`) intact.

## E4A smoke outcome
- E4A smoke: `passed`
- E4A smoke conditions: `full`, `minus_l_inst`, `minus_l_overlap`, `only_l_inst`, `only_l_overlap`, `zero_loss`
- zero_loss_no_update: `true`
- grouped_metric_schema_unchanged: `true`
- evaluator_semantics_unchanged: `true`

## S2A formal scope
- formal_matrix_conditions: `full`, `minus_l_inst`, `minus_l_overlap`, `only_l_inst`, `only_l_overlap`, `zero_loss`
- seeds: `0`, `1`
- sample_budgets: `seed0=100`, `seed1=50`
- GPU constraint note: `CUDA_VISIBLE_DEVICES=1,2; do not use GPU0/GPU3`

## Allowed execution scope
- Run the bounded S2A formal matrix on the landed E4A attribution surface.
- Preserve the settled S2 PASS evidence and the E4A smoke evidence.
- Refresh canonical latest/takeover surfaces and sync the formal result back to local.

## Required deliverables
- refreshed `STATUS.md`, `CURRENT_LOOP_BRIEF.md`, `CURRENT_GATE_PACK.md`, `WEB_SESSION_BRIEF.md`, `loop_state_latest.json`, `CONTROL_PLANE_STATE.json`
- refreshed `TAKEOVER_LATEST.md` and `TAKEOVER_LATEST.json`
- S2A formal matrix reports, mechanism metrics, result metrics, comparison, and judgment recommendation

## Not allowed this round
- any Pred-Obj work (E5/S3)
- any evaluator/protocol semantic change
- any shared-path touch
- scope widening outside the approved S2A formal mechanism-validation pack boundary

## Resume note
S2 PASS evidence is preserved; E4A smoke evidence is settled; the remaining action is bounded S2A formal mechanism validation and handoff refresh.
