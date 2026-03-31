# Current Loop Brief (Derived View)

**Derived view / anti-drift notice:** validate before use; canonical docs outrank this view.

- generated_at: `2026-03-30T22:58:57`
- source_digest: `9d0358e0226a5040e916077b01ab4f8e3d586253e21ddd271e05d784283ef036`
- state_version: `50dac0e49f1d`

## Read protocol (default)
1) Validate state views: `python tools/validate_state_views.py`
2) If OK, read only: `CURRENT_LOOP_BRIEF.md`, `loop_state_latest.json`, `CURRENT_GATE_PACK.md`, `CURRENT_EXECUTION_TICKET.md`, plus latest reports.
3) If STALE/CONFLICTED, read canonical control plane and regenerate: `python tools/render_state_views.py`.

## Current gate & tier
- active_gate: `S2`
- active_scientific_gate: `S2`
- evidence_tier: `formal`

## Current blocker summary
not-yet-generated

## Next smallest valid step
not-yet-declared

## Formal standard reminder
S2 closes only on clean official PP116 Oracle-Obj benchmark-loop evidence with valid Seen/Unseen/Harmonic reporting and B0/B1/B2 comparability.

## Re-entry condition
not-yet-declared

## Current execution scope objective
Run one clean official S2 rerun under the repaired formal path in the authoritative remote runtime, then refresh canonical surfaces and local sync-back for judgment readiness.

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
