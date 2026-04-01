from __future__ import annotations

import importlib.util
import sys
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping

import torch

try:
    from omegaconf import OmegaConf
except ImportError:  # pragma: no cover - environment-dependent optional dependency
    OmegaConf = None

from open_vocabulary_segmentation.stage2_protocol import (
    build_stage2_protocol,
    resolve_stage2_evaluator_binding,
)
from open_vocabulary_segmentation.stage2_protocol.formal_inputs_contract import (
    FormalInputsBundle,
    coerce_formal_inputs_bundle,
    validate_formal_inputs_bundle,
)
from open_vocabulary_segmentation.stage2_protocol.pp116_oracle_obj_evaluator import (
    compute_pp116_oracle_obj_runtime_evaluator_output,
)

from .competition import apply_sibling_competition, build_topk_support_targets
from .losses import build_default_loss_spec, compute_stage2_losses
from .modes import ResidualMode, parse_residual_mode
from .part_prototypes import build_part_prototype
from .retrieval import (
    build_retrieval_spec,
    build_stage2_prototype_bank,
    run_object_inside_retrieval,
)
from .text_prototypes import build_text_branch
from .visual_mapping import build_visual_mapping_spec, map_text_residual_to_visual


PP116_STAGE2_RESIDUAL_DEFAULT_CONFIG_PATH = Path(
    "src/open_vocabulary_segmentation/configs/pp116_stage2_residual/default.yml"
)

_DATASET_ENTRYPOINTS = {
    "pp116": "open_vocabulary_segmentation.segmentation.datasets.pp116_oracle_obj:get_pp116_oracle_obj_protocol_descriptor",
    "ade234": "open_vocabulary_segmentation.segmentation.datasets.ade234_instance_aware:get_ade234_instance_aware_protocol_descriptor",
}


@dataclass(frozen=True, slots=True)
class ResidualRouteResult:
    mode: str
    config_path: str
    protocol_bindings: dict[str, Any]
    retrieval_spec: dict[str, Any]
    losses: dict[str, float]
    grouped_metrics: dict[str, Any]
    debug: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def resolve_pp116_stage2_residual_config_path(
    config_path: str | Path | None = None,
) -> Path:
    path = Path(config_path) if config_path is not None else PP116_STAGE2_RESIDUAL_DEFAULT_CONFIG_PATH
    if not path.exists():
        raise FileNotFoundError(f"PP116 Stage-2 residual config path does not exist: {path}")
    return path


def _coerce_scalar(raw: str) -> Any:
    value = raw.strip()
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


@lru_cache(maxsize=32)
def _load_structured_config(path: Path) -> dict[str, dict[str, Any]]:
    if OmegaConf is not None:
        cfg = OmegaConf.load(path)
        return {
            "stage2_protocol": {
                "name": str(getattr(cfg.stage2_protocol, "name", "pp116_oracle_obj")),
                "formal_mode": bool(getattr(cfg.stage2_protocol, "formal_mode", False)),
            },
            "stage2_residual": {
                "mode": str(getattr(cfg.stage2_residual, "mode", "b2_residual_only")),
                "alpha_value": float(getattr(cfg.stage2_residual, "alpha_value", 1.0)),
                "tau_p": float(getattr(cfg.stage2_residual, "tau_p", 1.0)),
                "topk_k": int(getattr(cfg.stage2_residual, "topk_k", 1)),
                "support_scope": str(getattr(cfg.stage2_residual, "support_scope", "omega_o")),
                "competition_mode": str(
                    getattr(cfg.stage2_residual, "competition_mode", "sibling_competition")
                ),
            },
        }

    data: dict[str, dict[str, Any]] = {}
    current: str | None = None
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue
        if not line.startswith(" ") and line.endswith(":"):
            current = line[:-1].strip()
            data.setdefault(current, {})
            continue
        if current is None or not line.startswith("  "):
            continue
        stripped = line.strip()
        if ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        data[current][key.strip()] = _coerce_scalar(value)
    return data


def _resolve_mode_name(cfg: dict[str, dict[str, Any]], mode_name: str | None) -> str:
    if mode_name is not None:
        return mode_name
    cfg_mode = cfg.get("stage2_residual", {}).get("mode")
    if cfg_mode is None:
        raise ValueError("stage2_residual.mode is required in PP116 residual config")
    return str(cfg_mode)


@lru_cache(maxsize=16)
def _cached_build_stage2_protocol(protocol_name: str) -> Any:
    return build_stage2_protocol(protocol_name)


@lru_cache(maxsize=16)
def _cached_resolve_stage2_evaluator_binding(protocol_id: str) -> Any:
    descriptor = _cached_build_stage2_protocol(protocol_id)
    return resolve_stage2_evaluator_binding(descriptor)


