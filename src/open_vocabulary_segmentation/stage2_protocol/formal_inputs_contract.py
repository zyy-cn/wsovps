from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class FormalInputsBundle:
    file_name: str
    sem_seg_file_name: str
    obj_sem_seg_file_name: str
    category_id: int
    sibling_part_keys: list[str]
    object_text: list[float]
    part_texts: list[list[float]]
    patch_features: list[list[float]]
    support_mask: list[bool]
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
    if not isinstance(values, list) or not values:
        raise ValueError(f"{name} must be a non-empty list")
    return [float(v) for v in values]


def _as_float_matrix(name: str, values: Any) -> list[list[float]]:
    if not isinstance(values, list) or not values:
        raise ValueError(f"{name} must be a non-empty list")
    first = values[0]
    if isinstance(first, (int, float)):
        return [[float(v) for v in values]]
    return [[float(v) for v in row] for row in values]


def _as_bool_vector(name: str, values: Any) -> list[bool]:
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
    if int(bundle.category_id) <= 0:
        raise ValueError("formal bundle category_id must be positive")

    if bundle.evaluator_output_mode not in {"injected", "runtime"}:
        raise ValueError("formal bundle evaluator_output_mode must be one of {'injected','runtime'}")

    if not bundle.sibling_part_keys:
        raise ValueError("formal bundle requires non-empty sibling_part_keys")
    if len(bundle.part_texts) != len(bundle.sibling_part_keys):
        raise ValueError("part_texts row count must match sibling_part_keys length")
    if len(bundle.patch_features) != len(bundle.support_mask):
        raise ValueError("support_mask length must match patch_features row count")

    payload = bundle.formal_evaluator_output or {}
    iou_payload = payload.get("iou_by_part_class")
    if iou_payload is None:
        iou_payload = {}
    if not isinstance(iou_payload, Mapping):
        raise ValueError(
            "formal bundle requires mapping field: formal_evaluator_output.iou_by_part_class"
        )
    if bundle.evaluator_output_mode == "runtime" and len(iou_payload) > 0:
        raise ValueError(
            "formal bundle runtime mode forbids injected iou_by_part_class values"
        )
    if bundle.evaluator_output_mode == "injected" and len(iou_payload) == 0:
        raise ValueError(
            "formal bundle injected mode requires non-empty formal_evaluator_output.iou_by_part_class"
        )


def coerce_formal_inputs_bundle(payload: Mapping[str, Any]) -> FormalInputsBundle:
    bundle = FormalInputsBundle(
        file_name=str(payload.get("file_name", "")).strip(),
        sem_seg_file_name=str(payload.get("sem_seg_file_name", "")).strip(),
        obj_sem_seg_file_name=str(payload.get("obj_sem_seg_file_name", "")).strip(),
        category_id=int(payload.get("category_id", 0)),
        sibling_part_keys=[str(v).strip() for v in payload.get("sibling_part_keys", [])],
        evaluator_output_mode=str(payload.get("evaluator_output_mode", "runtime")).strip(),
        object_text=_as_float_vector("object_text", payload.get("object_text")),
        part_texts=_as_float_matrix("part_texts", payload.get("part_texts")),
        patch_features=_as_float_matrix("patch_features", payload.get("patch_features")),
        support_mask=_as_bool_vector("support_mask", payload.get("support_mask")),
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
