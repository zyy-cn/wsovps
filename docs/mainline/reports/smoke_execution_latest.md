# Smoke Execution

## Commands run
- Verified remote repo and env on `gpu4090d`.
- Installed `torch==2.1.0+cu118`, `torchvision==0.16.0+cu118`, `numpy==1.24.1`, `openai-clip==1.0.1`, `openmim`, `mmengine`, `mmsegmentation==0.30.0`, `pycocotools`, and `mmcv-full==1.7.2` in the canonical `wsovps` env.
- Patched remote VOC/Context config roots to repo-local symlink paths.
- Ran remote smoke with `PYTHONPATH=/home/zyy/code/wsovps/src/open_vocabulary_segmentation:/home/zyy/code/wsovps`.

## Smoke results
- `import torch`, `import clip`, `import cv2`, `import mmcv`, `import mmengine`, `import mmseg` all succeeded.
- `OmegaConf.load("configs/vitb_mlp_infonce.yaml")` succeeded.
- `ProjectionLayer.from_config(cfg["model"])` succeeded.
- Dummy forward on `ProjectionLayer` returned a `(2, 2)` similarity matrix.
- Canonical data and weight paths exist and are readable.
- `Config.fromfile("src/open_vocabulary_segmentation/segmentation/configs/_base_/datasets/pascal_voc12_20.py")` and `Config.fromfile("src/open_vocabulary_segmentation/segmentation/configs/_base_/datasets/pascal_context59.py")` succeeded after `PYTHONPATH` was set correctly.

## Exact blocker observed
- The canonical COCO feature artifacts expected by the faithful Stage-1 training path do not exist yet under `../coco2014_b14`.
- `train.py` defaults were rebound to that canonical path, but the files still need to be generated before a faithful Stage-1 run.
