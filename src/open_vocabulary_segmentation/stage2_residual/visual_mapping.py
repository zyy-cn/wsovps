from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable

from .modes import ResidualMode


PROTOCOL_ALIGNED_BUILDER_ENTRYPOINT = (
    "open_vocabulary_segmentation.segmentation.evaluation.stage2_protocol_builder"
    ".resolve_stage2_protocol_bindings"
)


@dataclass(frozen=True, slots=True)
class ResidualVisualMappingSpec:
    mode: ResidualMode
    phi_mapping_enabled: bool
    protocol_builder_entrypoint: str
    alpha_mode: str
    alpha_value: float
    notes: str = ""

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["mode"] = self.mode.value
        return payload


def _l2_normalize(vec: list[float], eps: float = 1e-8) -> list[float]:
    norm = sum(v * v for v in vec) ** 0.5
    denom = max(norm, eps)
    return [v / denom for v in vec]


def map_text_residual_to_visual(
    *,
    object_text: list[float],
    residual_texts: Iterable[list[float]],
    formal_mode: bool,
) -> list[list[float]]:
    """Deterministic object-conditioned Phi_o adapter for repair-round formal mode.

    This is intentionally lightweight and deterministic, but materially non-identity:
    each channel mixes residual and neighboring channels with object-conditioned weights.
    """
    out: list[list[float]] = []
    dim = len(object_text)
    if dim == 0:
        raise ValueError("object_text must be non-empty")
    obj = _l2_normalize(object_text)
    for residual in residual_texts:
        if len(residual) != dim:
            raise ValueError("residual_text dimension mismatch for Phi_o mapping")
        if not formal_mode:
            out.append(_l2_normalize(list(residual)))
            continue
        mapped: list[float] = []
        for i in range(dim):
            j = (i + 1) % dim
            k = (i + 2) % dim
            # Non-identity object-conditioned mixing.
            value = (
                0.70 * residual[i]
                + 0.20 * obj[i] * residual[j]
                - 0.10 * obj[j] * residual[k]
            )
            mapped.append(value)
        out.append(_l2_normalize(mapped))
    return out


def build_visual_mapping_spec(
    mode: ResidualMode,
    *,
    alpha_value: float = 1.0,
    protocol_builder_entrypoint: str = PROTOCOL_ALIGNED_BUILDER_ENTRYPOINT,
) -> ResidualVisualMappingSpec:
    if mode == ResidualMode.B2_RESIDUAL_ONLY:
        return ResidualVisualMappingSpec(
            mode=mode,
            phi_mapping_enabled=True,
            protocol_builder_entrypoint=protocol_builder_entrypoint,
            alpha_mode="fixed",
            alpha_value=alpha_value,
            notes="B2 residual-only path maps textual residual via protocol-aligned Phi_o route.",
        )
    return ResidualVisualMappingSpec(
        mode=mode,
        phi_mapping_enabled=False,
        protocol_builder_entrypoint=protocol_builder_entrypoint,
        alpha_mode="fixed",
        alpha_value=alpha_value,
        notes="B0/B1 disable residual visual mapping in E4 round-1.",
    )
