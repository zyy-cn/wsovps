from __future__ import annotations

from .contracts import ObjectSupportSpec


def describe_object_support(spec: ObjectSupportSpec) -> dict[str, object]:
    spec.validate()
    return spec.as_dict()


def build_object_support_spec(
    *,
    dataset_family: str,
    support_granularity: str,
    object_anchor_id: str,
    support_mask_semantics: str,
    valid_part_scope: str,
    taxonomy_scope: str,
    evaluator_namespace: str,
    split_id: str,
    notes: str = "",
) -> ObjectSupportSpec:
    spec = ObjectSupportSpec(
        dataset_family=dataset_family,  # type: ignore[arg-type]
        support_mode="oracle_obj",
        support_granularity=support_granularity,  # type: ignore[arg-type]
        object_anchor_id=object_anchor_id,
        support_mask_semantics=support_mask_semantics,
        valid_part_scope=valid_part_scope,
        taxonomy_scope=taxonomy_scope,
        evaluator_namespace=evaluator_namespace,
        split_id=split_id,
        notes=notes,
    )
    spec.validate()
    return spec
