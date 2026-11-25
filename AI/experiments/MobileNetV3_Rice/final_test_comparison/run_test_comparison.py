#!/usr/bin/env python3
"""One-pass, CPU-only final evaluation of YOLO11 and MobileNet on approved test.csv."""
from __future__ import annotations

import csv
import hashlib
import json
import logging
import math
import sys
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch
from PIL import Image
from torch import nn
from torch.utils.data import DataLoader, Dataset
from torchvision import models
from torchvision.models import MobileNet_V3_Large_Weights
from ultralytics import YOLO


ROOT = Path(__file__).resolve().parents[4]
DATA = ROOT / "AI/data/processed/rice_classification"
MANIFEST = DATA / "manifests/test.csv"
CLASS_MAP_PATH = DATA / "manifests/class_mapping.json"
MOBILE_CKPT = ROOT / "AI/experiments/MobileNetV3_Rice/best_model.pt"
YOLO_CKPT = ROOT / "rice/KrishokAI_results_archive/YOLO11_Rice_v1_local/weights/best.pt"
OUT = Path(__file__).resolve().parent
EXPECTED_TEST_SHA256 = "91fdd26f22243861fcf1eea53b3312d1e1bcdb5800ffa822f56ab486b3d59d9f"
EXPECTED_CLASSES = ["Blast", "Brown spot", "Healthy", "Leaf smut", "Rice Tungro", "Sheath blight"]
BATCH_SIZE = 32


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_manifest():
    actual = digest(MANIFEST)
    if actual != EXPECTED_TEST_SHA256:
        raise RuntimeError(f"Frozen test manifest hash mismatch: {actual}")
    mapping = json.loads(CLASS_MAP_PATH.read_text(encoding="utf-8"))
    class_to_id = {item["class_label"]: int(item["class_id"]) for item in mapping["classes"]}
    if [name for name, idx in sorted(class_to_id.items(), key=lambda pair: pair[1])] != EXPECTED_CLASSES:
        raise RuntimeError(f"Test class mapping mismatch: {class_to_id}")
    with MANIFEST.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    if len(rows) != 1463 or len({row["image_path"] for row in rows}) != 1463:
        raise RuntimeError(f"Unexpected frozen test inventory: {len(rows)} records")
    for row in rows:
        if row["class_label"] not in class_to_id or int(row["class_id"]) != class_to_id[row["class_label"]]:
            raise RuntimeError(f"Test label/mapping mismatch at {row['image_path']}")
        path = DATA / row["image_path"]
        if not path.is_file():
            raise FileNotFoundError(path)
    if not YOLO_CKPT.is_file() or not MOBILE_CKPT.is_file():
        raise FileNotFoundError("Both approved best checkpoints must exist before this final evaluation.")
    return rows, class_to_id, actual


class TestImages(Dataset):
    def __init__(self, rows, transform):
        self.rows = rows
        self.transform = transform

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, idx):
        row = self.rows[idx]
        path = DATA / row["image_path"]
        try:
            with Image.open(path) as image:
                image.load()
                tensor = self.transform(image.convert("RGB"))
        except Exception as exc:
            raise RuntimeError(f"Test image decode failed: {path}: {exc}") from exc
        return tensor, int(row["class_id"])


def metrics(y_true, y_pred, probabilities, class_names):
    n_classes = len(class_names)
    cm = np.zeros((n_classes, n_classes), dtype=np.int64)
    np.add.at(cm, (y_true, y_pred), 1)
    supports = cm.sum(axis=1)
    predicted = cm.sum(axis=0)
    rows = []
    for i, name in enumerate(class_names):
        tp = int(cm[i, i])
        precision = tp / predicted[i] if predicted[i] else 0.0
        recall = tp / supports[i] if supports[i] else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        rows.append({"class_id": i, "class": name, "precision": precision,
                     "recall": recall, "f1_score": f1, "support": int(supports[i])})
    ps = np.array([r["precision"] for r in rows])
    rs = np.array([r["recall"] for r in rows])
    fs = np.array([r["f1_score"] for r in rows])
    total = int(cm.sum())
    aggregates = {
        "accuracy": float(np.trace(cm) / total),
        "top5_accuracy": float(np.mean([int(y) in np.argsort(p)[-5:] for y, p in zip(y_true, probabilities)])),
        "macro_precision": float(ps.mean()), "macro_recall": float(rs.mean()),
        "macro_f1": float(fs.mean()),
        "weighted_precision": float(np.average(ps, weights=supports)),
        "weighted_recall": float(np.average(rs, weights=supports)),
        "weighted_f1": float(np.average(fs, weights=supports)),
        "test_images": total,
    }
    rows.extend([
        {"class_id": "", "class": "macro avg", "precision": aggregates["macro_precision"],
         "recall": aggregates["macro_recall"], "f1_score": aggregates["macro_f1"], "support": total},
        {"class_id": "", "class": "weighted avg", "precision": aggregates["weighted_precision"],
         "recall": aggregates["weighted_recall"], "f1_score": aggregates["weighted_f1"], "support": total},
    ])
    return cm, rows, aggregates


