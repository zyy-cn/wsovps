You are now operating inside the privatized WSOVPS v5p4-lite control plane.

Mission for this first run:
- align to the takeover-first private layer,
- verify that the archived S1 state remains internally coherent,
- repair only control-plane inconsistencies introduced by deployment,
- do not reopen training/evaluation or activate later gates.

Hard rules:
- Researcher + web-side GPT plan and judge; Codex executes.
- Preserve the local-first execution model. Do not switch to remote-first source editing.
- Treat `docs/mainline/takeover/TAKEOVER_LATEST.md` as the primary web-side handoff artifact.
- Do not declare any new scientific PASS from smoke checks, generic consistency checks, or missing-context assumptions.
- Do not start watcher/listener infrastructure unless the ticket explicitly requires long-running work. It does not for this round.

Read order for this first run:
1. `AGENTS.md`
2. `START_AUTOMATION.md`
3. `docs/mainline/INDEX.md`
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
14. `docs/mainline/PLAN.md`
15. `docs/mainline/IMPLEMENT.md`
16. `docs/mainline/METRICS_ACCEPTANCE.md`
17. `docs/mainline/EVIDENCE_REQUIREMENTS.md`
18. `docs/mainline/FAILURE_PLAYBOOK.md`
19. `docs/mainline/ENVIRONMENT_AND_VALIDATION.md`
20. `docs/mainline/CODEBASE_MAP.md`
21. `docs/mainline/DECISION_LOG.md`
22. `docs/mainline/gates/REGISTRY.json`
23. `docs/mainline/gates/active_gate.json`
24. `docs/mainline/gates/scientific/S1.md`
25. `docs/mainline/gates/engineering/E0.md`
26. `docs/mainline/gates/engineering/E1.md`
27. `docs/mainline/CURRENT_EXECUTION_TICKET.md`
28. latest reports under `docs/mainline/reports/*latest*`
29. `docs/mainline/takeover/TAKEOVER_LATEST.md`
30. `docs/mainline/state/CONTROL_PLANE_STATE.json`
31. `docs/mainline/state/CURRENT_EXECUTION_TICKET.json`

Then do exactly this:
1. Run:
   - `python tools/validate_gate_registry.py --repo-root .`
   - `python tools/validate_state_views.py --repo-root .`
   - `python tools/validate_control_plane_coherence.py --repo-root .` if available and applicable
2. Determine whether the privatized layer is coherent with the archived S1 truth:
   - active scientific gate must remain `S1`
   - evidence tier must remain `formal-benchmark-complete+official-comparison-complete+archive`
   - current scope must remain archive-only / closed
   - no long-running job should be active
   - no experiment should be implicitly reopened
3. If any inconsistency exists among ticket, status, registry, takeover, state json, or latest reports, repair only the minimum necessary control-plane files.
4. Do not run training, feature extraction, evaluation, remote sync, or gate activation.
5. Regenerate derived views and takeover after any state-bearing repair:
   - `python tools/render_state_views.py --repo-root .`
   - `python tools/render_takeover.py --repo-root .`
6. If you changed any state-bearing file, also refresh the durable latest artifacts needed for review so they match the repaired state:
   - `docs/mainline/reports/phase_gate_latest.txt`
   - `docs/mainline/reports/acceptance_latest.txt`
   - `docs/mainline/reports/evidence_latest.txt`
   - `docs/mainline/reports/code_provenance_report_latest.md`
   - `docs/mainline/reports/code_provenance_report_latest.json`
   - `docs/mainline/reports/remote_job_summary_latest.md`
   - `docs/mainline/reports/remote_job_summary_latest.json`
7. Stop after the smallest valid step. This first run is complete when the private layer is coherent and the takeover artifact is fresh.

Output requirements in your final message:
- whether the control plane is coherent or what you repaired,
- exact files touched,
- whether the archived S1 state remained closed,
- any remaining blocker that would prevent a future S2 activation prompt.
