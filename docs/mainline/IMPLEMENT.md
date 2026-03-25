# WSOVPS Mainline Implement Runbook

## 1. Before editing code
Always do these first.

### Tier A — low-token default
1. Run `python tools/validate_gate_registry.py`.
2. Run `python tools/validate_state_views.py`.
3. If both return OK, read:
   - `docs/mainline/OPERATING_CONSTITUTION.md`
   - `docs/mainline/CURRENT_LOOP_BRIEF.md`
   - `docs/mainline/loop_state_latest.json`
   - `docs/mainline/CURRENT_GATE_PACK.md`
   - `docs/mainline/CURRENT_EXECUTION_TICKET.md`
   - latest reports under `docs/mainline/reports/*latest*`

### Tier B — canonical fallback
If validation is STALE/CONFLICTED or anything is ambiguous:
1. Read `AGENTS.md`.
2. Read `docs/mainline/STATUS.md`.
3. Read `docs/mainline/gates/REGISTRY.json` and `docs/mainline/gates/active_gate.json`.
4. Read the active gate doc and required supporting engineering gate docs.
5. Read `docs/mainline/METRICS_ACCEPTANCE.md`.
6. Read `docs/mainline/EVIDENCE_REQUIREMENTS.md`.
7. Read `docs/mainline/FAILURE_PLAYBOOK.md`.
8. Read `docs/mainline/ENVIRONMENT_AND_VALIDATION.md`.
9. Read `docs/mainline/CODEBASE_MAP.md`.
10. Read `docs/mainline/DECISION_LOG.md` and `docs/mainline/CURRENT_EXECUTION_TICKET.md`.
11. Regenerate derived views after any state-bearing change: `python tools/render_state_views.py`.

Do not code before the active gate, blocker, evidence tier, next valid step, and current execution scope are clear.

## 2. Scope control
- Edit only files needed for the active gate.
- Do not enable default-off modules.
- Do not widen a failing Stage-1 reproduction into a redesign.
- Keep residual-part and Pred-Obj work out of scope until explicitly activated.
- Do not treat smoke-tier evidence as formal PASS.

## 3. Command discipline
- Local checks are informative.
- Canonical PASS depends on `ENVIRONMENT_AND_VALIDATION.md`.
- A gate PASS depends on both the acceptance contract and the evidence pack.
- In dual-gate mode, overall progression depends on scientific PASS and required engineering PASS together.
- Record files changed, commands run, local results, remote results, intended commit, remote HEAD, and whether they match.

## 4. Output discipline
- Task artifacts belong under `codex/<task_dir>/`.
- Mainline gate and acceptance artifacts belong under `docs/mainline/reports/`.
- Do not write loose report files in the repo root.
- `docs/mainline/reports/takeover_latest.md` is the mandatory user-facing handoff artifact for every meaningful execution cycle.

## 5. Mandatory report outputs
Every bounded iteration must write:
- `docs/mainline/reports/phase_gate_latest.txt`
- `docs/mainline/reports/acceptance_latest.txt`
- `docs/mainline/reports/evidence_latest.txt`
- `docs/mainline/reports/takeover_latest.md`

When required, also write:
- `docs/mainline/reports/worked_example_verification_latest.md`
- `docs/mainline/reports/worked_example_verification_latest.json`
- `docs/mainline/reports/training_watch_latest.txt`

Then:
- update `docs/mainline/STATUS.md` if state changed,
- regenerate all derived views.

Future execution prompts and iteration checklists must treat `takeover_latest.md` as the default upload-back artifact and must refresh it before declaring the cycle delivered.

## 6. Long-running training and durable wait-state
If a train/eval job will outlive the current loop:
1. start or confirm the job,
2. write the job identity, artifact paths, completion condition, and next resume action into `STATUS.md`,
3. mark the state `INCONCLUSIVE` or `BLOCKED` as appropriate,
4. stop the loop instead of waiting indefinitely.

Optional watcher policy:
- `tools/watch_training_job.py` may be used under a durable runner such as `nohup` or `tmux`.
- Prefer a structured terminal-state file over only free-text log parsing.
- If later review depends on synchronized local latest docs, prepare `tools/local_watch_remote_latest.py` before the long job is launched.
- Neither watcher nor listener may declare the scientific gate passed on its own.
