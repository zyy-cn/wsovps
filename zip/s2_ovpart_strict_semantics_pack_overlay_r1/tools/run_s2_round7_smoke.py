#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import torch
from PIL import Image

from open_vocabulary_segmentation.segmentation.datasets.pp116_oracle_obj import (
    PP116_PARTS_BY_OBJECT,
    build_pp116_official_object_conditioned_samples,
    get_pp116_object_key_from_category_id,
    get_pp116_oracle_obj_dataset_metadata,
)
from open_vocabulary_segmentation.stage2_protocol.formal_inputs_contract import FormalInputsBundle
from open_vocabulary_segmentation.stage2_residual.runtime import run_pp116_residual_route


RUN_ID = "RUN-S2-ROUND7-SMOKE-R1"
EXPERIMENT_ID = "EXP-S2-PP116-ORACLEOBJ-RESIDUAL-ONLY-FEASIBILITY"
WEIGHT_PATH = Path("/mnt/sda/zyy/code/wsovps/weights/vitb_mlp_infonce.pth")
WEIGHT_SHA256 = "8d573c49452350bc9db6f6d4358ddba717661bfe699d0a5f56e326c7b0fc1332"
K = 5
GRID_HW = (14, 14)
FORMAL_CONFIG = Path("src/open_vocabulary_segmentation/configs/pp116_stage2_residual/b2.yml")


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _l2(vec: np.ndarray) -> np.ndarray:
    return vec / (np.linalg.norm(vec) + 1e-8)


def _load_projection_matrix(weight_path: Path) -> np.ndarray:
    ckpt = torch.load(weight_path, map_location="cpu")
    source = ckpt["state_dict"] if isinstance(ckpt, dict) and "state_dict" in ckpt else ckpt
    if not isinstance(source, dict):
        raise ValueError("unsupported checkpoint format")
    for _, value in source.items():
        if torch.is_tensor(value) and value.ndim == 2:
            return value.detach().cpu().float().numpy()
    raise ValueError("no projection matrix (2D tensor) in checkpoint")


def _project(vec: np.ndarray, proj: np.ndarray) -> np.ndarray:
    if proj.shape[1] >= vec.shape[0]:
        x = np.zeros(proj.shape[1], dtype=np.float32)
        x[: vec.shape[0]] = vec
        out = proj @ x
    else:
        out = proj @ vec[: proj.shape[1]]
    return _l2(out.astype(np.float32))


def _string_vec(*args, **kwargs):
    raise RuntimeError("SYNTHETIC_TEXT_EMBEDDINGS_FORBIDDEN: implement real text encoder per DP-S2-OVPART-STRICT-SEMANTICS-R1")


def _extract_patch_features(*args, **kwargs):
    raise RuntimeError("SYNTHETIC_VISUAL_FEATURES_FORBIDDEN: implement real visual encoder per DP-S2-OVPART-STRICT-SEMANTICS-R1")


def _support_patch_mask(obj_mask: np.ndarray, category_id: int, gh: int, gw: int) -> list[bool]:
    support_region = obj_mask == int(category_id)
    flags: list[bool] = []
    for ys, xs in _grid_slices(obj_mask.shape[0], obj_mask.shape[1], gh, gw):
        flags.append(bool(np.any(support_region[ys, xs])))
    return flags



def _run() -> dict[str, Any]:
    repo_root = Path(__file__).resolve().parents[1]
    metadata = get_pp116_oracle_obj_dataset_metadata()
    if not WEIGHT_PATH.exists():
        raise FileNotFoundError(f"reproduced weight missing: {WEIGHT_PATH}")
    actual_sha = _sha256(WEIGHT_PATH)
    if actual_sha != WEIGHT_SHA256:
        raise RuntimeError(f"reproduced weight sha mismatch: {actual_sha}")

    projection = _load_projection_matrix(WEIGHT_PATH)
    samples = build_pp116_official_object_conditioned_samples(split="val", limit=K)
    if not samples:
        raise RuntimeError("no official object-conditioned PP116 samples found")

    gh, gw = GRID_HW
    results: list[dict[str, Any]] = []
    for sample in samples:
        file_name = sample["file_name"]
        sem_seg_file_name = sample["sem_seg_file_name"]
        obj_sem_seg_file_name = sample["obj_sem_seg_file_name"]
        category_id = int(sample["category_id"])
        object_class_key = get_pp116_object_key_from_category_id(category_id)
        sibling_part_keys = sorted(PP116_PARTS_BY_OBJECT[object_class_key])

        image = np.array(Image.open(file_name).convert("RGB"))
        obj_mask = np.array(Image.open(obj_sem_seg_file_name))
        support_mask = _support_patch_mask(obj_mask, category_id, gh, gw)
        if sum(1 for x in support_mask if x) < 2:
            continue
        patch_features = _extract_patch_features(image, projection, gh, gw)        object_text = _project(_string_vec(object_class_key), projection).tolist()
        part_texts = [
            _project(_string_vec(f"{object_class_key}::{part}"), projection).tolist()
            for part in sibling_part_keys
        ]
        bundle = FormalInputsBundle(
            file_name=file_name,
            sem_seg_file_name=sem_seg_file_name,
            obj_sem_seg_file_name=obj_sem_seg_file_name,
            category_id=category_id,
            sibling_part_keys=sibling_part_keys,
            object_text=object_text,
            part_texts=part_texts,
            patch_features=patch_features,
            support_mask=support_mask,
            formal_evaluator_output={
                "runtime_payload": {
                    "patch_grid_shape": [gh, gw],
                    
                }
            },
            evaluator_output_mode="runtime",
            object_class_key=object_class_key,
            split_tag="val",
            trace_key=f"{Path(file_name).stem}::cat{category_id}",
            feature_source=f"user_reproduced_projection::{WEIGHT_PATH}",
            support_source=f"oracle_obj_mask::{obj_sem_seg_file_name}",
            evaluator_source="pp116_official_evaluator_output",
            run_id=RUN_ID,
            protocol_name="pp116_oracle_obj",
            image_shape=[int(image.shape[0]), int(image.shape[1])],
            patch_grid_shape=[gh, gw],
            feature_dtype="float32",
        )
        out = run_pp116_residual_route(
            mode_name="b2_residual_only",
            config_path=FORMAL_CONFIG,
            formal_mode=True,
            formal_bundle=bundle,
        )
        results.append(
            {
                "sample": {
                    "file_name": file_name,
                    "sem_seg_file_name": sem_seg_file_name,
                    "obj_sem_seg_file_name": obj_sem_seg_file_name,
                    "category_id": category_id,
                },
                "grouped_metrics": out.grouped_metrics,
                "debug": out.debug,
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

    runs_dir = (
        repo_root
        / "docs/mainline/experiments/gates/S2/active/EXP-S2-PP116-ORACLEOBJ-RESIDUAL-ONLY-FEASIBILITY/runs"
        / RUN_ID
    )
    runs_dir.mkdir(parents=True, exist_ok=True)
    artifact = {
        "generated_at": _ts(),
        "run_id": RUN_ID,
        "experiment_id": EXPERIMENT_ID,
        "mode": "smoke",
        "subset_size": len(results),
        "dataset_root": metadata["data_root"],
        "weight": {"path": str(WEIGHT_PATH), "sha256": actual_sha},
        "metrics": {"raw": agg, "display_percent": agg_percent},
        "metric_source": "pp116_official_evaluator_output",
        "samples": results,
    }
    (runs_dir / "s2_round7_smoke_attempt.json").write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    return artifact


def main() -> None:
    print(json.dumps(_run(), indent=2))


if __name__ == "__main__":
    main()

