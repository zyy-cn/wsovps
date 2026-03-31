from __future__ import annotations

from typing import Any, Mapping

import numpy as np
from PIL import Image

from open_vocabulary_segmentation.stage2_protocol.formal_inputs_contract import FormalInputsBundle
from open_vocabulary_segmentation.segmentation.datasets.pp116_oracle_obj import (
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


def _to_int_mapping(raw: Any) -> dict[str, int]:
    if not isinstance(raw, Mapping):
        return {}
    out: dict[str, int] = {}
    for k, v in raw.items():
        try:
            out[str(k)] = int(v)
        except Exception:
            continue
    return out


def _binary_iou(pred: np.ndarray, gt: np.ndarray) -> float:
    inter = int(np.logical_and(pred, gt).sum())
    union = int(np.logical_or(pred, gt).sum())
    if union == 0:
        return 0.0
    return float(inter) / float(union)


def _build_pred_masks_from_assignments(
    *,
    assignments: Mapping[str, list[float]],
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
        for local_idx, patch_idx in enumerate(support_indices):
            if float(scores[local_idx]) < float(threshold):
                continue
            ys, xs = patch_slices[patch_idx]
            pred_mask[ys, xs] = True
        out[key] = pred_mask
    return out


def compute_pp116_oracle_obj_runtime_evaluator_output(
    *,
    bundle: FormalInputsBundle,
    assignments: Mapping[str, list[float]],
    sibling_assignment_keys: list[str],
    assignment_threshold: float = 0.5,
) -> dict[str, Any]:
    payload = bundle.formal_evaluator_output or {}
    runtime_payload = payload.get("runtime_payload", {}) if isinstance(payload, Mapping) else {}
    part_mask = np.array(Image.open(bundle.sem_seg_file_name))
    obj_mask = np.array(Image.open(bundle.obj_sem_seg_file_name))
    if part_mask.shape != obj_mask.shape:
        raise ValueError("part/object mask shape mismatch in runtime evaluator")

    support_region = obj_mask == int(bundle.category_id)
    if not bool(np.any(support_region)):
        raise ValueError("oracle-object support region is empty for category_id")

    patch_grid = runtime_payload.get("patch_grid_shape", bundle.patch_grid_shape)
    if not isinstance(patch_grid, list) or len(patch_grid) != 2:
        raise ValueError("runtime evaluator requires patch_grid_shape=[H,W]")
    patch_grid_shape = (int(patch_grid[0]), int(patch_grid[1]))

    support_patch_flags = list(bool(v) for v in bundle.support_mask)
    pred_masks = _build_pred_masks_from_assignments(
        assignments=assignments,
        sibling_assignment_keys=sibling_assignment_keys,
        support_patch_flags=support_patch_flags,
        image_shape=(int(part_mask.shape[0]), int(part_mask.shape[1])),
        patch_grid_shape=patch_grid_shape,
        threshold=float(assignment_threshold),
    )
    # Strict official mapping: sibling_part_id_map injection is forbidden.
    if isinstance(runtime_payload, Mapping) and "sibling_part_id_map" in runtime_payload:
        raise ValueError("sibling_part_id_map injection is forbidden under strict OV-PARTS alignment")
    explicit_map = {}

    object_class_key = bundle.object_class_key or get_pp116_object_key_from_category_id(
        int(bundle.category_id)
    )
    iou_by_part_class: dict[tuple[str, str], float] = {}
    for part_key, assign_key in zip(bundle.sibling_part_keys, sibling_assignment_keys):
        from open_vocabulary_segmentation.stage2_protocol.ovparts_pp116_official_taxonomy import get_official_part_class_id
        part_id = get_official_part_class_id(object_class_key, part_key)
        gt_mask = np.logical_and(support_region, part_mask == int(part_id))
        pred_mask = np.logical_and(support_region, pred_masks[assign_key])
        iou_by_part_class[(object_class_key, part_key)] = _binary_iou(pred_mask, gt_mask)

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
            "assignment_threshold": float(assignment_threshold),
            "patch_grid_shape": [int(patch_grid_shape[0]), int(patch_grid_shape[1])],
            "sibling_part_id_map": {},
        },
    }
