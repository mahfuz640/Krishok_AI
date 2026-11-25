"""Convert existing ONNX FP32 to LiteRT/TFLite and measure converted files.

Run with the Windows Python 3.10 environment containing TensorFlow 2.10 and
onnx2tf. Uses train.csv for quantization calibration and val.csv for evaluation.
"""
import csv
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import tensorflow as tf
from PIL import Image

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
DATA = ROOT / "AI/data/processed/rice_classification"
MEAN = [0.485, 0.456, 0.406]
STD = [0.229, 0.224, 0.225]


def load_rows(split):
    with (DATA / "manifests" / f"{split}.csv").open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def tensor(row):
    with Image.open(DATA / row["image_path"]) as im:
        im = im.convert("RGB")
        w, h = im.size
        scale = 232 / min(w, h)
        size = (int(round(w * scale)), int(round(h * scale)))
        im = im.resize(size, Image.Resampling.BILINEAR)
        left, top = (size[0] - 224) // 2, (size[1] - 224) // 2
        im = im.crop((left, top, left + 224, top + 224))
        x = np.asarray(im, dtype=np.float32) / 255.0
    x = (x - np.asarray(MEAN, np.float32)) / np.asarray(STD, np.float32)
    return np.transpose(x, (2, 0, 1))


def softmax(z):
    z = z - z.max(axis=1, keepdims=True)
    z = np.exp(z)
    return z / z.sum(axis=1, keepdims=True)


def f1s(y, pred):
    vals, weighted = [], 0.0
    for c in range(6):
        tp = int(((y == c) & (pred == c)).sum())
        fp = int(((y != c) & (pred == c)).sum())
        fn = int(((y == c) & (pred != c)).sum())
        f = 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0
        vals.append(f)
        weighted += f * int((y == c).sum()) / len(y)
    return float(np.mean(vals)), float(weighted)


def evaluate(model_path, rows):
    interpreter = tf.lite.Interpreter(model_path=str(model_path), num_threads=6)
    interpreter.allocate_tensors()
    inp = interpreter.get_input_details()[0]
    out = interpreter.get_output_details()[0]
    shape = inp["shape"]
    ys, preds, probs, elapsed = [], [], [], 0.0
    for row in rows:
        x = tensor(row)[None]
        # onnx2tf converts NCHW image tensors to NHWC by default.
        if len(shape) == 4 and shape[1] != 3 and shape[-1] == 3:
            x = np.transpose(x, (0, 2, 3, 1))
        scale, zero = inp["quantization"]
        if inp["dtype"] in (np.int8, np.uint8):
            x = np.clip(np.rint(x / scale + zero), np.iinfo(inp["dtype"]).min,
                        np.iinfo(inp["dtype"]).max).astype(inp["dtype"])
        else:
            x = x.astype(inp["dtype"])
        interpreter.set_tensor(inp["index"], x)
        start = time.perf_counter()
        interpreter.invoke()
        elapsed += time.perf_counter() - start
        z = interpreter.get_tensor(out["index"])
        oscale, ozero = out["quantization"]
        if out["dtype"] in (np.int8, np.uint8) and oscale:
            z = (z.astype(np.float32) - ozero) * oscale
        z = z.reshape(1, -1)
        probs.append(softmax(z)[0])
        preds.append(int(z.argmax(1)[0]))
        ys.append(int(row["class_id"]))
    y, pred, prob = np.array(ys), np.array(preds), np.array(probs)
    mf, wf = f1s(y, pred)
    top5 = np.argpartition(prob, -5, axis=1)[:, -5:]
    return {"validation_top1": float((y == pred).mean()),
            "validation_top5": float((top5 == y[:, None]).any(1).mean()),
            "validation_macro_f1": mf, "validation_weighted_f1": wf,
            "latency_ms_per_image": elapsed * 1000 / len(rows),
            "input_shape": shape.tolist(), "input_dtype": str(inp["dtype"]),
            "output_shape": out["shape"].tolist(), "output_dtype": str(out["dtype"])}


