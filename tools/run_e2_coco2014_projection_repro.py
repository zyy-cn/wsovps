#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
import re
import shlex
import subprocess
from pathlib import Path


def run_cmd(cmd, cwd, env=None, log_path=None):
    env_full = os.environ.copy()
    if env:
        env_full.update(env)
    p = subprocess.run(cmd, cwd=cwd, env=env_full, text=True, capture_output=True)
    if log_path:
        Path(log_path).parent.mkdir(parents=True, exist_ok=True)
        Path(log_path).write_text(f"$ {' '.join(cmd)}\n\nSTDOUT:\n{p.stdout}\n\nSTDERR:\n{p.stderr}\n")
    return p


def py_conda_cmd(*py_args, cuda_visible_devices="3"):
    script = "source /home/zyy/software/miniconda3/etc/profile.d/conda.sh && "
    script += "CUDA_VISIBLE_DEVICES=" + shlex.quote(cuda_visible_devices) + " "
    script += "conda run -n wsovps python " + shlex.join([str(a) for a in py_args])
    return ["bash", "-lc", script]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def find_dino_weight() -> Path | None:
    roots = [Path("/mnt/sda/zyy/code/wsovps/weights"), Path("/mnt/sda/zyy/weight"), Path("/mnt/sda/zyy/dataset")]
    pats = ["*dinov2*vitb14*reg*.pth", "*dinov2*vitb14*reg*.pt"]
    cands = []
    for r in roots:
        if not r.exists():
            continue
        for pat in pats:
            cands.extend([p for p in r.rglob(pat) if p.is_file()])
    cands = sorted(set(cands))
    return cands[0] if cands else None


def parse_failed_extract(log_text: str):
    m = re.search(r"Failed to extract (\d+) of (\d+)", log_text)
    if not m:
        return None, None
    return int(m.group(1)), int(m.group(2))


