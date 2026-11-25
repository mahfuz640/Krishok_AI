#!/usr/bin/env python3
"""Verified CPU-only MobileNetV3-Large training for the approved rice manifests."""
from __future__ import annotations

import csv
import hashlib
import json
import logging
import math
import os
import platform
import random
import shutil
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch
from PIL import Image
from torch import nn
from torch.utils.data import DataLoader, Dataset
from torchvision import models, transforms
from torchvision.models import MobileNet_V3_Large_Weights


ROOT = Path(__file__).resolve().parents[3]
DATA_ROOT = ROOT / "AI/data/processed/rice_classification"
MANIFEST_DIR = DATA_ROOT / "manifests"
OUT = Path(__file__).resolve().parent
LOG_PATH = OUT / "cpu_training.log"
SEED = 42
IMG_SIZE = 224
EPOCHS = 30
BATCH_SIZE = 32
PATIENCE = 8
LEARNING_RATE = 3e-4
WEIGHT_DECAY = 1e-4
NUM_WORKERS = 2
CLASS_TO_ID = {
    "Blast": 0,
    "Brown spot": 1,
    "Healthy": 2,
    "Leaf smut": 3,
    "Rice Tungro": 4,
    "Sheath blight": 5,
}
COUNTS = {"train": 6827, "val": 1463, "test": 1463}
MANIFEST_SHA256 = {
    "train.csv": "baf1004abaa44f3ddddd7bde3abc5cefc15d06904e4b441eb0dcf87ea41d0b0d",
    "val.csv": "60706b05853801deb524ea078bccc7c62ef4a23029008d7b28a649afed2d0145",
    "test.csv": "91fdd26f22243861fcf1eea53b3312d1e1bcdb5800ffa822f56ab486b3d59d9f",
}
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}


