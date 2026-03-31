from __future__ import annotations

from .contracts import EvaluatorBindingSpec, Stage2ProtocolDescriptor
from .object_support import build_object_support_spec

PP116_PROTOCOL_ID = "pp116_oracle_obj"
PP116_FORMAL_INPUTS_BUNDLE_CONTRACT = (
    "open_vocabulary_segmentation.stage2_protocol.formal_inputs_builder:build_formal_inputs_bundle"
)


def build_pp116_protocol_descriptor() -> Stage2ProtocolDescriptor:
    support = build_object_support_spec(
        dataset_family="pp116",
        support_granularity="class_union",
        object_anchor_id="dataset-defined",
        support_mask_semantics="union-style object-conditioned support",
        valid_part_scope="ov_parts_pp116_oracle_obj_merged_part_scope_v1",
        taxonomy_scope="ov_parts_pp116_merged_116_v1",
        evaluator_namespace="pp116_oracle_obj_official",
        split_id="ov_parts_pp116_gzsp_train_val_v1",
        notes="Class-union Oracle-Obj support semantics.",
    )
    evaluator = EvaluatorBindingSpec(
        dataset_family="pp116",
        support_mode="oracle_obj",
        support_granularity="class_union",
        split_id="ov_parts_pp116_gzsp_train_val_v1",
        taxonomy_scope="ov_parts_pp116_merged_116_v1",
        evaluator_name="pp116_oracle_obj_official_gzsp_evaluator",
        builder_entrypoint="open_vocabulary_segmentation.segmentation.evaluation.stage2_protocol_builder.resolve_stage2_protocol_bindings",
        notes=(
            "Source-locked offline PP116 evaluator binding. "
            "Formal mode requires canonical FormalInputsBundle payload."
        ),
    )
    descriptor = Stage2ProtocolDescriptor(
        protocol_id=PP116_PROTOCOL_ID,
        dataset_family="pp116",
        support_spec=support,
        evaluator_binding=evaluator,
        config_namespace="src/open_vocabulary_segmentation/configs/pp116",
        dataset_entrypoint="open_vocabulary_segmentation.segmentation.datasets.pp116_oracle_obj:get_pp116_oracle_obj_protocol_descriptor",
        notes=(
            "Protocol landing scaffold for PP116 Oracle-Obj. "
            f"formal_inputs_bundle={PP116_FORMAL_INPUTS_BUNDLE_CONTRACT}"
        ),
    )
    descriptor.validate()
    return descriptor