def _default_inputs() -> dict[str, Any]:
    return {
        "object_text": [1.0, 0.0, 0.0],
        "part_texts": [
            [0.25, 0.70, 0.15],
            [0.30, 0.15, 0.65],
        ],
        "patch_features": [
            [0.90, 0.10, 0.00],
            [0.20, 0.75, 0.05],
            [0.15, 0.20, 0.80],
        ],
        "support_mask": [True, True, False],
    }


def _resolve_formal_mode(
    cfg: dict[str, dict[str, Any]],
    formal_mode: bool | None,
) -> bool:
    if formal_mode is not None:
        return bool(formal_mode)
    return bool(cfg.get("stage2_protocol", {}).get("formal_mode", False))


def _coerce_vector_list(raw: Any) -> list[list[float]]:
    if not isinstance(raw, list) or not raw:
        raise ValueError("expected non-empty list for vector list input")
    first = raw[0]
    if isinstance(first, (int, float)):
        return [[float(v) for v in raw]]
    return [[float(v) for v in vec] for vec in raw]


def _resolve_inputs(
    *,
    is_formal_mode: bool,
    formal_bundle: FormalInputsBundle | Mapping[str, Any] | None,
    formal_inputs: Mapping[str, Any] | None,
    synthetic_inputs: dict[str, Any] | None,
) -> tuple[dict[str, Any], bool, FormalInputsBundle | None]:
    if is_formal_mode:
        if formal_inputs is not None:
            raise ValueError(
                "formal PP116 mode does not accept loose formal_inputs; use formal_bundle only"
            )
        if formal_bundle is None:
            raise ValueError(
                "formal PP116 mode requires formal_bundle and cannot use _default_inputs()"
            )
        bundle = (
            coerce_formal_inputs_bundle(formal_bundle)
            if isinstance(formal_bundle, Mapping)
            else formal_bundle
        )
        validate_formal_inputs_bundle(bundle)
        return {
            "object_text": bundle.object_text,
            "part_texts": bundle.part_texts,
            "patch_features": bundle.patch_features,
            "support_mask": bundle.support_mask,
        }, False, bundle

    inputs = _default_inputs()
    if synthetic_inputs:
        inputs.update(synthetic_inputs)
    return {
        "object_text": [float(v) for v in inputs["object_text"]],
        "part_texts": _coerce_vector_list(inputs["part_texts"]),
        "patch_features": _coerce_vector_list(inputs["patch_features"]),
        "support_mask": [bool(v) for v in inputs["support_mask"]],
    }, True, None


def _mean(values: list[float]) -> float:
    return sum(values) / max(len(values), 1)


def _metric_source_key(mode: ResidualMode) -> str:
    if mode == ResidualMode.B0_DIRECT:
        return "object_conditioned_part_text"
    if mode == ResidualMode.B1_OBJ_CONDITIONED_NO_RESIDUAL:
        return "object_conditioned_part_text"
    return "residual_part_prototype"


def _stable_offset(obj: str, part: str) -> float:
    token = f"{obj}:{part}".encode("utf-8")
    # Small deterministic jitter keeps per-part scores distinct but bounded.
    return ((sum(token) % 200) - 100) / 10000.0


