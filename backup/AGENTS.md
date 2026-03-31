# WSOVPS Automation AGENTS

This repository runs in document-driven automation mode.

## Read protocol

### Tier A — low-token default
1. Run `python tools/validate_state_views.py`.
2. If OK, read only:
   - `docs/mainline/CURRENT_LOOP_BRIEF.md`
   - `docs/mainline/loop_state_latest.json`
   - `docs/mainline/CURRENT_GATE_PACK.md`
   - `docs/mainline/CURRENT_EXECUTION_TICKET.md`
   - `docs/mainline/state/CURRENT_EXECUTION_TICKET.json`
   - `docs/mainline/takeover/TAKEOVER_LATEST.md`
   - latest reports under `docs/mainline/reports/*latest*`

### Tier B — canonical fallback
If validation returns STALE/CONFLICTED, or if you are starting a fresh session, changing gate/standard, or anything is ambiguous, read in this order:
1. `docs/mainline/INDEX.md`
2. `docs/mainline/PLAN.md`
3. `docs/mainline/IMPLEMENT.md`
4. `docs/mainline/STATUS.md`
5. `docs/mainline/ROLE_CHARTER.md`
6. `docs/mainline/SYNC_AND_EXECUTION_POLICY.md`
7. `docs/mainline/LISTENER_WATCHER_POLICY.md`
8. `docs/mainline/REMOTE_SUMMARY_PROTOCOL.md`
9. `docs/mainline/GIT_AND_SNAPSHOT_POLICY.md`
10. `docs/mainline/TAKEOVER_PROTOCOL.md`
11. `docs/mainline/EXPERIMENT_MANAGEMENT_POLICY.md`
12. `docs/mainline/DELIVERY_MODE_POLICY.md`
13. `docs/mainline/DESIGN_PACK_PROTOCOL.md`
14. `docs/mainline/designs/AGENTS.md`
15. `docs/mainline/experiments/AGENTS.md`
16. `docs/mainline/experiments/STATE_TRANSITIONS.md`
17. `docs/mainline/gates/REGISTRY.json`
18. `docs/mainline/gates/active_gate.json`
19. `docs/mainline/gates/scientific/S1.md`
20. `docs/mainline/gates/engineering/E0.md`
21. `docs/mainline/gates/engineering/E1.md`
22. `docs/mainline/METRICS_ACCEPTANCE.md`
23. `docs/mainline/EVIDENCE_REQUIREMENTS.md`
24. `docs/mainline/FAILURE_PLAYBOOK.md`
25. `docs/mainline/ENVIRONMENT_AND_VALIDATION.md`
26. `docs/mainline/CODEBASE_MAP.md`
27. `docs/mainline/DECISION_LOG.md`
28. `docs/mainline/CURRENT_EXECUTION_TICKET.md`
29. `docs/mainline/state/CURRENT_EXECUTION_TICKET.json`

**Anti-drift rule:** derived views never override canonical docs or executable truth. If they disagree, regenerate them.

## Mission
> Faithfully reproduce Talk2DINO on COCO Captions 2014 and obtain a reusable object projector Φ_o before any Oracle-Obj residual-part work.

## Role boundary
- Researcher + web-side GPT plan, approve, and judge.
- Codex executes bounded tickets.
- Codex must not silently become the research authority.

## Default execution model
- modify code locally first,
- capture every code change in a local git commit before remote execution,
- export a commit-derived tree to the remote runner when remote execution is needed,
- run remotely,
- summarize remotely,
- sync back small review artifacts, review packets, and post-run evidence packets,
- refresh takeover.

## Gate hierarchy and precedence
- Gate mode: `science-first-dual-gate`
- In dual-gate mode, the active scientific gate is authoritative.
- Supporting engineering gates exist only to make the active scientific gate reviewable and reproducible.
- No engineering PASS may activate the next scientific gate by itself.

## Operating style
- Make the smallest valid step toward the current gate.
- Do not widen scope to hide a failing result.
- Respect smoke vs formal evidence tiering.
- If docs and code disagree, correct the control plane toward current code/config/artifact truth.
- If the ticket is not long-running, do not turn on watcher/listener infrastructure.
- If the ticket is long-running, use the managed launch path and update registries.
- Refresh takeover after material state changes.

## Mini-safe execution rules
- For the current round, follow this priority order only: ticket machine-state json, nearest applicable AGENTS.md, registry/state json, takeover, then other latest docs. Do not let takeover override ticket authority.
- Do not infer missing experiment fields. If `experiment_id`, `run_id`, `question_type`, `level`, or `expected_next_status` are missing for experiment work, stop and repair the ticket first.
- Do not edit experiment registries, experiment indexes, or the takeover experiment ledger by hand. Use the dedicated tools.
- Do not interpret takeover as permission to change the ticket. Takeover is a review package, not the current execution authority.
- For code-changing work, do not proceed unless git preconditions are satisfied or the ticket explicitly states runtime-override-only work.
- If `delivery_mode=design_pack`, do not implement until the bound design pack is approved and validated.
