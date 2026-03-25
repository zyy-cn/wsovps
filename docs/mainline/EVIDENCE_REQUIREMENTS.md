# WSOVPS Evidence Requirements

This file defines the minimum durable evidence required before a gate may be marked `PASS`.

## 1. Universal evidence pack requirements
Every active gate should provide:
- quantitative indicators that directly support the gate objective,
- the exact commands run and artifact paths produced,
- one minimal worked example with inputs, intermediate steps, and outputs,
- a concise explanation of why the evidence is sufficient,
- archive copies under `docs/mainline/reports/archive/`.

## 2. Standard durable outputs
Unless a gate explicitly says otherwise, produce:
- `docs/mainline/reports/evidence_latest.txt`
- `docs/mainline/reports/worked_example_verification_latest.md`
- `docs/mainline/reports/worked_example_verification_latest.json`
- `docs/mainline/reports/takeover_latest.md`
- timestamped archive copies for each

## 3. Scientific evidence requirements
- Scientific gates require benchmark tables, exact commands, config / commit capture, and one worked example demonstrating the claimed behavior.
- For S1, evidence must include protocol-alignment notes and benchmark outputs on the declared OVS evaluation set.

## 4. Engineering-support evidence requirements
- Engineering gates require reproducible environment/path evidence, exact wrapper or command invocations, and durable notes that a new session can replay.
- If a long-running job is launched, watcher/listener readiness and re-entry conditions must be documented.

## 5. Gate-specific evidence requirements
- `S1`: benchmark report, acceptance report, evidence report, worked example, config snapshot, and checkpoint/load-integrity notes.
- `E0`: remote bootstrap facts, wrapper availability, environment activation evidence, and HEAD-consistency notes.
- `E1`: dataset/weights paths, feature readiness or extraction plan, and minimal train/eval open-file proof.

## 6. Long-running job evidence requirements
When a gate depends on a long-running job, also record:
- job identity or watcher manifest,
- intended commit and remote HEAD when canonical remote execution matters,
- log paths, artifact paths, and completion conditions,
- watcher-state output if watcher support is used,
- post-completion pull or report-generation outputs when applicable.

## 7. Judgment rule
- If acceptance looks satisfied but the evidence pack is incomplete, return `INCONCLUSIVE`, not `PASS`.
- If evidence contradicts the gate claim, return `FAIL`.
- If canonical validation is required and unavailable, return `BLOCKED` or `INCONCLUSIVE` according to `ENVIRONMENT_AND_VALIDATION.md`.

## 8. Mandatory handoff artifact
- Every meaningful execution cycle must refresh `docs/mainline/reports/takeover_latest.md`.
- A cycle is not considered delivered unless `docs/mainline/reports/takeover_latest.md` has been updated.
- The default user-facing upload-back artifact is `docs/mainline/reports/takeover_latest.md` only.
- Supporting latest/report files remain required as evidence where applicable, but they are secondary to the takeover document for handoff.

## Smoke versus formal evidence
Smoke / worked-example evidence may support debugging, quick falsification, or cheap sanity checks, but it does not by itself satisfy a formal gate unless the gate contract explicitly says so.

## Local latest-doc synchronization evidence
When long-running remote jobs require synchronized local latest docs, also record:
- whether a local latest-doc listener was required,
- which terminal-state protocol it used,
- which remote small files it polled or synchronized,
- which local latest docs/reports were updated,
- the explicit re-entry condition used for the next bounded review.

<!-- GATE_EVIDENCE_START:S1 -->
S1 evidence pack must include: faithful config id; exact training or evaluation command; dataset and checkpoint paths; benchmark outputs for the declared OVS tasks; a concise gap analysis against expected Talk2DINO behavior; one worked example; and explicit judgment on whether Φ_o is reusable for Stage 2.
<!-- GATE_EVIDENCE_END:S1 -->

## Prompt provenance evidence
When prompt provenance is enabled, record:
- the path to `docs/mainline/reports/prompt_used_latest.md`, and
- the matching archive pointer under `docs/mainline/reports/archive/` for that iteration.

## Cold-start recovery evidence
When a mid-project cold start occurs, record:
- the recovery artifacts under `docs/mainline/recovery/`, and
- any conflicts found between recovered context and current executable truth.

When a fresh web-side decision session is part of the workflow, keep these recovery pointers current:
- `docs/mainline/WEB_SESSION_BRIEF.md`
- `docs/mainline/state/CONTROL_PLANE_STATE.json`
- `docs/mainline/DECISION_LOG.md`
- `docs/mainline/CURRENT_EXECUTION_TICKET.md`