def parse_cuda_mem(log_text: str):
    m = re.search(r"CUDA max memory allocated bytes:\s*(\d+)", log_text)
    return int(m.group(1)) if m else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", default="/mnt/sda/zyy/code/wsovps")
    ap.add_argument("--batch-size-dino", type=int, default=64)
    ap.add_argument("--batch-size-text", type=int, default=256)
    ap.add_argument("--cuda-visible-devices", default="3")
    ap.add_argument(
        "--resume-from",
        choices=["convert", "dino_train", "dino_val", "text", "train"],
        default=None,
        help="Resume from a later stage after a previous failure.",
    )
    args = ap.parse_args()

    repo = Path(args.repo_root)
    logs = repo / "docs/mainline/reports/e2_repro_logs"
    out = {"status": "unknown", "checks": {}, "artifacts": {}, "logs": {}}
    stage_index = {"convert": 0, "dino_train": 1, "dino_val": 2, "text": 3, "train": 4}
    resume_idx = stage_index[args.resume_from] if args.resume_from else 0
    out["checks"]["cuda_visible_devices_target"] = args.cuda_visible_devices
    out["checks"]["resume_from"] = args.resume_from

    # B0 dataset checks
    required = [
        repo / "data/coco2014/train2014",
        repo / "data/coco2014/val2014",
        repo / "data/coco2014/annotations/captions_train2014.json",
        repo / "data/coco2014/annotations/captions_val2014.json",
    ]
    out["checks"]["v0_dataset"] = {str(p): p.exists() for p in required}
    if not all(out["checks"]["v0_dataset"].values()):
        out["status"] = "HARD_BLOCKER:DATASET_MISSING"
        print(json.dumps(out, indent=2))
        return

    # B1 CUDA gate
    import torch

    out["checks"]["cuda"] = {
        "torch_version": torch.__version__,
        "torch_cuda": torch.version.cuda,
        "cuda_available": bool(torch.cuda.is_available()),
        "cuda_device_count": int(torch.cuda.device_count()),
        "cuda_visible_devices": os.getenv("CUDA_VISIBLE_DEVICES"),
    }
    if not torch.cuda.is_available() or torch.cuda.device_count() == 0:
        out["status"] = "HARD_BLOCKER:CUDA_REQUIRED"
        print(json.dumps(out, indent=2))
        return

    # B2 CLIP cache check on GPU
    try:
        import clip

        model, _ = clip.load("ViT-B/16", device="cuda")
        out["checks"]["clip_gpu"] = {
            "ok": True,
            "param_device": str(next(model.parameters()).device),
        }
    except Exception as e:
        out["checks"]["clip_gpu"] = {"ok": False, "error": repr(e)}
        out["status"] = "HARD_BLOCKER:CLIP_CACHE_MISSING_OR_CPU"
        print(json.dumps(out, indent=2))
        return
    if "cuda" not in out["checks"]["clip_gpu"]["param_device"]:
        out["status"] = "HARD_BLOCKER:CLIP_CACHE_MISSING_OR_CPU"
        print(json.dumps(out, indent=2))
        return

    # B3 local DINO rule
    dino_repo = Path.home() / ".cache/torch/hub/facebookresearch_dinov2_main"
    dino_weight = find_dino_weight()
    out["checks"]["dino_local"] = {
        "repo": str(dino_repo),
        "repo_exists": dino_repo.exists(),
        "weight": str(dino_weight) if dino_weight else None,
        "weight_exists": bool(dino_weight and dino_weight.exists()),
    }
    if not dino_weight:
        out["status"] = "HARD_BLOCKER:DINO_LOCAL_WEIGHT_MISSING"
        print(json.dumps(out, indent=2))
        return
    if not dino_repo.exists():
        out["status"] = "HARD_BLOCKER:DINO_LOCAL_CODE_MISSING"
        print(json.dumps(out, indent=2))
        return
    out["checks"]["dino_local"]["weight_sha256"] = sha256_file(dino_weight)

    # Phase D1 conversion
    conv_cmd = [
        "python",
        "tools/convert_coco2014_captions_to_talk2dino_torch.py",
        "--train-json",
        "data/coco2014/annotations/captions_train2014.json",
        "--val-json",
        "data/coco2014/annotations/captions_val2014.json",
        "--train-out",
        "features/coco2014_b14/captions_train2014.torch",
        "--val-out",
        "features/coco2014_b14/captions_val2014.torch",
    ]
    if resume_idx <= stage_index["convert"]:
        p = run_cmd(conv_cmd, cwd=repo, log_path=logs / "convert.log")
        out["logs"]["convert"] = str(logs / "convert.log")
        if p.returncode != 0:
            out["status"] = "FAIL:CONVERSION"
            print(json.dumps(out, indent=2))
            return

    # Phase D2 DINO extraction
    dino_common = py_conda_cmd(
        "dino_extraction_v2.py",
        "--model",
        "dinov2_vitb14_reg",
        "--data_dir",
        "data/coco2014",
        "--resize_dim",
        "448",
        "--crop_dim",
        "448",
        "--batch_size",
        str(args.batch_size_dino),
        "--extract_avg_self_attn",
        "--extract_disentangled_self_attn",
        "--dinov2_local_repo",
        str(dino_repo),
        "--dinov2_local_weight",
        str(dino_weight),
    )
    if resume_idx <= stage_index["dino_train"]:
        p_train = run_cmd(
            dino_common + ["--ann_path", "features/coco2014_b14/captions_train2014.torch", "--out_path", "features/coco2014_b14/train.pth"],
            cwd=repo,
            env={"CUDA_VISIBLE_DEVICES": args.cuda_visible_devices},
            log_path=logs / "dino_train.log",
        )
        out["logs"]["dino_train"] = str(logs / "dino_train.log")
        if p_train.returncode != 0:
            out["status"] = "FAIL:DINO_TRAIN_EXTRACTION"
            print(json.dumps(out, indent=2))
            return
        f_train, t_train = parse_failed_extract(p_train.stdout + "\n" + p_train.stderr)
        out["checks"]["dino_train_n_errors"] = {"failed": f_train, "total": t_train}
        out["checks"]["dino_train_cuda_mem"] = parse_cuda_mem(p_train.stdout + "\n" + p_train.stderr)
        if f_train is None or f_train != 0:
            out["status"] = "FAIL:DUMMY_IMAGE_FALLBACK_DETECTED"
            print(json.dumps(out, indent=2))
            return
    if resume_idx <= stage_index["dino_val"]:
        p_val = run_cmd(
            dino_common + ["--ann_path", "features/coco2014_b14/captions_val2014.torch", "--out_path", "features/coco2014_b14/val.pth"],
            cwd=repo,
            env={"CUDA_VISIBLE_DEVICES": args.cuda_visible_devices},
            log_path=logs / "dino_val.log",
        )
        out["logs"]["dino_val"] = str(logs / "dino_val.log")
        if p_val.returncode != 0:
            out["status"] = "FAIL:DINO_VAL_EXTRACTION"
            print(json.dumps(out, indent=2))
            return
        f_val, t_val = parse_failed_extract(p_val.stdout + "\n" + p_val.stderr)
        out["checks"]["dino_val_n_errors"] = {"failed": f_val, "total": t_val}
        out["checks"]["dino_val_cuda_mem"] = parse_cuda_mem(p_val.stdout + "\n" + p_val.stderr)
        if f_val is None or f_val != 0:
            out["status"] = "FAIL:DUMMY_IMAGE_FALLBACK_DETECTED"
            print(json.dumps(out, indent=2))
            return

    # Phase D3 text extraction
    text_common = py_conda_cmd("text_features_extraction.py", "--model", "ViT-B/16", "--batch_size", str(args.batch_size_text))
    if resume_idx <= stage_index["text"]:
        p_txt_train = run_cmd(
            text_common + ["--ann_path", "features/coco2014_b14/train.pth", "--out_path", "features/coco2014_b14/train.pth"],
            cwd=repo,
            env={"CUDA_VISIBLE_DEVICES": args.cuda_visible_devices},
            log_path=logs / "text_train.log",
        )
        out["logs"]["text_train"] = str(logs / "text_train.log")
        if p_txt_train.returncode != 0:
            out["status"] = "FAIL:TEXT_TRAIN_EXTRACTION"
            print(json.dumps(out, indent=2))
            return
        p_txt_val = run_cmd(
            text_common + ["--ann_path", "features/coco2014_b14/val.pth", "--out_path", "features/coco2014_b14/val.pth"],
            cwd=repo,
            env={"CUDA_VISIBLE_DEVICES": args.cuda_visible_devices},
            log_path=logs / "text_val.log",
        )
        out["logs"]["text_val"] = str(logs / "text_val.log")
        if p_txt_val.returncode != 0:
            out["status"] = "FAIL:TEXT_VAL_EXTRACTION"
            print(json.dumps(out, indent=2))
            return
        out["checks"]["clip_cuda_mem"] = {
            "train": parse_cuda_mem(p_txt_train.stdout + "\n" + p_txt_train.stderr),
            "val": parse_cuda_mem(p_txt_val.stdout + "\n" + p_txt_val.stderr),
        }

    # Phase D4 train projection
    if resume_idx <= stage_index["train"]:
        p_train_proj = run_cmd(
            py_conda_cmd(
                "train.py",
                "--model_config",
                "configs/vitb_mlp_infonce.yaml",
                "--train_dataset",
                "features/coco2014_b14/train.pth",
                "--val_dataset",
                "features/coco2014_b14/val.pth",
                "--test_dataset",
                "features/coco2014_b14/val.pth",
                "--feature_name",
                "disentangled_self_attn",
                "--text_features",
                "ann_feats",
            ),
            cwd=repo,
            env={"CUDA_VISIBLE_DEVICES": args.cuda_visible_devices},
            log_path=logs / "train_projection.log",
        )
        out["logs"]["train_projection"] = str(logs / "train_projection.log")
        if p_train_proj.returncode != 0:
            out["status"] = "FAIL:TRAIN_PROJECTION"
            print(json.dumps(out, indent=2))
            return

    # V4 artifact check
    final_weight = repo / "weights/vitb_mlp_infonce.pth"
    out["artifacts"]["final_weight"] = {
        "path": str(final_weight),
        "exists": final_weight.exists(),
    }
    if final_weight.exists():
        st = final_weight.stat()
        out["artifacts"]["final_weight"].update(
            {
                "size": st.st_size,
                "mtime": st.st_mtime,
                "sha256": sha256_file(final_weight),
            }
        )
    if not final_weight.exists():
        out["status"] = "FAIL:FINAL_WEIGHT_MISSING"
        print(json.dumps(out, indent=2))
        return

    out["status"] = "PASS"
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
