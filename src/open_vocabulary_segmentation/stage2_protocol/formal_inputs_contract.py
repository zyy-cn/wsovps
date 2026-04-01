from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping

import torch


@dataclass(frozen=True, slots=True)
class FormalInputsBundle:
    file_name: str
    sem_seg_file_name: str
    obj_sem_seg_file_name: str
    category_id: int
    sibling_part_keys: list[str]
    object_text: Any
    part_texts: Any
    patch_features: Any
    support_mask: Any
    formal_evaluator_output: dict[str, Any] | None = None
    evaluator_output_mode: str = "runtime"
    object_class_key: str | None = None
    split_tag: str | None = None
    trace_key: str | None = None
    feature_source: str | None = None
    support_source: str | None = None
    evaluator_source: str | None = None
    run_id: str | None = None
    protocol_name: str | None = None
    image_shape: list[int] | None = None
    patch_grid_shape: list[int] | None = None
    feature_dtype: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _as_float_vector(name: str, values: Any) -> list[float]:
    if torch.is_tensor(values):
        if values.numel() == 0:
            raise ValueError(f"{name} must be a non-empty tensor")
        return values
    if not isinstance(values, list) or not values:
        raise ValueError(f"{name} must be a non-empty list")
    return [float(v) for v in values]


def _as_float_matrix(name: str, values: Any) -> list[list[float]]:
    if torch.is_tensor(values):
        if values.numel() == 0:
            raise ValueError(f"{name} must be a non-empty tensor")
        return values
    if not isinstance(values, list) or not values:
        raise ValueError(f"{name} must be a non-empty list")
    first = values[0]
    if isinstance(first, (int, float)):
        return [[float(v) for v in values]]
    return [[float(v) for v in row] for row in values]


def _as_bool_vector(name: str, values: Any) -> list[bool]:
    if torch.is_tensor(values):
        if values.numel() == 0:
            raise ValueError(f"{name} must be a non-empty tensor")
        return values
    if not isinstance(values, list) or not values:
        raise ValueError(f"{name} must be a non-empty list")
    return [bool(v) for v in values]


def validate_formal_inputs_bundle(bundle: FormalInputsBundle) -> None:
    required_sample_fields = {
        "file_name": bundle.file_name,
        "sem_seg_file_name": bundle.sem_seg_file_name,
        "obj_sem_seg_file_name": bundle.obj_sem_seg_file_name,
    }
    for name, value in required_sample_fields.items():
        if not str(value).strip():
            raise ValueError(f"formal bundle official sample field is required: {name}")
    if int(bundle.category_id) < 0:
        raise ValueError("formal bundle category_id must be non-negative")

    if bundle.evaluator_output_mode not in {"injected", "runtime"}:
        raise ValueError("formal bundle evaluator_output_mode must be one of {'injected','runtime'}")

    if not bundle.sibling_part_keys:
        raise ValueError("formal bundle requires non-empty sibling_part_keys")
    if torch.is_tensor(bundle.part_texts):
        if bundle.part_texts.ndim != 2 or bundle.part_texts.shape[0] <= 0:
            raise ValueError("part_texts tensor must be 2D and non-empty")
        part_text_count = int(bundle.part_texts.shape[0])
    else:
        if len(bundle.part_texts) <= 0:
            raise ValueError("part_texts must be non-empty")
        part_text_count = len(bundle.part_texts)
    if part_text_count != len(bundle.sibling_part_keys):
        raise ValueError("part_texts row count must match sibling_part_keys length")

    if torch.is_tensor(bundle.patch_features):
        if bundle.patch_features.ndim != 2 or bundle.patch_features.shape[0] <= 0:
            raise ValueError("patch_features tensor must be 2D and non-empty")
        patch_count = int(bundle.patch_features.shape[0])
    else:
        if len(bundle.patch_features) <= 0:
            raise ValueError("patch_features must be non-empty")
        patch_count = len(bundle.patch_features)
    if torch.is_tensor(bundle.support_mask):
        if bundle.support_mask.ndim != 1 or bundle.support_mask.shape[0] <= 0:
            raise ValueError("support_mask tensor must be 1D and non-empty")
        if bundle.support_mask.dtype != torch.bool:
            raise ValueError("support_mask tensor must have dtype=bool")
        support_count = int(bundle.support_mask.shape[0])
    else:
        if len(bundle.support_mask) <= 0:
            raise ValueError("support_mask must be non-empty")
        support_count = len(bundle.support_mask)
    if patch_count != support_count:
        raise ValueError("support_mask length must match patch_features row count")

    payload = bundle.formal_evaluator_output or {}
    iou_payload = payload.get("iou_by_part_class")
    if iou_payload is None:
        iou_payload = {}
    if not isinstance(iou_payload, Mapping):
        raise ValueError("formal_evaluator_output.iou_by_part_class must be a mapping when present")
    if bundle.evaluator_output_mode == "runtime" and len(iou_payload) > 0:
        raise ValueError(
            "formal bundle runtime mode forbids injected iou_by_part_class values"
        )
    if bundle.evaluator_output_mode == "injected" and len(iou_payload) == 0:
        raise ValueError(
            "formal bundle injected mode requires non-empty formal_evaluator_output.iou_by_part_class"
        )


def coerce_formal_inputs_bundle(payload: Mapping[str, Any]) -> FormalInputsBundle:
    object_text = payload.get("object_text")
    part_texts = payload.get("part_texts")
    patch_features = payload.get("patch_features")
    support_mask = payload.get("support_mask")
    bundle = FormalInputsBundle(
        file_name=str(payload.get("file_name", "")).strip(),
        sem_seg_file_name=str(payload.get("sem_seg_file_name", "")).strip(),
        obj_sem_seg_file_name=str(payload.get("obj_sem_seg_file_name", "")).strip(),
        category_id=int(payload.get("category_id", 0)),
        sibling_part_keys=[str(v).strip() for v in payload.get("sibling_part_keys", [])],
        evaluator_output_mode=str(payload.get("evaluator_output_mode", "runtime")).strip(),
        object_text=_as_float_vector("object_text", object_text),
        part_texts=_as_float_matrix("part_texts", part_texts),
        patch_features=_as_float_matrix("patch_features", patch_features),
        support_mask=_as_bool_vector("support_mask", support_mask),
        formal_evaluator_output=dict(payload.get("formal_evaluator_output", {}))
        if payload.get("formal_evaluator_output") is not None
        else {},
        object_class_key=str(payload.get("object_class_key", "")).strip() or None,
        split_tag=str(payload.get("split_tag", "")).strip() or None,
        trace_key=str(payload.get("trace_key", "")).strip() or None,
        feature_source=str(payload.get("feature_source", "")).strip() or None,
        support_source=str(payload.get("support_source", "")).strip() or None,
        evaluator_source=str(payload.get("evaluator_source", "")).strip() or None,
        run_id=payload.get("run_id"),
        protocol_name=payload.get("protocol_name"),
        image_shape=payload.get("image_shape"),
        patch_grid_shape=payload.get("patch_grid_shape"),
        feature_dtype=payload.get("feature_dtype"),
    )
    validate_formal_inputs_bundle(bundle)
    return bundle
