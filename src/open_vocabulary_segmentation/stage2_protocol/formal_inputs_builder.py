from __future__ import annotations

from typing import Any, Mapping

from .formal_inputs_contract import FormalInputsBundle, validate_formal_inputs_bundle
from .official_pp116_reference import canonical_sibling_part_keys


def _reorder_part_text_rows(
    *,
    input_part_keys: list[str],
    canonical_part_keys: list[str],
    part_texts: list[list[float]],
) -> list[list[float]]:
    key_to_idx = {key: idx for idx, key in enumerate(input_part_keys)}
    missing = [key for key in canonical_part_keys if key not in key_to_idx]
    if missing:
        raise ValueError(f"missing sibling_part_keys required by canonical order: {missing}")
    return [part_texts[key_to_idx[key]] for key in canonical_part_keys]


def build_formal_inputs_bundle(
    *,
    file_name: str,
    sem_seg_file_name: str,
    obj_sem_seg_file_name: str,
    category_id: int,
    sibling_part_keys: list[str],
    object_text: list[float],
    part_texts: list[list[float]],
    patch_features: list[list[float]],
    support_mask: list[bool],
    formal_evaluator_output: Mapping[str, Any] | None = None,
    evaluator_output_mode: str = "runtime",
    object_class_key: str | None = None,
    split_tag: str | None = None,
    trace_key: str | None = None,
    feature_source: str | None = None,
    support_source: str | None = None,
    evaluator_source: str | None = None,
    run_id: str | None = None,
    protocol_name: str | None = None,
    image_shape: list[int] | None = None,
    patch_grid_shape: list[int] | None = None,
    feature_dtype: str | None = None,
) -> FormalInputsBundle:
    canonical_keys = canonical_sibling_part_keys(
        object_class_key=(object_class_key or str(category_id)),
        sibling_part_keys=sibling_part_keys,
    )
    normalized_part_texts = _reorder_part_text_rows(
        input_part_keys=[str(k).strip() for k in sibling_part_keys],
        canonical_part_keys=canonical_keys,
        part_texts=[[float(v) for v in row] for row in part_texts],
    )
    bundle = FormalInputsBundle(
        file_name=str(file_name),
        sem_seg_file_name=str(sem_seg_file_name),
        obj_sem_seg_file_name=str(obj_sem_seg_file_name),
        category_id=int(category_id),
        sibling_part_keys=canonical_keys,
        object_text=[float(v) for v in object_text],
        part_texts=normalized_part_texts,
        patch_features=[[float(v) for v in row] for row in patch_features],
        support_mask=[bool(v) for v in support_mask],
        formal_evaluator_output=dict(formal_evaluator_output or {}),
        evaluator_output_mode=str(evaluator_output_mode),
        object_class_key=str(object_class_key).strip() if object_class_key else None,
        split_tag=str(split_tag).strip() if split_tag else None,
        trace_key=str(trace_key).strip() if trace_key else None,
        feature_source=str(feature_source).strip() if feature_source else None,
        support_source=str(support_source).strip() if support_source else None,
        evaluator_source=str(evaluator_source).strip() if evaluator_source else None,
        run_id=run_id,
        protocol_name=protocol_name,
        image_shape=image_shape,
        patch_grid_shape=patch_grid_shape,
        feature_dtype=feature_dtype,
    )
    validate_formal_inputs_bundle(bundle)
    return bundle

