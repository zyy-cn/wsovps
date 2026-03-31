# WSOVPS Skill Overlay Apply Notes

Base package audited: `wsovps_20260329.zip`

This overlay was rebuilt only from the latest renamed authority package uploaded in the current session.

## Included changes
- 4 new skills under `.agents/skills/*`
- AGENTS overlay updates
- mainline policy / runbook activation hooks
- refreshed derived views and takeover snapshots from the audited build path
- `POST_APPLY_REFRESH.sh`

## Apply
1. Extract this overlay at the repository root and allow overwrite.
2. Run:
   `bash POST_APPLY_REFRESH.sh`

The refresh step is required because `validate_state_views.py` is path-sensitive in the current project tooling.
