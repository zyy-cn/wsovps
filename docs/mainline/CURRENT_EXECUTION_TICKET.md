# Current Execution Ticket (Canonical Current-Round Scope)

This file is the canonical current-round scope for Codex.

## Objective
Execute one clean official S2 benchmark-loop rerun under repaired residual-core + formal-input closure semantics, emit Seen/Unseen/Harmonic mIoU from official evaluator-output path, and update canonical latest/takeover surfaces.

## Active gate binding
- active_gate: `S2`
- active_scientific_gate: `S2`
- evidence_tier: `formal`
- formal_standard_version: `wsovps-s2-v1`

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
- design_pack_id: `DP-S2-PP116-DATA-EVAL-FIDELITY-R1`
- design_pack_status: `approved`
- allowed_design_deviation: `false`
- milestone_id: `not-yet-declared`
- code_change_expected: `true`
- runtime_override_only: `false`
- working_tree_clean: `false`
- local_snapshot_id: `not-yet-declared`
- remote_snapshot_id: `not-yet-declared`
- remote_tree_verified: `true`
- config_snapshot_path: `not-yet-declared`

## Experiment binding
- experiment_id: `EXP-S2-PP116-ORACLEOBJ-RESIDUAL-ONLY-FEASIBILITY`
- run_id: `RUN-S2-ROUND6-FORMAL-R1`
- question_type: `scientific_feasibility`
- level: `formal`
- eligible_for_gate_judgment: `false`
- expected_next_status: `judgment_pending_after_round6`

## Round constraints
- Preserve `RUN-S2-ROUND4-FORMAL-R1` as prior bridge/intermediate evidence.
- Use remote authoritative runtime only (`/mnt/sda/zyy/code/wsovps`) for execution truth.
- No training/optimizer/parameter-update actions.
- Do not promote any gate.
- Keep PP116 asset discovery compatibility (`data/pascal_part116`) intact.

## Allowed execution scope
- Run fast preflight checks for formal-input closure, residual-core semantics, and grouped-evaluator metric source.
- Launch one clean official rerun (`RUN-S2-ROUND6-FORMAL-R1`) with no training.
- Refresh canonical latest/takeover surfaces and sync remote truth back to local.

## Required deliverables
- run artifact for `RUN-S2-ROUND6-FORMAL-R1` with official Seen/Unseen/Harmonic output
- refreshed `STATUS.md`, `phase_gate_latest.txt`, `acceptance_latest.txt`, `evidence_latest.txt`
- refreshed `TAKEOVER_LATEST.md` and `TAKEOVER_LATEST.json`

## Not allowed this round
- any training / optimizer / parameter update
- any gate promotion
- scope widening outside governed S2 benchmark-loop rerun boundary

## Resume note
After round-6 evidence is recorded, apply acceptance-threshold framing and record final S2 PASS/FAIL judgment.
