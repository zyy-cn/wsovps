from __future__ import annotations

from open_vocabulary_segmentation.stage2_protocol.ade234_binding import (
    ADE234_PROTOCOL_ID,
    build_ade234_protocol_descriptor,
)


def get_ade234_instance_aware_protocol_descriptor():
    """Return the Stage-2 descriptor for ADE234 instance-aware Oracle-Obj."""
    return build_ade234_protocol_descriptor()


def get_ade234_instance_aware_dataset_entrypoint() -> str:
    """Return the canonical dataset adapter entrypoint for protocol routing."""
    return f"{__name__}:get_ade234_instance_aware_protocol_descriptor"


def get_ade234_instance_aware_dataset_metadata() -> dict[str, str]:
    descriptor = build_ade234_protocol_descriptor()
    return {
        "protocol_id": ADE234_PROTOCOL_ID,
        "dataset_family": descriptor.dataset_family,
        "dataset_entrypoint": get_ade234_instance_aware_dataset_entrypoint(),
        "support_mode": descriptor.support_spec.support_mode,
        "support_granularity": descriptor.support_spec.support_granularity,
        "notes": descriptor.notes,
    }