def setup_logging() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler(LOG_PATH, encoding="utf-8")],
        force=True,
    )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def md5(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def verify_dataset() -> tuple[dict[str, list[dict[str, str]]], dict[str, str]]:
    logging.info("Starting strict read-only dataset verification")
    map_path = MANIFEST_DIR / "class_mapping.json"
    class_map = json.loads(map_path.read_text(encoding="utf-8"))
    actual_map = {item["class_label"]: int(item["class_id"]) for item in class_map.get("classes", [])}
    if actual_map != CLASS_TO_ID or class_map.get("uses_yolo_annotation_class_ids") is not False:
        raise RuntimeError(f"Approved class mapping mismatch: {actual_map}")

    frames: dict[str, list[dict[str, str]]] = {}
    for split, expected_count in COUNTS.items():
        manifest = MANIFEST_DIR / f"{split}.csv"
        actual_hash = sha256(manifest)
        if actual_hash != MANIFEST_SHA256[manifest.name]:
            raise RuntimeError(f"{manifest.name} SHA-256 mismatch: {actual_hash}")
        rows = read_csv(manifest)
        if len(rows) != expected_count:
            raise RuntimeError(f"{split} manifest count mismatch: {len(rows)} != {expected_count}")
        paths = [row["image_path"] for row in rows]
        if len(paths) != len(set(paths)):
            raise RuntimeError(f"Duplicate image_path rows in {split}.csv")
        if any(row["class_label"] not in CLASS_TO_ID for row in rows):
            raise RuntimeError(f"Unknown class in {split}.csv")
        for row in rows:
            if int(row["class_id"]) != CLASS_TO_ID[row["class_label"]]:
                raise RuntimeError(f"Class mapping mismatch for {row['image_path']}")
            if not row["image_path"].startswith(f"{split}/"):
                raise RuntimeError(f"Unexpected relative path for {split}: {row['image_path']}")

        folder = DATA_ROOT / split
        inventory = {
            path.relative_to(DATA_ROOT).as_posix()
            for path in folder.rglob("*")
            if path.is_file()
        }
        expected_paths = set(paths)
        missing, extra = expected_paths - inventory, inventory - expected_paths
        if missing or extra:
            raise RuntimeError(
                f"{split} path inventory mismatch: missing={sorted(missing)[:10]} extra={sorted(extra)[:10]}"
            )

        logging.info("Verifying/decode/hash %s images (%d total)", split, len(rows))
        for index, row in enumerate(rows, 1):
            path = DATA_ROOT / row["image_path"]
            if path.suffix.lower() not in IMAGE_SUFFIXES:
                raise RuntimeError(f"Unsupported image format: {path}")
            try:
                with Image.open(path) as image:
                    image.load()
                    if image.width != 1024 or image.height != 1024:
                        raise RuntimeError(f"Unexpected image dimensions for {path}: {image.size}")
            except Exception as exc:
                raise RuntimeError(f"Unreadable image; aborting without skipping: {path}: {exc}") from exc
            actual_md5 = md5(path)
            if actual_md5 != row["md5"]:
                raise RuntimeError(f"Image MD5 mismatch for {row['image_path']}: {actual_md5}")
            if index % 500 == 0 or index == len(rows):
                logging.info("%s verification progress: %d/%d", split, index, len(rows))
        frames[split] = rows

    # Exact duplicate groups cannot cross splits, and unresolved cross-class groups must be absent.
    split_groups = {
        split: {row["duplicate_group_id"] for row in rows}
        for split, rows in frames.items()
    }
    for first, second in (("train", "val"), ("train", "test"), ("val", "test")):
        overlap = split_groups[first] & split_groups[second]
        if overlap:
            raise RuntimeError(f"Exact duplicate groups cross {first}/{second}: {sorted(overlap)[:5]}")
    review = read_csv(MANIFEST_DIR / "cross_class_review.csv")
    unresolved = {row["group_id"] for row in review if row["review_status"] == "unresolved_excluded"}
    included = set.union(*split_groups.values())
    if unresolved & included:
        raise RuntimeError(f"Unresolved cross-class groups included: {sorted(unresolved & included)[:5]}")

    digests = {name: MANIFEST_SHA256[name] for name in MANIFEST_SHA256}
    report = [
        "# CPU Run Dataset Integrity Verification",
        "",
        "**Status: PASS.** Exact approved manifests, folder path inventories, image decoding, image MD5 hashes, class mapping, counts, duplicate group isolation, and cross-class exclusions all passed before training.",
        "",
        "| Split | Manifest rows | Files | Manifest SHA-256 |",
        "|---|---:|---:|---|",
    ]
    for split, rows in frames.items():
        report.append(f"| {split} | {len(rows)} | {len(rows)} | `{digests[f'{split}.csv']}` |")
    report.extend(
        [
            "",
            "Class mapping: " + ", ".join(f"{name}={idx}" for name, idx in CLASS_TO_ID.items()),
            "",
            "Test images were decoded and integrity-checked only; no test image was loaded by a model, optimizer, scheduler, or tuning process.",
            "",
        ]
    )
    (OUT / "cpu_run_integrity_report.md").write_text("\n".join(report), encoding="utf-8")
    logging.info("Dataset verification PASS; test manifest read only for integrity validation")
    return frames, digests


class ManifestDataset(Dataset):
    def __init__(self, rows: list[dict[str, str]], transform):
        self.rows = rows
        self.transform = transform

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, index: int):
        row = self.rows[index]
        path = DATA_ROOT / row["image_path"]
        try:
            with Image.open(path) as image:
                image.load()
                tensor = self.transform(image.convert("RGB"))
        except Exception as exc:
            raise RuntimeError(f"Image read failed; no sample was skipped: {path}: {exc}") from exc
        return tensor, int(row["class_id"])


def atomic_torch_save(payload: dict, path: Path) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    torch.save(payload, temporary)
    os.replace(temporary, path)


def run_epoch(model, loader, criterion, device, optimizer=None):
    training = optimizer is not None
    model.train(training)
    total_loss = 0.0
    total = 0
    correct = 0
    context = torch.enable_grad() if training else torch.inference_mode()
    with context:
        for images, labels in loader:
            images, labels = images.to(device), labels.to(device)
            if training:
                optimizer.zero_grad(set_to_none=True)
            logits = model(images)
            loss = criterion(logits, labels)
            if training:
                loss.backward()
                optimizer.step()
            total_loss += float(loss.item()) * labels.size(0)
            total += labels.size(0)
            correct += int((logits.argmax(1) == labels).sum().item())
    return total_loss / total, correct / total


