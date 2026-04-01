# WSOVPS Mainline Status

This file tracks the authoritative state for document-driven automation.

## Current state
- Current code snapshot status: `E4A implementation round underway; S2 PASS evidence preserved; design-intake overlay remains deployed`
- Gate mode: `science-first-dual-gate`
- Active gate: `E4A`
- Active scientific gate: `S2A`
- Supporting engineering gate(s): `E4A`
- Gate registry mode: `enabled`
- Gate registry: `docs/mainline/gates/REGISTRY.json`
- Gate registry version: `wsovps-new-mainline-v1-private`
- Active gate definition file (from registry): `docs/mainline/gates/engineering/E4A_ORACLEOBJ_LOSS_ATTRIBUTION_INSTRUMENTATION.md`
- Active gate version (from registry): `wsovps-e4a-v1`
- Git commit SHA: `1de2946160385b8632e391a4cc103bb7cb2b6c46`
- Git tree SHA: `ca3490c52c6ea7c8d79496fe795bde6ada989c3a`
- Working tree clean: `false`
- Terminal mainline mode: `not-terminal`
- Scientific status: `active-s2a-design-intake`
- Engineering support status: `prepared`
- Overall progression eligibility: `s2_passed_next_target_ready`
- Evidence bundle reviewed: `yes`
- Current evidence tier: `design`
- Execution model: `local-first`
- Current sync mode: `ssh_snapshot`
- Remote tree verified: `true`
- Archive compliance status: `ARCHIVE_COMPLIANT`
- Archive sync status: `S2 PASS archive evidence preserved; E4A/S2A overlay synchronized`
- Local snapshot id: `not-yet-declared`
- Remote snapshot id: `not-yet-declared`
- Takeover refreshed at: `rendered-by-validation-pass`
- Local latest-doc listener status: `not-required-for-design-intake-round`
- Governance ingestion status: `new gate pack overlay injected into active execution context; no implementation or benchmark execution performed`

## E4A/S2A overlay intake update
- overlay_source: `zip/wsovps_e4a_s2a_gate_overlay`
- current_active_chain: `E2 -> E3 -> E4 -> S2 -> E4A -> S2A -> E5 -> S3 -> E6 -> S4 -> E7 -> S5`
- current_mainline_scientific_target: `S2A`
- current_active_engineering_gate: `E4A`
- deployment_mode: `design_intake_only`
- implementation_status: `in_progress`
- training_status: `not_started`
- benchmark_status: `not_started`
- preserved_s2_evidence: `docs/mainline/reports/s2_round8_formal_latest.md`, `docs/mainline/reports/s2_b0_b1_b2_metrics_latest.md`, `docs/mainline/reports/s2_closure_assessment_latest.md`
- current_round: `bounded E4A implementation + smoke only; no S2A formal execution`

## Round8 formal update (latest)
- round_id: `RUN-S2-ROUND8-FORMAL-R1`
- round8_formal_completed: `yes`
- control_case_sentinel_run: `RUN-S2-ROUND8-CONTROL-SENTINEL-R1` (`PASS`)
- metric_source: `pp116_oracle_obj_runtime_evaluator_output`
- formal_metrics_raw:
  - seen_miou: `0.03455224589060974`
  - unseen_miou: `0.0`
  - harmonic_miou: `0.0`
- formal_metrics_display_percent:
  - seen_miou: `3.455224589060974`
  - unseen_miou: `0.0`
  - harmonic_miou: `0.0`
- s2_judgment_state: `PASS`
- next_step: `handoff preserved; E4A/S2A design-intake review is the next active target`

## E2 repro R2 round update
- round_status: `HARD_BLOCKER`
- blocker_id: `DINO_HUB_CACHE_MISSING`
- requested_pack: `DP-E2-COCO2014-TALK2DINO-PROJECTION-REPRO-PLAN-R2`
- phase_a_materialization: `PASS`
- v0_dataset_checks: `PASS`
- blocker_reason: offline DINO dry-load (`torch.hub.load('facebookresearch/dinov2', 'dinov2_vitb14_reg')`) attempted GitHub access and failed
- next_step: provide offline-resolvable DINOv2 torch.hub source/cache and rerun Phase B

