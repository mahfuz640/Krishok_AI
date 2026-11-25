"""Reproducible inference-only YOLO11n-cls test-set error analysis.

Run from repository root with an environment containing Ultralytics, torch,
NumPy, Pillow, and Matplotlib. This reads but never writes to the dataset.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
DATA = ROOT / "AI/data/processed/rice_classification"
MANIFESTS = DATA / "manifests"
WEIGHTS = ROOT / "rice/KrishokAI_results_archive/YOLO11_Rice_v1_local/weights/best.pt"
CLASS_NAMES = ["Blast", "Brown spot", "Healthy", "Leaf smut", "Rice Tungro", "Sheath blight"]
IMG_SIZE = 224


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def save_csv(path, rows, fields):
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = read_csv(MANIFESTS / "test.csv")
    assert len(rows) == 1463, f"Unexpected test row count: {len(rows)}"
    paths = [DATA / row["image_path"] for row in rows]
    assert all(p.is_file() for p in paths)
    class_names = CLASS_NAMES
    assert {int(r["class_id"]) for r in rows} == set(range(len(class_names)))
    y_true = np.array([int(r["class_id"]) for r in rows])

    model = YOLO(str(WEIGHTS))
    predictions = []
    # Batch inference only: no training, optimizer, or test-driven selection.
    for start in range(0, len(paths), 32):
        results = model.predict([str(p) for p in paths[start:start + 32]],
                                imgsz=IMG_SIZE, batch=32, device="cpu", verbose=False)
        predictions.extend((result.probs.data.detach().cpu().numpy() for result in results))
    probs = np.stack(predictions)
    y_pred = probs.argmax(axis=1)
    confidence = probs.max(axis=1)
    assert len(probs) == len(rows)

    cm = np.zeros((len(class_names), len(class_names)), dtype=np.int64)
    np.add.at(cm, (y_true, y_pred), 1)
    row_sums = cm.sum(axis=1, keepdims=True)
    cm_norm = cm / np.maximum(row_sums, 1)
    with (OUT / "confusion_matrix_normalized.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f); writer.writerow(["true_label\\predicted_label", *class_names])
        for name, values in zip(class_names, cm_norm): writer.writerow([name, *[f"{v:.8f}" for v in values]])
    with (OUT / "confusion_matrix_counts.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f); writer.writerow(["true_label\\predicted_label", *class_names])
        for name, values in zip(class_names, cm): writer.writerow([name, *map(int, values)])
    fig, ax = plt.subplots(figsize=(9, 8))
    im = ax.imshow(cm_norm, cmap="Blues", vmin=0, vmax=1)
    ax.set(xticks=range(6), yticks=range(6), xticklabels=class_names,
           yticklabels=class_names, xlabel="Predicted label", ylabel="True label",
           title="YOLO11n-cls Test Confusion Matrix (row-normalized)")
    plt.setp(ax.get_xticklabels(), rotation=35, ha="right", rotation_mode="anchor")
    for i in range(6):
        for j in range(6):
            ax.text(j, i, f"{cm_norm[i,j]:.1%}\n({cm[i,j]})", ha="center", va="center",
                    color="white" if cm_norm[i,j] > .55 else "black", fontsize=8)
    fig.colorbar(im, ax=ax, label="Fraction of true class")
    fig.tight_layout()
    fig.savefig(OUT / "normalized_confusion_matrix.png", dpi=180)
    plt.close(fig)

    metric_rows = []
    for i, name in enumerate(class_names):
        tp = int(cm[i, i]); support = int(cm[i].sum()); predicted = int(cm[:, i].sum())
        precision = tp / predicted if predicted else 0.0
        recall = tp / support if support else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        metric_rows.append({"class": name, "support": support, "precision": f"{precision:.6f}",
                            "recall": f"{recall:.6f}", "f1_score": f"{f1:.6f}"})
    save_csv(OUT / "per_class_metrics.csv", metric_rows,
             ["class", "support", "precision", "recall", "f1_score"])
    mis_rows = []
    for idx, (row, pred, conf) in enumerate(zip(rows, y_pred, confidence)):
        if pred != y_true[idx]:
            mis_rows.append({"image_path": row["image_path"], "true_label": class_names[y_true[idx]],
                             "predicted_label": class_names[pred], "confidence": f"{conf:.6f}"})
    save_csv(OUT / "misclassified_test_images.csv", mis_rows,
             ["image_path", "true_label", "predicted_label", "confidence"])

    # Sheath blight error contact sheets with source path and prediction score.
    sheath_errors = [(i, row, int(y_pred[i]), float(confidence[i]))
                     for i, row in enumerate(rows) if y_true[i] == 5 and y_pred[i] != 5]
    sheet_size, thumb = 20, (220, 220)
    for page_start in range(0, len(sheath_errors), sheet_size):
        page = sheath_errors[page_start:page_start + sheet_size]
        cols, cell_h, cell_w = 4, 270, 280
        canvas = Image.new("RGB", (cols * cell_w, math.ceil(len(page) / cols) * cell_h), "white")
        draw = ImageDraw.Draw(canvas)
        for n, (i, row, pred, conf) in enumerate(page):
            im = Image.open(paths[i]).convert("RGB")
            im.thumbnail(thumb)
            x, y = (n % cols) * cell_w, (n // cols) * cell_h
            canvas.paste(im, (x + (thumb[0] - im.width) // 2, y))
            text = f"True: Sheath blight\nPred: {class_names[pred]} ({conf:.1%})\n{row['filename']}"
            draw.multiline_text((x + 4, y + 224), text, fill="black", spacing=3)
        canvas.save(OUT / f"sheath_blight_misclassifications_{page_start // sheet_size + 1:02d}.jpg", quality=90)

    # Test split image integrity and visual-quality indicators. Laplacian variance
    # is a blur proxy; low values warrant review, not an automatic rejection.
    quality = []
    for row, path in zip(rows, paths):
        with Image.open(path) as image:
            gray = np.asarray(image.convert("L"), dtype=np.float32)
            lap = -4 * gray + np.roll(gray, 1, 0) + np.roll(gray, -1, 0) + np.roll(gray, 1, 1) + np.roll(gray, -1, 1)
            quality.append({"image_path": row["image_path"], "width": image.width, "height": image.height,
                            "format": image.format or "unknown", "laplacian_variance": float(lap.var()),
                            "mean_brightness": float(gray.mean()), "brightness_std": float(gray.std())})
    save_csv(OUT / "test_image_quality.csv", quality,
             ["image_path", "width", "height", "format", "laplacian_variance", "mean_brightness", "brightness_std"])

    # Exact duplicate/cross-split/cross-class audit from the preparation manifest.
    groups = read_csv(MANIFESTS / "duplicate_groups.csv")
    cross_class = read_csv(MANIFESTS / "cross_class_review.csv")
    split_counts = Counter(r["split"] for r in groups)
    test_groups = [r for r in groups if r["split"] == "test"]
    test_multi = [r for r in test_groups if int(r["member_count"]) > 1]
    unresolved = [r for r in cross_class if r["review_status"] == "unresolved_excluded"]
    non_test_groups = defaultdict(set)
    for r in groups:
        if r["split"] in {"train", "val", "test"}:
            non_test_groups[r["group_id"]].add(r["split"])
    cross_split = {g: s for g, s in non_test_groups.items() if len(s) > 1}
    duplicate_rows = [{"group_id": r["group_id"], "md5": r["md5"], "member_count": r["member_count"],
                       "class_labels": r["class_labels"], "split": r["split"],
                       "benchmark_status": r["benchmark_status"], "output_paths": r["output_paths"]}
                      for r in groups if int(r["member_count"]) > 1 or r["split"] == ""]
    save_csv(OUT / "duplicate_risk_groups.csv", duplicate_rows,
             ["group_id", "md5", "member_count", "class_labels", "split", "benchmark_status", "output_paths"])

    test_counts = Counter(r["class_label"] for r in rows)
    dims = Counter((q["width"], q["height"]) for q in quality)
    blur_values = np.array([q["laplacian_variance"] for q in quality])
    brightness_values = np.array([q["mean_brightness"] for q in quality])
    total = len(rows); accuracy = float((y_true == y_pred).mean())
    top5 = float(np.mean([y_true[i] in np.argsort(probs[i])[-5:] for i in range(total)]))
    report = {
        "model": "YOLO11n-cls", "checkpoint": str(WEIGHTS.relative_to(ROOT)),
        "test_manifest_sha256": hashlib.sha256((MANIFESTS / "test.csv").read_bytes()).hexdigest(),
        "test_images": total, "accuracy_top1": accuracy, "accuracy_top5": top5,
        "class_order": class_names, "test_class_counts": dict(test_counts),
        "sheath_blight_errors": len(sheath_errors),
        "sheath_blight_error_destinations": dict(Counter(class_names[p] for _, _, p, _ in sheath_errors)),
        "duplicate_audit": {"manifest_group_rows_by_split": dict(split_counts),
                             "test_exact_duplicate_groups": len(test_multi),
                             "test_groups_with_multiple_members": len(test_multi),
                             "cross_split_exact_duplicate_groups": len(cross_split),
                             "unresolved_cross_class_groups_excluded": len(unresolved),
                             "cross_class_review_status_counts": dict(Counter(r["review_status"] for r in cross_class)),
                             "note": "MD5 duplicate checks detect byte-identical files; near-duplicate visual similarity is not assessed."},
        "image_quality": {"image_dimensions": {f"{w}x{h}": n for (w, h), n in dims.items()},
                          "unreadable_images": 0,
                          "laplacian_variance_blur_proxy": {"median": float(np.median(blur_values)),
                            "p10": float(np.percentile(blur_values, 10)), "below_10": int((blur_values < 10).sum())},
                          "mean_brightness_0_255": {"median": float(np.median(brightness_values)),
                            "below_40": int((brightness_values < 40).sum()), "above_215": int((brightness_values > 215).sum())}},
        "inference": {"imgsz": IMG_SIZE, "device": "cpu", "training_or_tuning_performed": False}
    }
    (OUT / "analysis_summary.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    # Class-distribution chart for the test split.
    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.bar(list(test_counts), [test_counts[n] for n in test_counts], color="#4385b5")
    ax.set_ylabel("Images"); ax.set_title("Test Split Class Distribution"); ax.tick_params(axis="x", rotation=25)
    fig.tight_layout(); fig.savefig(OUT / "test_class_distribution.png", dpi=180); plt.close(fig)
    print(json.dumps({"top1": accuracy, "top5": top5, "misclassified": len(mis_rows),
                      "sheath_blight_errors": len(sheath_errors), "outputs": str(OUT)}, indent=2))


if __name__ == "__main__":
    main()
