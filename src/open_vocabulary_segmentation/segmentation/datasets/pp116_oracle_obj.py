from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from open_vocabulary_segmentation.stage2_protocol.pp116_binding import (
    PP116_FORMAL_INPUTS_BUNDLE_CONTRACT,
    PP116_PROTOCOL_ID,
    build_pp116_protocol_descriptor,
)
from open_vocabulary_segmentation.stage2_protocol.official_pp116_reference import (
    canonical_sibling_part_keys,
)


PP116_SEEN_OBJECTS = (
    "aeroplane",
    "bicycle",
    "bottle",
    "bus",
    "cat",
    "cow",
    "horse",
    "person",
    "pottedplant",
    "train",
    "tvmonitor",
)

PP116_UNSEEN_OBJECTS = (
    "bird",
    "car",
    "dog",
    "motorbike",
    "sheep",
)

PP116_PARTS_BY_OBJECT: dict[str, tuple[str, ...]] = {
    "aeroplane": ("body", "stern", "wing", "tail", "engine", "wheel"),
    "bicycle": ("wheel", "saddle", "handlebar", "chainwheel", "headlight"),
    "bird": ("wing", "tail", "head", "eye", "beak", "torso", "neck", "leg", "foot"),
    "bottle": ("body", "cap"),
    "bus": ("wheel", "headlight", "front", "side", "back", "roof", "mirror", "license_plate", "door", "window"),
    "car": ("wheel", "headlight", "front", "side", "back", "roof", "mirror", "license_plate", "door", "window"),
    "cat": ("tail", "head", "eye", "torso", "neck", "leg", "nose", "paw", "ear"),
    "cow": ("tail", "head", "eye", "torso", "neck", "leg", "ear", "muzzle", "horn"),
    "dog": ("tail", "head", "eye", "torso", "neck", "leg", "nose", "paw", "ear", "muzzle"),
    "horse": ("tail", "head", "eye", "torso", "neck", "leg", "ear", "muzzle", "hoof"),
    "motorbike": ("wheel", "saddle", "handlebar", "headlight"),
    "person": ("head", "eye", "torso", "neck", "leg", "foot", "nose", "ear", "eyebrow", "mouth", "hair", "lower_arm", "upper_arm", "hand"),
    "pottedplant": ("pot", "plant"),
    "sheep": ("tail", "head", "eye", "torso", "neck", "leg", "ear", "muzzle", "horn"),
    "train": ("headlight", "head", "front", "side", "back", "roof", "coach"),
    "tvmonitor": ("screen",),
}

