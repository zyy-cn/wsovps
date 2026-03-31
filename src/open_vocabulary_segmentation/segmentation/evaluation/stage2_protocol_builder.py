from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping

from open_vocabulary_segmentation.stage2_protocol.evaluator_binding import (
    build_stage2_protocol,
    resolve_stage2_evaluator_binding,
)
from open_vocabulary_segmentation.stage2_protocol.official_pp116_reference import (
    OFFICIAL_GROUPED_METRIC_KEYS,
    canonical_sibling_part_keys,
    format_grouped_metrics_payload,
)

_DATASET_ENTRYPOINTS = {
    "pp116": "open_vocabulary_segmentation.segmentation.datasets.pp116_oracle_obj:get_pp116_oracle_obj_protocol_descriptor",
    "ade234": "open_vocabulary_segmentation.segmentation.datasets.ade234_instance_aware:get_ade234_instance_aware_protocol_descriptor",
}


def resolve_stage2_dataset_entrypoint(protocol: str) -> str:
    descriptor = build_stage2_protocol(protocol)
    try:
        return _DATASET_ENTRYPOINTS[descriptor.dataset_family]
    except KeyError as exc:
        raise ValueError(
            f"unsupported dataset family for Stage-2 protocol: {descriptor.dataset_family}"
        ) from exc


def _harmonic_mean(seen_miou: float, unseen_miou: float) -> float:
    denom = seen_miou + unseen_miou
    return 0.0 if denom == 0.0 else 2.0 * seen_miou * unseen_miou / denom


def _mean(values: Iterable[float]) -> float:
    vals = [float(v) for v in values]
    return 0.0 if not vals else sum(vals) / len(vals)


def build_pp116_part_groups(
    parts_by_object: Mapping[str, Iterable[str]],
    seen_objects: Iterable[str],
    unseen_objects: Iterable[str],
) -> dict[str, list[tuple[str, str]]]:
    seen = []
    unseen = []
    for obj in seen_objects:
        for part in canonical_sibling_part_keys(obj, parts_by_object.get(obj, [])):
            seen.append((obj, part))
    for obj in unseen_objects:
        for part in canonical_sibling_part_keys(obj, parts_by_object.get(obj, [])):
            unseen.append((obj, part))
    return {"seen_part_classes": seen, "unseen_part_classes": unseen}


def compute_pp116_grouped_miou(
    iou_by_part_class: Mapping[tuple[str, str], float],
    seen_part_classes: Iterable[tuple[str, str]],
    unseen_part_classes: Iterable[tuple[str, str]],
) -> dict[str, float]:
    seen_keys = list(seen_part_classes)
    unseen_keys = list(unseen_part_classes)
    seen_vals = [iou_by_part_class[key] for key in seen_keys if key in iou_by_part_class]
    unseen_vals = [iou_by_part_class[key] for key in unseen_keys if key in iou_by_part_class]
    seen_miou = _mean(seen_vals)
    unseen_miou = _mean(unseen_vals)
    return {
        "seen_miou": seen_miou,
        "unseen_miou": unseen_miou,
        "harmonic_miou": _harmonic_mean(seen_miou, unseen_miou),
    }


def _normalize_part_class_key(key: Any) -> tuple[str, str] | None:
    if isinstance(key, tuple) and len(key) == 2:
        return str(key[0]), str(key[1])
    if isinstance(key, str) and "::" in key:
        lhs, rhs = key.split("::", 1)
        return lhs, rhs
    return None


def _normalize_iou_by_part_class(
    iou_by_part_class: Mapping[Any, float],
) -> dict[tuple[str, str], float]:
    out: dict[tuple[str, str], float] = {}
    for key, value in iou_by_part_class.items():
        norm = _normalize_part_class_key(key)
        if norm is None:
            continue
        out[norm] = float(value)
    return out


def compute_pp116_grouped_miou_from_evaluator_output(
    evaluator_output: Mapping[str, Any],
    grouped_part_classes: Mapping[str, Iterable[tuple[str, str]]],
) -> dict[str, Any]:
    iou_raw = evaluator_output.get("iou_by_part_class")
    if not isinstance(iou_raw, Mapping):
        raise ValueError("formal evaluator output must provide mapping field: iou_by_part_class")

    normalized_iou = _normalize_iou_by_part_class(iou_raw)
    grouped_raw = compute_pp116_grouped_miou(
        iou_by_part_class=normalized_iou,
        seen_part_classes=grouped_part_classes.get("seen_part_classes", []),
        unseen_part_classes=grouped_part_classes.get("unseen_part_classes", []),
    )
    presentation = format_grouped_metrics_payload(grouped_raw)
    return {
        **grouped_raw,
        "raw": presentation["raw"],
        "display_percent": presentation["display_percent"],
        "presentation": presentation,
        "official_metric_keys": list(OFFICIAL_GROUPED_METRIC_KEYS),
    }


def _load_pp116_dataset_metadata() -> dict[str, Any]:
    dataset_path = (
        Path(__file__).resolve().parent.parent / "datasets" / "pp116_oracle_obj.py"
    )
    repo_root = dataset_path.parents[4]
    src_root = repo_root / "src"
    if str(src_root) not in sys.path:
        sys.path.insert(0, str(src_root))
    spec = importlib.util.spec_from_file_location("pp116_oracle_obj", dataset_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"unable to load PP116 dataset module from {dataset_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.get_pp116_oracle_obj_dataset_metadata()


def _build_pp116_evaluator_payload() -> dict[str, Any]:
    dataset_metadata = _load_pp116_dataset_metadata()
    part_groups = build_pp116_part_groups(
        parts_by_object=dataset_metadata["parts_by_object"],
        seen_objects=dataset_metadata["seen_objects"],
        unseen_objects=dataset_metadata["unseen_objects"],
    )
    return {
        "protocol_semantics": "pp116_oracle_obj_generalized_zero_shot",
        "dataset_metadata": dataset_metadata,
        "split_source": dataset_metadata["obj_ann_split_dirs"],
        "seen_unseen_source": {
            "seen_objects": dataset_metadata["seen_objects"],
            "unseen_objects": dataset_metadata["unseen_objects"],
        },
        "grouped_part_classes": part_groups,
        "metrics_output_keys": ["seen_miou", "unseen_miou", "harmonic_miou"],
        "metrics_entrypoint": (
            "open_vocabulary_segmentation.segmentation.evaluation.stage2_protocol_builder."
            "compute_pp116_grouped_miou"
        ),
        "formal_metrics_entrypoint": (
            "open_vocabulary_segmentation.segmentation.evaluation.stage2_protocol_builder."
            "compute_pp116_grouped_miou_from_evaluator_output"
        ),
        "metrics_presentation": {
            "raw_scale": "0_to_1",
            "display_percent_scale": "0_to_100",
        },
        "metrics_rule": "harmonic = 2*seen*unseen/(seen+unseen), 0 when denominator is 0",
    }


def resolve_stage2_protocol_bindings(protocol: str) -> dict[str, Any]:
    descriptor = build_stage2_protocol(protocol)
    evaluator_binding = resolve_stage2_evaluator_binding(descriptor)
    bindings: dict[str, Any] = {
        "protocol_id": descriptor.protocol_id,
        "dataset_family": descriptor.dataset_family,
        "dataset_entrypoint": resolve_stage2_dataset_entrypoint(protocol),
        "evaluator_binding": evaluator_binding.as_dict(),
    }
    if descriptor.dataset_family == "pp116":
        bindings["pp116_evaluator_payload"] = _build_pp116_evaluator_payload()
    return bindings