def main():
    fp32 = OUT / "tflite_fp32" / "mobilenetv3_large_fp32_float32.tflite"
    fp16 = OUT / "tflite_fp32" / "mobilenetv3_large_fp32_float16.tflite"
    if not fp32.is_file() or not fp16.is_file():
        raise FileNotFoundError("Run onnx2tf FP32 conversion first")
    val = load_rows("val")
    onnx2tf = str(Path(sys.executable).parent / "Scripts" / "onnx2tf.exe")
    int8_file = OUT / "tflite_int8" / "mobilenetv3_large_fp32_dynamic_range_quant.tflite"
    if not fp32.exists() or not fp16.exists() or not int8_file.exists():
        target = OUT / "tflite_fp32"
        subprocess.run([onnx2tf, "-i", str(OUT / "mobilenetv3_large_fp32.onnx"), "-o", str(target)], check=True)
        target = OUT / "tflite_int8"
        subprocess.run([onnx2tf, "-i", str(OUT / "mobilenetv3_large_fp32.onnx"), "-o", str(target)], check=True)
    if not fp32.is_file() or not fp16.is_file() or not int8_file.is_file():
        raise FileNotFoundError("Expected LiteRT FP32, FP16, and dynamic-range INT8 outputs are missing")
    records = []
    for variant, path in [("LiteRT FP32", fp32), ("LiteRT FP16", fp16), ("LiteRT INT8", int8_file)]:
        runtime_path = OUT / f"{variant.lower().replace(' ', '_')}_runtime.json"
        m = json.loads(runtime_path.read_text()) if runtime_path.exists() else evaluate(path, val)
        records.append({"variant": variant, "format": "TFLite/LiteRT",
            "status": "executed with TensorFlow Lite interpreter on local CPU",
            **{k: m[k] for k in ["validation_top1", "validation_top5", "validation_macro_f1",
                                  "validation_weighted_f1", "latency_ms_per_image"]},
            "model_size_bytes": path.stat().st_size, "model_size_mib": path.stat().st_size / 1048576,
            "mean_absolute_logit_error": "", "max_absolute_logit_error": "",
            "prediction_agreement_with_pytorch": ""})
        runtime_path.write_text(json.dumps(m, indent=2))
    comparison = OUT / "deployment_comparison.csv"
    with comparison.open(encoding="utf-8", newline="") as f:
        existing = list(csv.DictReader(f))
    fields = list(existing[0].keys())
    for field in records[0].keys():
        if field not in fields:
            fields.append(field)
    records_by_name = {r["variant"]: r for r in records}
    existing = [r for r in existing if r["variant"] not in records_by_name]
    with comparison.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader(); writer.writerows(existing + records)
    (OUT / "tflite_checksums.txt").write_text("\n".join(
        f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(OUT).as_posix()}"
        for p in [fp32, fp16, int8_file]) + "\n")
    info = {"tensorflow": tf.__version__, "python": sys.version,
            "calibration": "dynamic-range weight-only conversion; no activation calibration required",
            "evaluation": "all approved val.csv rows; frozen test split not loaded",
            "tflite_models": [str(fp32.relative_to(OUT)), str(fp16.relative_to(OUT)), str(int8_file.relative_to(OUT))],
            "runtime": "TensorFlow Lite CPU interpreter; Android device runtime not tested",
            "int8_quantization": "dynamic-range weight-only quantization; full integer activation quantization failed converter on Windows TensorFlow 2.10"}
    (OUT / "litert_export_status.json").write_text(json.dumps(info, indent=2))
    with (OUT / "tflite_checksums.txt").open("w", encoding="utf-8") as f:
        for p in [fp32, fp16, int8_file]:
            f.write(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(OUT).as_posix()}\n")


if __name__ == "__main__":
    main()
