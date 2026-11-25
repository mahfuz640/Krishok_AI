# MobileNetV3-Large deployment preparation report

## Source and integrity

- Exact source checkpoint: `../best_model.pt` (17,042,371 bytes).
- SHA-256: `99bd70c5fa8ee99c1d578c44e6099cd8133499ddfdaf1609180cf6530846e5b0`. Hash is unchanged after export; source was read only.
- Checkpoint epoch: 5. The six-class mapping matches the approved manifest: Blast, Brown spot, Healthy, Leaf smut, Rice Tungro, Sheath blight.

## Frozen test boundary

The frozen test split and labels were not read for export, calibration, or deployment comparison. All quality metrics below use the 1,463-image validation split. ONNX INT8 calibration used up to the first 256 approved training rows without labels. LiteRT dynamic-range INT8 uses weight-only quantization. No retraining or test-label changes were made.

## Preprocessing

Pillow RGB decode; torchvision ImageNet V2 evaluation transform: resize shorter edge to 232 with bilinear interpolation and antialiasing, center crop 224 x 224, convert to float32 [0,1], then normalize channels with mean [0.485, 0.456, 0.406] and std [0.229, 0.224, 0.225]. PyTorch, ONNX, and Core ML use NCHW. TFLite uses NHWC. All models accept normalized tensors; image decoding and transforms are external. See `preprocessing_config.json`.

## Validation comparison

Sizes are serialized file sizes. Latency is local CPU model inference only; preprocessing is excluded.

| Variant | Top-1 | Top-5 | Macro F1 | Size MiB | Latency ms/image |
|---|---:|---:|---:|---:|---:|
| PyTorch FP32 | 0.8927 | 0.9973 | 0.8770 | 16.25 | 16.66 |
| ONNX FP32 | 0.8927 | 0.9973 | 0.8770 | 16.06 | 3.36 |
| ONNX FP16 | 0.8934 | 0.9973 | 0.8781 | 8.06 | 3.45 |
| ONNX INT8 | 0.1975 | 0.8264 | 0.0934 | 4.50 | 8.88 |
| LiteRT FP32 | 0.8927 | 0.9973 | 0.8770 | 16.06 | 3.53 |
| LiteRT FP16 | 0.8934 | 0.9973 | 0.8781 | 8.07 | 3.70 |
| LiteRT INT8 | 0.8729 | 0.9973 | 0.8556 | 4.31 | 396.03 |

ONNX FP32 numerical consistency vs PyTorch: mean absolute logit error 2.64e-06; maximum 1.76e-05; top-1 prediction agreement 1.0000. ONNX FP16 agreement is recorded in `deployment_comparison.csv`.

## Export status and suitability

- ONNX FP32 and FP16 passed ONNX structural checks and executed with ONNX Runtime CPU. FP32 matched PyTorch validation predictions exactly. FP16 retained validation quality and reduced size by about half.
- ONNX INT8 has severe validation degradation and is rejected as a deployment candidate.
- LiteRT/TFLite FP32, FP16, and dynamic-range INT8 were executed on the local TensorFlow Lite CPU interpreter. Dynamic-range INT8 keeps accuracy close but is very slow on this host; it is weight-only INT8, not full integer quantization.
- Full integer TFLite conversion was attempted and failed in the available TensorFlow 2.10/onnx2tf conversion path; no full integer artifact is claimed.
- Core ML neuralnetwork `.mlmodel` conversion and serialization succeeded. Core ML runtime evaluation is not available on Windows.
- No Android or iOS device was available for testing. This report makes no mobile compatibility claim.

## Frozen-test comparison context

The supplied one-pass frozen comparison remains recorded in `../final_test_comparison/test_comparison_summary.json`: MobileNetV3-Large top-1 88.59%, top-5 99.79%, macro F1 0.8726, weighted F1 0.8870, 4,209,718 parameters, 16.25 MiB checkpoint, 21.96 ms/image CPU. YOLO11n-cls top-1 75.12%, macro F1 0.7163, 3.05 MiB. Frozen-test figures were not recomputed or used to tune exports.

## Artifacts

See `model_manifest.json` and `model_checksums.txt` for checkpoint and export identity. The source best checkpoint was preserved.
