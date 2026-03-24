# WSOVPS Automation AGENTS

This repository runs in **document-driven automation mode**.

## Read protocol (anti-drift, low-token capable)

### Tier A — low-token default
1. Run `python tools/validate_gate_registry.py`.
2. Run `python tools/validate_state_views.py`.
3. If both return OK, read only:
   - `docs/mainline/OPERATING_CONSTITUTION.md`
   - `docs/mainline/CURRENT_LOOP_BRIEF.md`
   - `docs/mainline/loop_state_latest.json`
   - `docs/mainline/CURRENT_GATE_PACK.md`
   - `docs/mainline/CURRENT_EXECUTION_TICKET.md`
   - latest reports under `docs/mainline/reports/*latest*`

### Tier B — canonical fallback
If validation is STALE/CONFLICTED, or if you are starting a fresh session, changing gates, or anything is ambiguous, read in this order:
1. `docs/mainline/INDEX.md`
2. `docs/mainline/PLAN.md`
3. `docs/mainline/IMPLEMENT.md`
4. `docs/mainline/STATUS.md`
5. `docs/mainline/gates/REGISTRY.json`
6. `docs/mainline/gates/active_gate.json`
7. `docs/mainline/gates/scientific/S1.md`
8. any active supporting engineering gate docs
9. `docs/mainline/METRICS_ACCEPTANCE.md`
10. `docs/mainline/EVIDENCE_REQUIREMENTS.md`
11. `docs/mainline/FAILURE_PLAYBOOK.md`
12. `docs/mainline/ENVIRONMENT_AND_VALIDATION.md`
13. `docs/mainline/CODEBASE_MAP.md`
14. `docs/mainline/DECISION_LOG.md`
15. `docs/mainline/CURRENT_EXECUTION_TICKET.md`
16. `docs/outline/wsovps_outline_v5.tex` as goal-layer context only

**Anti-drift rule:** derived views never override canonical docs or executable truth.

## Mission
The current mainline exists to prove the project's core claim:

> Faithfully reproduce Talk2DINO on COCO Captions 2014 and obtain a reviewable, reusable object projector Φ_o before activating Oracle-Obj residual-part experiments.

Any code change that does not directly strengthen that claim should not enter the mainline by default.

## Authority and precedence
Priority order:
1. `AGENTS.md`
2. `docs/mainline/*`
3. repo skills under `.agents/skills/*`
4. current code / configs / artifacts
5. the current user prompt, as long as it does not conflict with 1–4

Historical chats, stale notes, or ad hoc plans are not authoritative.

## Default-on mainline scope
- Faithful Talk2DINO reproduction and object-grounding verification.
- The smallest supporting engineering work needed to make S1 reviewable.
- Durable wait-state, watcher support, and local latest-doc listener setup when long-running jobs are required.

## Default-off modules
Do not enable these unless the active gate explicitly allows them:
- Oracle-Obj residual-part training or evaluation before S1 is formally reviewable.
- Pred-Obj / non-oracle instance-source exploration.
- Non-faithful projector redesigns or historical alternative projector lines.
- Ad hoc evaluation shortcuts, demo-only paths, or HuggingFace-only inference as a substitute for the benchmark path.

## Gate hierarchy and precedence
- Gate mode: `science-first-dual-gate`
- Active scientific gate: `S1 — Talk2DINO faithful reproduction`
- Required supporting engineering gates right now: `E0 — bootstrap and environment alignment`, `E1 — data/weights/features readiness`
- No engineering PASS may activate Stage 2 by itself.
- Smoke / worked-example evidence may support debugging, but it does not count as formal PASS unless the gate contract explicitly says so.

## Operating style
- Make the smallest valid step toward the active scientific gate.
- Prefer faithful reproduction over opportunistic redesign.
- If the blocker is missing implementation, missing launch, or a broken execution path, implement or start the smallest real fix instead of staying in document-only reconciliation.
- If docs and code disagree, correct the control plane toward current executable truth.
- If a long-running task is required, convert it into documented wait-state rather than waiting inside chat.
- If later review depends on synchronized local latest docs, ensure the local latest-doc listener path is ready before launching the long job.
- Treat `docs/mainline/CURRENT_EXECUTION_TICKET.md` as the canonical current-round scope limiter.

## Validation model
- Local checks are informative.
- Canonical PASS is determined by `docs/mainline/ENVIRONMENT_AND_VALIDATION.md`.
- A remote PASS only counts if remote `HEAD == intended local commit`.
- A gate PASS only counts if the acceptance contract and the evidence pack are both complete.
- In dual-gate mode, overall progression counts only if scientific PASS and required engineering PASS are both satisfied.

## Reporting discipline
Every bounded iteration must update:
- `docs/mainline/reports/phase_gate_latest.txt`
- `docs/mainline/reports/acceptance_latest.txt`
- `docs/mainline/reports/evidence_latest.txt`

When required, also update:
- `docs/mainline/reports/worked_example_verification_latest.md`
- `docs/mainline/reports/worked_example_verification_latest.json`
- `docs/mainline/reports/training_watch_latest.txt`

Whenever state changes materially, also update:
- `docs/mainline/STATUS.md`
- `docs/mainline/DECISION_LOG.md` when the approved scope changes
- derived views via `python tools/render_state_views.py`