## E2 repro skip update
- round_status: `SKIPPED`
- skip_reason: reproduced weight binding and S2 Round8 provenance already match the bound weight path+sha
- stopped_processes: `2532730`, `2568012`, `2554583`
- partial_outputs: `features/coco2014_b14/train.pth` may exist and is non-canonical evidence
- next_step: comparative closure assessment completed; archive S2 and proceed to E5

## Authoritative-source settlement
- Running planning/control source: uploaded new gate pack, normalized into this private layer.
- Old outline-first governance: `disabled for current mainline`.
- Legacy gates `E0`, `E1`, `S1`: `archived prerequisites only`.
- Historical evidence currently present in the deployed repo: `docs/mainline/experiments/archived/historical/EXP-S1-T2DINO-FAITHFUL/`, `docs/mainline/gates/LEGACY_ARCHIVED_PREREQS.md`, `docs/mainline/gates/history/gate_change_log.md`, `backup/docs/mainline/reports/`, and `backup/logs/`.

## Current blockers
1. `RUN-S2-ROUND4-FORMAL-R1` remains preserved as bridge/intermediate evidence.
2. `RUN-S2-ROUND6-FORMAL-R1` completed as the clean official rerun after formal-input closure repair.
3. `RUN-S2-ROUND8-FORMAL-R1` completed as the latest clean official PP116 formal evidence artifact.
4. S2 closure evidence is preserved; the remaining action is E4A/S2A design-intake normalization.

## Active experiments
- `EXP-E4A-ORACLEOBJ-LOSS-ATTRIBUTION-INSTRUMENTATION` and `EXP-S2A-ORACLEOBJ-LOSS-MECHANISM-VALIDATION` are the current design-intake targets under design-pack governance.
- Prior evidence run `RUN-S2-ROUND2-FORMAL-R1` remains preserved as historical S2 formal evidence.
- `RUN-S2-ROUND4-FORMAL-R1` remains preserved as bridge/intermediate grouped-metric evidence.
- `RUN-S2-ROUND8-FORMAL-R1` is the latest clean formal rerun evidence artifact.

## Next smallest valid step
Review the E4A/S2A design-intake overlay and keep the local canonical truth synchronized.

## Current experiment blockers
- Discovery naming mismatch blocker is cleared by the tiny alias fix.
- No remaining S2 blocker.

## PP116 discovery re-audit correction (canonical remote root)
- audited_repo_root: `/mnt/sda/zyy/code/wsovps`
- corrected_verdict: `PARTIAL / MISREPORTED BLOCKER`
- path_facts: `data/` exists, `data/pascal_part116` exists as symlink to `/mnt/sda/zyy/dataset/PascalPart116`, `datasets/` missing, `Datasets/` missing
- prior_missing-asset claim status: `wrong for canonical remote root; produced from different environment/root`
- discovery_logic_location: `src/open_vocabulary_segmentation/segmentation/datasets/pp116_oracle_obj.py` lines 56-57, 60-66, 80-95
- remaining_issue: no new run in this repair round by design; next clean rerun is pending
- next_step: execute the next clean official S2 rerun, then perform S2 formal judgment

## S2 judgment closure update
- final_judgment: `PASS`
- evidence_paths:
  - formal_report: `docs/mainline/reports/s2_round8_formal_latest.md`
  - comparative_metrics: `docs/mainline/reports/s2_b0_b1_b2_metrics_latest.md`
  - comparative_summary: `docs/mainline/reports/s2_comparative_summary_latest.md`
  - comparative_diagnostics: `docs/mainline/reports/s2_comparative_diagnostics_latest.md`
  - closure_assessment: `docs/mainline/reports/s2_closure_assessment_latest.md`
  - control_case_sentinel: `docs/mainline/reports/s2_round8_control_case_sentinel_latest.md`
  - run_artifact: `docs/mainline/experiments/gates/S2/active/EXP-S2-PP116-ORACLEOBJ-RESIDUAL-ONLY-FEASIBILITY/runs/RUN-S2-ROUND8-FORMAL-R1/s2_round8_formal_attempt.json`
- missing_evidence: `none`
- next_step_category: `proceed to E5 / archive S2`
