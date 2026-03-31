# WSOVPS Evidence Requirements

This file defines the minimum durable evidence required before a gate may be marked `PASS`.

## Universal evidence pack requirements
Every active gate should provide, at minimum:
- the exact commands run and the artifact paths produced,
- one minimal worked example or tiny smoke result when the gate changes implementation paths,
- a concise explanation of why the evidence is sufficient,
- archive copies under `docs/mainline/reports/archive/` for durable recovery.

## Module-development evidence additions
When a gate implements or lands a module/protocol/mechanism, also require:
- the approved design-pack identity,
- a tiny smoke result before larger execution,
- a delta review packet listing changed files, compatibility notes, smoke results, and unresolved risks,
- explicit statement of whether shared paths were touched.

## Judgment rule
- If acceptance is satisfied but the required evidence pack is incomplete, return `INCONCLUSIVE`, not `PASS`.
- If smoke proves wiring but not the formal contract, do not declare formal PASS.
