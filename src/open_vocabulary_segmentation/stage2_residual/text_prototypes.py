from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable

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


def build_object_conditioned_part_texts(
    object_text: list[float],
    part_texts: list[list[float]],
) -> list[list[float]]:
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
    object_conditioned_part_texts: list[list[float]],
    object_text: list[float],
    eps: float = 1e-8,
) -> list[list[float]]:
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
    object_text: list[float],
    part_texts: Iterable[Iterable[float]] | Iterable[float],
) -> ResidualTextSpec:
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
