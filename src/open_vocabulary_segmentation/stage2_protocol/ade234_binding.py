from __future__ import annotations

from .contracts import EvaluatorBindingSpec, Stage2ProtocolDescriptor
from .object_support import build_object_support_spec

ADE234_PROTOCOL_ID = "ade234_instance_aware"


def build_ade234_protocol_descriptor() -> Stage2ProtocolDescriptor:
    support = build_object_support_spec(
        dataset_family="ade234",
        support_granularity="instance_aware",
        object_anchor_id="dataset-defined-instance-anchor",
        support_mask_semantics="instance-aware support",
        valid_part_scope="ade234-protocol-defined",
        taxonomy_scope="ade234-protocol-defined",
        evaluator_namespace="ade234",
        split_id="ade234-protocol-split",
        notes="Not union-style support.",
    )
    evaluator = EvaluatorBindingSpec(
        dataset_family="ade234",
        support_mode="oracle_obj",
        support_granularity="instance_aware",
        split_id="ade234-protocol-split",
        taxonomy_scope="ade234-protocol-defined",
        evaluator_name="ade234_protocol_evaluator",
        builder_entrypoint="open_vocabulary_segmentation.segmentation.evaluation.stage2_protocol_builder.resolve_stage2_protocol_bindings",
        notes="Explicit ADE234 routing.",
    )
    descriptor = Stage2ProtocolDescriptor(
        protocol_id=ADE234_PROTOCOL_ID,
        dataset_family="ade234",
        support_spec=support,
        evaluator_binding=evaluator,
        config_namespace="src/open_vocabulary_segmentation/configs/ade234_parts",
        dataset_entrypoint="open_vocabulary_segmentation.segmentation.datasets.ade234_instance_aware:get_ade234_instance_aware_protocol_descriptor",
        notes="Protocol landing scaffold for ADE234 instance-aware Oracle-Obj.",
    )
    descriptor.validate()
    return descriptor
