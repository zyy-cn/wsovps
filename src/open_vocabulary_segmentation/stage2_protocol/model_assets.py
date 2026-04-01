from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import numpy as np
import torch
from PIL import Image

DINOV2_REPO_DIR_CANDIDATES = (
    Path("/mnt/sda/zyy/code/dinov2"),
    Path("/mnt/sda/zyy/code/wsovps/third_party/dinov2"),
)
DINOV2_WEIGHT_PATH_CANDIDATES = (
    Path("/mnt/sda/zyy/weight/DINOv2/dinov2_vitb14_reg4_pretrain.pth"),
)
DINOV2_IMAGE_SIZE = 224
DINOV2_IMAGENET_MEAN = (0.485, 0.456, 0.406)
DINOV2_IMAGENET_STD = (0.229, 0.224, 0.225)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def resolve_local_dinov2_repo_dir() -> Path:
    for candidate in DINOV2_REPO_DIR_CANDIDATES:
        if candidate.exists():
            return candidate
    searched = ", ".join(str(path) for path in DINOV2_REPO_DIR_CANDIDATES)
    raise FileNotFoundError(
        "offline DINOv2 source checkout not found; searched: "
        f"{searched}"
    )


def resolve_local_dinov2_weight_path() -> Path:
    for candidate in DINOV2_WEIGHT_PATH_CANDIDATES:
        if candidate.exists():
            return candidate
    searched = ", ".join(str(path) for path in DINOV2_WEIGHT_PATH_CANDIDATES)
    raise FileNotFoundError(
        "offline DINOv2 vitb14 reg weight not found; searched: "
        f"{searched}"
    )


def load_local_dinov2_vitb14_reg(
    *,
    device: torch.device,
    weight_path: Path | None = None,
) -> tuple[torch.nn.Module, dict[str, Any]]:
    repo_dir = resolve_local_dinov2_repo_dir()
    resolved_weight_path = weight_path or resolve_local_dinov2_weight_path()
    model = torch.hub.load(
        repo_or_dir=str(repo_dir),
        model="dinov2_vitb14_reg",
        source="local",
        pretrained=False,
    )
    checkpoint = torch.load(resolved_weight_path, map_location="cpu")
    state_dict = checkpoint.get("state_dict", checkpoint) if isinstance(checkpoint, dict) else checkpoint
    if not isinstance(state_dict, dict):
        raise ValueError(f"unsupported DINOv2 checkpoint format: {resolved_weight_path}")
    missing, unexpected = model.load_state_dict(state_dict, strict=True)
    if missing or unexpected:
        raise RuntimeError(
            "offline DINOv2 checkpoint failed strict load: "
            f"missing={missing} unexpected={unexpected}"
        )
    model = model.to(device)
    model.eval()
    return model, {
        "repo_dir": str(repo_dir),
        "weight_path": str(resolved_weight_path),
        "weight_sha256": _sha256(resolved_weight_path),
        "model_name": "dinov2_vitb14_reg",
        "device": str(device),
    }


def build_dinov2_preprocess(image_size: int = DINOV2_IMAGE_SIZE):
    def _preprocess(image: Image.Image) -> torch.Tensor:
        if not isinstance(image, Image.Image):
            raise TypeError("image must be a PIL image")
        resized = image.convert("RGB").resize((image_size, image_size), Image.BICUBIC)
        arr = np.asarray(resized, dtype="float32") / 255.0
        tensor = torch.from_numpy(arr).permute(2, 0, 1)
        mean = torch.tensor(DINOV2_IMAGENET_MEAN, dtype=tensor.dtype)[:, None, None]
        std = torch.tensor(DINOV2_IMAGENET_STD, dtype=tensor.dtype)[:, None, None]
        return (tensor - mean) / std

    return _preprocess


def extract_dinov2_patch_tokens(
    image: Image.Image,
    *,
    model: torch.nn.Module,
    preprocess,
    device: torch.device,
) -> tuple[torch.Tensor, tuple[int, int]]:
    image_tensor = preprocess(image).unsqueeze(0).to(device)
    with torch.no_grad():
        outputs = model.forward_features(image_tensor)
        patch_tokens = outputs["x_norm_patchtokens"]
        if isinstance(patch_tokens, list):
            patch_tokens = patch_tokens[0]
        if patch_tokens.dim() == 3:
            patch_tokens = patch_tokens[0]
    patch_size = int(getattr(model, "patch_size", 14))
    gh = int(image_tensor.shape[-2]) // patch_size
    gw = int(image_tensor.shape[-1]) // patch_size
    return patch_tokens.detach(), (gh, gw)
