#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

import torch


def convert_one(in_json: Path, out_torch: Path) -> dict:
    payload = json.loads(in_json.read_text())
    images = [{"id": int(x["id"]), "file_name": str(x["file_name"])} for x in payload["images"]]
    annotations = [
        {"id": int(x["id"]), "image_id": int(x["image_id"]), "caption": str(x["caption"])}
        for x in payload["annotations"]
    ]
    out = {"images": images, "annotations": annotations}
    out_torch.parent.mkdir(parents=True, exist_ok=True)
    torch.save(out, out_torch)
    return {
        "images_json": len(payload["images"]),
        "annotations_json": len(payload["annotations"]),
        "images_torch": len(images),
        "annotations_torch": len(annotations),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--train-json", required=True)
    ap.add_argument("--val-json", required=True)
    ap.add_argument("--train-out", required=True)
    ap.add_argument("--val-out", required=True)
    args = ap.parse_args()

    train_stats = convert_one(Path(args.train_json), Path(args.train_out))
    val_stats = convert_one(Path(args.val_json), Path(args.val_out))
    print({"train": train_stats, "val": val_stats})


if __name__ == "__main__":
    main()
