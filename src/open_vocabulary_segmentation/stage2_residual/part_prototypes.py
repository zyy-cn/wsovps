from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable

import torch

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


def _tensor_l2_normalize(vec: torch.Tensor, eps: float = 1e-8) -> torch.Tensor:
    return vec / vec.norm(dim=-1, keepdim=True).clamp_min(eps)


def _support_pool_object_prototype(
    *,
    patch_features: list[list[float]] | torch.Tensor,
    support_mask: list[bool] | torch.Tensor,
) -> tuple[list[float] | torch.Tensor, int]:
    if torch.is_tensor(patch_features) or torch.is_tensor(support_mask):
        feats = patch_features if torch.is_tensor(patch_features) else torch.as_tensor(patch_features)
        mask = support_mask if torch.is_tensor(support_mask) else torch.as_tensor(support_mask, dtype=torch.bool, device=feats.device)
        if feats.ndim != 2 or mask.ndim != 1:
            raise ValueError("patch_features and support_mask tensor inputs must be 2D/1D")
        if feats.shape[0] != mask.shape[0]:
            raise ValueError("patch_features and support_mask length mismatch")
        support_feats = feats[mask]
        if support_feats.numel() == 0:
            raise ValueError("support_mask selected zero patch features")
        return _tensor_l2_normalize(support_feats.mean(dim=0)), int(support_feats.shape[0])
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
    patch_features: list[list[float]] | torch.Tensor,
    support_mask: list[bool] | torch.Tensor,
    residual_directions: Iterable[list[float]] | torch.Tensor | None,
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
    if torch.is_tensor(residual_directions):
        directions_tensor = residual_directions
        if directions_tensor.ndim != 2:
            raise ValueError("residual_directions tensor must be 2D")
        part_prototypes = []
        for direction in directions_tensor:
            if len(object_prototype) != int(direction.shape[0]):
                raise ValueError("object_prototype and residual_direction must have identical dimensions")
            raw_part = object_prototype + alpha_value * direction
            part_prototypes.append(_tensor_l2_normalize(raw_part))
        return PartPrototypeSpec(
            mode=mode,
            object_prototype=object_prototype,
            residual_directions=directions_tensor,
            alpha_value=alpha_value,
            part_prototypes=torch.stack(part_prototypes, dim=0),
            support_scope=support_scope,
            support_count=support_count,
        )
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
