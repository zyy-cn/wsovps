from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable

import torch

from .modes import ResidualMode


@dataclass(frozen=True, slots=True)
class ResidualTextSpec:
    mode: ResidualMode
    object_text: list[float]
    part_texts: list[list[float]]
    object_conditioned_part_texts: list[list[float]]
    residual_texts: list[list[float]] | None
    sibling_part_count: int
    residual_enabled: bool

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["mode"] = self.mode.value
        return payload


def _is_tensor(value: object) -> bool:
    return torch.is_tensor(value)


def _dot(lhs: list[float], rhs: list[float]) -> float:
    return sum(a * b for a, b in zip(lhs, rhs))


def _norm_squared(vec: list[float]) -> float:
    return _dot(vec, vec)


def _sub(lhs: list[float], rhs: list[float]) -> list[float]:
    return [a - b for a, b in zip(lhs, rhs)]


def _l2_normalize(vec: list[float], eps: float = 1e-8) -> list[float]:
    norm = sum(v * v for v in vec) ** 0.5
    denom = max(norm, eps)
    return [v / denom for v in vec]


def _tensor_l2_normalize(vec: torch.Tensor, eps: float = 1e-8) -> torch.Tensor:
    return vec / vec.norm(dim=-1, keepdim=True).clamp_min(eps)


def build_object_conditioned_part_texts(
    object_text: list[float] | torch.Tensor,
    part_texts: list[list[float]] | torch.Tensor,
) -> list[list[float]] | torch.Tensor:
    if _is_tensor(object_text) or _is_tensor(part_texts):
        obj = object_text if torch.is_tensor(object_text) else torch.as_tensor(object_text)
        parts = part_texts if torch.is_tensor(part_texts) else torch.as_tensor(part_texts, dtype=obj.dtype, device=obj.device)
        if parts.ndim == 1:
            parts = parts.unsqueeze(0)
        if obj.ndim != 1 or parts.ndim != 2:
            raise ValueError("object_text and part_texts tensor inputs must be 1D and 2D")
        if obj.shape[-1] != parts.shape[-1]:
            raise ValueError("object_text and part_text must have identical dimensions")
        return obj.unsqueeze(0) + parts
    out: list[list[float]] = []
    for part_text in part_texts:
        if len(object_text) != len(part_text):
            raise ValueError("object_text and part_text must have identical dimensions")
        out.append([o + p for o, p in zip(object_text, part_text)])
    return out


def build_object_conditioned_part_text(
    object_text: list[float],
    part_text: list[float],
) -> list[float]:
    """Legacy single-part wrapper kept for backward-compatible imports."""
    return build_object_conditioned_part_texts(object_text, [part_text])[0]


def orthogonal_residual_texts(
    object_conditioned_part_texts: list[list[float]] | torch.Tensor,
    object_text: list[float] | torch.Tensor,
    eps: float = 1e-8,
) -> list[list[float]] | torch.Tensor:
    if _is_tensor(object_conditioned_part_texts) or _is_tensor(object_text):
        obj = object_text if torch.is_tensor(object_text) else torch.as_tensor(object_text, dtype=torch.float32)
        conditioned = (
            object_conditioned_part_texts
            if torch.is_tensor(object_conditioned_part_texts)
            else torch.as_tensor(object_conditioned_part_texts, dtype=obj.dtype, device=obj.device)
        )
        if conditioned.ndim == 1:
            conditioned = conditioned.unsqueeze(0)
        if obj.ndim != 1 or conditioned.ndim != 2:
            raise ValueError("residual text tensor inputs must be 1D/2D")
        denom = obj.pow(2).sum().clamp_min(eps)
        coeff = (conditioned * obj.unsqueeze(0)).sum(dim=-1, keepdim=True) / denom
        residuals = conditioned - coeff * obj.unsqueeze(0)
        return _tensor_l2_normalize(residuals, eps=eps)
    denom = max(_norm_squared(object_text), eps)
    residuals: list[list[float]] = []
    for object_conditioned_part_text in object_conditioned_part_texts:
        if len(object_conditioned_part_text) != len(object_text):
            raise ValueError("residual text inputs must have identical dimensions")
        coeff = _dot(object_conditioned_part_text, object_text) / denom
        projection = [coeff * o for o in object_text]
        residuals.append(_l2_normalize(_sub(object_conditioned_part_text, projection)))
    return residuals


