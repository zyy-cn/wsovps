# Deployment Instructions — Clean WSOVPS v5p4-lite Private Layer

## What this package is
This is a clean replacement overlay that removes the old-control-plane contamination found in the first overlay.

## Deploy
1. Unzip this package at the root of the existing `wsovps` repository.
2. Allow overwrite of the previously generated private-layer files.
3. Do not delete project source code, logs, data, weights, or archived reports.
4. Start Codex from repo root.
5. Paste `project_specific_prompt2_wsovps_v5p4_lite_clean.md`.

## Expected first-run behavior
- validate gate registry / state views / coherence
- repair only control-plane inconsistencies if any remain
- preserve the archived S1 state
- do not start new training or evaluation
