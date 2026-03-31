from __future__ import annotations

from .ade234_binding import ADE234_PROTOCOL_ID, build_ade234_protocol_descriptor
from .contracts import EvaluatorBindingSpec, Stage2ProtocolDescriptor
from .pp116_binding import PP116_PROTOCOL_ID, build_pp116_protocol_descriptor

_BUILDERS = {
    PP116_PROTOCOL_ID: build_pp116_protocol_descriptor,
    "pp116": build_pp116_protocol_descriptor,
    ADE234_PROTOCOL_ID: build_ade234_protocol_descriptor,
    "ade234": build_ade234_protocol_descriptor,
}


def build_stage2_protocol(protocol_name: str) -> Stage2ProtocolDescriptor:
    try:
        descriptor = _BUILDERS[protocol_name]()
    except KeyError as exc:
        raise ValueError(f"unknown Stage-2 protocol: {protocol_name}") from exc
    descriptor.validate()
    return descriptor


def resolve_stage2_evaluator_binding(
    protocol: str | Stage2ProtocolDescriptor,
) -> EvaluatorBindingSpec:
    descriptor = build_stage2_protocol(protocol) if isinstance(protocol, str) else protocol
    descriptor.validate()
    return descriptor.evaluator_binding
