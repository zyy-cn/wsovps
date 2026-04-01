#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import random
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any

import numpy as np
import torch


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from open_vocabulary_segmentation.segmentation.datasets.pp116_oracle_obj import (  # noqa: E402
    PP116_PARTS_BY_OBJECT,
    build_pp116_official_object_conditioned_samples,
    get_pp116_object_key_from_category_id,
    get_pp116_oracle_obj_dataset_metadata,
)
from open_vocabulary_segmentation.stage2_protocol.formal_inputs_builder import (  # noqa: E402
    build_formal_inputs_bundle,
)
from open_vocabulary_segmentation.stage2_residual.attribution import (  # noqa: E402
    ATTRIBUTION_CONDITIONS,
    build_pp116_residual_attribution_state,
    run_attribution_condition,
)
from open_vocabulary_segmentation.stage2_residual.losses import build_loss_spec_from_condition  # noqa: E402
from open_vocabulary_segmentation.stage2_residual.runtime import run_pp116_residual_route  # noqa: E402
from tools.run_s2_round7_smoke import (  # noqa: E402
    CLIP_CACHE_PATH,
    WEIGHT_PATH,
    WEIGHT_SHA256,
    _encode_texts,
    _extract_patch_features,
    _load_real_encoders,
    _read_mask_array,
    _read_rgb_image,
    _sha256,
    _support_patch_mask,
)


DEFAULT_CONDITIONS: tuple[str, ...] = ATTRIBUTION_CONDITIONS
DEFAULT_MODE_NAME = "b2_residual_only"
DEFAULT_CONFIG_PATH = "src/open_vocabulary_segmentation/configs/pp116_stage2_residual/b2.yml"
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "outputs" / "s2a_formal" / "RUN-S2A-FORMAL-R2"
DEFAULT_RUN_ID = "RUN-S2A-FORMAL-R2"
DEFAULT_GPU_VISIBLE = "1,2"
DEFAULT_PP116_SPLIT = "val"
DEFAULT_ORACLE_OBJ_SOURCE = "pp116_oracle_obj"
SEED_SAMPLE_BUDGETS = {0: 100, 1: 50}


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run one bounded S2A Oracle-Obj loss mechanism formal validation slice."
    )
    parser.add_argument(
        "--condition",
        required=True,
        choices=list(DEFAULT_CONDITIONS),
        help="Loss-switch condition for the formal run.",
    )
    parser.add_argument("--seed", required=True, type=int, help="Deterministic seed.")
    parser.add_argument(
        "--max_samples",
        required=True,
        type=int,
        help="Maximum number of official PP116 samples to evaluate.",
    )
    parser.add_argument(
        "--output_dir",
        required=True,
        type=Path,
        help="Run output directory for per-condition/seed JSON artifacts.",
    )
    parser.add_argument(
        "--pp116_split",
        default=DEFAULT_PP116_SPLIT,
        help="Official PP116 split to evaluate.",
    )
    parser.add_argument(
        "--oracle_obj_source",
        default=DEFAULT_ORACLE_OBJ_SOURCE,
        help="Canonical oracle-object source identifier (recorded only).",
    )
    parser.add_argument(
        "--export_probes",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Export compact per-sample probe payloads.",
    )
    parser.add_argument(
        "--gpu_visible",
        default=DEFAULT_GPU_VISIBLE,
        help="Expected CUDA_VISIBLE_DEVICES binding; validated only.",
    )
    return parser


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")


def _write_json(path: Path, payload: Any) -> None:
    _write_text(path, json.dumps(payload, indent=2, sort_keys=True))


def _to_jsonable(value: Any) -> Any:
    if torch.is_tensor(value):
        if value.ndim == 0:
            return value.item()
        return value.detach().cpu().tolist()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_jsonable(item) for item in value]
    return value


def _mean_or_zero(values: list[float]) -> float:
    return float(mean(values)) if values else 0.0


def _percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    arr = np.asarray(values, dtype=np.float64)
    return float(np.percentile(arr, q))


def _normalize_iou_values(iou_by_part_class: Any) -> list[float]:
    if not isinstance(iou_by_part_class, dict):
        return []
    out: list[float] = []
    for value in iou_by_part_class.values():
        try:
            out.append(float(value))
        except (TypeError, ValueError):
            continue
    return out


