# YOLO11n-cls error analysis summary

## Model evaluation

Evaluation used the existing `best.pt` checkpoint and the approved 1,463-row test manifest; no training or test-driven tuning was performed. Recorded top-1 accuracy is **75.12%** and top-5 accuracy is **95.01%**. Macro F1 is **0.7163**; weighted F1 is **0.7151**. There are **364** misclassified test images. See `classification_report.csv`, `confusion_matrix.png`, and `normalized_confusion_matrix.png`.

## Main error

Sheath blight recall is **17.90%**. The model predicts Rice Tungro for **103** Sheath blight images and Healthy for **53**. It predicts Sheath blight only 46 times, all correctly. Pair-specific contact sheets and detailed interpretation are in `sheath_blight_analysis.md`.

## Dataset and leakage integrity

Project-side manifest/file inventories match exactly: train 6,827; validation 1,463; test 1,463. No missing or extra files; no MD5 duplicate group crosses splits; all 8 unresolved cross-class groups are excluded. The named Sheath blight_1022.jpg is readable locally. The reported remote scan counts (5,635 train and 1,464 validation) cannot be attributed to a specific cause without the Colab runtime inventory/scan logs; see `dataset_discrepancy_report.md`.

## Recommended next steps

1. Reconcile the Google Colab runtime image inventory with approved manifest SHA-256 values and per-path sets before any further training.
2. Review Sheath blight ? Rice Tungro and Sheath blight ? Healthy galleries with a qualified reviewer; do not alter labels without documented review.
3. Assess near-duplicate leakage separately; current duplicate grouping is exact MD5 only.
4. Keep this test evaluation frozen; use a separate validation-only process for any future model selection.
