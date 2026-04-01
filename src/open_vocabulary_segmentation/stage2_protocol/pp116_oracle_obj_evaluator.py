from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping

import numpy as np
from PIL import Image
import torch

from open_vocabulary_segmentation.stage2_protocol.formal_inputs_contract import FormalInputsBundle
from open_vocabulary_segmentation.segmentation.datasets.pp116_oracle_obj import (
    PP116_PARTS_BY_OBJECT,
    get_pp116_object_key_from_category_id,
)


def _grid_slices(h: int, w: int, gh: int, gw: int) -> list[tuple[slice, slice]]:
    y_edges = np.linspace(0, h, gh + 1).astype(int)
    x_edges = np.linspace(0, w, gw + 1).astype(int)
    out: list[tuple[slice, slice]] = []
    for yi in range(gh):
        for xi in range(gw):
            ys, ye = y_edges[yi], y_edges[yi + 1]
            xs, xe = x_edges[xi], x_edges[xi + 1]
            out.append((slice(ys, ye), slice(xs, xe)))
    return out


@lru_cache(maxsize=128)
def build_patch_index_map_cpu(h: int, w: int, gh: int, gw: int) -> torch.Tensor:
    y_edges = np.linspace(0, h, gh + 1).astype(int)
    x_edges = np.linspace(0, w, gw + 1).astype(int)
    y_coords = torch.arange(h, dtype=torch.int64)
    x_coords = torch.arange(w, dtype=torch.int64)
    y_bins = torch.bucketize(y_coords, torch.tensor(y_edges[1:-1], dtype=torch.int64), right=True)
    x_bins = torch.bucketize(x_coords, torch.tensor(x_edges[1:-1], dtype=torch.int64), right=True)
    return y_bins[:, None] * int(gw) + x_bins[None, :]


@lru_cache(maxsize=256)
def build_patch_index_map_cuda(
    h: int,
    w: int,
    gh: int,
    gw: int,
    device_str: str,
) -> torch.Tensor:
    return build_patch_index_map_cpu(h, w, gh, gw).to(device=torch.device(device_str))


def build_patch_index_map(h: int, w: int, gh: int, gw: int, *, device: torch.device) -> torch.Tensor:
    return build_patch_index_map_cuda(h, w, gh, gw, str(device))


@lru_cache(maxsize=4096)
def _load_mask_array(path: str) -> np.ndarray:
    return np.array(Image.open(path))


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _strict_pack_root() -> Path:
    return (
        _repo_root()
        / "docs/mainline/designs/GATE_S2/DP-S2-OVPART-STRICT-SEMANTICS-R1"
    )


