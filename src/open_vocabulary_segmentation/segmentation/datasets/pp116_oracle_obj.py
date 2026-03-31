from __future__ import annotations

import json
import re
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

VOC_CATEGORY_ID_TO_OBJECT_KEY: dict[int, str] = {
    1: "aeroplane",
    2: "bicycle",
    3: "bird",
    5: "bottle",
    6: "bus",
    7: "car",
    8: "cat",
    10: "cow",
    12: "dog",
    13: "horse",
    14: "motorbike",
    15: "person",
    16: "pottedplant",
    17: "sheep",
    19: "train",
    20: "tvmonitor",
}


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
    key = VOC_CATEGORY_ID_TO_OBJECT_KEY.get(int(category_id))
    if key is None:
        raise ValueError(f"unsupported PP116 category_id for object-conditioned sample: {category_id}")
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

    samples: list[dict[str, Any]] = []
    for part_path in sorted(part_dir.glob("*.png")):
        if part_path.name.startswith("._"):
            continue
        stem = part_path.stem
        file_name = img_dir / f"{stem}.jpg"
        obj_sem_seg_file_name = obj_dir / f"{stem}.png"
        if not file_name.exists() or not obj_sem_seg_file_name.exists():
            continue
        obj_mask = np.array(Image.open(obj_sem_seg_file_name))
        category_ids = sorted(
            int(v) for v in np.unique(obj_mask) if int(v) not in {0, 255}
        )
        for category_id in category_ids:
            if category_id not in VOC_CATEGORY_ID_TO_OBJECT_KEY:
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
    }