def save_confusion(cm, names, path, normalized=False):
    values = cm / np.maximum(cm.sum(axis=1, keepdims=True), 1) if normalized else cm
    fig, ax = plt.subplots(figsize=(9, 7))
    im = ax.imshow(values, cmap="Blues", vmin=0, vmax=1 if normalized else None)
    ax.set(xticks=range(len(names)), yticks=range(len(names)), xticklabels=names, yticklabels=names,
           xlabel="Predicted class", ylabel="True class",
           title=f"{'Normalized ' if normalized else ''}Test Confusion Matrix")
    plt.setp(ax.get_xticklabels(), rotation=35, ha="right")
    for i in range(len(names)):
        for j in range(len(names)):
            label = f"{values[i,j]:.1%}\n({cm[i,j]})" if normalized else str(cm[i,j])
            ax.text(j, i, label, ha="center", va="center",
                    color="white" if values[i,j] > (0.55 if normalized else cm.max() * 0.55) else "black", fontsize=8)
    fig.colorbar(im, ax=ax, label="Fraction of true class" if normalized else "Images")
    fig.tight_layout(); fig.savefig(path, dpi=180); plt.close(fig)


def main():
    existing = [item.name for item in OUT.iterdir()
                if item.name not in {Path(__file__).name, "__pycache__"}] if OUT.exists() else []
    if existing:
        raise FileExistsError(f"Refusing to overwrite comparison artifacts: {existing}")
    OUT.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    torch.set_num_threads(min(6, __import__("os").cpu_count() or 1))
    rows, class_to_id, test_digest = read_manifest()
    class_names = EXPECTED_CLASSES
    y_true = np.array([int(row["class_id"]) for row in rows], dtype=np.int64)
    paths = [DATA / row["image_path"] for row in rows]
    logging.info("Final single-pass evaluation on %d frozen test rows; test hash %s", len(rows), test_digest)

    # MobileNet: same approved test path order, no gradients/updates, one pass.
    weights = MobileNet_V3_Large_Weights.DEFAULT
    transform = weights.transforms()
    mobile = models.mobilenet_v3_large(weights=None)
    mobile.classifier[-1] = nn.Linear(mobile.classifier[-1].in_features, len(class_names))
    checkpoint = torch.load(MOBILE_CKPT, map_location="cpu", weights_only=True)
    if checkpoint.get("class_to_id") != class_to_id:
        raise RuntimeError("MobileNet checkpoint class map differs from approved class mapping")
    mobile.load_state_dict(checkpoint["model_state_dict"])
    mobile.eval()
    loader = DataLoader(TestImages(rows, transform), batch_size=BATCH_SIZE, shuffle=False,
                        num_workers=2, pin_memory=False)
    mobile_probabilities = []
    mobile_start = time.perf_counter()
    with torch.inference_mode():
        for batch, _labels in loader:
            mobile_probabilities.extend(torch.softmax(mobile(batch), dim=1).cpu().numpy())
    mobile_elapsed = time.perf_counter() - mobile_start
    mobile_probabilities = np.stack(mobile_probabilities)
    mobile_pred = mobile_probabilities.argmax(axis=1)
    logging.info("MobileNet test inference completed in %.2f seconds", mobile_elapsed)

    # YOLO: class order must exactly match the folder-derived approved class mapping.
    yolo = YOLO(str(YOLO_CKPT))
    yolo_names = [yolo.names[i] for i in range(len(yolo.names))]
    if yolo_names != class_names:
        raise RuntimeError(f"YOLO checkpoint class order mismatch: {yolo_names} != {class_names}")
    yolo_probabilities = []
    yolo_start = time.perf_counter()
    for start in range(0, len(paths), BATCH_SIZE):
        results = yolo.predict([str(p) for p in paths[start:start+BATCH_SIZE]], imgsz=224,
                               batch=BATCH_SIZE, device="cpu", verbose=False)
        for result in results:
            yolo_probabilities.append(result.probs.data.cpu().numpy())
    yolo_elapsed = time.perf_counter() - yolo_start
    yolo_probabilities = np.stack(yolo_probabilities)
    yolo_pred = yolo_probabilities.argmax(axis=1)
    logging.info("YOLO test inference completed in %.2f seconds", yolo_elapsed)

    outputs = {
        "MobileNetV3-Large": (mobile_pred, mobile_probabilities, mobile_elapsed,
                              sum(p.numel() for p in mobile.parameters()), MOBILE_CKPT),
        "YOLO11n-cls": (yolo_pred, yolo_probabilities, yolo_elapsed,
                        sum(p.numel() for p in yolo.model.parameters()), YOLO_CKPT),
    }
    comparison = []
    all_class_rows = []
    prediction_rows = []
    for model_name, (pred, probs, elapsed, params, ckpt_path) in outputs.items():
        cm, class_rows, aggregate = metrics(y_true, pred, probs, class_names)
        safe = model_name.lower().replace("-", "_").replace(" ", "_")
        for row in class_rows:
            all_class_rows.append({"model": model_name, **row})
        save_confusion(cm, class_names, OUT / f"{safe}_confusion_matrix.png")
        save_confusion(cm, class_names, OUT / f"{safe}_normalized_confusion_matrix.png", normalized=True)
        with (OUT / f"{safe}_confusion_matrix.csv").open("w", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream); writer.writerow(["true\\predicted", *class_names])
            for name, matrix_row in zip(class_names, cm): writer.writerow([name, *map(int, matrix_row)])
        comparison.append({"model": model_name, **aggregate, "parameters": int(params),
                           "checkpoint_bytes": ckpt_path.stat().st_size,
                           "checkpoint_MiB": ckpt_path.stat().st_size / (1024**2),
                           "inference_total_seconds": elapsed,
                           "latency_mean_ms_per_image": elapsed / len(rows) * 1000,
                           "inference_device": "cpu", "test_manifest_sha256": test_digest})
        for row, pred_id, prob in zip(rows, pred, probs):
            prediction_rows.append({"model": model_name, "image_path": row["image_path"],
                "true_class_id": int(row["class_id"]), "true_class": row["class_label"],
                "predicted_class_id": int(pred_id), "predicted_class": class_names[int(pred_id)],
                "confidence": float(np.max(prob))})
    fields = ["model", "accuracy", "top5_accuracy", "macro_precision", "macro_recall", "macro_f1",
              "weighted_precision", "weighted_recall", "weighted_f1", "test_images", "parameters",
              "checkpoint_bytes", "checkpoint_MiB", "inference_total_seconds", "latency_mean_ms_per_image",
              "inference_device", "test_manifest_sha256"]
    with (OUT/"model_comparison.csv").open("w",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=fields); writer.writeheader(); writer.writerows(comparison)
    write_rows = all_class_rows
    with (OUT/"per_class_metrics.csv").open("w",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=["model","class_id","class","precision","recall","f1_score","support"])
        writer.writeheader(); writer.writerows(write_rows)
    with (OUT/"test_predictions.csv").open("w",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=["model","image_path","true_class_id","true_class","predicted_class_id","predicted_class","confidence"])
        writer.writeheader(); writer.writerows(prediction_rows)
    summary={"evaluation":"one-pass final test evaluation; inference only; no tuning",
             "test_images":len(rows),"test_manifest_sha256":test_digest,
             "class_to_id":class_to_id,"test_labels_modified":False,
             "test_used_for_training_or_tuning":False,"models":comparison}
    (OUT/"test_comparison_summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    logging.info("Comparison completed: %s", json.dumps(comparison,ensure_ascii=False))


if __name__ == "__main__":
    main()

