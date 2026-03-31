# WSOVPS Mainline Implement Runbook

## 1. Before editing code
### Tier A — low-token default
1. Run `python tools/validate_gate_registry.py`.
2. Run `python tools/validate_state_views.py`.
3. If OK, read only:
   - `docs/mainline/OPERATING_CONSTITUTION.md`
   - `docs/mainline/CURRENT_LOOP_BRIEF.md`
   - `docs/mainline/loop_state_latest.json`
   - `docs/mainline/CURRENT_GATE_PACK.md`
   - `docs/mainline/CURRENT_EXECUTION_TICKET.md`
   - latest reports under `docs/mainline/reports/*latest*`
4. Confirm the smallest next valid step from `CURRENT_LOOP_BRIEF.md`.

### Tier B — canonical fallback
If validation is STALE/CONFLICTED or anything is ambiguous:
1. Read `AGENTS.md`.
2. Determine gate mode and current active gate from `STATUS.md`.
3. Read `docs/mainline/gates/REGISTRY.json` and `docs/mainline/gates/active_gate.json`.
4. Read the active engineering gate doc and the current scientific target doc.
5. Identify blocking acceptance conditions from `METRICS_ACCEPTANCE.md`.
6. Identify required evidence pack from `EVIDENCE_REQUIREMENTS.md`.
7. Identify the smallest valid step and fallback.
8. Read `docs/mainline/DECISION_LOG.md` if needed.
9. After any state-changing iteration, regenerate derived views: `python tools/render_state_views.py` and `python tools/render_takeover.py`.

## 1A. Gate-registry-first rule
If `docs/mainline/gates/REGISTRY.json` exists, it is the primary running-gate source. Do not infer current gate semantics from old outlines, old gate docs, or stale status prose.

## 2. Scope control
- Edit only files needed for the current gate.
- Do not enable default-off modules.
- Do not broaden a failing experiment into a redesign.
- Do not reinterpret environment failures as algorithmic failures.
- In dual-gate mode, all engineering work must directly serve the current scientific target.
- For `E2`, prioritize settlement of control-plane truth, archive mapping, registry/index integrity, and manifest-based reconciliation.

## 3. Command discipline
- Local checks are informative unless the environment contract declares them canonical.
- A gate passes only if its acceptance contract and evidence pack are both satisfied.
- For long-running gates, durable wait-state is mandatory.

## 4. Output discipline
- Task artifacts belong under `codex/<task_dir>/`.
- Mainline gate and acceptance artifacts belong under `docs/mainline/reports/`.
- Do not write loose root-level output files.

## 5. Mandatory report outputs
- `docs/mainline/reports/phase_gate_latest.txt`
- `docs/mainline/reports/acceptance_latest.txt`
- `docs/mainline/reports/evidence_latest.txt`
- any gate-specific summary/manifests required by the active gate
- `docs/mainline/CURRENT_LOOP_BRIEF.md` and `docs/mainline/loop_state_latest.json`
- `docs/mainline/WEB_SESSION_BRIEF.md`
- `docs/mainline/state/CONTROL_PLANE_STATE.json`
- `docs/mainline/takeover/TAKEOVER_LATEST.md`

## 6. Long-running training and durable wait-state
Later training/eval gates may use watcher/listener machinery. `E2` should not enable it unless the actual repo audit identifies a real active long job that must be reconciled.
