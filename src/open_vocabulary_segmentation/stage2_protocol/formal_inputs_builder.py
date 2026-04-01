from __future__ import annotations

from typing import Any, Mapping

import torch

from .formal_inputs_contract import FormalInputsBundle, validate_formal_inputs_bundle
from .official_pp116_reference import canonical_sibling_part_keys


def _reorder_part_text_rows(
    *,
    input_part_keys: list[str],
    canonical_part_keys: list[str],
    part_texts: Any,
) -> Any:
    key_to_idx = {key: idx for idx, key in enumerate(input_part_keys)}
    missing = [key for key in canonical_part_keys if key not in key_to_idx]
    if missing:
        raise ValueError(f"missing sibling_part_keys required by canonical order: {missing}")
    if torch.is_tensor(part_texts):
        indices = torch.tensor([key_to_idx[key] for key in canonical_part_keys], device=part_texts.device)
        return part_texts.index_select(0, indices)
    return [part_texts[key_to_idx[key]] for key in canonical_part_keys]


def build_formal_inputs_bundle(
    *,
    file_name: str,
    sem_seg_file_name: str,
    obj_sem_seg_file_name: str,
    category_id: int,
    sibling_part_keys: list[str],
    object_text: Any,
    part_texts: Any,
    patch_features: Any,
    support_mask: Any,
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
        part_texts=part_texts,
    )
    if torch.is_tensor(object_text) and not object_text.is_cuda:
        raise AssertionError("formal bundle object_text tensor must be on CUDA")
    if torch.is_tensor(normalized_part_texts) and not normalized_part_texts.is_cuda:
        raise AssertionError("formal bundle part_texts tensor must be on CUDA")
    if torch.is_tensor(patch_features) and not patch_features.is_cuda:
        raise AssertionError("formal bundle patch_features tensor must be on CUDA")
    if torch.is_tensor(support_mask):
        if support_mask.dtype != torch.bool:
            raise AssertionError("formal bundle support_mask tensor must have dtype=bool")
        if not support_mask.is_cuda:
            raise AssertionError("formal bundle support_mask tensor must be on CUDA")
    bundle = FormalInputsBundle(
        file_name=str(file_name),
        sem_seg_file_name=str(sem_seg_file_name),
        obj_sem_seg_file_name=str(obj_sem_seg_file_name),
        category_id=int(category_id),
        sibling_part_keys=canonical_keys,
        object_text=object_text,
        part_texts=normalized_part_texts,
        patch_features=patch_features,
        support_mask=support_mask,
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