def evaluate_validation(model, loader, rows, class_names, device):
    model.eval()
    y_true: list[int] = []
    y_pred: list[int] = []
    with torch.inference_mode():
        for images, labels in loader:
            logits = model(images.to(device))
            y_true.extend(labels.tolist())
            y_pred.extend(logits.argmax(1).cpu().tolist())
    if len(y_true) != len(rows) or len(y_pred) != len(rows):
        raise RuntimeError(f"Validation prediction count mismatch: expected {len(rows)}, got {len(y_pred)}")
    n = len(class_names)
    cm = np.zeros((n, n), dtype=np.int64)
    np.add.at(cm, (np.asarray(y_true), np.asarray(y_pred)), 1)
    metrics = []
    f1_values, support_values = [], []
    for class_id, name in enumerate(class_names):
        tp = int(cm[class_id, class_id])
        support = int(cm[class_id, :].sum())
        predicted = int(cm[:, class_id].sum())
        precision = tp / predicted if predicted else 0.0
        recall = tp / support if support else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if precision + recall else 0.0
        metrics.append({"class_id": class_id, "class": name, "precision": precision,
                        "recall": recall, "f1_score": f1, "support": support})
        f1_values.append(f1)
        support_values.append(support)
    accuracy = float(np.trace(cm) / cm.sum())
    macro_p = float(np.mean([row["precision"] for row in metrics]))
    macro_r = float(np.mean([row["recall"] for row in metrics]))
    macro_f1 = float(np.mean(f1_values))
    weighted_f1 = float(np.average(f1_values, weights=support_values))
    metrics.extend([
        {"class_id": "", "class": "macro avg", "precision": macro_p, "recall": macro_r,
         "f1_score": macro_f1, "support": int(cm.sum())},
        {"class_id": "", "class": "weighted avg", "precision": float(np.average([r["precision"] for r in metrics], weights=support_values)),
         "recall": float(np.average([r["recall"] for r in metrics], weights=support_values)),
         "f1_score": weighted_f1, "support": int(cm.sum())},
    ])
    return cm, metrics, {"accuracy": accuracy, "macro_precision": macro_p,
                         "macro_recall": macro_r, "macro_f1": macro_f1,
                         "weighted_f1": weighted_f1}


def benchmark_cpu(model, tensors: torch.Tensor) -> dict:
    model = model.to("cpu").eval()
    warmups, iterations = 5, 50
    with torch.inference_mode():
        for i in range(warmups):
            model(tensors[i % len(tensors)].unsqueeze(0))
        samples = []
        for i in range(iterations):
            sample = tensors[i % len(tensors)].unsqueeze(0)
            started = time.perf_counter()
            model(sample)
            samples.append((time.perf_counter() - started) * 1000)
    return {"device": "cpu", "batch_size": 1, "threads": torch.get_num_threads(),
            "timed_iterations": iterations, "mean_ms": float(np.mean(samples)),
            "median_ms": float(np.median(samples)), "p95_ms": float(np.percentile(samples, 95)),
            "scope": "forward only; preprocessed 224x224 validation tensors"}


