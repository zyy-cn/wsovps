# WSOVPS Mainline Phase/Gate Runbook

This runbook defines one bounded supervisor iteration for the document-driven control plane.

## Read protocol (anti-drift, low-token capable)

### Tier A — low-token default
0. if gate registry exists, validate it first: `python tools/validate_gate_registry.py`
1. validate derived state views: `python tools/validate_state_views.py`
   - if OK, read only: `OPERATING_CONSTITUTION`, `CURRENT_LOOP_BRIEF`, `loop_state_latest.json`, `CURRENT_GATE_PACK`, `CURRENT_EXECUTION_TICKET`, and latest reports.

### Tier B — canonical fallback
If validation is STALE/CONFLICTED or anything is ambiguous, read the canonical control plane:
1. `AGENTS.md`
2. `START_AUTOMATION.md`
3. `docs/mainline/INDEX.md`
4. `docs/mainline/PLAN.md`
5. `docs/mainline/IMPLEMENT.md`
6. `docs/mainline/STATUS.md`
7. `docs/mainline/METRICS_ACCEPTANCE.md`
8. `docs/mainline/EVIDENCE_REQUIREMENTS.md`
9. `docs/mainline/FAILURE_PLAYBOOK.md`
10. `docs/mainline/ENVIRONMENT_AND_VALIDATION.md`
11. `docs/mainline/CODEBASE_MAP.md`
12. `docs/mainline/SUPERVISOR_STATE_MACHINE.md`
13. `docs/mainline/DECISION_LOG.md`
14. `docs/mainline/CURRENT_EXECUTION_TICKET.md`

Anti-drift rule: derived views never override canonical docs or executable truth.

## Standard bounded loop

0. validate derived state views (low-token mode):
   - if gate registry exists, run: `python tools/validate_gate_registry.py`
   - run: `python tools/validate_state_views.py`
   - if OK, use Tier-A read set (`CURRENT_LOOP_BRIEF`, `loop_state_latest.json`, `CURRENT_GATE_PACK`, `CURRENT_EXECUTION_TICKET`, latest reports)
   - if STALE/CONFLICTED, read canonical docs and regenerate via `python tools/render_state_views.py`
1. identify gate mode,
2. identify the active gate or active scientific gate,
3. in dual-gate mode, identify the required supporting engineering gate(s),
4. identify the blocker that currently prevents gate completion,
5. identify whether the current evidence tier is smoke/worked-example or formal,
6. identify the minimum required evidence pack,
7. identify the smallest next valid step,
8. confirm that the step is explicitly allowed by `CURRENT_EXECUTION_TICKET.md`,
9. execute only that scoped step when appropriate,
10. evaluate scientific acceptance, engineering support acceptance, and overall progression when applicable,
11. update `docs/mainline/STATUS.md`,
12. write/update `docs/mainline/reports/phase_gate_latest.txt`, `acceptance_latest.txt`, `evidence_latest.txt`, and any required worked-example outputs,
13. if a long-running job has been started or confirmed, update wait-state, ensure any required local latest-doc listener path is ready, and stop,
14. regenerate derived state views for the next iteration: `python tools/render_state_views.py`
15. stop.

## Wait-state handling
If the smallest next valid step is a long-running training or evaluation job:
- start or confirm the job,
- write the durable wait-state fields,
- optionally launch a remote watcher if the project uses watcher support,
- if later review depends on synchronized local latest docs, verify or prepare the local latest-doc listener path before leaving the loop,
- do not wait indefinitely inside the same bounded loop,
- do not activate a new gate until the required evidence has been recovered and judged.

## Terminal mode
When terminal mode is active:
- do not activate a new gate,
- allow only bounded terminal revalidation,
- refresh terminal summary and evidence outputs as needed,
- stop.

## Fresh web-session cold-start protocol
When a new web-side assistant session is used to continue the same project, reconstruct the current control-plane state in this order:
1. `docs/mainline/takeover/TAKEOVER_LATEST.md`
2. `docs/mainline/WEB_SESSION_BRIEF.md`
3. `docs/mainline/state/CONTROL_PLANE_STATE.json`
4. `docs/mainline/DECISION_LOG.md`
5. `docs/mainline/CURRENT_EXECUTION_TICKET.md`
6. `docs/mainline/gates/active_gate.json` and the active gate document
7. latest reports under `docs/mainline/reports/*latest*`

This protocol restores context for discussion and gate control. Canonical docs and executable truth still win on conflict.

## Skill routing hints
- `delivery_mode=design_pack` or approved development-gate design pack landing step → `design-pack-execution`
- experiment metadata / run / summary / closure mutation → `experiment-ledger-operator`
- `long_running: true` step or managed wait-state → `long-job-orchestrator`
- material state change or takeover refresh → `takeover-refresh-and-handoff`
