# YOLO11n-cls test error analysis

## Scope and provenance

Inference-only analysis of the 1,463 images listed in `AI/data/processed/rice_classification/manifests/test.csv`, using `rice/KrishokAI_results_archive/YOLO11_Rice_v1_local/weights/best.pt` at 224 px. The test manifest SHA-256 is recorded in `analysis_summary.json`. The test labels were read from the manifest and were not changed. No training, tuning, or checkpoint writes were performed. The checkpoint and prior evaluation artifacts were preserved.

The rerun reproduces the supplied headline scores: **75.12% top-1** and **95.01% top-5**. There are **364 misclassified images** in the exported CSV.

## Main finding: Sheath blight

Of 257 Sheath blight test images, 46 are correct (17.90% recall) and 211 are errors. The most frequent destinations match the reported issue: Rice Tungro **103** and Healthy **53**. Remaining errors are Brown spot **44**, Leaf smut **6**, and Blast **5**. Sheath blight precision is 100% because the model's 46 predictions of that class were all correct; it rarely predicts the class.

This is a strong class-specific recall failure. The largest confusion is with Rice Tungro, and the dataset audit separately records unresolved cross-class exact duplicates between those two labels (excluded from the prepared benchmark). This warrants human review of representative examples and original labels before drawing a biological conclusion. The error gallery provides all 211 cases in paginated contact sheets.

## Per-class results

| Class | Test support | Precision | Recall | F1 |
|---|---:|---:|---:|---:|
| Blast | 199 | 0.8173 | 0.8543 | 0.8354 |
| Brown spot | 326 | 0.7294 | 0.8436 | 0.7824 |
| Healthy | 236 | 0.7739 | 0.9280 | 0.8439 |
| Leaf smut | 109 | 0.7297 | 0.7431 | 0.7364 |
| Rice Tungro | 336 | 0.7032 | 0.9167 | 0.7959 |
| Sheath blight | 257 | 1.0000 | 0.1790 | 0.3036 |

The machine-readable report is `per_class_metrics.csv`. The confusion matrix values are row-normalized (true class rows) in the PNG and CSV; integer counts are provided separately.

## Dataset distribution and image quality

Test class counts are Blast 199, Brown spot 326, Healthy 236, Leaf smut 109, Rice Tungro 336, and Sheath blight 257. Counts range from 109 to 336, so the test set is not class-balanced; Leaf smut has the smallest support. All 1,463 images decoded successfully and measured 1024×1024 JPEG. The median grayscale mean brightness was 115.4/255, with no image below 40 or above 215. The Laplacian-variance blur proxy had median 144.5 and 10th percentile 79.8; none fell below the deliberately conservative 10-point severe-blur flag. These are screening statistics, not a substitute for visual review, and do not assess focus or disease visibility directly.

## Duplicate and cross-class risk

The preparation manifest groups byte-identical images using MD5. There are **4 exact duplicate groups within test**, all Sheath blight pairs. This means 8 test entries represent 4 distinct byte patterns, so the effective unique-image count is 1,459. No byte-identical group crosses train, validation, and test splits. Eight known cross-class exact-duplicate groups (including Rice Tungro/Sheath blight pairs) are marked unresolved and excluded from the prepared benchmark. Full details are in `duplicate_risk_groups.csv` and the source `cross_class_review.csv`.

MD5 detects exact byte matches only. Near-duplicate images (resized, recompressed, or visually similar photographs) were not assessed, so a near-duplicate leakage risk remains unquantified.

## Artifacts

- `normalized_confusion_matrix.png`, `confusion_matrix_normalized.csv`, `confusion_matrix_counts.csv`
- `per_class_metrics.csv`
- `misclassified_test_images.csv` with image path, true label, predicted label, and top-1 confidence
- `sheath_blight_misclassifications_*.jpg` paginated visual gallery
- `test_class_distribution.png`, `test_image_quality.csv`
- `duplicate_risk_groups.csv`, `analysis_summary.json`
- `run_error_analysis.py` to reproduce the inference and reports

Run from the repository root with an environment containing Ultralytics, PyTorch, NumPy, Pillow, and Matplotlib:

```powershell
conda run -n car python documentation/YOLO11_error_analysis/run_error_analysis.py
```
