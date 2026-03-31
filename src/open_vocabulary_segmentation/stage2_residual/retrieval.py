from __future__ import annotations

from dataclasses import asdict, dataclass

from .modes import ResidualMode
from .part_prototypes import PartPrototypeSpec
from .text_prototypes import ResidualTextSpec


@dataclass(frozen=True, slots=True)
class RetrievalSpec:
    mode: ResidualMode
    support_scope: str
    competition_mode: str
    tau_p: float
    prototype_order: tuple[str, ...]
    notes: str = ""

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["mode"] = self.mode.value
        return payload


def _dot(lhs: list[float], rhs: list[float]) -> float:
    return sum(a * b for a, b in zip(lhs, rhs))


def _l2_norm(vec: list[float], eps: float = 1e-8) -> float:
    return max(sum(v * v for v in vec) ** 0.5, eps)


def _cosine(lhs: list[float], rhs: list[float], eps: float = 1e-8) -> float:
    if len(lhs) != len(rhs):
        raise ValueError("retrieval vectors must have identical dimensions")
    return _dot(lhs, rhs) / (_l2_norm(lhs, eps) * _l2_norm(rhs, eps))


def _inside_support(
    patch_features: list[list[float]],
    support_mask: list[bool],
) -> list[list[float]]:
    if len(patch_features) != len(support_mask):
        raise ValueError("patch_features and support_mask length mismatch")
    return [feat for feat, keep in zip(patch_features, support_mask) if keep]


def _resolve_sibling_keys(mode: ResidualMode, count: int) -> list[str]:
    if mode == ResidualMode.B0_DIRECT:
        return [f"part_{i:03d}_direct" for i in range(count)]
    if mode == ResidualMode.B1_OBJ_CONDITIONED_NO_RESIDUAL:
        return [f"part_{i:03d}_obj_cond" for i in range(count)]
    return [f"part_{i:03d}_residual" for i in range(count)]


def build_stage2_prototype_bank(
    mode: ResidualMode,
    *,
    text_spec: ResidualTextSpec,
    part_spec: PartPrototypeSpec,
) -> dict[str, list[float]]:
    if text_spec.sibling_part_count <= 0:
        raise ValueError("sibling part set must be non-empty")
    keys = _resolve_sibling_keys(mode, text_spec.sibling_part_count)
    if mode == ResidualMode.B0_DIRECT:
        return {
            key: text_spec.part_texts[idx]
            for idx, key in enumerate(keys)
        }
    if mode == ResidualMode.B1_OBJ_CONDITIONED_NO_RESIDUAL:
        return {
            key: text_spec.object_conditioned_part_texts[idx]
            for idx, key in enumerate(keys)
        }
    if part_spec.part_prototypes is None:
        raise ValueError("B2 residual-only retrieval requires part prototypes")
    return {
        key: part_spec.part_prototypes[idx]
        for idx, key in enumerate(keys)
    }


def build_retrieval_spec(
    mode: ResidualMode,
    prototype_bank: dict[str, list[float]],
    *,
    support_scope: str = "omega_o",
    competition_mode: str = "sibling_competition",
    tau_p: float = 1.0,
) -> RetrievalSpec:
    if tau_p <= 0:
        raise ValueError("tau_p must be > 0")
    notes = (
        "Object-inside retrieval over protocol-conditioned support."
        if mode == ResidualMode.B2_RESIDUAL_ONLY
        else "Object-inside retrieval over non-residual path."
    )
    return RetrievalSpec(
        mode=mode,
        support_scope=support_scope,
        competition_mode=competition_mode,
        tau_p=tau_p,
        prototype_order=tuple(prototype_bank.keys()),
        notes=notes,
    )


def run_object_inside_retrieval(
    mode: ResidualMode,
    *,
    patch_features: list[list[float]],
    support_mask: list[bool],
    prototype_bank: dict[str, list[float]],
    tau_p: float,
) -> dict[str, list[float]]:
    if tau_p <= 0:
        raise ValueError("tau_p must be > 0")
    inside_features = _inside_support(patch_features, support_mask)
    if not inside_features:
        raise ValueError("support_mask selected zero patch features")
    scores: dict[str, list[float]] = {}
    for proto_name, proto in prototype_bank.items():
        scores[proto_name] = [_cosine(feat, proto) / tau_p for feat in inside_features]
    if not scores:
        raise ValueError("retrieval prototype_bank must be non-empty")
    return scores
