from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable


@dataclass(frozen=True, slots=True)
class CompetitionSpec:
    competition_mode: str
    sibling_groups: tuple[tuple[str, ...], ...]
    notes: str = ""

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def _softmax(values: list[float]) -> list[float]:
    if not values:
        return []
    pivot = max(values)
    exps = [pow(2.718281828459045, v - pivot) for v in values]
    denom = sum(exps)
    if denom <= 0:
        return [0.0 for _ in values]
    return [v / denom for v in exps]


def apply_sibling_competition(
    scores: dict[str, list[float]],
    *,
    sibling_groups: list[list[str]] | None = None,
) -> dict[str, list[float]]:
    if not scores:
        return {}
    score_keys = list(scores.keys())
    score_len = len(next(iter(scores.values())))
    for key, row in scores.items():
        if len(row) != score_len:
            raise ValueError(f"sibling competition score length mismatch for key={key}")

    if sibling_groups is None:
        sibling_groups = [score_keys]

    for key in score_keys:
        if key.startswith("object_"):
            raise ValueError("sibling competition set must exclude object channels")

    normalized = {key: [0.0] * score_len for key in score_keys}
    for group in sibling_groups:
        if not group:
            continue
        missing = [name for name in group if name not in scores]
        if missing:
            raise ValueError(f"sibling group references unknown prototypes: {missing}")
        for index in range(score_len):
            group_scores = [scores[name][index] for name in group]
            group_probs = _softmax(group_scores)
            for name, prob in zip(group, group_probs):
                normalized[name][index] = prob
    return normalized


def resolve_topk_count(*, support_count: int, topk_spec: int | float) -> int:
    if support_count <= 0:
        raise ValueError("support_count must be positive")
    if isinstance(topk_spec, float):
        if not (0.0 < topk_spec <= 1.0):
            raise ValueError("topk_ratio must be in (0, 1]")
        return max(1, int(round(support_count * topk_spec)))
    return max(1, min(int(topk_spec), support_count))


def _l2_normalize(vec: list[float], eps: float = 1e-8) -> list[float]:
    norm = sum(v * v for v in vec) ** 0.5
    denom = max(norm, eps)
    return [v / denom for v in vec]


def build_topk_support_targets(
    *,
    assignments: dict[str, list[float]],
    support_features: list[list[float]],
    topk_spec: int | float,
) -> dict[str, list[float]]:
    if not assignments:
        return {}
    support_count = len(support_features)
    k = resolve_topk_count(support_count=support_count, topk_spec=topk_spec)
    dim = len(support_features[0]) if support_features else 0
    out: dict[str, list[float]] = {}
    for key, probs in assignments.items():
        if len(probs) != support_count:
            raise ValueError(f"assignment/support length mismatch for {key}")
        ranked = sorted(range(support_count), key=lambda i: probs[i], reverse=True)[:k]
        weight_sum = sum(probs[i] for i in ranked)
        if weight_sum <= 0:
            weights = [1.0 / len(ranked)] * len(ranked)
        else:
            weights = [probs[i] / weight_sum for i in ranked]
        pooled = [0.0] * dim
        for idx, w in zip(ranked, weights):
            feat = support_features[idx]
            for d, val in enumerate(feat):
                pooled[d] += w * val
        out[key] = _l2_normalize(pooled)
    return out
