# Start WSOVPS Automation

Deploy this private layer at the **repository root** of the canonical `wsovps` checkout.

Required paths after deployment:
- `AGENTS.md`
- `.codex/config.toml`
- `.agents/skills/*`
- `docs/mainline/*`
- `docs/outline/wsovps_outline_v5.tex`
- `docs/runbooks/mainline_phase_gate_runbook.md`
- `tools/remote_verify_project.sh`
- `tools/watch_training_job.py`
- `tools/local_watch_remote_latest.py`
- `tools/render_state_views.py`
- `tools/validate_gate_registry.py`
- `tools/validate_state_views.py`

## First run
From the repo root:

```bash
codex
```

Then paste the generated project-specific Prompt 2 from `wsovps_prompt2_first_run.txt`.

## Important
The current active scientific gate is already `S1 — Talk2DINO faithful reproduction`, but Codex must first close the required supporting engineering evidence for `E0` and `E1` before any formal S1 judgment.

## Deployment-flow guarantee
This adaptation does not change the kit deployment flow:
- deploy at repo root,
- start Codex from repo root,
- paste Prompt 2,
- begin the first bounded iteration.
