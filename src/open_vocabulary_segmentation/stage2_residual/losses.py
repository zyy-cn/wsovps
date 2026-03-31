from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class ResidualLossSpec:
    use_l_inst: bool
    use_l_overlap: bool
    excluded_losses: tuple[str, ...]
    notes: str = ""

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def build_default_loss_spec() -> ResidualLossSpec:
    return ResidualLossSpec(
        use_l_inst=True,
        use_l_overlap=True,
        excluded_losses=("l_tv", "l_view", "l_ctr", "l_rec"),
        notes="E4 minimal residual-only objective keeps only L_inst and L_overlap active.",
    )


def _mean(values: list[float]) -> float:
    return sum(values) / max(len(values), 1)


def _dot(lhs: list[float], rhs: list[float]) -> float:
    return sum(a * b for a, b in zip(lhs, rhs))


def _norm(vec: list[float], eps: float = 1e-8) -> float:
    return max(sum(v * v for v in vec) ** 0.5, eps)


def _cosine(lhs: list[float], rhs: list[float], eps: float = 1e-8) -> float:
    if len(lhs) != len(rhs):
        raise ValueError("cosine vectors must have identical dimensions")
    return _dot(lhs, rhs) / (_norm(lhs, eps) * _norm(rhs, eps))


def compute_l_inst(
    v_part: dict[str, list[float]],
    z_targets: dict[str, list[float]],
) -> float:
    penalties: list[float] = []
    for key, pred in v_part.items():
        target = z_targets.get(key)
        if target is None:
            continue
        penalties.append(1.0 - _cosine(pred, target))
    return _mean(penalties)


def compute_l_overlap(
    assignments: dict[str, list[float]],
    overlap_pairs: list[tuple[str, str]] | None = None,
) -> float:
    if not assignments:
        return 0.0
    keys = list(assignments.keys())
    if overlap_pairs is None:
        overlap_pairs = [(keys[i], keys[j]) for i in range(len(keys)) for j in range(i + 1, len(keys))]
    penalties: list[float] = []
    for lhs, rhs in overlap_pairs:
        if lhs not in assignments or rhs not in assignments:
            continue
        lhs_scores = assignments[lhs]
        rhs_scores = assignments[rhs]
        if len(lhs_scores) != len(rhs_scores):
            raise ValueError("L_overlap assignment length mismatch")
        num = sum(a * b for a, b in zip(lhs_scores, rhs_scores))
        den = sum(lhs_scores) + sum(rhs_scores) + 1e-8
        penalties.append(num / den)
    return _mean(penalties)


def compute_stage2_losses(
    assignments: dict[str, list[float]],
    *,
    v_part: dict[str, list[float]] | None = None,
    z_targets: dict[str, list[float]] | None = None,
    supervision: dict[str, list[float]] | None = None,
    overlap_pairs: list[tuple[str, str]] | None = None,
    loss_spec: ResidualLossSpec | None = None,
) -> dict[str, float]:
    spec = loss_spec or build_default_loss_spec()
    losses: dict[str, float] = {}
    if spec.use_l_inst:
        if v_part is not None and z_targets is not None:
            losses["l_inst"] = compute_l_inst(v_part, z_targets)
        elif supervision is not None:
            # Compatibility fallback for legacy smoke-only callers.
            losses["l_inst"] = compute_l_inst(
                {k: assignments[k] for k in assignments},
                {k: supervision.get(k, assignments[k]) for k in assignments},
            )
        else:
            raise ValueError("compute_stage2_losses requires v_part/z_targets or supervision")
    if spec.use_l_overlap:
        losses["l_overlap"] = compute_l_overlap(assignments, overlap_pairs=overlap_pairs)
    return losses
