# WSOVPS Mainline Status

This file tracks the authoritative state for document-driven automation.

## Current state
- Current code snapshot status: `clean official S2 rerun RUN-S2-ROUND6-FORMAL-R1 completed under repaired formal-input closure + residual-core semantics`
- Gate mode: `science-first-dual-gate`
- Active gate: `S2`
- Active scientific gate: `S2`
- Supporting engineering gate(s): `E2`
- Gate registry mode: `enabled`
- Gate registry: `docs/mainline/gates/REGISTRY.json`
- Gate registry version: `wsovps-new-mainline-v1-private`
- Active gate definition file (from registry): `docs/mainline/gates/engineering/E2_KIT_MIGRATION_AND_ARCHIVE_RECONCILIATION.md`
- Active gate version (from registry): `wsovps-e2-v1`
- Git commit SHA: `1de2946160385b8632e391a4cc103bb7cb2b6c46`
- Git tree SHA: `ca3490c52c6ea7c8d79496fe795bde6ada989c3a`
- Working tree clean: `false`
- Terminal mainline mode: `not-terminal`
- Scientific status: `active-s2-formal-rerun-completed-round6`
- Engineering support status: `settled`
- Overall progression eligibility: `s2_ready_for_acceptance_judgment`
- Evidence bundle reviewed: `yes`
- Current evidence tier: `formal`
- Execution model: `local-first`
- Current sync mode: `ssh_snapshot`
- Remote tree verified: `true`
- Archive compliance status: `ARCHIVE_COMPLIANT`
- Archive sync status: `local and remote archive surfaces synchronized; review/latest remains absent; remote snapshot marker remains unbound`
- Local snapshot id: `not-yet-declared`
- Remote snapshot id: `not-yet-declared`
- Takeover refreshed at: `rendered-by-validation-pass`
- Local latest-doc listener status: `not-required-for-current-normalization-round`
- Governance ingestion status: `upgraded private-layer governance injected into active execution context; no gate promotion performed`

## Authoritative-source settlement
- Running planning/control source: uploaded new gate pack, normalized into this private layer.
- Old outline-first governance: `disabled for current mainline`.
- Legacy gates `E0`, `E1`, `S1`: `archived prerequisites only`.
- Historical evidence currently present in the deployed repo: `docs/mainline/experiments/archived/historical/EXP-S1-T2DINO-FAITHFUL/`, `docs/mainline/gates/LEGACY_ARCHIVED_PREREQS.md`, `docs/mainline/gates/history/gate_change_log.md`, `backup/docs/mainline/reports/`, and `backup/logs/`.

## Current blockers
1. `RUN-S2-ROUND4-FORMAL-R1` remains preserved as bridge/intermediate evidence.
2. `RUN-S2-ROUND6-FORMAL-R1` completed as the clean official rerun after formal-input closure repair.
3. Preflight checks passed for asset discovery, formal-input closure enforcement, residual-core semantics, and grouped bridge provenance.
4. S2 remains `INCONCLUSIVE` until acceptance-threshold framing is applied to round-6 metrics.

## Active experiments
- `EXP-S2-PP116-ORACLEOBJ-RESIDUAL-ONLY-FEASIBILITY` is the current scientific target under design-pack governance.
- Prior evidence run `RUN-S2-ROUND2-FORMAL-R1` remains preserved as historical S2 formal evidence.
- `RUN-S2-ROUND4-FORMAL-R1` remains preserved as bridge/intermediate grouped-metric evidence.
- `RUN-S2-ROUND6-FORMAL-R1` is the latest clean formal rerun evidence artifact.

## Next smallest valid step
Apply project acceptance-threshold framing to `RUN-S2-ROUND6-FORMAL-R1` and record final S2 PASS/FAIL judgment.

## Current experiment blockers
- Discovery naming mismatch blocker is cleared by the tiny alias fix.
- Remaining blocker before final judgment is explicit acceptance-threshold application over round-6 formal metrics.

## PP116 discovery re-audit correction (canonical remote root)
- audited_repo_root: `/mnt/sda/zyy/code/wsovps`
- corrected_verdict: `PARTIAL / MISREPORTED BLOCKER`
- path_facts: `data/` exists, `data/pascal_part116` exists as symlink to `/mnt/sda/zyy/dataset/PascalPart116`, `datasets/` missing, `Datasets/` missing
- prior_missing-asset claim status: `wrong for canonical remote root; produced from different environment/root`
- discovery_logic_location: `src/open_vocabulary_segmentation/segmentation/datasets/pp116_oracle_obj.py` lines 56-57, 60-66, 80-95
- remaining_issue: no new run in this repair round by design; next clean rerun is pending
- next_step: execute the next clean official S2 rerun, then perform S2 formal judgment