def _capture_runtime_evaluator_output():
    import open_vocabulary_segmentation.stage2_protocol.pp116_oracle_obj_evaluator as eval_module  # noqa: WPS433,E501

    original = eval_module.compute_pp116_oracle_obj_runtime_evaluator_output
    state: dict[str, Any] = {"last": None}

    def _wrapped(*args: Any, **kwargs: Any) -> dict[str, Any]:
        result = original(*args, **kwargs)
        state["last"] = result
        return result

    eval_module.compute_pp116_oracle_obj_runtime_evaluator_output = _wrapped
    return state, original, eval_module


def _restore_runtime_evaluator_output(original: Any, module: Any) -> None:
    module.compute_pp116_oracle_obj_runtime_evaluator_output = original


def _set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def _assert_gpu_binding(expected_visible: str) -> torch.device:
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA_REQUIRED")
    env_visible = os.environ.get("CUDA_VISIBLE_DEVICES")
    if env_visible is None:
        raise RuntimeError("CUDA_VISIBLE_DEVICES must be set to 1,2 for S2A formal")
    if env_visible != expected_visible:
        raise RuntimeError(
            f"CUDA_VISIBLE_DEVICES mismatch: expected {expected_visible!r}, got {env_visible!r}"
        )
    if torch.cuda.device_count() != 2:
        raise RuntimeError(f"expected 2 CUDA devices under binding {expected_visible!r}")
    return torch.device("cuda")


def _select_samples(*, split: str, seed: int, max_samples: int) -> list[dict[str, Any]]:
    samples = build_pp116_official_object_conditioned_samples(split=split)
    samples = sorted(
        samples,
        key=lambda sample: (
            str(sample["file_name"]),
            int(sample["category_id"]),
            str(sample["sem_seg_file_name"]),
        ),
    )
    rng = random.Random(int(seed))
    rng.shuffle(samples)
    return samples[: max(int(max_samples), 0)]


def _sample_identity(sample: dict[str, Any]) -> dict[str, Any]:
    file_name = str(sample["file_name"])
    sem_seg_file_name = str(sample["sem_seg_file_name"])
    obj_sem_seg_file_name = str(sample["obj_sem_seg_file_name"])
    category_id = int(sample["category_id"])
    object_class_key = get_pp116_object_key_from_category_id(category_id)
    sibling_part_keys = sorted(PP116_PARTS_BY_OBJECT[object_class_key])
    return {
        "file_name": file_name,
        "sem_seg_file_name": sem_seg_file_name,
        "obj_sem_seg_file_name": obj_sem_seg_file_name,
        "category_id": category_id,
        "object_class_key": object_class_key,
        "sibling_part_keys": sibling_part_keys,
    }


def _build_bundle_and_state(
    *,
    sample: dict[str, Any],
    clip_model: Any,
    projection: Any,
    dino_model: Any,
    dino_preprocess: Any,
    device: torch.device,
    split: str,
    mode_name: str,
    config_path: str,
    loss_condition: str,
) -> tuple[Any, Any, dict[str, Any], dict[str, Any]]:
    sample_file_name = str(sample["file_name"])
    sem_seg_file_name = str(sample["sem_seg_file_name"])
    obj_sem_seg_file_name = str(sample["obj_sem_seg_file_name"])
    category_id = int(sample["category_id"])
    object_class_key = get_pp116_object_key_from_category_id(category_id)
    sibling_part_keys = sorted(PP116_PARTS_BY_OBJECT[object_class_key])
    image = _read_rgb_image(sample_file_name)
    patch_features, (gh, gw) = _extract_patch_features(
        image,
        dino_model=dino_model,
        preprocess=dino_preprocess,
        device=device,
    )
    obj_mask = _read_mask_array(obj_sem_seg_file_name)
    support_mask = _support_patch_mask(obj_mask, category_id, gh, gw, device=device)
    if int(support_mask.sum().item()) < 1:
        raise RuntimeError(
            f"selected official sample has empty oracle-object support after patch masking: {sample_file_name}"
        )
    encoded = _encode_texts(
        [object_class_key] + [f"{object_class_key}::{part}" for part in sibling_part_keys],
        clip_model=clip_model,
        projection=projection,
        device=device,
    )
    object_text = encoded[0]
    part_texts = encoded[1:]
    bundle = build_formal_inputs_bundle(
        file_name=sample_file_name,
        sem_seg_file_name=sem_seg_file_name,
        obj_sem_seg_file_name=obj_sem_seg_file_name,
        category_id=category_id,
        sibling_part_keys=sibling_part_keys,
        object_text=object_text,
        part_texts=part_texts,
        patch_features=patch_features,
        support_mask=support_mask,
        formal_evaluator_output={"runtime_payload": {"patch_grid_shape": [gh, gw]}},
        evaluator_output_mode="runtime",
        object_class_key=object_class_key,
        split_tag=split,
        trace_key=f"{Path(sample_file_name).stem}::cat{category_id}",
        feature_source=f"dinov2_patch_tokens::{sample_file_name}",
        support_source=f"oracle_obj_mask::{obj_sem_seg_file_name}",
        evaluator_source="pp116_official_evaluator_output",
        run_id=DEFAULT_RUN_ID,
        protocol_name="pp116_oracle_obj",
        image_shape=[int(obj_mask.shape[0]), int(obj_mask.shape[1])],
        patch_grid_shape=[gh, gw],
        feature_dtype=str(patch_features.dtype).replace("torch.", ""),
    )

    state = build_pp116_residual_attribution_state(
        mode_name=mode_name,
        config_path=config_path,
        formal_mode=True,
        formal_bundle=bundle,
        loss_spec=build_loss_spec_from_condition(loss_condition),
    )
    route = run_pp116_residual_route(
        mode_name=mode_name,
        config_path=config_path,
        formal_mode=True,
        formal_bundle=bundle,
    )
    return bundle, state, {
        "sample": {
            "file_name": sample_file_name,
            "sem_seg_file_name": sem_seg_file_name,
            "obj_sem_seg_file_name": obj_sem_seg_file_name,
            "category_id": category_id,
            "object_class_key": object_class_key,
            "sibling_part_keys": sibling_part_keys,
            "patch_grid_shape": [gh, gw],
        },
        "route": route,
    }