OBJ_CLASS_NAMES: tuple[str, ...] = (
    "aeroplane",
    "bicycle",
    "bird",
    "boat",
    "bottle",
    "bus",
    "car",
    "cat",
    "chair",
    "cow",
    "diningtable",
    "dog",
    "horse",
    "motorbike",
    "person",
    "pottedplant",
    "sheep",
    "sofa",
    "train",
    "tvmonitor",
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _candidate_roots() -> tuple[Path, ...]:
    root = _repo_root()
    return (
        root / "Datasets" / "Pascal-Part-116",
        root / "datasets" / "Pascal-Part-116",
        root / "data" / "pascal_part116",
        root / "data" / "Pascal-Part-116",
    )


def _required_dirs(dataset_root: Path) -> dict[str, Path]:
    return {
        "images_train": dataset_root / "images" / "train",
        "images_val": dataset_root / "images" / "val",
        "obj_train": dataset_root / "annotations_detectron2_obj" / "train",
        "obj_val": dataset_root / "annotations_detectron2_obj" / "val",
        "part_train": dataset_root / "annotations_detectron2_part" / "train",
        "part_val": dataset_root / "annotations_detectron2_part" / "val",
    }


def _discover_pp116_data_root() -> Path:
    for candidate in _candidate_roots():
        if not candidate.exists():
            continue
        required = _required_dirs(candidate)
        missing = [name for name, path in required.items() if not path.exists()]
        if missing:
            raise FileNotFoundError(
                "PP116 root exists but required subdirectories are missing: "
                f"{candidate} missing {missing}"
            )
        return candidate
    raise FileNotFoundError(
        "No local official Pascal-Part-116 asset found. Expected one of: "
        + ", ".join(str(p) for p in _candidate_roots())
    )


def _sample_json_files(dataset_root: Path) -> dict[str, Path | None]:
    required = _required_dirs(dataset_root)
    out: dict[str, Path | None] = {}
    for key in ("obj_train", "obj_val", "part_train", "part_val"):
        files = sorted(required[key].glob("*.json"))
        out[key] = files[0] if files else None
    return out


def _official_mapping_path() -> Path:
    return (
        _repo_root()
        / "docs/mainline/designs/GATE_S2/DP-S2-OVPART-STRICT-SEMANTICS-R1"
        / "OFFICIAL_PP116_OBJECT_PART_TO_CLASS_ID.json"
    )


@lru_cache(maxsize=1)
def _load_official_object_part_to_class_id() -> dict[str, int]:
    mapping_path = _official_mapping_path()
    if not mapping_path.exists():
        raise FileNotFoundError(f"official PP116 mapping JSON missing: {mapping_path}")
    payload = json.loads(mapping_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("official PP116 mapping JSON must be an object")
    return {str(key): int(value) for key, value in payload.items()}


def _obj_label_count_path(part_split_dir: Path) -> Path:
    return part_split_dir.parent / f"{part_split_dir.name}_obj_label_count.json"


def _generate_obj_label_count_json(
    *,
    obj_split_dir: Path,
    output_path: Path,
) -> dict[str, list[int]]:
    payload: dict[str, list[int]] = {}
    for mask_path in sorted(obj_split_dir.glob("*.png")):
        if mask_path.name.startswith("._"):
            continue
        mask = np.array(Image.open(mask_path))
        labels = sorted(int(value) for value in np.unique(mask) if int(value) != 255)
        payload[mask_path.name] = labels
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return payload


def _load_or_generate_obj_label_count(
    *,
    part_split_dir: Path,
    obj_split_dir: Path,
) -> dict[str, list[int]]:
    label_count_path = _obj_label_count_path(part_split_dir)
    if label_count_path.exists():
        payload = json.loads(label_count_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError(f"obj label-count JSON must be an object: {label_count_path}")
        return {
            str(key): [int(value) for value in values]
            for key, values in payload.items()
            if isinstance(values, list)
        }
    return _generate_obj_label_count_json(obj_split_dir=obj_split_dir, output_path=label_count_path)


def _decode_object_key(category_id: int, *, mode: str) -> str | None:
    index = int(category_id) if mode == "zero_based" else int(category_id) - 1
    if index < 0 or index >= len(OBJ_CLASS_NAMES):
        return None
    return OBJ_CLASS_NAMES[index]


def _score_decode_mode(
    *,
    dataset_root: Path,
    split: str,
    mode: str,
) -> tuple[int, int]:
    part_split_dir = dataset_root / "annotations_detectron2_part" / split
    obj_split_dir = dataset_root / "annotations_detectron2_obj" / split
    label_count = _load_or_generate_obj_label_count(
        part_split_dir=part_split_dir,
        obj_split_dir=obj_split_dir,
    )
    official_mapping = _load_official_object_part_to_class_id()
    hits = 0
    evaluated = 0
    for part_path in sorted(part_split_dir.glob("*.png")):
        if part_path.name.startswith("._"):
            continue
        cats = label_count.get(part_path.name, [])
        if not cats:
            continue
        obj_path = obj_split_dir / part_path.name
        if not obj_path.exists():
            continue
        part_mask = np.array(Image.open(part_path))
        obj_mask = np.array(Image.open(obj_path))
        for category_id in cats:
            object_key = _decode_object_key(category_id, mode=mode)
            if object_key is None or object_key not in PP116_PARTS_BY_OBJECT:
                continue
            support_region = obj_mask == int(category_id)
            if not bool(np.any(support_region)):
                continue
            gt_labels = {
                int(value)
                for value in np.unique(part_mask[support_region])
                if int(value) != 255
            }
            expected_part_ids = {
                official_mapping[f"{object_key}::{part_key}"]
                for part_key in PP116_PARTS_BY_OBJECT[object_key]
                if f"{object_key}::{part_key}" in official_mapping
            }
            if not expected_part_ids:
                continue
            evaluated += 1
            if gt_labels & expected_part_ids:
                hits += 1
    return hits, evaluated


@lru_cache(maxsize=1)
def _resolve_pp116_category_decode_mode() -> str:
    dataset_root = _discover_pp116_data_root()
    scores = {
        mode: _score_decode_mode(dataset_root=dataset_root, split="val", mode=mode)
        for mode in ("zero_based", "one_based")
    }
    zero_hits, zero_eval = scores["zero_based"]
    one_hits, one_eval = scores["one_based"]
    if zero_hits > one_hits and zero_hits > 0:
        return "zero_based"
    if one_hits > zero_hits and one_hits > 0:
        return "one_based"
    if zero_hits == one_hits == 0:
        raise RuntimeError(
            "unable to resolve PP116 category decode convention: both zero_based and "
            f"one_based yielded zero intersections; scores={scores}"
        )
    raise RuntimeError(
        "ambiguous PP116 category decode convention; expected a unique winner "
        f"between zero_based and one_based, got scores={scores}"
    )


def _summarize_coco_like_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    summary: dict[str, Any] = {
        "path": str(path),
        "top_level_type": type(data).__name__,
    }
    if isinstance(data, dict):
        summary["top_keys"] = sorted(data.keys())
        for key in ("images", "annotations", "categories"):
            value = data.get(key)
            if isinstance(value, list):
                summary[f"{key}_len"] = len(value)
                if value and isinstance(value[0], dict):
                    summary[f"{key}_sample_keys"] = sorted(value[0].keys())
    elif isinstance(data, list):
        summary["list_len"] = len(data)
        if data and isinstance(data[0], dict):
            summary["sample_keys"] = sorted(data[0].keys())
    return summary


def _basic_normalize(text: str) -> str:
    t = text.strip().lower()
    t = t.replace("'s", " ")
    t = t.replace("-", " ").replace("/", " ")
    t = re.sub(r"\s+", " ", t).strip()
    return t


def normalize_object_name(name: str) -> str:
    t = _basic_normalize(name)
    aliases = {
        "airplane": "aeroplane",
        "tv monitor": "tvmonitor",
        "motor bike": "motorbike",
        "potted plant": "pottedplant",
    }
    if t in aliases:
        return aliases[t]
    return t.replace(" ", "_")


def normalize_part_name(name: str) -> str:
    t = _basic_normalize(name)
    replacements = {
        "license plate": "license_plate",
        "lower arm": "lower_arm",
        "upper arm": "upper_arm",
        "chain wheel": "chainwheel",
        "head light": "headlight",
    }
    t = replacements.get(t, t)
    directional_tokens = {"left", "right", "front", "back", "upper", "lower"}
    tokens = [tok for tok in t.split() if tok not in directional_tokens]
    t = "_".join(tokens)
    t = t.replace("__", "_").strip("_")
    if t == "license":
        t = "license_plate"
    return t


def get_pp116_oracle_obj_protocol_descriptor():
    """Return the Stage-2 descriptor for PP116 Oracle-Obj."""
    return build_pp116_protocol_descriptor()


def get_pp116_oracle_obj_dataset_entrypoint() -> str:
    """Return the canonical dataset adapter entrypoint for protocol routing."""
    return f"{__name__}:get_pp116_oracle_obj_protocol_descriptor"


def get_pp116_canonical_sibling_part_keys(object_class_key: str) -> list[str]:
    parts = PP116_PARTS_BY_OBJECT.get(object_class_key, ())
    return canonical_sibling_part_keys(object_class_key, parts)


def get_pp116_object_key_from_category_id(category_id: int) -> str:
    mode = _resolve_pp116_category_decode_mode()
    key = _decode_object_key(int(category_id), mode=mode)
    if key is None or key not in PP116_PARTS_BY_OBJECT:
        raise ValueError(
            "unsupported PP116 category_id for object-conditioned sample: "
            f"{category_id} under mode={mode}"
        )
    return key


def build_pp116_official_object_conditioned_samples(
    *,
    split: str = "val",
    limit: int | None = None,
) -> list[dict[str, Any]]:
    data_root = _discover_pp116_data_root()
    img_dir = data_root / "images" / split
    part_dir = data_root / "annotations_detectron2_part" / split
    obj_dir = data_root / "annotations_detectron2_obj" / split
    label_count = _load_or_generate_obj_label_count(
        part_split_dir=part_dir,
        obj_split_dir=obj_dir,
    )

    samples: list[dict[str, Any]] = []
    for part_path in sorted(part_dir.glob("*.png")):
        if part_path.name.startswith("._"):
            continue
        stem = part_path.stem
        file_name = img_dir / f"{stem}.jpg"
        obj_sem_seg_file_name = obj_dir / f"{stem}.png"
        if not file_name.exists() or not obj_sem_seg_file_name.exists():
            continue
        category_ids = [int(v) for v in label_count.get(part_path.name, [])]
        for category_id in category_ids:
            try:
                get_pp116_object_key_from_category_id(category_id)
            except ValueError:
                continue
            samples.append(
                {
                    "file_name": str(file_name),
                    "sem_seg_file_name": str(part_path),
                    "obj_sem_seg_file_name": str(obj_sem_seg_file_name),
                    "category_id": int(category_id),
                }
            )
            if limit is not None and len(samples) >= limit:
                return samples
    return samples


def get_pp116_oracle_obj_dataset_metadata() -> dict[str, Any]:
    descriptor = build_pp116_protocol_descriptor()
    data_root = _discover_pp116_data_root()
    required = _required_dirs(data_root)
    sample_jsons = _sample_json_files(data_root)
    schema_summary: dict[str, Any] = {}
    for name, path in sample_jsons.items():
        schema_summary[name] = (
            _summarize_coco_like_json(path) if path is not None else {"error": "no_json_found"}
        )

    return {
        "protocol_id": PP116_PROTOCOL_ID,
        "dataset_family": descriptor.dataset_family,
        "dataset_entrypoint": get_pp116_oracle_obj_dataset_entrypoint(),
        "support_mode": descriptor.support_spec.support_mode,
        "support_granularity": descriptor.support_spec.support_granularity,
        "split_id": descriptor.support_spec.split_id,
        "taxonomy_scope": descriptor.support_spec.taxonomy_scope,
        "notes": descriptor.notes,
        "formal_inputs_bundle_contract": PP116_FORMAL_INPUTS_BUNDLE_CONTRACT,
        "data_root": str(data_root),
        "image_split_dirs": {
            "train": str(required["images_train"]),
            "val": str(required["images_val"]),
        },
        "obj_ann_split_dirs": {
            "train": str(required["obj_train"]),
            "val": str(required["obj_val"]),
        },
        "part_ann_split_dirs": {
            "train": str(required["part_train"]),
            "val": str(required["part_val"]),
        },
        "seen_objects": list(PP116_SEEN_OBJECTS),
        "unseen_objects": list(PP116_UNSEEN_OBJECTS),
        "parts_by_object": {k: list(v) for k, v in PP116_PARTS_BY_OBJECT.items()},
        "canonical_sibling_part_keys_by_object": {
            k: get_pp116_canonical_sibling_part_keys(k) for k in PP116_PARTS_BY_OBJECT
        },
        "schema_summary": schema_summary,
        "normalization_rules": {
            "object": "lowercase, strip possessive, normalize aliases, replace spaces with underscore",
            "part": "lowercase, alias replacements, remove directional tokens, underscore join",
        },
        "official_sample_fields": [
            "file_name",
            "sem_seg_file_name",
            "obj_sem_seg_file_name",
            "category_id",
        ],
        "official_object_conditioned_sample_preview": build_pp116_official_object_conditioned_samples(
            split="val",
            limit=1,
        ),
        "category_decode_mode": _resolve_pp116_category_decode_mode(),
        "obj_label_count_paths": {
            "train": str(
                _obj_label_count_path(data_root / "annotations_detectron2_part" / "train")
            ),
            "val": str(
                _obj_label_count_path(data_root / "annotations_detectron2_part" / "val")
            ),
        },
    }
