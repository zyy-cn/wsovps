#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
from contextlib import contextmanager
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any

import clip
import numpy as np
import torch
import torch.nn as nn
from PIL import Image

from open_vocabulary_segmentation.segmentation.datasets.pp116_oracle_obj import (
    PP116_PARTS_BY_OBJECT,
    build_pp116_official_object_conditioned_samples,
    get_pp116_object_key_from_category_id,
    get_pp116_oracle_obj_dataset_metadata,
)
from open_vocabulary_segmentation.stage2_protocol.model_assets import (
    build_dinov2_preprocess,
    extract_dinov2_patch_tokens,
    load_local_dinov2_vitb14_reg,
    resolve_local_dinov2_weight_path,
)
from open_vocabulary_segmentation.stage2_protocol.pp116_oracle_obj_evaluator import (
    build_support_patch_mask,
    _support_patch_flags_reference,
)
from open_vocabulary_segmentation.stage2_protocol.formal_inputs_builder import (
    build_formal_inputs_bundle,
)
import open_vocabulary_segmentation.stage2_residual.runtime as residual_runtime


RUN_ID = "RUN-S2-ROUND7-SMOKE-R1"
EXPERIMENT_ID = "EXP-S2-PP116-ORACLEOBJ-RESIDUAL-ONLY-FEASIBILITY"
WEIGHT_PATH = Path("/mnt/sda/zyy/code/wsovps/weights/vitb_mlp_infonce.pth")
WEIGHT_SHA256 = "8d573c49452350bc9db6f6d4358ddba717661bfe699d0a5f56e326c7b0fc1332"
REPRODUCED_WEIGHT_BINDING_REPORT = Path("docs/mainline/reports/reproduced_weight_binding_latest.md")
CLIP_MODEL_NAME = "ViT-B/16"
CLIP_CACHE_PATH = Path("/home/zyy/.cache/clip/ViT-B-16.pt")
K = 5
FORMAL_CONFIG = Path("src/open_vocabulary_segmentation/configs/pp116_stage2_residual/b2.yml")


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run bounded PP116 Round7 smoke evaluation.")
    parser.add_argument("--k", type=int, default=K)
    parser.add_argument("--run-id", type=str, default=RUN_ID)
    parser.add_argument("--split", type=str, default="val")
    parser.add_argument("--file-name", type=str, default=None)
    parser.add_argument("--category-id", type=int, default=None)
    parser.add_argument("--mode", choices=["smoke", "formal"], default="smoke")
    parser.add_argument("--mode-name", type=str, default="b2_residual_only")
    parser.add_argument("--config-path", type=str, default=str(FORMAL_CONFIG))
    return parser


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _read_reproduced_weight_binding(repo_root: Path) -> tuple[Path, str]:
    text = (repo_root / REPRODUCED_WEIGHT_BINDING_REPORT).read_text(encoding="utf-8")
    path_match = re.search(r"chosen_weight_path:\s*`([^`]+)`", text)
    sha_match = re.search(r"sha256:\s*`([^`]+)`", text)
    if path_match is None or sha_match is None:
        raise RuntimeError(
            f"unable to parse reproduced weight binding report: {REPRODUCED_WEIGHT_BINDING_REPORT}"
        )
    return Path(path_match.group(1)), sha_match.group(1)