def _aggregate_mechanism_results(sample_runs: list[dict[str, Any]]) -> dict[str, Any]:
    if not sample_runs:
        return {}
    fields = (
        "inst_alignment_mean",
        "sibling_confusion_mean",
        "prototype_separation_mean",
        "support_top1_margin_mean",
        "support_background_margin_mean",
        "assignment_entropy_mean",
    )
    agg = {field: _mean_or_zero([float(run["probe_payload"][field]) for run in sample_runs]) for field in fields}
    per_part: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for run in sample_runs:
        for key, payload in run["probe_payload"]["per_part"].items():
            for metric_name, metric_value in payload.items():
                try:
                    per_part[key][metric_name].append(float(metric_value))
                except (TypeError, ValueError):
                    continue
    agg["per_part"] = {
        key: {metric: _mean_or_zero(values) for metric, values in metrics.items()}
        for key, metrics in per_part.items()
    }
    agg["condition_count"] = len(sample_runs)
    return agg


def _aggregate_result_metrics(sample_runs: list[dict[str, Any]]) -> dict[str, Any]:
    seen = [float(run["grouped_metrics"]["seen_miou"]) for run in sample_runs]
    unseen = [float(run["grouped_metrics"]["unseen_miou"]) for run in sample_runs]
    harmonic = [float(run["grouped_metrics"]["harmonic_miou"]) for run in sample_runs]
    raw = {
        "seen_miou": _mean_or_zero(seen),
        "unseen_miou": _mean_or_zero(unseen),
        "harmonic_miou": _mean_or_zero(harmonic),
    }
    display_percent = {key: value * 100.0 for key, value in raw.items()}
    return {
        "raw": raw,
        "display_percent": display_percent,
        "condition_count": len(sample_runs),
    }


