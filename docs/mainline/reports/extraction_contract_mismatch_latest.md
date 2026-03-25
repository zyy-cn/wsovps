# Extraction Contract Mismatch

## Summary
- The README-documented faithful feature extraction path uses official COCO 2014 JSON inputs:
  - `../coco/captions_train2014.json`
  - `../coco/captions_val2014.json`
- The local extractor previously treated ordinary file inputs as `torch.load`-able artifacts unless the input was a directory or tar archive.
- That behavior produced `_pickle.UnpicklingError: invalid load key, '{'` on the official JSON inputs.

## Local-only compatibility patch
- `dino_extraction_v2.py` now loads `ann_path` with `json.load` when the path ends with `.json`.
- `dino_extraction_v2.py` now also accepts the modern DINOv2 hub return value when it is a dict, using the existing feature keys directly.
- Existing directory, tar, and PTH behavior is unchanged.

## Why this is faithful
- The README already defines JSON inputs for the faithful Talk2DINO feature-extraction commands.
- The patch only restores the documented JSON contract and the model-output contract expected by the current faithful extraction path.
- Downstream feature computation is unchanged.
