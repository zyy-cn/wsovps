# E0 Bootstrap Report

## Judgment
- E0: `PASS` at the support-path level, with remote env/bootstrap aligned and smoke-validated.

## Evidence
- Canonical remote repo verified at `/home/zyy/code/wsovps` with origin `git@github.com:zyy-cn/wsovps.git`.
- Remote conda env `wsovps` exists and activates cleanly on `gpu4090d`.
- Python `3.10.20`, torch `2.1.0+cu118`, CUDA `11.8`, `mmcv-full 1.7.2`, `mmengine 0.10.7`, `mmsegmentation 0.30.0`, `openai-clip 1.0.1` present.
- `clip`, `cv2`, `mmcv`, `mmengine`, `mmseg`, and `ProjectionLayer` smoke imports/forward all succeeded.
- Canonical wrapper `tools/remote_verify_project.sh` is present and the remote shell recipe works.

## Notes
- GitHub sync is still being finalized in the workspace; the environment/bootstrap itself is complete.
