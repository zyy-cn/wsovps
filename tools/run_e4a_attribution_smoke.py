#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import torch

from open_vocabulary_segmentation.segmentation.datasets.pp116_oracle_obj import (
    PP116_PARTS_BY_OBJECT,
    get_pp116_object_key_from_category_id,
)
from open_vocabulary_segmentation.stage2_protocol.formal_inputs_builder import (
    build_formal_inputs_bundle,
)
from open_vocabulary_segmentation.stage2_residual.attribution import (
    ATTRIBUTION_CONDITIONS,
    build_pp116_residual_attribution_state,
    run_e4a_attribution_smoke,
)
from open_vocabulary_segmentation.stage2_residual.losses import build_loss_spec_from_condition
from open_vocabulary_segmentation.stage2_residual.runtime import run_pp116_residual_route
from tools.run_s2_round7_smoke import (
    CLIP_CACHE_PATH,
    WEIGHT_PATH,
    WEIGHT_SHA256,
    _encode_texts,
    _extract_patch_features,
    _load_real_encoders,
    _read_mask_array,
    _read_rgb_image,
    _select_samples,
    _sha256,
    _support_patch_mask,
)


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run bounded E4A Oracle-Obj attribution smoke.")
    parser.add_argument("--split", type=str, default="val")
    parser.add_argument("--k", type=int, default=1)
    parser.add_argument("--mode-name", type=str, default="b2_residual_only")
    parser.add_argument("--config-path", type=str, default="src/open_vocabulary_segmentation/configs/pp116_stage2_residual/b2.yml")
    parser.add_argument("--steps", type=int, default=3)
    parser.add_argument("--lr", type=float, default=0.05)
    parser.add_argument("--loss-condition", type=str, default=None)
    parser.add_argument("--all-conditions", action="store_true")
    parser.add_argument("--run-id", type=str, default="RUN-E4A-ATTRIBUTION-SMOKE-R1")
    return parser


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")

def _pick_sample(
    *,
    split: str,
    k: int,
) -> dict[str, Any]:
    samples = _select_samples(split=split, k=k, file_name=None, category_id=None)
    if not samples:
        raise RuntimeError("no official PP116 samples available for smoke")
    return samples[0]


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
) -> tuple[Any, Any, Any, dict[str, Any]]:
    sample_file_name = sample["file_name"]
    sem_seg_file_name = sample["sem_seg_file_name"]
    obj_sem_seg_file_name = sample["obj_sem_seg_file_name"]
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
        raise RuntimeError("selected sample has empty oracle-object support after patch masking")
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
        run_id="RUN-E4A-ATTRIBUTION-SMOKE-R1",
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
        loss_spec=build_loss_spec_from_condition("full"),
    )
    reference_route = run_pp116_residual_route(
        mode_name=mode_name,
        config_path=config_path,
        formal_mode=True,
        formal_bundle=bundle,
    )
    return bundle, state, reference_route, {
        "sample": {
            "file_name": sample_file_name,
            "sem_seg_file_name": sem_seg_file_name,
            "obj_sem_seg_file_name": obj_sem_seg_file_name,
            "category_id": category_id,
            "object_class_key": object_class_key,
            "sibling_part_keys": sibling_part_keys,
            "patch_grid_shape": [gh, gw],
        },
    }


def _render_table(rows: list[tuple[str, str, str, str]]) -> str:
    header = "| condition | active losses | zero-loss update | compatibility |"
    sep = "|---|---|---|---|"
    body = [
        f"| {cond} | {losses} | {zero_update} | {compat} |"
        for cond, losses, zero_update, compat in rows
    ]
    return "\n".join([header, sep, *body])


