# Environment Audit

| Item | Value | Evidence |
|---|---|---|
| Remote host | `gpu4090d` | SSH verification |
| Remote repo | `/home/zyy/code/wsovps` | `git remote -v` |
| Conda env | `wsovps` | `conda env list` |
| Python | `3.10.20` | remote smoke |
| Torch | `2.1.0+cu118` | remote smoke |
| Torchvision | `0.16.0+cu118` | pip install / smoke |
| CUDA visibility | `True` / `11.8` | remote smoke |
| NumPy | `1.24.1` | remote smoke |
| CLIP module | `openai-clip 1.0.1` | `import clip` |
| mmcv | `1.7.2` | remote smoke |
| mmengine | `0.10.7` | remote smoke |
| mmsegmentation | `0.30.0` | remote smoke |
| opencv-python | `4.13.0.92` | remote smoke |
| `cv2` import | ok | remote smoke |
