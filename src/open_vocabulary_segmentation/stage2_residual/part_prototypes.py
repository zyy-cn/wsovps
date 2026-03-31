from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable

from .modes import ResidualMode


@dataclass(frozen=True, slots=True)
class PartPrototypeSpec:
    mode: ResidualMode
    object_prototype: list[float]
    residual_directions: list[list[float]] | None
    alpha_value: float
    part_prototypes: list[list[float]] | None
    support_scope: str
    support_count: int

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["mode"] = self.mode.value
        return payload


def _l2_normalize(vec: list[float], eps: float = 1e-8) -> list[float]:
    norm = sum(v * v for v in vec) ** 0.5
    denom = max(norm, eps)
    return [v / denom for v in vec]


def _support_pool_object_prototype(
    *,
    patch_features: list[list[float]],
    support_mask: list[bool],
) -> tuple[list[float], int]:
    if len(patch_features) != len(support_mask):
        raise ValueError("patch_features and support_mask length mismatch")
    support_feats = [feat for feat, keep in zip(patch_features, support_mask) if keep]
    if not support_feats:
        raise ValueError("support_mask selected zero patch features")
    dim = len(support_feats[0])
    accum = [0.0] * dim
    w = 1.0 / len(support_feats)
    for feat in support_feats:
        if len(feat) != dim:
            raise ValueError("patch_features channel dimension mismatch")
        for i, val in enumerate(feat):
            accum[i] += w * val
    return _l2_normalize(accum), len(support_feats)


def build_part_prototype(
    mode: ResidualMode,
    *,
    patch_features: list[list[float]],
    support_mask: list[bool],
    residual_directions: Iterable[list[float]] | None,
    alpha_value: float = 1.0,
    support_scope: str = "omega_o",
) -> PartPrototypeSpec:
    object_prototype, support_count = _support_pool_object_prototype(
        patch_features=patch_features,
        support_mask=support_mask,
    )
    if mode != ResidualMode.B2_RESIDUAL_ONLY:
        return PartPrototypeSpec(
            mode=mode,
            object_prototype=object_prototype,
            residual_directions=None,
            alpha_value=alpha_value,
            part_prototypes=None,
            support_scope=support_scope,
            support_count=support_count,
        )
    if residual_directions is None:
        raise ValueError("B2 residual-only prototype construction requires residual_directions")
    directions = [list(d) for d in residual_directions]
    part_prototypes: list[list[float]] = []
    for direction in directions:
        if len(object_prototype) != len(direction):
            raise ValueError("object_prototype and residual_direction must have identical dimensions")
        raw_part = [o + alpha_value * d for o, d in zip(object_prototype, direction)]
        part_prototypes.append(_l2_normalize(raw_part))
    return PartPrototypeSpec(
        mode=mode,
        object_prototype=object_prototype,
        residual_directions=directions,
        alpha_value=alpha_value,
        part_prototypes=part_prototypes,
        support_scope=support_scope,
        support_count=support_count,
    )
