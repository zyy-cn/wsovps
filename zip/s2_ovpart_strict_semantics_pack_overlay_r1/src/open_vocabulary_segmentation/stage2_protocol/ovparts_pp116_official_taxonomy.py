from __future__ import annotations

"""OFFLINE OFFICIAL TAXONOMY (OV-PARTS Pascal-Part-116)

Source of truth: OV_PARTS baselines/data/datasets/register_pascal_part_116.py (CLASS_NAMES, len=116)
Mask label values: see OV_PARTS baselines/data/datasets/mask_cls_collect.py, which collects np.unique(mask) excluding ignore_label=255.
Therefore, class IDs are treated as the raw pixel values (excluding 255), and for PP116 parts they are 0-based indices into CLASS_NAMES.

This module exists to remove any inference-based part-id mapping.
"""

from typing import Dict, Tuple
import re

OFFICIAL_CLASS_NAMES = [
  "aeroplane's body",
  "aeroplane's stern",
  "aeroplane's wing",
  "aeroplane's tail",
  "aeroplane's engine",
  "aeroplane's wheel",
  "bicycle's wheel",
  "bicycle's saddle",
  "bicycle's handlebar",
  "bicycle's chainwheel",
  "bicycle's headlight",
  "bird's wing",
  "bird's tail",
  "bird's head",
  "bird's eye",
  "bird's beak",
  "bird's torso",
  "bird's neck",
  "bird's leg",
  "bird's foot",
  "bottle's body",
  "bottle's cap",
  "bus's wheel",
  "bus's headlight",
  "bus's front",
  "bus's side",
  "bus's back",
  "bus's roof",
  "bus's mirror",
  "bus's license plate",
  "bus's door",
  "bus's window",
  "car's wheel",
  "car's headlight",
  "car's front",
  "car's side",
  "car's back",
  "car's roof",
  "car's mirror",
  "car's license plate",
  "car's door",
  "car's window",
  "cat's tail",
  "cat's head",
  "cat's eye",
  "cat's torso",
  "cat's neck",
  "cat's leg",
  "cat's nose",
  "cat's paw",
  "cat's ear",
  "cow's tail",
  "cow's head",
  "cow's eye",
  "cow's torso",
  "cow's neck",
  "cow's leg",
  "cow's ear",
  "cow's muzzle",
  "cow's horn",
  "dog's tail",
  "dog's head",
  "dog's eye",
  "dog's torso",
  "dog's neck",
  "dog's leg",
  "dog's nose",
  "dog's paw",
  "dog's ear",
  "dog's muzzle",
  "horse's tail",
  "horse's head",
  "horse's eye",
  "horse's torso",
  "horse's neck",
  "horse's leg",
  "horse's ear",
  "horse's muzzle",
  "horse's hoof",
  "motorbike's wheel",
  "motorbike's saddle",
  "motorbike's handlebar",
  "motorbike's headlight",
  "person's head",
  "person's eye",
  "person's torso",
  "person's neck",
  "person's leg",
  "person's foot",
  "person's nose",
  "person's ear",
  "person's eyebrow",
  "person's mouth",
  "person's hair",
  "person's lower arm",
  "person's upper arm",
  "person's hand",
  "pottedplant's pot",
  "pottedplant's plant",
  "sheep's tail",
  "sheep's head",
  "sheep's eye",
  "sheep's torso",
  "sheep's neck",
  "sheep's leg",
  "sheep's ear",
  "sheep's muzzle",
  "sheep's horn",
  "train's headlight",
  "train's head",
  "train's front",
  "train's side",
  "train's back",
  "train's roof",
  "train's coach",
  "tvmonitor's screen"
]

def _norm_basic(t: str) -> str:
    t = (t or "").strip().lower()
    t = t.replace("'s", " ")
    t = t.replace("-", " ").replace("/", " ")
    t = re.sub(r"\s+", " ", t).strip()
    return t

def normalize_object_key(name: str) -> str:
    t = _norm_basic(name)
    aliases = {
        "airplane": "aeroplane",
        "tv monitor": "tvmonitor",
        "motor bike": "motorbike",
        "potted plant": "pottedplant",
    }
    t = aliases.get(t, t)
    return t.replace(" ", "_")

def normalize_part_key(name: str) -> str:
    t = _norm_basic(name)
    replacements = {
        "license plate": "license_plate",
        "lower arm": "lower_arm",
        "upper arm": "upper_arm",
        "chain wheel": "chainwheel",
        "head light": "headlight",
    }
    t = replacements.get(t, t)
    return t.replace(" ", "_")

OFFICIAL_OBJECT_PART_TO_CLASS_ID: Dict[Tuple[str, str], int] = {}
for cid, cname in enumerate(OFFICIAL_CLASS_NAMES):
    if "'s " in cname:
        obj, part = cname.split("'s ", 1)
    else:
        parts = cname.split()
        obj, part = parts[0], " ".join(parts[1:])
    ok = normalize_object_key(obj)
    pk = normalize_part_key(part)
    OFFICIAL_OBJECT_PART_TO_CLASS_ID[(ok, pk)] = int(cid)

def get_official_part_class_id(object_key: str, part_key: str) -> int:
    ok = normalize_object_key(object_key)
    pk = normalize_part_key(part_key)
    if (ok, pk) not in OFFICIAL_OBJECT_PART_TO_CLASS_ID:
        raise KeyError("no official PP116 class_id for object=%r part=%r" % (ok, pk))
    return OFFICIAL_OBJECT_PART_TO_CLASS_ID[(ok, pk)]