def orthogonal_residual_text(
    object_conditioned_part_text: list[float],
    object_text: list[float],
    eps: float = 1e-8,
) -> list[float]:
    """Legacy single-part wrapper kept for backward-compatible imports."""
    return orthogonal_residual_texts([object_conditioned_part_text], object_text, eps=eps)[0]


def _coerce_part_texts(part_texts: Iterable[Iterable[float]] | Iterable[float]) -> list[list[float]]:
    raw = list(part_texts)
    if not raw:
        raise ValueError("part_texts must be non-empty")
    first = raw[0]
    if isinstance(first, (int, float)):
        return [list(float(v) for v in raw)]  # single-part fallback for legacy smoke paths
    return [list(float(v) for v in part) for part in raw]  # sibling set path


def build_text_branch(
    mode: ResidualMode,
    object_text: list[float] | torch.Tensor,
    part_texts: Iterable[Iterable[float]] | Iterable[float] | torch.Tensor,
) -> ResidualTextSpec:
    if _is_tensor(object_text) or _is_tensor(part_texts):
        object_text_tensor = object_text if torch.is_tensor(object_text) else torch.as_tensor(object_text)
        part_texts_tensor = part_texts if torch.is_tensor(part_texts) else torch.as_tensor(part_texts, dtype=object_text_tensor.dtype, device=object_text_tensor.device)
        if part_texts_tensor.ndim == 1:
            part_texts_tensor = part_texts_tensor.unsqueeze(0)
        object_text_norm = _tensor_l2_normalize(object_text_tensor.float())
        sibling_part_texts = _tensor_l2_normalize(part_texts_tensor.float())
        object_conditioned = build_object_conditioned_part_texts(object_text_norm, sibling_part_texts)
        if mode == ResidualMode.B2_RESIDUAL_ONLY:
            residuals = orthogonal_residual_texts(object_conditioned, object_text_norm)
            return ResidualTextSpec(
                mode=mode,
                object_text=object_text_norm,
                part_texts=sibling_part_texts,
                object_conditioned_part_texts=object_conditioned,
                residual_texts=residuals,
                sibling_part_count=int(sibling_part_texts.shape[0]),
                residual_enabled=True,
            )
        return ResidualTextSpec(
            mode=mode,
            object_text=object_text_norm,
            part_texts=sibling_part_texts,
            object_conditioned_part_texts=object_conditioned,
            residual_texts=None,
            sibling_part_count=int(sibling_part_texts.shape[0]),
            residual_enabled=False,
        )
    object_text_norm = _l2_normalize([float(v) for v in object_text])
    sibling_part_texts = [_l2_normalize(p) for p in _coerce_part_texts(part_texts)]
    object_conditioned = build_object_conditioned_part_texts(object_text_norm, sibling_part_texts)
    if mode == ResidualMode.B2_RESIDUAL_ONLY:
        residuals = orthogonal_residual_texts(object_conditioned, object_text_norm)
        return ResidualTextSpec(
            mode=mode,
            object_text=object_text_norm,
            part_texts=sibling_part_texts,
            object_conditioned_part_texts=object_conditioned,
            residual_texts=residuals,
            sibling_part_count=len(sibling_part_texts),
            residual_enabled=True,
        )
    return ResidualTextSpec(
        mode=mode,
        object_text=object_text_norm,
        part_texts=sibling_part_texts,
        object_conditioned_part_texts=object_conditioned,
        residual_texts=None,
        sibling_part_count=len(sibling_part_texts),
        residual_enabled=False,
    )
