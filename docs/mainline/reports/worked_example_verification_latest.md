# Worked Example Verification

## Example
- Input: `ProjectionLayer` built from `configs/vitb_mlp_infonce.yaml`.
- Visual tensor: shape `(2, 768)`.
- Text tensor: shape `(2, 512)`.
- Forward call: `model(visual, text)`.

## Intermediate steps
- `OmegaConf.load("configs/vitb_mlp_infonce.yaml")` parsed the model config.
- `ProjectionLayer.from_config(cfg["model"])` constructed the projection module.
- The module projected text into DINO space and computed pairwise similarity.

## Output
- Similarity tensor shape: `(2, 2)`.

## Why this suffices
- It proves the canonical Stage-1 projection module can be constructed and execute a bounded forward step in the repaired remote environment.
