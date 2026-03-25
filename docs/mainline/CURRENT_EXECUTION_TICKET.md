# Current Execution Ticket (Canonical Current-Round Scope)

This file is the canonical current-round execution scope for Codex.

## Objective
Complete the first bounded iteration after privatization:
1. verify the control plane and canonical environment assumptions,
2. close the minimum E0 and E1 evidence gaps,
3. if unblocked, execute the smallest S1-serving smoke verification of the faithful Talk2DINO path.

## Active gate binding
- active_gate: `S1 — Talk2DINO faithful reproduction`
- active_scientific_gate: `S1 — Talk2DINO faithful reproduction`
- evidence_tier: `smoke`
- formal_standard_version: `v1`

## Formal PASS requires
- Do **not** declare formal S1 PASS in this first-round ticket unless the full S1 evidence pack is unexpectedly completed.
- E0 must record canonical remote/bootstrap/environment/wrapper facts.
- E1 must record dataset / weight / feature readiness for the faithful path.
- Any S1 smoke result must still be reported as smoke unless the full benchmark contract is satisfied.

## Smoke-only evidence that does NOT count as formal PASS
- a single successful import, dry run, or short smoke launch
- a single checkpoint load without a complete benchmark report
- a single VOC / Context / COCO score without the full protocol/evidence pack
- demo or HuggingFace inference results

## Allowed execution scope
- validate gate registry and state-view tooling
- inspect and bind the authoritative Stage-1 entrypoints
- verify canonical environment and wrapper facts
- verify dataset / weight / feature paths or the exact gaps
- run the smallest faithful smoke check that directly serves S1
- repair only blocking issues discovered by that scope
- if a long-running job becomes necessary, convert it into durable wait-state and prepare watcher/listener readiness

## Required deliverables from Codex this round
- `docs/mainline/reports/phase_gate_latest.txt`
- `docs/mainline/reports/acceptance_latest.txt`
- `docs/mainline/reports/evidence_latest.txt`
- `docs/mainline/reports/takeover_latest.md`
- update `docs/mainline/STATUS.md` if state changed
- regenerate `docs/mainline/CURRENT_LOOP_BRIEF.md`
- regenerate `docs/mainline/loop_state_latest.json`
- regenerate `docs/mainline/CURRENT_GATE_PACK.md`
- regenerate `docs/mainline/WEB_SESSION_BRIEF.md`
- regenerate `docs/mainline/state/CONTROL_PLANE_STATE.json`

## Not allowed this round
- declare formal PASS from smoke-only evidence
- activate Stage 2 or Stage 3 work
- redesign the projector path away from faithful Talk2DINO before the faithful path is judged
- broaden scope beyond the smallest step that serves S1

## GitHub sync record
- synced_commit: `0be9668`
- sync_status: `complete`

## Sync correction note
- workflow: `local edits only; remote run only`
- remote code editing in this run: `not allowed`
- takeover rule: `docs/mainline/reports/takeover_latest.md` is the mandatory upload-back artifact
- authoritative commit truth: `0be9668` on local, GitHub, and remote deployed clone

## Resume / re-entry note
After any wait-state or manual interruption, resume by reading `STATUS.md`, `CURRENT_EXECUTION_TICKET.md`, `gates/REGISTRY.json`, the active gate docs, and latest reports before taking the next bounded step.
