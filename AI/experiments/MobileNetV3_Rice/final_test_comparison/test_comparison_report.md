# Final Test Comparison — MobileNetV3-Large vs YOLO11n-cls

**Evaluation type:** Single-pass inference-only comparison. No training, tuning, threshold changes, or label edits were performed. Both models received the same 1,463 ordered test images and approved class IDs from the frozen `test.csv` manifest.

- Test manifest SHA-256: `91fdd26f22243861fcf1eea53b3312d1e1bcdb5800ffa822f56ab486b3d59d9f`
- Class order: Blast, Brown spot, Healthy, Leaf smut, Rice Tungro, Sheath blight.
- Device: CPU for both.

## Overall results

| Metric | MobileNetV3-Large | YOLO11n-cls | Difference (MobileNet − YOLO) |
|---|---:|---:|---:|
| Top-1 accuracy | 88.59% | 75.12% | +13.47 percentage points |
| Top-5 accuracy | 99.79% | 95.01% | +4.78 percentage points |
| Macro precision | 87.10% | 79.23% | +7.87 percentage points |
| Macro recall | 87.78% | 74.41% | +13.37 percentage points |
| Macro F1 | 0.8726 | 0.7163 | +0.1564 |
| Weighted F1 | 0.8870 | 0.7151 | +0.1719 |

MobileNetV3-Large achieved higher top-1 accuracy, top-5 accuracy, macro precision/recall/F1, and weighted F1 on this test evaluation. Its biggest practical trade-off is footprint: **4,209,718 parameters / 16.25 MiB** versus YOLO11n-cls **1,538,790 parameters / 3.05 MiB**.

## Per-class F1

| Class | MobileNetV3-Large | YOLO11n-cls |
|---|---:|---:|
| Blast | 0.8497 | 0.8354 |
| Brown spot | 0.8456 | 0.7824 |
| Healthy | 0.9391 | 0.8439 |
| Leaf smut | 0.7407 | 0.7364 |
| Rice Tungro | 0.9159 | 0.7959 |
| Sheath blight | 0.9447 | 0.3036 |

## CPU inference timing

Batch 32; reported elapsed time includes each model's preprocessing and inference path. This is a single run on the same CPU, so small timing differences are not a stable performance claim.

| Model | Total time, 1,463 images | Mean per image |
|---|---:|---:|
| MobileNetV3-Large | 32.13 s | 21.96 ms |
| YOLO11n-cls | 31.65 s | 21.63 ms |

GPU timing is unavailable because this machine has no CUDA GPU.

## Interpretation and artifacts

On the approved test split, MobileNetV3-Large is the stronger classifier, especially for Sheath blight. YOLO11n-cls is substantially smaller, while observed CPU throughput was nearly the same in this batch run.

Raw and normalized confusion matrices, per-class metrics, all predictions/confidences, summary JSON, and the reproducible inference script are in this folder. Test labels remain unchanged. Since these test results are now visible and used for comparison, do not use this test split to tune or select future models; reserve a new held-out set for another final comparison.
