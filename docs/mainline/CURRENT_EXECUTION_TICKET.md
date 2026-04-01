# Current Execution Ticket (Canonical Current-Round Scope)

This file is the canonical current-round scope for Codex.

## Objective
Deploy and normalize the E4A/S2A design-intake overlay so the mainline control plane reflects the post-S2 scientific target S2A with E4A as the minimum supporting engineering gate, then update the authoritative latest/takeover surfaces.

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
- design_pack_id: `DP-E4A-ORACLEOBJ-LOSS-ATTRIBUTION-INSTRUMENTATION-R1`
- design_pack_status: `approved`
- allowed_design_deviation: `false`
- milestone_id: `not-yet-declared`
- code_change_expected: `false`
- runtime_override_only: `false`
- working_tree_clean: `false`
- local_snapshot_id: `not-yet-declared`
- remote_snapshot_id: `not-yet-declared`
- remote_tree_verified: `true`
- config_snapshot_path: `not-yet-declared`
- governance_ingestion_note: `git state audited; see docs/mainline/reports/git_state_audit_latest.md for the bounded E4A/S2A overlay/control-plane boundary`
- archive_sync_note: `remote alignment will be captured in docs/mainline/reports/sync_alignment_latest.md after the bounded commit is applied`

## Experiment binding
- experiment_id: `EXP-E4A-ORACLEOBJ-LOSS-ATTRIBUTION-INSTRUMENTATION`
- run_id: `not-yet-declared`
- question_type: `design_intake`
- level: `design`
- eligible_for_gate_judgment: `false`
- expected_next_status: `design_intake_ready`

## Bound design packs
- `DP-E4A-ORACLEOBJ-LOSS-ATTRIBUTION-INSTRUMENTATION-R1`
- `DP-S2A-ORACLEOBJ-LOSS-MECHANISM-VALIDATION-R1`

## Round constraints
- Preserve S2 PASS evidence and provenance.
- Use remote authoritative runtime only (`/mnt/sda/zyy/code/wsovps`) for execution truth.
- No implementation, training, or benchmark execution.
- Do not promote any gate outside canonical design-intake normalization.
- Keep PP116 asset discovery compatibility (`data/pascal_part116`) intact.

## Allowed execution scope
- Normalize the current control-plane truth to reflect the E4A/S2A design-intake overlay.
- Preserve the settled S2 PASS evidence and provenance.
- Refresh canonical latest/takeover surfaces and sync the normalized truth back to local.

## Required deliverables
- refreshed `STATUS.md`, `CURRENT_LOOP_BRIEF.md`, `CURRENT_GATE_PACK.md`, `WEB_SESSION_BRIEF.md`, `loop_state_latest.json`, `CONTROL_PLANE_STATE.json`
- refreshed `TAKEOVER_LATEST.md` and `TAKEOVER_LATEST.json`
- deployment report for the E4A/S2A overlay

## Not allowed this round
- any implementation / training / benchmark execution
- any gate promotion
- scope widening outside the design-intake normalization boundary

## Resume note
S2 PASS evidence is preserved; the remaining action is E4A/S2A design-intake normalization and handoff.