def main() -> None:
    setup_logging()
    if not torch.cuda.is_available():
        device = torch.device("cpu")
    else:
        raise RuntimeError("This entry point is explicitly CPU-only; CUDA unexpectedly detected.")
    existing = [name for name in ("best_model.pt", "last_model.pt", "training_history.csv") if (OUT / name).exists()]
    if existing:
        raise FileExistsError(f"Refusing to overwrite existing experiment artifacts: {existing}")

    torch.set_num_threads(min(6, os.cpu_count() or 1))
    torch.set_num_interop_threads(1)
    random.seed(SEED)
    np.random.seed(SEED)
    torch.manual_seed(SEED)
    torch.use_deterministic_algorithms(True, warn_only=True)

    frames, manifest_digests = verify_dataset()
    class_names = [name for name, _ in sorted(CLASS_TO_ID.items(), key=lambda pair: pair[1])]
    weights = MobileNet_V3_Large_Weights.DEFAULT
    eval_transform = weights.transforms()
    mean, std = eval_transform.mean, eval_transform.std
    train_transform = transforms.Compose([
        transforms.RandomResizedCrop(IMG_SIZE, scale=(0.80, 1.0), interpolation=transforms.InterpolationMode.BILINEAR),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.ToTensor(),
        transforms.Normalize(mean=mean, std=std),
    ])
    train_loader = DataLoader(
        ManifestDataset(frames["train"], train_transform), batch_size=BATCH_SIZE,
        shuffle=True, num_workers=NUM_WORKERS, pin_memory=False,
        generator=torch.Generator().manual_seed(SEED),
    )
    val_loader = DataLoader(
        ManifestDataset(frames["val"], eval_transform), batch_size=BATCH_SIZE,
        shuffle=False, num_workers=NUM_WORKERS, pin_memory=False,
    )

    logging.info("Loading ImageNet-pretrained MobileNetV3-Large on CPU")
    model = models.mobilenet_v3_large(weights=weights)
    model.classifier[-1] = nn.Linear(model.classifier[-1].in_features, len(class_names))
    model = model.to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=LEARNING_RATE, weight_decay=WEIGHT_DECAY)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="min", factor=0.5, patience=3)
    best_path, last_path = OUT / "best_model.pt", OUT / "last_model.pt"
    history = []
    best_val_loss = math.inf
    best_epoch = 0
    stale_epochs = 0
    started_all = time.perf_counter()

    for epoch in range(1, EPOCHS + 1):
        epoch_started = time.perf_counter()
        train_loss, train_acc = run_epoch(model, train_loader, criterion, device, optimizer)
        val_loss, val_acc = run_epoch(model, val_loader, criterion, device)
        scheduler.step(val_loss)
        lr = float(optimizer.param_groups[0]["lr"])
        history.append({"epoch": epoch, "train_loss": train_loss, "train_accuracy": train_acc,
                        "val_loss": val_loss, "val_accuracy": val_acc, "learning_rate": lr})
        checkpoint = {
            "model_state_dict": model.state_dict(), "class_to_id": CLASS_TO_ID,
            "epoch": epoch, "val_loss": val_loss, "seed": SEED,
            "train_manifest_sha256": manifest_digests["train.csv"],
            "val_manifest_sha256": manifest_digests["val.csv"],
            "test_used_for_training_or_tuning": False,
        }
        atomic_torch_save(checkpoint, last_path)
        if val_loss < best_val_loss - 1e-4:
            best_val_loss, best_epoch, stale_epochs = val_loss, epoch, 0
            atomic_torch_save(checkpoint, best_path)
        else:
            stale_epochs += 1
        write_csv(OUT / "training_history.csv", history,
                  ["epoch", "train_loss", "train_accuracy", "val_loss", "val_accuracy", "learning_rate"])
        logging.info(
            "Epoch %02d/%02d train_loss=%.5f val_loss=%.5f train_acc=%.4f val_acc=%.4f lr=%.3g "
            "elapsed=%.1f min stale=%d/%d",
            epoch, EPOCHS, train_loss, val_loss, train_acc, val_acc, lr,
            (time.perf_counter() - epoch_started) / 60, stale_epochs, PATIENCE,
        )
        if stale_epochs >= PATIENCE:
            logging.info("Early stopping at epoch %d; best epoch %d", epoch, best_epoch)
            break

    total_minutes = (time.perf_counter() - started_all) / 60
    with (OUT / "training_history.csv").open("r", encoding="utf-8", newline="") as stream:
        history_rows = list(csv.DictReader(stream))
    curve = {key: [float(row[key]) for row in history_rows] for key in ("train_loss", "val_loss")}
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(range(1, len(curve["train_loss"]) + 1), curve["train_loss"], label="Train loss")
    ax.plot(range(1, len(curve["val_loss"]) + 1), curve["val_loss"], label="Validation loss")
    ax.set(xlabel="Epoch", ylabel="Cross-entropy loss", title="MobileNetV3-Large CPU training")
    ax.grid(True); ax.legend(); fig.tight_layout()
    fig.savefig(OUT / "training_validation_loss_curves.png", dpi=160)
    plt.close(fig)

    best = torch.load(best_path, map_location="cpu", weights_only=True)
    if best["class_to_id"] != CLASS_TO_ID:
        raise RuntimeError("Best checkpoint has a mismatched class mapping")
    eval_model = models.mobilenet_v3_large(weights=None)
    eval_model.classifier[-1] = nn.Linear(eval_model.classifier[-1].in_features, len(class_names))
    eval_model.load_state_dict(best["model_state_dict"])
    eval_model.to(device).eval()
    cm, metric_rows, aggregate = evaluate_validation(eval_model, val_loader, frames["val"], class_names, device)
    write_csv(OUT / "validation_classification_report.csv", metric_rows,
              ["class_id", "class", "precision", "recall", "f1_score", "support"])

    fig, ax = plt.subplots(figsize=(9, 7))
    image = ax.imshow(cm, cmap="Blues")
    ax.set(xticks=range(6), yticks=range(6), xticklabels=class_names, yticklabels=class_names,
           xlabel="Predicted class", ylabel="True class", title="MobileNetV3-Large validation confusion matrix")
    plt.setp(ax.get_xticklabels(), rotation=35, ha="right")
    for i in range(6):
        for j in range(6):
            ax.text(j, i, str(cm[i, j]), ha="center", va="center",
                    color="white" if cm[i, j] > cm.max() * 0.55 else "black")
    fig.colorbar(image, ax=ax, label="Images"); fig.tight_layout()
    fig.savefig(OUT / "validation_confusion_matrix.png", dpi=180)
    plt.close(fig)

    # Benchmark fixed, preprocessed validation tensors. No test data is involved.
    bench_rows = frames["val"][:50]
    bench_tensors = []
    for row in bench_rows:
        with Image.open(DATA_ROOT / row["image_path"]) as image:
            image.load()
            bench_tensors.append(eval_transform(image.convert("RGB")))
    bench_tensor = torch.stack(bench_tensors)
    cpu_latency = benchmark_cpu(eval_model, bench_tensor)
    parameter_count = sum(parameter.numel() for parameter in eval_model.parameters())
    best_bytes = best_path.stat().st_size
    last_bytes = last_path.stat().st_size
    metrics = {
        "model": "MobileNetV3-Large", "weights": "ImageNet pretrained",
        "seed": SEED, "epochs_completed": len(history_rows), "best_epoch": best_epoch,
        "training_minutes": total_minutes, "validation_images": len(frames["val"]),
        **aggregate, "class_to_id": CLASS_TO_ID,
        "train_manifest_sha256": manifest_digests["train.csv"],
        "val_manifest_sha256": manifest_digests["val.csv"],
        "test_manifest_sha256": manifest_digests["test.csv"],
        "test_used_for_training_or_tuning": False,
        "parameters": int(parameter_count), "best_checkpoint_bytes": best_bytes,
        "best_checkpoint_MiB": best_bytes / (1024 ** 2),
        "last_checkpoint_bytes": last_bytes, "cpu_inference_latency": cpu_latency,
        "gpu_inference_latency": {"status": "unavailable", "reason": "No CUDA GPU is present; CPU-only run."},
        "latency_scope": "Forward-only, batch-one inference on preprocessed 224x224 validation tensors.",
    }
    (OUT / "validation_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    (OUT / "inference_latency.json").write_text(json.dumps({
        "cpu": cpu_latency, "gpu": metrics["gpu_inference_latency"],
        "parameters": int(parameter_count), "best_checkpoint_bytes": best_bytes,
        "best_checkpoint_MiB": best_bytes / (1024 ** 2), "validation_images_for_benchmark": len(bench_rows),
    }, indent=2), encoding="utf-8")
    environment = {
        "model": "torchvision.mobilenet_v3_large", "pretrained_weights": str(weights),
        "seed": SEED, "image_size": IMG_SIZE, "epochs_max": EPOCHS, "batch_size": BATCH_SIZE,
        "optimizer": "AdamW", "scheduler": "ReduceLROnPlateau", "early_stopping_patience": PATIENCE,
        "torch": torch.__version__, "torchvision": __import__("torchvision").__version__,
        "python": platform.python_version(), "device": "cpu",
        "cpu": platform.processor(), "cpu_threads": torch.get_num_threads(),
        "train_manifest_sha256": manifest_digests["train.csv"],
        "val_manifest_sha256": manifest_digests["val.csv"],
        "test_manifest_sha256": manifest_digests["test.csv"],
        "test_used_for_training_or_tuning": False,
    }
    (OUT / "environment.json").write_text(json.dumps(environment, indent=2), encoding="utf-8")
    logging.info("Training finished: %s", json.dumps(metrics, ensure_ascii=False))
    logging.info("Best checkpoint: %s", best_path)
    logging.info("Last checkpoint: %s", last_path)


if __name__ == "__main__":
    main()

