You are operating inside the deployed WSOVPS repository after a gate-pack-driven private-layer migration.

Read first, in this exact order:
1. `AGENTS.md`
2. `docs/mainline/INDEX.md`
3. `docs/mainline/STATUS.md`
4. `docs/mainline/gates/REGISTRY.json`
5. `docs/mainline/gates/active_gate.json`
6. `docs/mainline/gates/engineering/E2_KIT_MIGRATION_AND_ARCHIVE_RECONCILIATION.md`
7. `docs/mainline/gates/scientific/S2_PP116_ORACLEOBJ_RESIDUAL_ONLY_FEASIBILITY.md`
8. `docs/mainline/CURRENT_EXECUTION_TICKET.md`
9. `docs/mainline/experiments/REGISTRY.json`
10. latest reports under `docs/mainline/reports/*latest*`

Operating rules:
- This project is gate-driven, not outline-driven.
- The uploaded new gate pack has already superseded outline-first planning for the running mainline.
- Legacy `E0`, `E1`, `S1` are archived prerequisite evidence only; do not let them override the active chain.
- Preserve the v5p4-lite role model: researcher + web-side GPT plan; Codex executes.
- Preserve the local-first execution model. Do not default to remote-first source editing.
- Do not fabricate experiment status, metrics, or historical evidence that is not present in the real deployed repo.
- Do not advance to `E3`, `E4`, or `S2` claims in this round.
- Do not start a long-running job unless the repo audit reveals a true blocker that cannot be resolved within E2 scope, and if that happens, first repair the ticket/state and record durable wait-state.

Your task in this round is to execute `E2` only:
1. Audit the real deployed repo for any existing legacy control-plane docs, old gate traces, archive surfaces, and active truth conflicts.
2. Keep the new gate chain authoritative:
   `E2 -> E3 -> E4 -> S2 -> E5 -> S3 -> E6 -> S4 -> E7 -> S5`
3. Treat legacy `E0`, `E1`, `S1` as archived prerequisite context only.
4. Reconcile the actual deployed repo into one canonical current control plane under `docs/mainline/*`.
5. Populate or repair the following E2 deliverables using real repo truth:
   - `docs/mainline/reports/migration_summary_latest.md`
   - `docs/mainline/reports/legacy_archive_index_latest.md`
   - `docs/mainline/reports/remote_runtime_manifest_latest.md`
   - `docs/mainline/reports/phase_gate_latest.txt`
   - `docs/mainline/reports/acceptance_latest.txt`
   - `docs/mainline/reports/evidence_latest.txt`
6. Ensure experiment registry semantics remain explicit:
   - archived historical evidence,
   - current active E2 experiment,
   - prepared placeholder future-gate experiments.
7. Run the tool-backed render/validation flow:
   - `python tools/render_experiment_index.py`
   - `python tools/render_state_views.py`
   - `python tools/render_code_provenance_report.py`
   - `python tools/render_takeover.py`
   - `python tools/validate_gate_registry.py`
   - `python tools/validate_experiment_registry.py`
   - `python tools/validate_state_views.py`
   - `python tools/validate_control_plane_coherence.py`
8. Update `docs/mainline/STATUS.md` and refresh takeover so a fresh web-side GPT session can review the settled E2 state.

Deliverable style for this round:
- make the smallest valid changes only,
- prefer archive/reconciliation/validation over new modeling work,
- write durable reports,
- clearly label any unresolved blocker as `INCONCLUSIVE` rather than stretching to a pass.
