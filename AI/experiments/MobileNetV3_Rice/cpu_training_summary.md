# MobileNetV3-Large CPU Training Run Report

**Status:** Completed  
**Execution:** Local CPU, PyTorch CPU build  
**Training data:** Approved train and validation manifests only  
**Test partition:** Kept frozen; the images were decoded and hash-verified during integrity preflight but were never passed to the model, optimizer, scheduler, or evaluation loop.

## Preflight

All manifest SHA-256 checks, exact path inventories, image decoding and per-file MD5 checks passed before training. Split counts were train 6,827, validation 1,463, and test 1,463. All six class IDs matched the approved mapping, duplicate groups did not cross splits, and unresolved cross-class duplicate groups were excluded. Details: `cpu_run_integrity_report.md`.

## Training configuration

- ImageNet-pretrained MobileNetV3-Large; classifier replaced with six outputs.
- 224 × 224 input, AdamW, ReduceLROnPlateau, early stopping patience 8.
- Seed 42; batch size 32; maximum 30 epochs.
- Stopped after 13 epochs; best validation-loss checkpoint is epoch 5.
- Elapsed training time: 94.67 minutes.

## Best-checkpoint validation results

| Metric | Result |
|---|---:|
| Accuracy | 89.27% |
| Macro precision | 87.41% |
| Macro recall | 88.39% |
| Macro F1 | 0.8770 |
| Weighted F1 | 0.8930 |

Per-class metrics and validation confusion matrix are in `validation_classification_report.csv` and `validation_confusion_matrix.png`. Loss curves are in `training_validation_loss_curves.png`.

## Model size and latency

- Parameters: 4,209,718.
- Best checkpoint: 17,042,371 bytes (16.25 MiB).
- CPU batch-one forward latency: mean 19.18 ms, median 19.15 ms, p95 25.80 ms.
- Latency used 50 preprocessed 224 × 224 validation tensors; image decoding and preprocessing are excluded.
- GPU latency: unavailable; no CUDA GPU was present.

## Artifacts

- `best_model.pt`, `last_model.pt`
- `training_history.csv`, `training_validation_loss_curves.png`
- `validation_classification_report.csv`, `validation_confusion_matrix.png`, `validation_metrics.json`
- `inference_latency.json`, `environment.json`, `cpu_training.log`
- `train_mobilenet_cpu.py` (reproducible CPU run entry point)

The approved dataset and manifests were read-only. YOLO11 checkpoints were not modified. No test accuracy or test metrics were generated.