@lru_cache(maxsize=1)
def _load_official_object_part_to_class_id() -> dict[str, int]:
    mapping_path = _strict_pack_root() / "OFFICIAL_PP116_OBJECT_PART_TO_CLASS_ID.json"
    if not mapping_path.exists():
        raise FileNotFoundError(
            "strict OV-PARTS semantics pack mapping is missing: "
            f"{mapping_path}"
        )
    payload = json.loads(mapping_path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("official PP116 object-part mapping must be a JSON object")
    return {str(key): int(value) for key, value in payload.items()}


def _binary_iou(pred: np.ndarray, gt: np.ndarray) -> float:
    inter = int(np.logical_and(pred, gt).sum())
    union = int(np.logical_or(pred, gt).sum())
    if union == 0:
        return 0.0
    return float(inter) / float(union)


def _support_patch_flags_reference(
    support_region: np.ndarray,
    *,
    gh: int,
    gw: int,
) -> list[bool]:
    flags: list[bool] = []
    for ys, xs in _grid_slices(support_region.shape[0], support_region.shape[1], gh, gw):
        flags.append(bool(np.any(support_region[ys, xs])))
    return flags


def build_support_patch_mask(
    *,
    obj_mask: np.ndarray | torch.Tensor,
    category_id: int,
    gh: int,
    gw: int,
    device: torch.device,
) -> torch.Tensor:
    if torch.is_tensor(obj_mask):
        obj_mask_tensor = obj_mask.to(device=device)
    else:
        obj_mask_tensor = torch.from_numpy(np.asarray(obj_mask)).to(device=device)
    support_region = obj_mask_tensor.eq(int(category_id))
    patch_index_map = build_patch_index_map(
        int(obj_mask_tensor.shape[0]), int(obj_mask_tensor.shape[1]), gh, gw, device=device
    )
    out = torch.zeros(int(gh * gw), device=device, dtype=torch.float32)
    out.scatter_reduce_(0, patch_index_map.reshape(-1), support_region.reshape(-1).float(), reduce="amax", include_self=True)
    return out.gt(0)


def _scatter_patch_counts(mask: torch.Tensor, patch_index_map: torch.Tensor, patch_count: int) -> torch.Tensor:
    counts = torch.zeros(int(patch_count), device=mask.device, dtype=torch.int64)
    counts.scatter_add_(0, patch_index_map.reshape(-1), mask.reshape(-1).to(dtype=torch.int64))
    return counts


def _build_pred_masks_from_assignments_reference(
    *,
    assignments: Mapping[str, list[float] | torch.Tensor],
    sibling_assignment_keys: list[str],
    support_patch_flags: list[bool],
    image_shape: tuple[int, int],
    patch_grid_shape: tuple[int, int],
    threshold: float,
) -> dict[str, np.ndarray]:
    h, w = image_shape
    gh, gw = patch_grid_shape
    patch_slices = _grid_slices(h, w, gh, gw)
    support_indices = [idx for idx, keep in enumerate(support_patch_flags) if keep]
    support_count = len(support_indices)
    if support_count <= 0:
        raise ValueError("official runtime evaluator requires non-empty oracle-object support")
    for key in sibling_assignment_keys:
        scores = assignments.get(key)
        if scores is None or len(scores) != support_count:
            raise ValueError(f"assignment length mismatch for key={key}")

    out: dict[str, np.ndarray] = {}
    for key in sibling_assignment_keys:
        pred_mask = np.zeros((h, w), dtype=bool)
        scores = assignments[key]
        if torch.is_tensor(scores):
            scores_iter = scores.detach().float().cpu().tolist()
        else:
            scores_iter = list(scores)
        for local_idx, patch_idx in enumerate(support_indices):
            if float(scores_iter[local_idx]) < float(threshold):
                continue
            ys, xs = patch_slices[patch_idx]
            pred_mask[ys, xs] = True
        out[key] = pred_mask
    return out


def _compute_pp116_oracle_obj_runtime_evaluator_output_reference(
    *,
    bundle: FormalInputsBundle,
    assignments: Mapping[str, list[float] | torch.Tensor],
    sibling_assignment_keys: list[str],
    assignment_threshold: float = 0.5,
) -> dict[str, Any]:
    payload = bundle.formal_evaluator_output or {}
    runtime_payload = payload.get("runtime_payload", {}) if isinstance(payload, Mapping) else {}
    part_mask = _load_mask_array(bundle.sem_seg_file_name)
    obj_mask = _load_mask_array(bundle.obj_sem_seg_file_name)
    if part_mask.shape != obj_mask.shape:
        raise ValueError("part/object mask shape mismatch in runtime evaluator")

    support_region = obj_mask == int(bundle.category_id)
    if not bool(np.any(support_region)):
        raise ValueError("oracle-object support region is empty for category_id")

    patch_grid = runtime_payload.get("patch_grid_shape", bundle.patch_grid_shape)
    if not isinstance(patch_grid, list) or len(patch_grid) != 2:
        raise ValueError("runtime evaluator requires patch_grid_shape=[H,W]")
    patch_grid_shape = (int(patch_grid[0]), int(patch_grid[1]))
    support_patch_flags = (
        list(bool(v) for v in bundle.support_mask.detach().cpu().tolist())
        if torch.is_tensor(bundle.support_mask)
        else list(bool(v) for v in bundle.support_mask)
    )
    pred_masks = _build_pred_masks_from_assignments_reference(
        assignments=assignments,
        sibling_assignment_keys=sibling_assignment_keys,
        support_patch_flags=support_patch_flags,
        image_shape=(int(part_mask.shape[0]), int(part_mask.shape[1])),
        patch_grid_shape=patch_grid_shape,
        threshold=float(assignment_threshold),
    )
    decoded_object_key = get_pp116_object_key_from_category_id(int(bundle.category_id))
    object_class_key = decoded_object_key
    official_mapping = _load_official_object_part_to_class_id()
    gt_labels_in_obj = sorted(int(value) for value in np.unique(part_mask[support_region]) if int(value) != 255)
    expected_part_ids = sorted(
        official_mapping[f"{object_class_key}::{part_key}"]
        for part_key in PP116_PARTS_BY_OBJECT[object_class_key]
        if f"{object_class_key}::{part_key}" in official_mapping
    )
    intersection = sorted(set(gt_labels_in_obj) & set(expected_part_ids))
    if gt_labels_in_obj and not intersection:
        raise ValueError(
            "PP116 category decode intersection check failed: "
            f"file_name={bundle.file_name} category_id={bundle.category_id} "
            f"decoded_object_key={object_class_key} "
            f"gt_labels_in_obj={gt_labels_in_obj[:30]} "
            f"expected_part_ids={expected_part_ids[:30]}"
        )
    iou_by_part_class: dict[tuple[str, str], float] = {}
    for part_key, assign_key in zip(bundle.sibling_part_keys, sibling_assignment_keys):
        mapping_key = f"{object_class_key}::{part_key}"
        if mapping_key not in official_mapping:
            raise KeyError(f"official PP116 mapping missing key: {mapping_key}")
        part_id = official_mapping[mapping_key]
        gt_mask = np.logical_and(support_region, part_mask == int(part_id))
        pred_mask = np.logical_and(support_region, pred_masks[assign_key])
        iou_by_part_class[(object_class_key, part_key)] = _binary_iou(pred_mask, gt_mask)
    return {
        "iou_by_part_class": iou_by_part_class,
        "runtime_provenance": {
            "entrypoint": (
                "open_vocabulary_segmentation.stage2_protocol.pp116_oracle_obj_evaluator:"
                "_compute_pp116_oracle_obj_runtime_evaluator_output_reference"
            ),
            "sem_seg_file_name": bundle.sem_seg_file_name,
            "obj_sem_seg_file_name": bundle.obj_sem_seg_file_name,
            "category_id": int(bundle.category_id),
            "decoded_object_key": object_class_key,
            "assignment_threshold": float(assignment_threshold),
            "patch_grid_shape": [int(patch_grid_shape[0]), int(patch_grid_shape[1])]
        },
    }


def _build_selection_matrix(
    *,
    assignments: Mapping[str, list[float] | torch.Tensor],
    sibling_assignment_keys: list[str],
    support_mask: torch.Tensor,
    threshold: float,
) -> torch.Tensor:
    support_indices = torch.nonzero(support_mask, as_tuple=False).squeeze(1)
    support_count = int(support_indices.numel())
    if support_count <= 0:
        raise ValueError("official runtime evaluator requires non-empty oracle-object support")
    for key in sibling_assignment_keys:
        scores = assignments.get(key)
        if scores is None or len(scores) != support_count:
            raise ValueError(f"assignment length mismatch for key={key}")

    rows: list[torch.Tensor] = []
    for key in sibling_assignment_keys:
        scores = assignments[key]
        if torch.is_tensor(scores):
            score_tensor = scores.detach().to(device=support_mask.device, dtype=torch.float32)
        else:
            score_tensor = torch.tensor(list(scores), device=support_mask.device, dtype=torch.float32)
        selected = score_tensor.ge(float(threshold))
        full_sel = torch.zeros_like(support_mask, dtype=torch.bool, device=support_mask.device)
        full_sel[support_indices] = selected
        rows.append(full_sel)
    return torch.stack(rows, dim=0)


def compute_pp116_oracle_obj_runtime_evaluator_output(
    *,
    bundle: FormalInputsBundle,
    assignments: Mapping[str, list[float] | torch.Tensor],
    sibling_assignment_keys: list[str],
    assignment_threshold: float = 0.5,
) -> dict[str, Any]:
    payload = bundle.formal_evaluator_output or {}
    runtime_payload = payload.get("runtime_payload", {}) if isinstance(payload, Mapping) else {}
    device = bundle.patch_features.device if torch.is_tensor(bundle.patch_features) else torch.device("cpu")
    part_mask_np = _load_mask_array(bundle.sem_seg_file_name)
    obj_mask_np = _load_mask_array(bundle.obj_sem_seg_file_name)
    if part_mask_np.shape != obj_mask_np.shape:
        raise ValueError("part/object mask shape mismatch in runtime evaluator")
    part_mask = torch.from_numpy(part_mask_np).to(device=device)
    obj_mask = torch.from_numpy(obj_mask_np).to(device=device)

    support_region = obj_mask.eq(int(bundle.category_id))
    if not bool(support_region.any().item()):
        raise ValueError("oracle-object support region is empty for category_id")

    patch_grid = runtime_payload.get("patch_grid_shape", bundle.patch_grid_shape)
    if "sibling_part_id_map" in runtime_payload:
        raise ValueError(
            "strict OV-PARTS runtime evaluator forbids runtime_payload.sibling_part_id_map"
        )
    if not isinstance(patch_grid, list) or len(patch_grid) != 2:
        raise ValueError("runtime evaluator requires patch_grid_shape=[H,W]")
    patch_grid_shape = (int(patch_grid[0]), int(patch_grid[1]))

    support_mask = (
        bundle.support_mask.to(device=device, dtype=torch.bool)
        if torch.is_tensor(bundle.support_mask)
        else torch.tensor(list(bool(v) for v in bundle.support_mask), device=device, dtype=torch.bool)
    )
    patch_index_map = build_patch_index_map(
        int(part_mask.shape[0]),
        int(part_mask.shape[1]),
        int(patch_grid_shape[0]),
        int(patch_grid_shape[1]),
        device=device,
    )
    selection_matrix = _build_selection_matrix(
        assignments=assignments,
        sibling_assignment_keys=sibling_assignment_keys,
        support_mask=support_mask,
        threshold=float(assignment_threshold),
    )

    decoded_object_key = get_pp116_object_key_from_category_id(int(bundle.category_id))
    if bundle.object_class_key is not None and bundle.object_class_key != decoded_object_key:
        raise ValueError(
            "formal bundle object_class_key mismatch: "
            f"bundle={bundle.object_class_key} decoded={decoded_object_key}"
        )
    object_class_key = decoded_object_key
    official_mapping = _load_official_object_part_to_class_id()
    gt_labels_in_obj = sorted(
        int(value)
        for value in torch.unique(part_mask[support_region]).detach().cpu().tolist()
        if int(value) != 255
    )
    expected_part_ids = sorted(
        official_mapping[f"{object_class_key}::{part_key}"]
        for part_key in PP116_PARTS_BY_OBJECT[object_class_key]
        if f"{object_class_key}::{part_key}" in official_mapping
    )
    intersection = sorted(set(gt_labels_in_obj) & set(expected_part_ids))
    # Some official val object supports have no part labels inside the object mask.
    # Keep strict decode fail-fast only when GT labels exist but do not intersect expected IDs.
    if gt_labels_in_obj and not intersection:
        raise ValueError(
            "PP116 category decode intersection check failed: "
            f"file_name={bundle.file_name} category_id={bundle.category_id} "
            f"decoded_object_key={object_class_key} "
            f"gt_labels_in_obj={gt_labels_in_obj[:30]} "
            f"expected_part_ids={expected_part_ids[:30]}"
        )
    patch_count = int(patch_grid_shape[0] * patch_grid_shape[1])
    obj_count_per_patch = _scatter_patch_counts(support_region, patch_index_map, patch_count)
    part_keys: list[str] = []
    part_count_rows: list[torch.Tensor] = []
    for part_key in bundle.sibling_part_keys:
        mapping_key = f"{object_class_key}::{part_key}"
        if mapping_key not in official_mapping:
            raise KeyError(f"official PP116 mapping missing key: {mapping_key}")
        part_id = official_mapping[mapping_key]
        gt_mask = support_region & part_mask.eq(int(part_id))
        part_count_rows.append(_scatter_patch_counts(gt_mask, patch_index_map, patch_count))
        part_keys.append(part_key)
    part_count_matrix = torch.stack(part_count_rows, dim=0)
    pred_pixels = (selection_matrix.to(dtype=torch.int64) * obj_count_per_patch.unsqueeze(0)).sum(dim=1, dtype=torch.int64)
    gt_pixels = part_count_matrix.sum(dim=1)
    inter = (selection_matrix.to(dtype=torch.int64) * part_count_matrix).sum(dim=1, dtype=torch.int64)
    union = pred_pixels + gt_pixels - inter
    iou_tensor = torch.where(
        union > 0,
        inter.to(dtype=torch.float64) / union.to(dtype=torch.float64),
        torch.zeros_like(union, dtype=torch.float64),
    )
    iou_values = iou_tensor.detach().cpu().tolist()
    iou_by_part_class = {
        (object_class_key, part_key): float(iou)
        for part_key, iou in zip(part_keys, iou_values)
    }

    return {
        "iou_by_part_class": iou_by_part_class,
        "runtime_provenance": {
            "entrypoint": (
                "open_vocabulary_segmentation.stage2_protocol.pp116_oracle_obj_evaluator:"
                "compute_pp116_oracle_obj_runtime_evaluator_output"
            ),
            "sem_seg_file_name": bundle.sem_seg_file_name,
            "obj_sem_seg_file_name": bundle.obj_sem_seg_file_name,
            "category_id": int(bundle.category_id),
            "decoded_object_key": object_class_key,
            "assignment_threshold": float(assignment_threshold),
            "patch_grid_shape": [int(patch_grid_shape[0]), int(patch_grid_shape[1])],
            "official_part_class_mapping_source": str(
                _strict_pack_root() / "OFFICIAL_PP116_OBJECT_PART_TO_CLASS_ID.json"
            ),
            "gt_labels_in_obj": gt_labels_in_obj,
            "expected_part_ids": expected_part_ids,
            "intersection_part_ids": intersection,
            "empty_gt_labels_in_obj": len(gt_labels_in_obj) == 0,
        },
    }
