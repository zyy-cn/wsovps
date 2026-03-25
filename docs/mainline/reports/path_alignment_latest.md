# Path Alignment

| Item | Expected path | Actual target | Exists/readable | Action taken |
|---|---|---|---|---|
| Pascal VOC data | `data/pascal_voc` | `/mnt/sda/zyy/dataset/pascal_voc` | yes | Rebound VOC configs to repo-local symlink root |
| Pascal Context data | `data/pascal_context` | `/mnt/sda/zyy/dataset/pascal_context` | yes | Rebound Context configs to repo-local symlink root |
| Talk2DINO weights | `weights/talk2dino` | `/mnt/sda/zyy/weight/talk2dino` | yes | Verified `vitb_mlp_infonce.pth` and `vitl_mlp_infonce.pth` |
| CLIP weights | `weights/CLIP` | `/mnt/sda/zyy/weight/CLIP` | yes | Verified symlink chain and readability |
| DINOv2 weights | `weights/DINOv2` | `/mnt/sda/zyy/weight/DINOv2` | yes | Verified symlink chain and readability |
| VOC config root | `./data/pascal_voc/VOCdevkit/VOC2012` | repo-local tree | yes | Patched `pascal_voc12*.py` and `t_pascal_voc12_20.py` |
| Context config root | `./data/pascal_context/VOCdevkit/VOC2010` | repo-local tree | yes | Patched `pascal_context*.py` and `t_pascal_context59.py` |
| Context ann dir | `SegmentationClass` | `SegmentationClass` | yes | Replaced stale `SegmentationClassContext` binding |
| Context split | `ImageSets/Segmentation/{train,val}.txt` | `ImageSets/Segmentation/{train,val}.txt` | yes | Replaced stale `SegmentationContext/*` binding |
| COCO feature path | `../coco2014_b14/*.pth` | missing | no | Rebound `train.py` defaults; feature materialization still blocked |


## Workflow correction
- Local edits only; remote run only.
- No additional E1 path patch is required; canonical `../coco2014_b14/*.pth` is already the declared target.
