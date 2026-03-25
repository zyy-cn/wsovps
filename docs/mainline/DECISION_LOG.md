# Decision Log

This log records approved control-plane decisions.
Newest approved decision stays in `## Latest approved decision`.

## Latest approved decision
- decision_id: `wsovps-intake-v1`
- approved_at: `2026-03-24 17:27:20`
- approved_by: `user+assistant`
- active_gate: `S1 — Talk2DINO faithful reproduction`
- active_scientific_gate: `S1 — Talk2DINO faithful reproduction`
- evidence_tier: `smoke`
- formal_standard_version: `v1`

### Summary
Render a private mainline for WSOVPS with science-first dual-gate control. Keep S1 as the active scientific gate, use E0 and E1 as the supporting engineering gates, and forbid Oracle-Obj residual-part work until the faithful Talk2DINO reproduction path becomes reviewable.

### Formal PASS requires
- E0 and E1 evidence complete.
- S1 benchmark/evidence pack complete.
- Smoke evidence does not count as formal PASS.

### Allowed execution scope
- bootstrap and environment alignment
- data/weights/features readiness
- smallest faithful S1 smoke verification
- durable wait-state setup when required

### Not allowed
- activate S2 or S3
- count smoke-only evidence as formal PASS
- silently replace the faithful Stage-1 path with a different mainline

### Current round note
- Remote `gpu4090d` environment was repaired in place to `torch 2.1.0+cu118`, `mmcv-full 1.7.2`, `mmengine 0.10.7`, `mmsegmentation 0.30.0`, `openai-clip 1.0.1`.
- Canonical data/weight symlinks were verified.
- Remote smoke passed for import, config parsing, and `ProjectionLayer` forward step.
- The canonical COCO 2014 data root `data/coco2014` was audited on `gpu4090d`, and the official 2014 caption JSONs were found under `annotations/`.
- The README paths `../coco/captions_train2014.json` and `../coco/captions_val2014.json` were materialized through symlink/path alignment.
- The faithful extraction failed on the first command because `dino_extraction_v2.py` still called `torch.load(ann_path)` before the local patch, and therefore could not consume the JSON annotation inputs.
- A local-only compatibility patch now restores `.json` loading via `json.load` while preserving dir/tar/PTH behavior.
- Canonical COCO feature `.pth` artifacts could not yet be materialized until the patched code is deployed to the remote repo and replayed.

### Workflow correction note
- Local edits only; remote run only.
- Remote code is treated as a deploy target, not a patch target, for this run.

### Takeover protocol note
- `docs/mainline/reports/takeover_latest.md` is the canonical single-document handoff artifact.
- `docs/mainline/TAKEOVER_SCHEMA.md` defines the structured content that takeover reports must carry.
- When a cycle involves inspection, inventory, path audit, artifact verification, or failure diagnosis, the takeover report must embed the decision-critical subset directly.
- Supporting latest/report files remain evidence, but they are secondary to the takeover document for user upload-back.

### Approval-reduction note
- `.codex/config.toml` is repo-scoped to reduce approval interruptions in trusted runs.
- `docs/runbooks/codex_approval_reduction.md` records the recommended allowlist prefixes and the user-level rule text.

### Git sync cadence note
- Refreshing `docs/mainline/reports/takeover_latest.md` does not by itself require a Git commit or push.
- Commit and push are the default synchronization point at gate completion.
- Earlier sync is allowed only when operationally necessary or explicitly requested.

### Next ticket file
- `docs/mainline/CURRENT_EXECUTION_TICKET.md`

## Prior approved decisions
- none yet