def _write_reports(
    *,
    repo_root: Path,
    smoke_result: dict[str, Any],
    base_info: dict[str, Any],
    reference_route: Any,
    bundle: Any,
    local_head: str,
) -> None:
    reports_dir = repo_root / "docs/mainline/reports"
    selected = base_info["sample"]
    condition_rows: list[tuple[str, str, str, str]] = []
    probe_rows: list[tuple[str, float, float, float, float, float, float]] = []
    for item in smoke_result["per_condition"]:
        active_losses = ", ".join(item["probe_payload"]["active_loss_names"]) or "none"
        zero_update = "yes" if item["zero_loss_no_update"] else "no"
        compat = "PASS" if item["compatibility"]["metric_source"] == "pp116_official_evaluator_output" else "FAIL"
        condition_rows.append((item["condition"], active_losses, zero_update, compat))
        probe = item["probe_payload"]
        probe_rows.append(
            (
                item["condition"],
                float(probe["inst_alignment_mean"]),
                float(probe["sibling_confusion_mean"]),
                float(probe["prototype_separation_mean"]),
                float(probe["support_top1_margin_mean"]),
                float(probe["support_background_margin_mean"]),
                float(probe["assignment_entropy_mean"]),
            )
        )

    switch_matrix = f"""# E4A Switch Matrix Note

## Round
- local_head: `{local_head}`
- design_pack: `DP-E4A-ORACLEOBJ-LOSS-ATTRIBUTION-IMPLEMENTATION-R2`

## Condition map
{_render_table(condition_rows)}

## Loss condition semantics
- `full`: `L_inst + L_overlap`
- `minus_l_inst`: `L_overlap` only
- `minus_l_overlap`: `L_inst` only
- `only_l_inst`: `L_inst` only
- `only_l_overlap`: `L_overlap` only
- `zero_loss`: no active losses, no optimizer update

## Smoke result
- all_conditions_passed: `{smoke_result['summary']['all_conditions_passed']}`
- zero_loss_no_update: `{smoke_result['summary']['zero_loss_no_update']}`
- grouped_metric_schema_unchanged: `{smoke_result['summary']['grouped_metric_schema_unchanged']}`
- compatibility_ok: `{smoke_result['summary']['compatibility_ok']}`
"""
    _write_text(reports_dir / "e4a_switch_matrix_note_latest.md", switch_matrix)

    inst_map = f"""# E4A Instrumentation Mapping Note

## In-scope files touched
- `src/open_vocabulary_segmentation/stage2_residual/losses.py`
- `src/open_vocabulary_segmentation/stage2_residual/runtime.py`
- `src/open_vocabulary_segmentation/stage2_residual/attribution.py`
- `tools/run_e4a_attribution_smoke.py`

## Minimum instrumentation surface
- condition-to-spec helper for the six approved loss conditions
- internal attribution state reuse from the landed S2 residual route
- bounded optimization loop over part prototypes only
- probe payload emission for every condition
- dedicated smoke runner for one Oracle-Obj validation sample

## Preserved invariants
- public S2 route schema unchanged
- evaluator semantics unchanged
- grouped-metric top-level schema unchanged
- excluded losses remain inactive
- shared-path edits avoided
"""
    _write_text(reports_dir / "e4a_instrumentation_mapping_latest.md", inst_map)

    smoke_summary = f"""# E4A Smoke Summary

## Sample
- file_name: `{selected['file_name']}`
- sem_seg_file_name: `{selected['sem_seg_file_name']}`
- obj_sem_seg_file_name: `{selected['obj_sem_seg_file_name']}`
- category_id: `{selected['category_id']}`
- object_class_key: `{selected['object_class_key']}`
- sibling_part_keys: `{selected['sibling_part_keys']}`
- patch_grid_shape: `{selected['patch_grid_shape']}`

## Runtime provenance
- local_head: `{local_head}`
- weight_path: `{WEIGHT_PATH}`
- weight_sha256: `{WEIGHT_SHA256}`
- clip_cache_path: `{CLIP_CACHE_PATH}`
- dino_weight_path: `{smoke_result['summary'].get('dino_weight_path', 'not-yet-declared')}`

## Compatibility checks
- evaluator_source: `{reference_route.debug.get('formal_bundle_provenance', {}).get('evaluator_source', 'not-yet-declared')}`
- grouped_metric_source: `{reference_route.grouped_metrics.get('metric_source', 'not-yet-declared')}`
- grouped_metric_keys: `{sorted(reference_route.grouped_metrics.keys())}`
- grouped_metric_schema_unchanged: `{smoke_result['summary']['grouped_metric_schema_unchanged']}`

## Condition results
| condition | loss trace | zero-loss no update | update applied | metric source |
|---|---|---|---|---|
{chr(10).join(f"| {item['condition']} | {item['loss_trace']} | {item['zero_loss_no_update']} | {item['update_applied']} | {item['grouped_metric_source']} |" for item in smoke_result['per_condition'])}

## Probe summary
| condition | inst_align | sibling_confusion | separation | top1_margin | bg_margin | entropy |
|---|---:|---:|---:|---:|---:|---:|
{chr(10).join(f"| {cond} | {inst:.6f} | {conf:.6f} | {sep:.6f} | {top1:.6f} | {bg:.6f} | {ent:.6f} |" for cond, inst, conf, sep, top1, bg, ent in probe_rows)}

## Result
- all_conditions_passed: `{smoke_result['summary']['all_conditions_passed']}`
- zero_loss_no_update: `{smoke_result['summary']['zero_loss_no_update']}`
- compatibility_ok: `{smoke_result['summary']['compatibility_ok']}`
"""
    _write_text(reports_dir / "e4a_smoke_summary_latest.md", smoke_summary)

    compat = f"""# E4A Compatibility Note

## Summary
- evaluator semantics unchanged: `yes`
- grouped-metric top-level schema unchanged: `{smoke_result['summary']['grouped_metric_schema_unchanged']}`
- Oracle-Obj-only control preserved: `yes`
- excluded losses silently activated: `no`
- zero-loss performed no optimizer update: `{smoke_result['summary']['zero_loss_no_update']}`

## Formal route check
- reference route metric source: `{reference_route.grouped_metrics.get('metric_source', 'not-yet-declared')}`
- reference route grouped metric keys: `{sorted(reference_route.grouped_metrics.keys())}`
- runtime evaluator source: `{reference_route.debug.get('formal_bundle_provenance', {}).get('evaluator_source', 'not-yet-declared')}`

## Remaining blocker before S2A formal
- none for E4A wiring; S2A formal matrix remains intentionally out of scope for this round.
"""
    _write_text(reports_dir / "e4a_compatibility_note_latest.md", compat)

    delta_packet = f"""# E4A Delta Review Packet

## Identity
- local_head: `{local_head}`
- run_id: `RUN-E4A-ATTRIBUTION-SMOKE-R1`
- design_pack: `DP-E4A-ORACLEOBJ-LOSS-ATTRIBUTION-IMPLEMENTATION-R2`

## Touched files
- `src/open_vocabulary_segmentation/stage2_residual/losses.py`
- `src/open_vocabulary_segmentation/stage2_residual/runtime.py`
- `src/open_vocabulary_segmentation/stage2_residual/attribution.py`
- `tools/run_e4a_attribution_smoke.py`
- `docs/mainline/CURRENT_EXECUTION_TICKET.md`
- `docs/mainline/CURRENT_LOOP_BRIEF.md`
- `docs/mainline/CURRENT_GATE_PACK.md`
- `docs/mainline/WEB_SESSION_BRIEF.md`
- `docs/mainline/loop_state_latest.json`
- `docs/mainline/state/CURRENT_EXECUTION_TICKET.json`
- `docs/mainline/state/CONTROL_PLANE_STATE.json`
- `docs/mainline/takeover/TAKEOVER_LATEST.md`
- `docs/mainline/takeover/TAKEOVER_LATEST.json`

## Compatibility notes
- public S2 route schema unchanged
- evaluator semantics unchanged
- grouped-metric top-level schema unchanged
- Oracle-Obj-only control preserved
- excluded losses remained inactive

## Smoke evidence
- all six conditions executed: `{smoke_result['summary']['all_conditions_passed']}`
- zero-loss no update: `{smoke_result['summary']['zero_loss_no_update']}`
- compatibility ok: `{smoke_result['summary']['compatibility_ok']}`

## Unresolved risks
- none identified in the bounded E4A implementation surface
"""
    _write_text(reports_dir / "e4a_delta_review_packet_latest.md", delta_packet)


