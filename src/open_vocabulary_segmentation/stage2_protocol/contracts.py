from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal

DatasetFamily = Literal["pp116", "ade234"]
SupportMode = Literal["oracle_obj"]
SupportGranularity = Literal["class_union", "instance_aware"]


@dataclass(frozen=True, slots=True)
class ObjectSupportSpec:
    dataset_family: DatasetFamily
    support_mode: SupportMode
    support_granularity: SupportGranularity
    object_anchor_id: str
    support_mask_semantics: str
    valid_part_scope: str
    taxonomy_scope: str
    evaluator_namespace: str
    split_id: str
    notes: str = ""

    def validate(self) -> None:
        if self.support_mode != "oracle_obj":
            raise ValueError(f"unsupported support_mode: {self.support_mode}")
        if self.dataset_family not in {"pp116", "ade234"}:
            raise ValueError(f"unsupported dataset_family: {self.dataset_family}")
        if self.support_granularity not in {"class_union", "instance_aware"}:
            raise ValueError(f"unsupported support_granularity: {self.support_granularity}")

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class EvaluatorBindingSpec:
    dataset_family: DatasetFamily
    support_mode: SupportMode
    support_granularity: SupportGranularity
    split_id: str
    taxonomy_scope: str
    evaluator_name: str
    builder_entrypoint: str
    notes: str = ""

    def validate(self) -> None:
        if self.support_mode != "oracle_obj":
            raise ValueError(f"unsupported support_mode: {self.support_mode}")
        if self.dataset_family not in {"pp116", "ade234"}:
            raise ValueError(f"unsupported dataset_family: {self.dataset_family}")
        if self.support_granularity not in {"class_union", "instance_aware"}:
            raise ValueError(f"unsupported support_granularity: {self.support_granularity}")

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class Stage2ProtocolDescriptor:
    protocol_id: str
    dataset_family: DatasetFamily
    support_spec: ObjectSupportSpec
    evaluator_binding: EvaluatorBindingSpec
    config_namespace: str
    dataset_entrypoint: str
    notes: str = ""

    def validate(self) -> None:
        self.support_spec.validate()
        self.evaluator_binding.validate()
        if self.support_spec.dataset_family != self.dataset_family:
            raise ValueError("support_spec.dataset_family does not match descriptor dataset_family")
        if self.evaluator_binding.dataset_family != self.dataset_family:
            raise ValueError("evaluator_binding.dataset_family does not match descriptor dataset_family")
        if self.support_spec.support_mode != self.evaluator_binding.support_mode:
            raise ValueError("support_mode mismatch between support and evaluator bindings")
        if self.support_spec.support_granularity != self.evaluator_binding.support_granularity:
            raise ValueError("support_granularity mismatch between support and evaluator bindings")
        if self.support_spec.split_id != self.evaluator_binding.split_id:
            raise ValueError("split_id mismatch between support and evaluator bindings")
        if self.support_spec.taxonomy_scope != self.evaluator_binding.taxonomy_scope:
            raise ValueError("taxonomy_scope mismatch between support and evaluator bindings")

    def as_dict(self) -> dict[str, Any]:
        return {
            "protocol_id": self.protocol_id,
            "dataset_family": self.dataset_family,
            "support_spec": self.support_spec.as_dict(),
            "evaluator_binding": self.evaluator_binding.as_dict(),
            "config_namespace": self.config_namespace,
            "dataset_entrypoint": self.dataset_entrypoint,
            "notes": self.notes,
        }