@lru_cache(maxsize=1)
def _load_stage2_protocol_builder_module() -> Any:
    eval_builder_path = (
        Path(__file__).resolve().parent.parent
        / "segmentation"
        / "evaluation"
        / "stage2_protocol_builder.py"
    )
    repo_root = eval_builder_path.parents[4]
    src_root = repo_root / "src"
    if str(src_root) not in sys.path:
        sys.path.insert(0, str(src_root))
    spec = importlib.util.spec_from_file_location(
        "stage2_protocol_builder_direct", eval_builder_path
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"unable to load stage2 protocol builder from {eval_builder_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@lru_cache(maxsize=16)
def _resolve_grouped_part_classes(protocol_name: str) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    module = _load_stage2_protocol_builder_module()
    bindings = module.resolve_stage2_protocol_bindings(protocol_name)
    payload = bindings.get("pp116_evaluator_payload", {})
    grouped = payload.get("grouped_part_classes", {})
    seen = [tuple(item) for item in grouped.get("seen_part_classes", [])]
    unseen = [tuple(item) for item in grouped.get("unseen_part_classes", [])]
    return seen, unseen


def _emit_grouped_metrics(
    *,
    mode: ResidualMode,
    assignments: dict[str, list[float]],
    protocol_name: str,
    formal_mode: bool,
    formal_evaluator_output: Mapping[str, Any] | None,
) -> dict[str, Any]:
    module = _load_stage2_protocol_builder_module()
    seen_part_classes, unseen_part_classes = _resolve_grouped_part_classes(protocol_name)

    if formal_mode:
        if formal_evaluator_output is None:
            raise ValueError(
                "formal PP116 mode requires evaluator output mapping and cannot use synthetic/default fallback"
            )
        grouped_miou = module.compute_pp116_grouped_miou_from_evaluator_output(
            evaluator_output=formal_evaluator_output,
            grouped_part_classes={
                "seen_part_classes": seen_part_classes,
                "unseen_part_classes": unseen_part_classes,
            },
        )
        grouped_miou["metric_source"] = "pp116_official_evaluator_output"
        grouped_miou["part_class_count"] = len(
            module._normalize_iou_by_part_class(formal_evaluator_output.get("iou_by_part_class", {}))
        )
        return grouped_miou

    source_key = _metric_source_key(mode)
    source_values = assignments.get(source_key, [])
    base_value = _mean(source_values)

    iou_by_part_class: dict[tuple[str, str], float] = {}
    for cls in seen_part_classes + unseen_part_classes:
        obj, part = cls
        value = min(max(base_value + _stable_offset(obj, part), 0.0), 1.0)
        iou_by_part_class[(obj, part)] = value

    grouped_miou = module.compute_pp116_grouped_miou(
        iou_by_part_class=iou_by_part_class,
        seen_part_classes=seen_part_classes,
        unseen_part_classes=unseen_part_classes,
    )
    grouped_miou["metric_source"] = "pp116_grouped_contract_via_stage2_protocol_builder"
    grouped_miou["metric_source_key"] = source_key
    grouped_miou["part_class_count"] = len(iou_by_part_class)
    return grouped_miou


def run_pp116_residual_route(
    *,
    mode_name: str | None = None,
    config_path: str | Path | None = None,
    synthetic_inputs: dict[str, Any] | None = None,
    formal_mode: bool | None = None,
    formal_bundle: FormalInputsBundle | Mapping[str, Any] | None = None,
    formal_inputs: Mapping[str, Any] | None = None,
    formal_evaluator_output: Mapping[str, Any] | None = None,
) -> ResidualRouteResult:
    cfg_path = resolve_pp116_stage2_residual_config_path(config_path)
    cfg = _load_structured_config(cfg_path)
    protocol_name = str(cfg.get("stage2_protocol", {}).get("name", "pp116_oracle_obj"))
    if protocol_name != "pp116_oracle_obj":
        raise ValueError(
            f"E4 PP116-first route received unsupported stage2_protocol.name={protocol_name!r}"
        )

    mode = parse_residual_mode(_resolve_mode_name(cfg, mode_name))
    is_formal_mode = _resolve_formal_mode(cfg, formal_mode)
    descriptor = _cached_build_stage2_protocol(protocol_name)
    evaluator_binding = _cached_resolve_stage2_evaluator_binding(protocol_name)
    protocol_bindings = {
        "protocol_id": descriptor.protocol_id,
        "dataset_family": descriptor.dataset_family,
        "dataset_entrypoint": _DATASET_ENTRYPOINTS[descriptor.dataset_family],
        "evaluator_binding": evaluator_binding.as_dict(),
    }

    inputs, used_default_inputs, resolved_formal_bundle = _resolve_inputs(
        is_formal_mode=is_formal_mode,
        formal_bundle=formal_bundle,
        formal_inputs=formal_inputs,
        synthetic_inputs=synthetic_inputs,
    )
    if is_formal_mode:
        if formal_evaluator_output is not None:
            raise ValueError(
                "formal PP116 mode does not accept loose formal_evaluator_output; use formal_bundle only"
            )
        assert resolved_formal_bundle is not None
        evaluator_output = resolved_formal_bundle.formal_evaluator_output or {}
        injected_iou = evaluator_output.get("iou_by_part_class", {})
        if isinstance(injected_iou, Mapping) and len(injected_iou) > 0:
            raise ValueError("formal PP116 mode forbids injected iou_by_part_class")
    else:
        evaluator_output = formal_evaluator_output

    text_spec = build_text_branch(mode, inputs["object_text"], inputs["part_texts"])
    visual_spec = build_visual_mapping_spec(
        mode,
        alpha_value=float(cfg.get("stage2_residual", {}).get("alpha_value", 1.0)),
    )
    residual_texts = text_spec.residual_texts or []
    mapped_residuals = map_text_residual_to_visual(
        object_text=text_spec.object_text,
        residual_texts=residual_texts,
        formal_mode=is_formal_mode and mode == ResidualMode.B2_RESIDUAL_ONLY,
    )
    part_spec = build_part_prototype(
        mode,
        patch_features=inputs["patch_features"],
        support_mask=inputs["support_mask"],
        residual_directions=mapped_residuals if mode == ResidualMode.B2_RESIDUAL_ONLY else None,
        alpha_value=float(cfg.get("stage2_residual", {}).get("alpha_value", 1.0)),
    )

    prototype_bank = build_stage2_prototype_bank(mode, text_spec=text_spec, part_spec=part_spec)
    tau_p = float(cfg.get("stage2_residual", {}).get("tau_p", 1.0))
    retrieval_spec = build_retrieval_spec(
        mode,
        prototype_bank,
        support_scope=str(cfg.get("stage2_residual", {}).get("support_scope", "omega_o")),
        competition_mode=str(
            cfg.get("stage2_residual", {}).get("competition_mode", "sibling_competition")
        ),
        tau_p=tau_p,
    )
    retrieval_scores = run_object_inside_retrieval(
        mode,
        patch_features=inputs["patch_features"],
        support_mask=inputs["support_mask"],
        prototype_bank=prototype_bank,
        tau_p=tau_p,
    )
    sibling_keys = [key for key in prototype_bank.keys() if key != "object_text"]
    if not sibling_keys:
        sibling_keys = list(prototype_bank.keys())
    assignments = apply_sibling_competition(
        retrieval_scores,
        sibling_groups=[sibling_keys],
    )
    if torch.is_tensor(inputs["patch_features"]) and torch.is_tensor(inputs["support_mask"]):
        support_features = inputs["patch_features"][inputs["support_mask"]]
    else:
        support_features = [
            feat for feat, keep in zip(inputs["patch_features"], inputs["support_mask"]) if keep
        ]
    topk_spec = int(cfg.get("stage2_residual", {}).get("topk_k", 1))
    z_targets = build_topk_support_targets(
        assignments=assignments,
        support_features=support_features,
        topk_spec=topk_spec,
    )
    v_part = {key: prototype_bank[key] for key in sibling_keys}
    losses = compute_stage2_losses(
        assignments,
        v_part=v_part,
        z_targets=z_targets,
        loss_spec=build_default_loss_spec(),
    )
    if (
        is_formal_mode
        and resolved_formal_bundle is not None
        and resolved_formal_bundle.evaluator_output_mode == "runtime"
    ):
        evaluator_output = compute_pp116_oracle_obj_runtime_evaluator_output(
            bundle=resolved_formal_bundle,
            assignments=assignments,
            sibling_assignment_keys=sibling_keys,
        )
    grouped_metrics = _emit_grouped_metrics(
        mode=mode,
        assignments=assignments,
        protocol_name=protocol_name,
        formal_mode=is_formal_mode,
        formal_evaluator_output=evaluator_output,
    )

    return ResidualRouteResult(
        mode=mode.value,
        config_path=str(cfg_path),
        protocol_bindings=protocol_bindings,
        retrieval_spec=retrieval_spec.as_dict(),
        losses=losses,
        grouped_metrics=grouped_metrics,
        debug={
            "formal_mode": is_formal_mode,
            "formal_core_uses_default_inputs": used_default_inputs,
            "formal_bundle_required": is_formal_mode,
            "formal_bundle_present": resolved_formal_bundle is not None,
            "formal_bundle_identity": (
                {
                    "file_name": resolved_formal_bundle.file_name,
                    "sem_seg_file_name": resolved_formal_bundle.sem_seg_file_name,
                    "obj_sem_seg_file_name": resolved_formal_bundle.obj_sem_seg_file_name,
                    "category_id": resolved_formal_bundle.category_id,
                }
                if resolved_formal_bundle is not None
                else None
            ),
            "formal_bundle_provenance": (
                {
                    "feature_source": resolved_formal_bundle.feature_source,
                    "support_source": resolved_formal_bundle.support_source,
                    "evaluator_source": resolved_formal_bundle.evaluator_source,
                    "evaluator_output_mode": resolved_formal_bundle.evaluator_output_mode,
                    "trace_key": resolved_formal_bundle.trace_key,
                }
                if resolved_formal_bundle is not None
                else None
            ),
            "v_o_source": "support_pooling",
            "delta_source": "Phi_o",
            "z_present": bool(z_targets),
            "tau_p": tau_p,
            "topk_k": topk_spec,
            "visual_mapping_enabled": visual_spec.phi_mapping_enabled,
            "sibling_part_count": len(sibling_keys),
            "prototype_keys": list(prototype_bank.keys()),
            "assignment_keys": list(assignments.keys()),
        },
    )