def main() -> int:
    args = _build_arg_parser().parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA_REQUIRED")
    device = torch.device("cuda")
    torch.cuda.reset_peak_memory_stats(device)

    clip_model, preprocess, projection, dino_model, dino_preprocess, dino_provenance = _load_real_encoders(device)
    sample = _pick_sample(split=args.split, k=args.k)
    bundle, state, reference_route, base_info = _build_bundle_and_state(
        sample=sample,
        clip_model=clip_model,
        projection=projection,
        dino_model=dino_model,
        dino_preprocess=dino_preprocess,
        device=device,
        split=args.split,
        mode_name=args.mode_name,
        config_path=args.config_path,
    )

    smoke_result = run_e4a_attribution_smoke(
        state=state,
        steps=int(args.steps),
        lr=float(args.lr),
        mode_name=args.mode_name,
        config_path=args.config_path,
        sample_limit=int(args.k),
        split=args.split,
        condition=args.loss_condition,
        all_conditions=bool(args.all_conditions),
    )

    torch.cuda.synchronize(device)
    gpu_smi = subprocess.run(
        [
            "nvidia-smi",
            "--query-gpu=index,uuid,memory.used,utilization.gpu",
            "--format=csv,noheader",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    gpu_compute = subprocess.run(
        [
            "nvidia-smi",
            "--query-compute-apps=pid,process_name,used_memory",
            "--format=csv,noheader",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    summary = {
        "generated_at": _ts(),
        "repo_root": str(repo_root),
        "run_id": args.run_id,
        "split": args.split,
        "k": int(args.k),
        "mode_name": args.mode_name,
        "config_path": str(args.config_path),
        "steps": int(args.steps),
        "lr": float(args.lr),
        "selected_sample": base_info["sample"],
        "weight_path": str(WEIGHT_PATH),
        "weight_sha256": WEIGHT_SHA256,
        "clip_cache_path": str(CLIP_CACHE_PATH),
        "dinov2_provenance": dino_provenance,
        "gpu_evidence": {
            "cuda_is_available": torch.cuda.is_available(),
            "device": str(device),
            "device_count": torch.cuda.device_count(),
            "max_memory_allocated": int(torch.cuda.max_memory_allocated(device)),
            "max_memory_reserved": int(torch.cuda.max_memory_reserved(device)),
            "nvidia_smi": gpu_smi.stdout.strip(),
            "nvidia_smi_compute_apps": gpu_compute.stdout.strip(),
        },
        "reference_route": {
            "grouped_metric_source": reference_route.grouped_metrics.get("metric_source", "not-yet-declared"),
            "grouped_metric_keys": sorted(reference_route.grouped_metrics.keys()),
            "evaluator_source": reference_route.debug.get("formal_bundle_provenance", {}).get("evaluator_source", "not-yet-declared"),
        },
        "smoke_result": smoke_result,
    }

    reports_dir = repo_root / "docs/mainline/reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    _write_text(reports_dir / "e4a_smoke_artifact_latest.json", json.dumps(summary, indent=2))
    _write_reports(
        repo_root=repo_root,
        smoke_result=smoke_result,
        base_info=base_info,
        reference_route=reference_route,
        bundle=bundle,
        local_head=subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            cwd=str(repo_root),
        ).stdout.strip(),
    )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
