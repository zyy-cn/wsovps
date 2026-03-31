# Start Automation for WSOVPS

This project uses the mainline workflow kit in document-driven automation mode.

## Deployment flow
The deployment flow is unchanged from the base kit:
1. place the project-private layer at repo root,
2. keep `AGENTS.md` and `START_AUTOMATION.md` at repo root,
3. keep `docs/mainline/*` as the canonical control plane,
4. run Codex from repo root with the project-specific first-run prompt.

## Current operating defaults
- takeover-first web handoff,
- local-first code modification,
- remote runner execution mirrors,
- managed watcher/listener only for long-running tickets,
- gate-boundary git, ssh snapshot by default,
- gate-first lightweight experiment management,
- mini-safe experiment mutations through tools only.

## Additional v5p4-lite controls
- commit-bound execution and runtime-override config snapshots,
- delivery-mode control (`prompt`, `mini_spec`, `design_pack`),
- gate-bound design packs for web-side GPT planning attachments,
- post-run evidence packets under experiment/run directories,
- provenance hardening,
- non-decision review packets,
- takeover-first cold-start recovery.
