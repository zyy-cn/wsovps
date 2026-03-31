# Adaptation Summary

## Adaptation mode
Existing-project upgrade, not fresh-project bootstrap.

## Why
The uploaded WSOVPS package already contained a mature private control plane with completed S1 archive state. Resetting it to a blank intake would lose running truth.

## Key upgrade decisions
- preserved `science-first-dual-gate`
- preserved active scientific gate `S1`
- preserved frozen archive status instead of reopening execution
- switched primary handoff from legacy `docs/mainline/reports/takeover_latest.md` to `docs/mainline/takeover/TAKEOVER_LATEST.md`
- added v5p4-lite role, sync, watcher/listener, design-pack, experiment, post-run, review-packet, and provenance policy files
- initialized empty experiment registries rather than fabricating experiment history
- kept long-job infrastructure available but disabled for the current archive-only ticket
