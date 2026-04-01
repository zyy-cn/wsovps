from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable

import torch


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
    scores: dict[str, list[float] | torch.Tensor],
    *,
    sibling_groups: list[list[str]] | None = None,
) -> dict[str, list[float] | torch.Tensor]:
    if not scores:
        return {}
    score_keys = list(scores.keys())
    if sibling_groups is None:
        sibling_groups = [score_keys]

    for key in score_keys:
        if key.startswith("object_"):
            raise ValueError("sibling competition set must exclude object channels")
    first = next(iter(scores.values()))
    if torch.is_tensor(first):
        score_len = int(first.shape[0])
        normalized: dict[str, list[float] | torch.Tensor] = {
            key: torch.zeros(score_len, dtype=first.dtype, device=first.device) for key in score_keys
        }
        for key, row in scores.items():
            if not torch.is_tensor(row) or row.shape[0] != score_len:
                raise ValueError(f"sibling competition score length mismatch for key={key}")
    else:
        score_len = len(first)
        for key, row in scores.items():
            if len(row) != score_len:
                raise ValueError(f"sibling competition score length mismatch for key={key}")
        normalized = {key: [0.0] * score_len for key in score_keys}
    for group in sibling_groups:
        if not group:
            continue
        missing = [name for name in group if name not in scores]
        if missing:
            raise ValueError(f"sibling group references unknown prototypes: {missing}")
        if torch.is_tensor(first):
            stacked = torch.stack([scores[name] for name in group], dim=0)
            probs = torch.softmax(stacked, dim=0)
            for name, prob in zip(group, probs):
                normalized[name] = prob
        else:
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
    assignments: dict[str, list[float] | torch.Tensor],
    support_features: list[list[float]] | torch.Tensor,
    topk_spec: int | float,
) -> dict[str, list[float] | torch.Tensor]:
    if not assignments:
        return {}
    if torch.is_tensor(support_features):
        support_count = int(support_features.shape[0])
        dim = int(support_features.shape[1])
    else:
        support_count = len(support_features)
        dim = len(support_features[0]) if support_features else 0
    k = resolve_topk_count(support_count=support_count, topk_spec=topk_spec)
    out: dict[str, list[float] | torch.Tensor] = {}
    for key, probs in assignments.items():
        if torch.is_tensor(probs):
            if int(probs.shape[0]) != support_count:
                raise ValueError(f"assignment/support length mismatch for {key}")
            ranked = torch.topk(probs, k=min(k, support_count)).indices
            selected = probs.index_select(0, ranked)
            weight_sum = selected.sum()
            if float(weight_sum) <= 0:
                weights = torch.full((int(ranked.shape[0]),), 1.0 / max(int(ranked.shape[0]), 1), device=probs.device, dtype=probs.dtype)
            else:
                weights = selected / weight_sum.clamp_min(1e-8)
            feats = support_features if torch.is_tensor(support_features) else torch.as_tensor(support_features, dtype=probs.dtype, device=probs.device)
            pooled = (feats.index_select(0, ranked) * weights.unsqueeze(-1)).sum(dim=0)
            out[key] = pooled / pooled.norm(dim=-1, keepdim=True).clamp_min(1e-8)
        else:
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
