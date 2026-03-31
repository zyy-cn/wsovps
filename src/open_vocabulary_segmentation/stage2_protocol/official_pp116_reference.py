from __future__ import annotations

from typing import Any, Iterable, Mapping

OFFICIAL_GROUPED_METRIC_KEYS = ("seen_miou", "unseen_miou", "harmonic_miou")


def to_display_percent(value: float) -> float:
    return float(value) * 100.0


def format_grouped_metrics_payload(
    raw_metrics: Mapping[str, float],
    *,
    keys: Iterable[str] = OFFICIAL_GROUPED_METRIC_KEYS,
) -> dict[str, dict[str, float]]:
    raw: dict[str, float] = {}
    display_percent: dict[str, float] = {}
    for key in keys:
        val = float(raw_metrics[key])
        raw[key] = val
        display_percent[key] = to_display_percent(val)
    return {
        "raw": raw,
        "display_percent": display_percent,
    }


def canonical_sibling_part_keys(
    object_class_key: str,
    sibling_part_keys: Iterable[str],
) -> list[str]:
    keys = [str(k).strip() for k in sibling_part_keys if str(k).strip()]
    if not keys:
        raise ValueError(f"no sibling_part_keys provided for object_class_key={object_class_key!r}")
    return sorted(set(keys))


def align_iou_by_part_class_to_siblings(
    iou_by_part_class: Mapping[Any, float],
    *,
    object_class_key: str,
    sibling_part_keys: Iterable[str],
) -> dict[tuple[str, str], float]:
    canonical_parts = canonical_sibling_part_keys(
        object_class_key=object_class_key,
        sibling_part_keys=sibling_part_keys,
    )
    canonical_set = set(canonical_parts)
    aligned: dict[tuple[str, str], float] = {}
    for raw_key, value in iou_by_part_class.items():
        if isinstance(raw_key, tuple) and len(raw_key) == 2:
            obj_key = str(raw_key[0])
            part_key = str(raw_key[1])
        elif isinstance(raw_key, str) and "::" in raw_key:
            obj_key, part_key = raw_key.split("::", 1)
        else:
            continue
        if obj_key != object_class_key:
            continue
        if part_key not in canonical_set:
            continue
        aligned[(obj_key, part_key)] = float(value)

    missing = [part_key for part_key in canonical_parts if (object_class_key, part_key) not in aligned]
    if missing:
        raise ValueError(
            "formal evaluator output missing sibling-part keys for "
            f"{object_class_key!r}: {missing}"
        )
    return aligned
