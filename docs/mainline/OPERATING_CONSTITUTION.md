# Operating Constitution (Authoritative)

This document is an authoritative, compact rule set for day-to-day Codex loops.
It exists to avoid rereading the full canonical control plane every iteration.

**Authority & anti-drift rule:**
- This constitution is authoritative.
- `CURRENT_LOOP_BRIEF.md`, `loop_state_latest.json`, `CURRENT_GATE_PACK.md`, `WEB_SESSION_BRIEF.md`, and `state/CONTROL_PLANE_STATE.json` are *derived views*.
- If derived views conflict with canonical docs (`STATUS.md`, gate contracts, evidence requirements, code/config/artifacts), canonical truth wins.
- If validation indicates derived views are stale or conflicted, fall back to the canonical control plane and regenerate views.

## R1. Code truth outranks stale prose
Executable truth (current code/config/artifacts) outranks stale control-plane text.
Old gate judgments may be downgraded or reopened when the formal standard changes.

## R2. Science-first; engineering serves science
Scientific gates are authoritative. Engineering work must directly support the active scientific gate.
Do not expand engineering scope into unrelated work.

## R3. Smoke vs formal tiering
Smoke/worked-example checks support debugging and cheap falsification.
They do not count as formal PASS unless the acceptance contract explicitly allows it.

## R4. Trade-off judgment default
If headline/benchmark metrics materially improve while an important diagnostic materially worsens,
default to `INCONCLUSIVE` unless the formal acceptance contract explicitly accepts the regression.

## R5. Long jobs: durable wait-state + dual-plane monitoring
Long-running remote work must become durable wait-state.
Remote watcher is optional; when later review depends on synchronized local latest docs, a local latest-doc listener is also required.
Do not launch a long job when local review depends on synced latest docs and no local listener path is ready.
Every wait-state must define an explicit re-entry condition.

## R6. Current-round execution scope is explicit
`CURRENT_EXECUTION_TICKET.md` is the canonical current-round scope limiter for Codex execution.
Do not rely on stale chat summaries when the ticket exists.

## R7. Cold-start recovery mode
For mid-project cold starts, restore progress context from latest + archive/handoff/reports first.
For fresh web-side decision sessions, prefer the lightweight read set: `WEB_SESSION_BRIEF.md`, `state/CONTROL_PLANE_STATE.json`, `DECISION_LOG.md`, and `CURRENT_EXECUTION_TICKET.md`.
Recovery is a context layer; it does not override current executable truth.

## R8. Prompt provenance
Archive the execution prompt used each iteration when prompt provenance is enabled.
Prompt archives support recovery of execution intent; they do not override current truth.

## R9. Mandatory takeover handoff
Every meaningful execution cycle must refresh `docs/mainline/reports/takeover_latest.md`.
The default user-facing upload-back artifact is `docs/mainline/reports/takeover_latest.md` only.
Supporting latest/report files remain evidence, but they are secondary to the takeover document for handoff.
