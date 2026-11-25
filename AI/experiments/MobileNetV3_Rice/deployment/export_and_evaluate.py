#!/usr/bin/env python3
"""Export and validate the frozen MobileNetV3-Large checkpoint.

Export comparisons use the approved train split for quantization calibration and
the validation split for quality measurement. The frozen test split is never read.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import platform
import shutil
import sys
import time
from pathlib import Path

import numpy as np
import onnx
import onnxruntime as ort
import torch
from PIL import Image
from torch import nn
from torch.utils.data import DataLoader, Dataset
from torchvision import models
from torchvision.models import MobileNet_V3_Large_Weights

torch.set_num_threads(6)


ROOT = Path(__file__).resolve().parents[4]
EXP = ROOT / "AI/experiments/MobileNetV3_Rice"
OUT = Path(__file__).resolve().parent
DATA = ROOT / "AI/data/processed/rice_classification"
MAPPING = ["Blast", "Brown spot", "Healthy", "Leaf smut", "Rice Tungro", "Sheath blight"]
MEAN = [0.485, 0.456, 0.406]
STD = [0.229, 0.224, 0.225]
SIZE = 224


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def model_load():
    ckpt_path = EXP / "best_model.pt"
    ckpt = torch.load(ckpt_path, map_location="cpu", weights_only=True)
    expected = {name: i for i, name in enumerate(MAPPING)}
    if ckpt.get("class_to_id") != expected:
        raise RuntimeError(f"Checkpoint class mapping mismatch: {ckpt.get('class_to_id')}")
    if ckpt.get("test_used_for_training_or_tuning") is not False:
        raise RuntimeError("Checkpoint lacks the expected frozen-test guard metadata")
    model = models.mobilenet_v3_large(weights=None)
    model.classifier[-1] = nn.Linear(model.classifier[-1].in_features, 6)
    model.load_state_dict(ckpt["model_state_dict"], strict=True)
    return model.eval(), ckpt


class Rows(Dataset):
    def __init__(self, split: str):
        path = DATA / "manifests" / f"{split}.csv"
        with path.open(encoding="utf-8-sig", newline="") as f:
            self.rows = list(csv.DictReader(f))
        self.split = split

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, i):
        row = self.rows[i]
        with Image.open(DATA / row["image_path"]) as image:
            x = MobileNet_V3_Large_Weights.IMAGENET1K_V2.transforms()(image.convert("RGB"))
        return x.numpy(), int(row["class_id"])


def evaluate_torch(model, loader):
    y_true, y_pred, y_prob, y_logits, elapsed = [], [], [], [], 0.0
    with torch.inference_mode():
        for x, y in loader:
            start = time.perf_counter()
            z = model(x)
            elapsed += time.perf_counter() - start
            y_true.extend(y.numpy().tolist())
            y_pred.extend(z.argmax(1).numpy().tolist())
            y_prob.extend(z.softmax(1).numpy().tolist())
            y_logits.extend(z.numpy().tolist())
    result = metrics(np.array(y_true), np.array(y_pred), np.array(y_prob), elapsed)
    result["predictions"] = y_pred
    result["logits"] = y_logits
    return result


def metrics(y, pred, prob, elapsed):
    per_f1 = []
    weighted = 0.0
    for c in range(6):
        tp = int(((pred == c) & (y == c)).sum())
        fp = int(((pred == c) & (y != c)).sum())
        fn = int(((pred != c) & (y == c)).sum())
        f = 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.0
        per_f1.append(f)
        weighted += f * int((y == c).sum()) / len(y)
    top5 = np.argpartition(prob, -5, axis=1)[:, -5:]
    return {"top1_accuracy": float((pred == y).mean()),
            "top5_accuracy": float((top5 == y[:, None]).any(axis=1).mean()),
            "macro_f1": float(np.mean(per_f1)), "weighted_f1": float(weighted),
            "latency_ms_per_image": float(elapsed * 1000 / len(y))}


class Calib:
    def __init__(self, loader):
        self.it = iter(loader)
    def get_next(self):
        try:
            x, _ = next(self.it)
        except StopIteration:
            return None
        return {"input": x.numpy()}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    ckpt_path = EXP / "best_model.pt"
    before_hash = sha256(ckpt_path)
    model, ckpt = model_load()
    validation = Rows("val")
    train = Rows("train")
    val_loader = DataLoader(validation, batch_size=1, shuffle=False, num_workers=0)
    train_loader = DataLoader(torch.utils.data.Subset(train, range(min(256, len(train)))),
                              batch_size=1, shuffle=False, num_workers=0)

    # The script reproduces torchvision ImageNet V2 evaluation preprocessing:
    # RGB decode, Resize(232, bilinear, antialias), center crop to 224, ToTensor, Normalize.
    weights_transform = MobileNet_V3_Large_Weights.IMAGENET1K_V2.transforms()
    class TorchEval(Dataset):
        def __len__(self): return len(validation.rows)
        def __getitem__(self, i):
            row = validation.rows[i]
            with Image.open(DATA / row["image_path"]) as image:
                x = weights_transform(image.convert("RGB"))
            return x, int(row["class_id"])
    eval_loader = DataLoader(TorchEval(), batch_size=1, shuffle=False, num_workers=0)
    baseline = evaluate_torch(model, eval_loader)

    fp32 = OUT / "mobilenetv3_large_fp32.onnx"
    sample = torch.zeros(1, 3, SIZE, SIZE)
    if not fp32.exists():
        torch.onnx.export(model, sample, fp32, input_names=["input"], output_names=["logits"],
                          opset_version=17, dynamo=False, dynamic_axes={"input": {0: "batch"}, "logits": {0: "batch"}})
    onnx.checker.check_model(str(fp32), full_check=True)

    import onnxconverter_common
    fp16 = OUT / "mobilenetv3_large_fp16.onnx"
    if not fp16.exists():
        fp16_model = onnxconverter_common.float16.convert_float_to_float16(
            onnx.load(str(fp32)), keep_io_types=True)
        onnx.save(fp16_model, str(fp16))
    onnx.checker.check_model(str(fp16), full_check=True)

    import onnxruntime.quantization as quant
    int8 = OUT / "mobilenetv3_large_int8_train_calibrated.onnx"
    if not int8.exists():
        quant.quantize_static(str(fp32), str(int8), Calib(train_loader),
                          quant_format=quant.QuantFormat.QDQ, per_channel=True,
                          activation_type=quant.QuantType.QInt8, weight_type=quant.QuantType.QInt8,
                          calibrate_method=quant.CalibrationMethod.MinMax,
                          extra_options={"ActivationSymmetric": True, "WeightSymmetric": True})
    onnx.checker.check_model(str(int8), full_check=True)

    rows = []
    for name, path in [("PyTorch FP32", None), ("ONNX FP32", fp32),
                       ("ONNX FP16", fp16), ("ONNX INT8", int8)]:
        if path is None:
            result = baseline
        else:
            session = ort.InferenceSession(str(path), providers=["CPUExecutionProvider"])
            ys, ps, probs, logits, duration = [], [], [], [], 0.0
            for x, y in eval_loader:
                array = x.numpy()
                start = time.perf_counter()
                z = session.run(["logits"], {"input": array})[0]
                duration += time.perf_counter() - start
                exp = np.exp(z - z.max(axis=1, keepdims=True))
                probs.extend((exp / exp.sum(axis=1, keepdims=True)).tolist())
                logits.extend(z.tolist())
                ys.append(int(y.item())); ps.append(int(z.argmax(1)[0]))
            result = metrics(np.array(ys), np.array(ps), np.array(probs), duration)
            differences = np.abs(np.asarray(baseline["logits"]) - np.asarray(logits))
            result["mean_absolute_logit_error"] = float(differences.mean())
            result["max_absolute_logit_error"] = float(differences.max())
            result["prediction_agreement_with_pytorch"] = float(np.mean(
                np.asarray(baseline["predictions"]) == np.asarray(ps)))
        size = ckpt_path.stat().st_size if path is None else path.stat().st_size
        rows.append({"variant": name, "format": "PyTorch checkpoint" if path is None else "ONNX",
                     "status": "executed on local CPU", "validation_top1": result["top1_accuracy"],
                     "validation_top5": result["top5_accuracy"], "validation_macro_f1": result["macro_f1"],
                     "validation_weighted_f1": result["weighted_f1"],
                     "model_size_bytes": size, "model_size_mib": size / 1048576,
                     "latency_ms_per_image": result["latency_ms_per_image"],
                     "mean_absolute_logit_error": result.get("mean_absolute_logit_error", 0.0),
                     "max_absolute_logit_error": result.get("max_absolute_logit_error", 0.0),
                     "prediction_agreement_with_pytorch": result.get("prediction_agreement_with_pytorch", 1.0)})
    with (OUT / "deployment_comparison.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)

    # Best-effort Core ML export. Execution is not available on Windows.
    coreml_status = "not attempted"
    try:
        import coremltools as ct
        traced = torch.jit.trace(model, sample)
        ml = ct.convert(traced, inputs=[ct.TensorType(name="input", shape=sample.shape)],
                        outputs=[ct.TensorType(name="logits")], convert_to="neuralnetwork")
        ml.save(str(OUT / "mobilenetv3_large_fp32.mlmodel"))
        coreml_status = "neuralnetwork .mlmodel converted; Core ML runtime execution unavailable on Windows"
    except Exception as e:
        coreml_status = f"conversion failed: {type(e).__name__}: {e}"

    tflite_status = "FP32 and FP16 LiteRT/TFLite exported and executed on Windows CPU; dynamic-range INT8 weight-only exported and executed. Full integer activation quantization failed in TensorFlow 2.10 converter. Android device not tested."
    if sha256(ckpt_path) != before_hash:
        raise RuntimeError("Source checkpoint changed during export")

    mapping = {name: i for i, name in enumerate(MAPPING)}
    (OUT / "preprocessing_config.json").write_text(json.dumps({
        "input_color": "RGB", "decode": "Pillow RGB", "evaluation_resize": "shorter edge 232, bilinear, antialias=True",
        "center_crop": [224, 224], "tensor_layout": "NCHW", "input_shape": [1, 3, 224, 224],
        "input_dtype": "float32", "scale": "uint8 to float32 [0,1]",
        "normalization": {"mean": MEAN, "std": STD}, "source": "torchvision MobileNet_V3_Large_Weights.IMAGENET1K_V2.transforms()",
        "model_input_layouts": {"pytorch": "NCHW", "onnx": "NCHW", "coreml_tensor": "NCHW", "tflite": "NHWC"},
        "classes": mapping,
        "export_input_contract": "normalized float32 NCHW; decoding/resize/crop/normalization are external to model"
    }, indent=2), encoding="utf-8")
    manifest = {"model": "MobileNetV3-Large", "selection": "provisional primary rice disease classifier",
        "source_checkpoint": "../best_model.pt", "source_checkpoint_sha256": before_hash,
        "source_checkpoint_bytes": ckpt_path.stat().st_size, "source_preserved": True,
        "checkpoint_epoch": ckpt.get("epoch"), "class_mapping": mapping,
        "architecture": "torchvision.models.mobilenet_v3_large; classifier[-1]=Linear(1280,6)",
        "parameters": sum(p.numel() for p in model.parameters()),
        "preprocessing": "preprocessing_config.json", "test_set_used_for_export_or_quantization": False,
        "calibration": "first 256 rows of approved train.csv; no labels used",
        "validation_comparison": "deployment_comparison.csv",
        "onnx": {p.name: {"sha256": sha256(p), "bytes": p.stat().st_size} for p in [fp32, fp16, int8]},
        "tflite_status": tflite_status, "coreml_status": coreml_status,
        "baseline_validation": baseline, "conversion_environment": {
            "python": sys.version, "platform": platform.platform(), "torch": torch.__version__,
            "torchvision": __import__("torchvision").__version__, "onnx": onnx.__version__,
            "onnxruntime": ort.__version__}}
    (OUT / "model_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (OUT / "model_checksums.txt").write_text(
        "SHA-256 checksums (source checkpoint and generated deployment models)\n" +
        f"{before_hash}  ../best_model.pt\n" + "".join(f"{sha256(p)}  {p.name}\n" for p in [fp32, fp16, int8]) +
        ((OUT / "tflite_checksums.txt").read_text(encoding="utf-8") if (OUT / "tflite_checksums.txt").exists() else ""), encoding="utf-8")
    report = ["# MobileNetV3-Large deployment preparation report", "",
        "## Source and integrity", "", f"- Checkpoint: `../best_model.pt` ({ckpt_path.stat().st_size:,} bytes).",
        f"- SHA-256: `{before_hash}`. The file hash was unchanged across export.",
        f"- Checkpoint epoch: {ckpt.get('epoch')}; class mapping verified against approved mapping.",
        "- Original checkpoint was read only and preserved.", "",
        "## Frozen test boundary", "", "No test images or labels were read for conversion, calibration, or this deployment comparison. Quantization used up to 256 train images without labels; quality metrics and latency use the validation split only.", "",
        "## Preprocessing and outputs", "", "The model accepts normalized float32 NCHW tensors. Exact torchvision ImageNet V2 evaluation preprocessing is specified in `preprocessing_config.json`. ONNX FP32, FP16, and INT8 models passed ONNX structural checks and were executed with ONNX Runtime CPU. Metrics and artifact sizes are in `deployment_comparison.csv`.", "",
        "## Conversion status", "", f"- LiteRT/TFLite: {tflite_status}.", f"- Core ML: {coreml_status}.",
        "- Local Windows conversion or runtime execution does not establish Android/iOS device compatibility. Android and iOS device validation remains required before claiming mobile compatibility.", "",
        "## Numerical consistency", "", "See PyTorch and ONNX FP32 validation rows in `deployment_comparison.csv`. Accuracy and F1 differences are measured on the same approved validation rows. Latencies are local CPU measurements and are not comparable to the earlier end-to-end frozen-test timing because preprocessing/runtime conditions differ.", "",
        "## Frozen comparison context", "", "The supplied final frozen-test comparison remains recorded in the existing experiment artifact: MobileNetV3-Large top-1 88.59%, top-5 99.79%, macro F1 0.8726, weighted F1 0.8870, 4,209,718 parameters, 16.25 MiB checkpoint, 21.96 ms/image CPU. YOLO11n-cls top-1 75.12%, macro F1 0.7163, 3.05 MiB. These figures were not recomputed or used to tune exports.", ""]
    (OUT / "deployment_report.md").write_text("\n".join(report), encoding="utf-8")


if __name__ == "__main__":
    main()
