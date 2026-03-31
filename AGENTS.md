# WSOVPS Private-Layer Agent Notes

## Execution law
- Researcher + web-side GPT decide.
- Codex executes bounded work.
- Do not widen scope silently.

## Development gate law
- For new module/protocol work, use an approved Design Pack before implementation.
- Respect in-scope / out-of-scope / allowed-path / forbidden-path boundaries.
- Use tiny smoke before larger execution.
- Produce packet-backed evidence and a delta review packet for code-changing module work.
- Do not auto-promote the next gate after settlement.


## Read protocol
- Run `python tools/validate_state_views.py` before trusting low-token derived views.
- If validation passes, prefer `docs/mainline/CURRENT_LOOP_BRIEF.md`, `docs/mainline/loop_state_latest.json`, `docs/mainline/CURRENT_GATE_PACK.md`, `docs/mainline/CURRENT_EXECUTION_TICKET.md`, and `docs/mainline/takeover/TAKEOVER_LATEST.md`.
- If validation returns `STALE` or `CONFLICTED`, fall back to canonical docs under `docs/mainline/*` and regenerate derived views.

## Skill invocation overlay
- Use `mainline-supervisor` for one bounded mainline loop.
- Use `mainline-phase-gate-check` to determine the active gate, blockers, and smallest next step.
- Use `mainline-eval-acceptance` for acceptance judgments after evidence lands.
- Use `design-pack-execution` for `delivery_mode=design_pack` or any approved development-gate design pack landing step.
- Use `experiment-ledger-operator` whenever experiment metadata, run binding, summary, or closure state must change.
- Use `long-job-orchestrator` for `long_running: true` tickets or any bounded step that must enter managed wait-state.
- Use `takeover-refresh-and-handoff` after material state changes, evidence changes, or experiment-state changes.
- These skills refine execution behavior; they do not override ticket authority, canonical docs, or researcher/web-side GPT judgment boundaries.