def _gpu_evidence(device: torch.device) -> dict[str, Any]:
    torch.cuda.synchronize(device)
    smi = subprocess.run(
        [
            "nvidia-smi",
            "--query-gpu=index,uuid,memory.used,utilization.gpu",
            "--format=csv,noheader",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    compute = subprocess.run(
        [
            "nvidia-smi",
            "--query-compute-apps=pid,process_name,used_memory",
            "--format=csv,noheader",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    return {
        "cuda_is_available": torch.cuda.is_available(),
        "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
        "device_count": torch.cuda.device_count(),
        "logical_device": str(device),
        "max_memory_allocated": int(torch.cuda.max_memory_allocated(device)),
        "max_memory_reserved": int(torch.cuda.max_memory_reserved(device)),
        "nvidia_smi": smi.stdout.strip(),
        "nvidia_smi_compute_apps": compute.stdout.strip(),
    }


def _condition_result_dir(output_dir: Path, seed: int, condition: str) -> Path:
    return output_dir / f"seed_{seed}" / condition


def _run_single_condition(
    *,
    condition: str,
    seed: int,
    max_samples: int,
    output_dir: Path,
    split: str,
    oracle_obj_source: str,
    export_probes: bool,
    gpu_visible: str,
) -> dict[str, Any]:
    device = _assert_gpu_binding(gpu_visible)
    if condition not in DEFAULT_CONDITIONS:
        raise ValueError(f"unsupported loss condition: {condition}")
    sample_budget = min(int(max_samples), SEED_SAMPLE_BUDGETS.get(int(seed), int(max_samples)))
    if sample_budget <= 0:
        raise ValueError("max_samples must be positive after applying seed budget")

    _set_seed(int(seed))
    torch.cuda.reset_peak_memory_stats(device)
    metadata = get_pp116_oracle_obj_dataset_metadata()
    clip_model, preprocess, projection, dino_model, dino_preprocess, dino_provenance = _load_real_encoders(device)

    selected_samples = _select_samples(split=split, seed=seed, max_samples=sample_budget)
    if not selected_samples:
        raise RuntimeError("no official PP116 samples available for S2A formal matrix")

    sample_runs: list[dict[str, Any]] = []
    probe_exports: list[dict[str, Any]] = []

    for sample in selected_samples:
        state_capture, original_eval, eval_module = _capture_runtime_evaluator_output()
        try:
            bundle, state, bundle_info = _build_bundle_and_state(
                sample=sample,
                clip_model=clip_model,
                projection=projection,
                dino_model=dino_model,
                dino_preprocess=dino_preprocess,
                device=device,
                split=split,
                mode_name=DEFAULT_MODE_NAME,
                config_path=DEFAULT_CONFIG_PATH,
                loss_condition=condition,
            )
        finally:
            _restore_runtime_evaluator_output(original_eval, eval_module)

        evaluator_output = state_capture["last"] or {}
        iou_values = _normalize_iou_values(evaluator_output.get("iou_by_part_class"))
        iou_stats = {
            "count": len(iou_values),
            "min": float(min(iou_values)) if iou_values else 0.0,
            "mean": float(sum(iou_values) / len(iou_values)) if iou_values else 0.0,
            "max": float(max(iou_values)) if iou_values else 0.0,
        }

        condition_result = run_attribution_condition(
            state=state,
            condition=condition,
            steps=0 if condition == "zero_loss" else 3,
            lr=0.05,
            mode_name=DEFAULT_MODE_NAME,
            config_path=DEFAULT_CONFIG_PATH,
            sample_limit=sample_budget,
            split=split,
        )

        sample_result = {
            "sample": bundle_info["sample"],
            "mechanism": {
                "loss_spec": condition_result["loss_spec"],
                "loss_trace": condition_result["loss_trace"],
                "final_losses": condition_result["final_losses"],
                "probe_payload": condition_result["probe_payload"],
                "param_deltas": condition_result["param_deltas"],
                "zero_loss_no_update": condition_result["zero_loss_no_update"],
                "update_applied": condition_result["update_applied"],
            },
            "result_metrics": {
                "grouped_metrics": _to_jsonable(condition_result["grouped_metrics"]),
                "grouped_metric_source": condition_result["grouped_metric_source"],
                "grouped_metric_keys": condition_result["grouped_metric_keys"],
                "compatibility": condition_result["compatibility"],
            },
            "evaluator_output": {
                "runtime_provenance": evaluator_output.get("runtime_provenance", {}),
                "iou_stats": iou_stats,
            },
            "bundle_provenance": {
                "evaluator_source": state.debug.get("formal_bundle_provenance", {}).get(
                    "evaluator_source", "not-yet-declared"
                ),
                "feature_source": state.debug.get("formal_bundle_provenance", {}).get(
                    "feature_source", "not-yet-declared"
                ),
                "support_source": state.debug.get("formal_bundle_provenance", {}).get(
                    "support_source", "not-yet-declared"
                ),
                "patch_feature_source": "dinov2",
                "delta_source": state.debug.get("delta_source", "Phi_o"),
                "visual_mapping_enabled": bool(state.debug.get("visual_mapping_enabled", False)),
                "dinov2_provenance": dino_provenance,
                "oracle_obj_source": oracle_obj_source,
            },
        }
        sample_runs.append(sample_result)
        if export_probes:
            probe_exports.append(
                {
                    "sample": sample_result["sample"],
                    "condition": condition,
                    "seed": int(seed),
                    "mechanism": sample_result["mechanism"],
                    "result_metrics": sample_result["result_metrics"],
                    "evaluator_output": sample_result["evaluator_output"],
                }
            )

    mechanism_metrics = _aggregate_mechanism_results(sample_runs)
    result_metrics = _aggregate_result_metrics(sample_runs)

    zero_loss_no_update = condition == "zero_loss" and all(
        bool(item["mechanism"]["zero_loss_no_update"]) for item in sample_runs
    )
    grouped_schema_keys = sample_runs[0]["result_metrics"]["grouped_metric_keys"]
    compatibility_ok = all(
        item["result_metrics"]["compatibility"]["metric_source"] == "pp116_official_evaluator_output"
        and item["result_metrics"]["compatibility"]["evaluator_source"] == "pp116_official_evaluator_output"
        for item in sample_runs
    )
    grouped_schema_unchanged = all(
        item["result_metrics"]["grouped_metric_keys"] == grouped_schema_keys for item in sample_runs
    )
    no_excluded_loss_activated = True
    all_conditions_passed = (
        bool(sample_runs)
        and compatibility_ok
        and grouped_schema_unchanged
        and no_excluded_loss_activated
        and (condition != "zero_loss" or zero_loss_no_update)
    )

    summary = {
        "run_id": DEFAULT_RUN_ID,
        "condition": condition,
        "seed": int(seed),
        "max_samples": int(max_samples),
        "effective_sample_budget": int(sample_budget),
        "selected_split": split,
        "oracle_obj_source": oracle_obj_source,
        "selected_sample_count": len(sample_runs),
        "all_conditions_passed": all_conditions_passed,
        "zero_loss_no_update": zero_loss_no_update,
        "grouped_metric_schema_unchanged": grouped_schema_unchanged,
        "compatibility_ok": compatibility_ok,
        "no_excluded_loss_activated": no_excluded_loss_activated,
        "weight_path": str(WEIGHT_PATH),
        "weight_sha256": WEIGHT_SHA256,
        "clip_cache_path": str(CLIP_CACHE_PATH),
        "dinov2_provenance": dino_provenance,
        "gpu_evidence": _gpu_evidence(device),
        "sample_ids": [sample["sample"] for sample in sample_runs],
        "sample_count": len(sample_runs),
    }

    artifact = {
        "generated_at": _ts(),
        "run_id": DEFAULT_RUN_ID,
        "experiment_id": "EXP-S2A-ORACLEOBJ-LOSS-MECHANISM-VALIDATION",
        "condition": condition,
        "seed": int(seed),
        "max_samples": int(max_samples),
        "effective_sample_budget": int(sample_budget),
        "pp116_split": split,
        "oracle_obj_source": oracle_obj_source,
        "mode_name": DEFAULT_MODE_NAME,
        "config_path": DEFAULT_CONFIG_PATH,
        "commands": {
            "runner": (
                "CUDA_VISIBLE_DEVICES=1,2 python tools/run_s2a_loss_mechanism_formal.py "
                f"--condition {condition} --seed {seed} --max_samples {max_samples} "
                f"--output_dir {output_dir}"
            )
        },
        "summary": summary,
        "sample_runs": sample_runs,
        "mechanism_metrics": mechanism_metrics,
        "result_metrics": result_metrics,
        "probe_exports": probe_exports if export_probes else [],
    }

    run_dir = _condition_result_dir(output_dir, int(seed), condition)
    run_dir.mkdir(parents=True, exist_ok=True)
    _write_json(run_dir / "run_summary.json", artifact["summary"])
    _write_json(run_dir / "mechanism_metrics.json", mechanism_metrics)
    _write_json(run_dir / "result_metrics.json", result_metrics)
    _write_json(run_dir / "artifact.json", artifact)
    if export_probes:
        _write_json(run_dir / "probe_exports.json", probe_exports)
    return artifact


def main() -> int:
    args = _build_arg_parser().parse_args()
    if args.condition not in DEFAULT_CONDITIONS:
        raise ValueError(f"unsupported loss condition: {args.condition}")
    device = _assert_gpu_binding(args.gpu_visible)
    _ = device  # explicit early gate check
    artifact = _run_single_condition(
        condition=args.condition,
        seed=int(args.seed),
        max_samples=int(args.max_samples),
        output_dir=Path(args.output_dir),
        split=str(args.pp116_split),
        oracle_obj_source=str(args.oracle_obj_source),
        export_probes=bool(args.export_probes),
        gpu_visible=str(args.gpu_visible),
    )
    print(json.dumps(_to_jsonable(artifact), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