class _ProjectionMLP(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.linear_layer = nn.Linear(512, 768)
        self.hidden_layers = nn.ModuleList([nn.Linear(768, 768)])
        self.act = nn.Tanh()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.linear_layer(x.float())
        for hidden_layer in self.hidden_layers:
            x = self.act(x)
            x = hidden_layer(x)
        return x


def _load_projection(weight_path: Path, device: torch.device) -> _ProjectionMLP:
    model = _ProjectionMLP().to(device)
    ckpt = torch.load(weight_path, map_location="cpu")
    state = ckpt["state_dict"] if isinstance(ckpt, dict) and "state_dict" in ckpt else ckpt
    if not isinstance(state, dict):
        raise ValueError("unsupported reproduced projection checkpoint format")
    model.load_state_dict(state, strict=True)
    model.eval()
    return model


def _load_real_encoders(device: torch.device) -> tuple[Any, Any, _ProjectionMLP, Any, Any, dict[str, str]]:
    repo_root = Path(__file__).resolve().parents[1]
    bound_weight_path, bound_weight_sha = _read_reproduced_weight_binding(repo_root)
    if bound_weight_path != WEIGHT_PATH:
        raise RuntimeError(
            f"reproduced weight binding path mismatch: report={bound_weight_path} constant={WEIGHT_PATH}"
        )
    if bound_weight_sha != WEIGHT_SHA256:
        raise RuntimeError(
            f"reproduced weight binding sha256 mismatch: report={bound_weight_sha} constant={WEIGHT_SHA256}"
        )
    if not WEIGHT_PATH.exists():
        raise FileNotFoundError(f"reproduced projection checkpoint missing: {WEIGHT_PATH}")
    if _sha256(WEIGHT_PATH) != WEIGHT_SHA256:
        raise RuntimeError("reproduced projection checkpoint sha256 mismatch")
    if not CLIP_CACHE_PATH.exists():
        raise FileNotFoundError(
            "strict offline smoke requires local CLIP cache file: "
            f"{CLIP_CACHE_PATH}"
        )
    clip_model, preprocess = clip.load(
        CLIP_MODEL_NAME,
        device=device,
        download_root=str(CLIP_CACHE_PATH.parent),
    )
    clip_model.eval()
    dino_weight_path = resolve_local_dinov2_weight_path()
    dino_model, dino_provenance = load_local_dinov2_vitb14_reg(
        device=device,
        weight_path=dino_weight_path,
    )
    dino_preprocess = build_dinov2_preprocess()
    if dino_provenance["weight_sha256"] != _sha256(dino_weight_path):
        raise RuntimeError("offline DINOv2 weight sha256 mismatch")
    return clip_model, preprocess, _load_projection(WEIGHT_PATH, device), dino_model, dino_preprocess, dino_provenance


def _encode_texts(
    texts: list[str],
    *,
    clip_model: Any,
    projection: _ProjectionMLP,
    device: torch.device,
    ) -> torch.Tensor:
    with torch.no_grad():
        tokens = clip.tokenize(texts, truncate=True).to(device)
        text_features = clip_model.encode_text(tokens).float()
        projected = projection(text_features)
        projected = projected / projected.norm(dim=-1, keepdim=True).clamp_min(1e-8)
    return projected


def _extract_patch_features(
    image: Image.Image,
    *,
    dino_model: Any,
    preprocess: Any,
    device: torch.device,
) -> tuple[torch.Tensor, tuple[int, int]]:
    patch_tokens, (gh, gw) = extract_dinov2_patch_tokens(
        image,
        model=dino_model,
        preprocess=preprocess,
        device=device,
    )
    if not isinstance(patch_tokens, torch.Tensor):
        raise TypeError("DINO patch extraction must return a torch.Tensor")
    return patch_tokens, (gh, gw)


def _support_patch_mask_reference(
    obj_mask: np.ndarray,
    category_id: int,
    gh: int,
    gw: int,
    *,
    device: torch.device,
) -> torch.Tensor:
    support_region = obj_mask == int(category_id)
    flags = _support_patch_flags_reference(support_region, gh=gh, gw=gw)
    return torch.tensor(flags, dtype=torch.bool, device=device)


def _support_patch_mask(
    obj_mask: np.ndarray,
    category_id: int,
    gh: int,
    gw: int,
    *,
    device: torch.device,
) -> torch.Tensor:
    return build_support_patch_mask(
        obj_mask=obj_mask,
        category_id=category_id,
        gh=gh,
        gw=gw,
        device=device,
    )


@lru_cache(maxsize=4096)
def _read_mask_array(path: str) -> np.ndarray:
    return np.array(Image.open(path))


@lru_cache(maxsize=4096)
def _read_rgb_image(path: str) -> Image.Image:
    return Image.open(path).convert("RGB")


def _normalize_iou_values(iou_by_part_class: Any) -> list[float]:
    if not isinstance(iou_by_part_class, dict):
        return []
    values: list[float] = []
    for value in iou_by_part_class.values():
        try:
            values.append(float(value))
        except (TypeError, ValueError):
            continue
    return values


@contextmanager
def _capture_runtime_evaluator_output() -> Any:
    original = residual_runtime.compute_pp116_oracle_obj_runtime_evaluator_output
    state: dict[str, Any] = {"last": None}

    def _wrapped(*args: Any, **kwargs: Any) -> dict[str, Any]:
        result = original(*args, **kwargs)
        state["last"] = result
        return result

    residual_runtime.compute_pp116_oracle_obj_runtime_evaluator_output = _wrapped
    try:
        yield state
    finally:
        residual_runtime.compute_pp116_oracle_obj_runtime_evaluator_output = original


def _select_samples(
    *,
    split: str,
    k: int,
    file_name: str | None,
    category_id: int | None,
) -> list[dict[str, Any]]:
    samples = build_pp116_official_object_conditioned_samples(split=split)
    if file_name is not None:
        selected = [
            sample
            for sample in samples
            if sample["file_name"] == file_name
            and (category_id is None or int(sample["category_id"]) == int(category_id))
        ]
        if not selected:
            raise RuntimeError(
                f"requested control-case sample not found: file_name={file_name} "
                f"category_id={category_id} split={split}"
            )
        return selected[:1]
    return samples[: max(int(k), 0)]


def _run(
    *,
    run_id: str = RUN_ID,
    k: int = K,
    split: str = "val",
    file_name: str | None = None,
    category_id: int | None = None,
    mode: str = "smoke",
    mode_name: str = "b2_residual_only",
    config_path: str | Path = FORMAL_CONFIG,
) -> dict[str, Any]:
    repo_root = Path(__file__).resolve().parents[1]
    requested_file_name = file_name
    requested_category_id = category_id
    metadata = get_pp116_oracle_obj_dataset_metadata()
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA_REQUIRED")
    device = torch.device("cuda")
    torch.cuda.reset_peak_memory_stats(device)
    clip_model, preprocess, projection, dino_model, dino_preprocess, dino_provenance = _load_real_encoders(device)
    patch_feature_source = "dinov2"
    if patch_feature_source != "dinov2":
        raise RuntimeError("patch_feature_source assertion failed: expected dinov2")

    samples = _select_samples(
        split=split,
        k=k,
        file_name=file_name,
        category_id=category_id,
    )
    if not samples:
        raise RuntimeError("no official object-conditioned PP116 samples found")

    results: list[dict[str, Any]] = []
    text_cache: dict[tuple[str, tuple[str, ...]], torch.Tensor] = {}
    patch_features_cache: dict[str, tuple[torch.Tensor, tuple[int, int]]] = {}
    for sample in samples:
        sample_file_name = sample["file_name"]
        sem_seg_file_name = sample["sem_seg_file_name"]
        obj_sem_seg_file_name = sample["obj_sem_seg_file_name"]
        sample_category_id = int(sample["category_id"])
        object_class_key = get_pp116_object_key_from_category_id(sample_category_id)
        sibling_part_keys = sorted(PP116_PARTS_BY_OBJECT[object_class_key])

        if sample_file_name not in patch_features_cache:
            image = _read_rgb_image(sample_file_name)
            patch_features_cache[sample_file_name] = _extract_patch_features(
                image,
                dino_model=dino_model,
                preprocess=dino_preprocess,
                device=device,
            )
        obj_mask = _read_mask_array(obj_sem_seg_file_name)
        patch_features, (gh, gw) = patch_features_cache[sample_file_name]
        support_mask = _support_patch_mask(obj_mask, sample_category_id, gh, gw, device=device)
        if int(support_mask.sum().item()) < 2:
            continue

        text_cache_key = (object_class_key, tuple(sibling_part_keys))
        if text_cache_key not in text_cache:
            text_cache[text_cache_key] = _encode_texts(
                [object_class_key] + [f"{object_class_key}::{part}" for part in sibling_part_keys],
                clip_model=clip_model,
                projection=projection,
                device=device,
            )
        encoded_texts = text_cache[text_cache_key]
        object_text = encoded_texts[0]
        part_texts = encoded_texts[1:]
        bundle = build_formal_inputs_bundle(
            file_name=sample_file_name,
            sem_seg_file_name=sem_seg_file_name,
            obj_sem_seg_file_name=obj_sem_seg_file_name,
            category_id=sample_category_id,
            sibling_part_keys=sibling_part_keys,
            object_text=object_text,
            part_texts=part_texts,
            patch_features=patch_features,
            support_mask=support_mask,
            formal_evaluator_output={"runtime_payload": {"patch_grid_shape": [gh, gw]}},
            evaluator_output_mode="runtime",
            object_class_key=object_class_key,
            split_tag=split,
            trace_key=f"{Path(sample_file_name).stem}::cat{sample_category_id}",
            feature_source=f"{patch_feature_source}_patch_tokens::{dino_provenance['weight_path']}",
            support_source=f"oracle_obj_mask::{obj_sem_seg_file_name}",
            evaluator_source="pp116_official_evaluator_output",
            run_id=run_id,
            protocol_name="pp116_oracle_obj",
            image_shape=[int(obj_mask.shape[0]), int(obj_mask.shape[1])],
            patch_grid_shape=[gh, gw],
            feature_dtype=str(patch_features.dtype).replace("torch.", ""),
        )
        with _capture_runtime_evaluator_output() as capture:
            out = residual_runtime.run_pp116_residual_route(
                mode_name=mode_name,
                config_path=config_path,
                formal_mode=True,
                formal_bundle=bundle,
            )
        evaluator_output = capture["last"] or {}
        iou_values = _normalize_iou_values(evaluator_output.get("iou_by_part_class"))
        iou_stats = {
            "count": len(iou_values),
            "min": float(min(iou_values)) if iou_values else 0.0,
            "mean": float(sum(iou_values) / len(iou_values)) if iou_values else 0.0,
            "max": float(max(iou_values)) if iou_values else 0.0,
        }
        results.append(
            {
                "sample": {
                    "file_name": sample_file_name,
                    "sem_seg_file_name": sem_seg_file_name,
                    "obj_sem_seg_file_name": obj_sem_seg_file_name,
                    "category_id": sample_category_id,
                },
                "grouped_metrics": out.grouped_metrics,
                "iou_stats": iou_stats,
                "runtime_evaluator_output": {
                    "runtime_provenance": evaluator_output.get("runtime_provenance", {}),
                },
                "debug": {
                    **out.debug,
                    "patch_feature_source": patch_feature_source,
                    "visual_mapping_branch": "phi_only_normalized_residual",
                    "dinov2_provenance": dino_provenance,
                },
            }
        )

    if not results:
        raise RuntimeError("no smoke samples remained after support filter")

    seen = [float(r["grouped_metrics"]["seen_miou"]) for r in results]
    unseen = [float(r["grouped_metrics"]["unseen_miou"]) for r in results]
    harmonic = [float(r["grouped_metrics"]["harmonic_miou"]) for r in results]
    agg = {
        "seen_miou": float(np.mean(seen)),
        "unseen_miou": float(np.mean(unseen)),
        "harmonic_miou": float(np.mean(harmonic)),
    }
    agg_percent = {k: v * 100.0 for k, v in agg.items()}
    torch.cuda.synchronize(device)
    gpu_evidence = {
        "device": str(device),
        "cuda_is_available": torch.cuda.is_available(),
        "cuda_device_count": torch.cuda.device_count(),
        "max_memory_allocated": int(torch.cuda.max_memory_allocated(device)),
        "max_memory_reserved": int(torch.cuda.max_memory_reserved(device)),
    }

    runs_dir = (
        repo_root
        / "docs/mainline/experiments/gates/S2/active/EXP-S2-PP116-ORACLEOBJ-RESIDUAL-ONLY-FEASIBILITY/runs"
        / run_id
    )
    runs_dir.mkdir(parents=True, exist_ok=True)
    artifact = {
        "generated_at": _ts(),
        "run_id": run_id,
        "experiment_id": EXPERIMENT_ID,
        "mode": mode,
        "completed": True,
        "subset_size": len(results),
        "requested_subset_size": int(k),
        "selected_split": split,
        "selected_file_name": requested_file_name,
        "selected_category_id": requested_category_id,
        "dataset_root": metadata["data_root"],
        "category_decode_mode": metadata.get("category_decode_mode"),
        "weight": {"path": str(WEIGHT_PATH), "sha256": WEIGHT_SHA256},
        "clip_cache_path": str(CLIP_CACHE_PATH),
        "dinov2": dino_provenance,
        "patch_feature_source": patch_feature_source,
        "mode_name": mode_name,
        "config_path": str(config_path),
        "metrics": {"raw": agg, "display_percent": agg_percent},
        "metric_source": (
            "pp116_oracle_obj_runtime_evaluator_output"
            if mode == "formal"
            else "pp116_smoke_diagnostic_via_official_evaluator_output"
        ),
        "gpu_evidence": gpu_evidence,
        "evidence_tier": (
            "formal_official_evaluator_output" if mode == "formal" else "smoke_diagnostic_not_official"
        ),
        "is_official_evidence": mode == "formal",
        "samples": results,
    }
    artifact_name = "s2_round8_formal_attempt.json" if mode == "formal" else "s2_round7_smoke_attempt.json"
    (runs_dir / artifact_name).write_text(
        json.dumps(artifact, indent=2),
        encoding="utf-8",
    )
    return artifact


def main() -> None:
    args = _build_arg_parser().parse_args()
    print(
        json.dumps(
            _run(
                run_id=args.run_id,
                k=args.k,
                split=args.split,
                file_name=args.file_name,
                category_id=args.category_id,
                mode=args.mode,
                mode_name=args.mode_name,
                config_path=args.config_path,
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
