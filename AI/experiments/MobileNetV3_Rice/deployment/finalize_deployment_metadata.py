"""Refresh deployment manifest, checksum inventory, and summary report."""
import csv
import hashlib
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
EXP = OUT.parent
CKPT = EXP / "best_model.pt"


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def info(path):
    return {"path": path.relative_to(OUT).as_posix(), "bytes": path.stat().st_size,
            "sha256": sha(path)}


def main():
    manifest_path = OUT / "model_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["baseline_validation"] = {k: v for k, v in manifest["baseline_validation"].items()
        if k in {"top1_accuracy", "top5_accuracy", "macro_f1", "weighted_f1", "latency_ms_per_image"}}
    manifest["source_checkpoint_sha256_verified_after_export"] = sha(CKPT)
    manifest["source_checkpoint_unchanged"] = sha(CKPT) == manifest["source_checkpoint_sha256"]
    manifest["coreml_artifact"] = info(OUT / "mobilenetv3_large_fp32.mlmodel")
    tflite = [OUT / "tflite_fp32" / "mobilenetv3_large_fp32_float32.tflite",
              OUT / "tflite_fp32" / "mobilenetv3_large_fp32_float16.tflite",
              OUT / "tflite_int8" / "mobilenetv3_large_fp32_dynamic_range_quant.tflite"]
    manifest["litert_artifacts"] = [info(p) for p in tflite]
    manifest["litert_runtime_status"] = json.loads((OUT / "litert_export_status.json").read_text())
    manifest["litert_int8_type"] = "Dynamic range, weight-only INT8; FP32 input/output; not full integer"
    manifest["full_integer_tflite_status"] = "Conversion attempted with representative data but failed in TensorFlow 2.10/onnx2tf; no full-integer file produced"
    manifest["coreml_status"] = "Core ML neuralnetwork .mlmodel serialized successfully; runtime unavailable on Windows"
    manifest["android_device_tested"] = False
    manifest["ios_device_tested"] = False
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    models = [CKPT, OUT / "mobilenetv3_large_fp32.onnx", OUT / "mobilenetv3_large_fp16.onnx",
              OUT / "mobilenetv3_large_int8_train_calibrated.onnx",
              OUT / "mobilenetv3_large_fp32.mlmodel", *tflite]
    lines = ["SHA-256 checksums for source and deployment artifacts"]
    lines += [f"{sha(p)}  {p.relative_to(EXP).as_posix()}" for p in models]
    (OUT / "model_checksums.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    with (OUT / "deployment_comparison.csv").open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    by = {r["variant"]: r for r in rows}
    report = ["# MobileNetV3-Large deployment preparation report", "",
        "## Source and integrity", "",
        f"- Exact source checkpoint: `../best_model.pt` ({CKPT.stat().st_size:,} bytes).",
        f"- SHA-256: `{sha(CKPT)}`. Hash is unchanged after export; source was read only.",
        "- Checkpoint epoch: 5. The six-class mapping matches the approved manifest: Blast, Brown spot, Healthy, Leaf smut, Rice Tungro, Sheath blight.", "",
        "## Frozen test boundary", "",
        "The frozen test split and labels were not read for export, calibration, or deployment comparison. All quality metrics use the 1,463-image validation split. ONNX INT8 calibration used up to the first 256 approved training rows without labels. LiteRT dynamic-range INT8 uses weight-only quantization. No retraining or test-label changes were made.", "",
        "## Preprocessing", "",
        "Pillow RGB decode; torchvision ImageNet V2 evaluation transform: resize shorter edge to 232 with bilinear interpolation and antialiasing, center crop 224 x 224, convert to float32 [0,1], then normalize channels with mean [0.485, 0.456, 0.406] and std [0.229, 0.224, 0.225]. PyTorch, ONNX, and Core ML use NCHW. TFLite uses NHWC. All models accept normalized tensors; image decoding and transforms are external. See `preprocessing_config.json`.", "",
        "## Validation comparison", "", "Sizes are serialized file sizes. Latency is local CPU model inference only; preprocessing is excluded.", "",
        "| Variant | Top-1 | Top-5 | Macro F1 | Size MiB | Latency ms/image |",
        "|---|---:|---:|---:|---:|---:|"]
    for name in ["PyTorch FP32", "ONNX FP32", "ONNX FP16", "ONNX INT8", "LiteRT FP32", "LiteRT FP16", "LiteRT INT8"]:
        r = by[name]
        report.append(f"| {name} | {float(r['validation_top1']):.4f} | {float(r['validation_top5']):.4f} | {float(r['validation_macro_f1']):.4f} | {float(r['model_size_mib']):.2f} | {float(r['latency_ms_per_image']):.2f} |")
    report += ["", "ONNX FP32 numerical consistency vs PyTorch: "
        f"mean absolute logit error {float(by['ONNX FP32']['mean_absolute_logit_error']):.3g}; maximum {float(by['ONNX FP32']['max_absolute_logit_error']):.3g}; top-1 prediction agreement {float(by['ONNX FP32']['prediction_agreement_with_pytorch']):.4f}. ONNX FP16 agreement is recorded in `deployment_comparison.csv`.", "",
        "## Export status and suitability", "",
        "- ONNX FP32 and FP16 passed ONNX structural checks and executed with ONNX Runtime CPU. FP32 matched PyTorch validation predictions exactly. FP16 retained validation quality and reduced size by about half.",
        "- ONNX INT8 has severe validation degradation and is rejected as a deployment candidate.",
        "- LiteRT/TFLite FP32, FP16, and dynamic-range INT8 were executed on the local TensorFlow Lite CPU interpreter. Dynamic-range INT8 keeps accuracy close but is very slow on this host; it is weight-only INT8, not full integer quantization.",
        "- Full integer TFLite conversion was attempted and failed in the available TensorFlow 2.10/onnx2tf conversion path; no full integer artifact is claimed.",
        "- Core ML neuralnetwork `.mlmodel` conversion and serialization succeeded. Core ML runtime evaluation is not available on Windows.",
        "- No Android or iOS device was available for testing. This report makes no mobile compatibility claim.", "",
        "## Frozen-test comparison context", "",
        "The supplied one-pass frozen comparison remains recorded in `../final_test_comparison/test_comparison_summary.json`: MobileNetV3-Large top-1 88.59%, top-5 99.79%, macro F1 0.8726, weighted F1 0.8870, 4,209,718 parameters, 16.25 MiB checkpoint, 21.96 ms/image CPU. YOLO11n-cls top-1 75.12%, macro F1 0.7163, 3.05 MiB. Frozen-test figures were not recomputed or used to tune exports.", "",
        "## Artifacts", "", "See `model_manifest.json` and `model_checksums.txt` for checkpoint and export identity. The source best checkpoint was preserved.", ""]
    (OUT / "deployment_report.md").write_text("\n".join(report), encoding="utf-8")


if __name__ == "__main__":
    main()
