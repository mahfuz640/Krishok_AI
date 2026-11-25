# Krishok AI rice classification notebooks

## Dataset upload to Google Drive

1. Upload the complete prepared folder from the project:
   AI/data/processed/rice_classification/
2. Keep the directory structure unchanged under:
   MyDrive/Krishok_AI/data/processed/rice_classification/
3. Include train, val, and test class folders and the entire manifests directory. Do not regenerate or edit the approved CSV files. Do not upload or use the original dataset ZIPs for these notebooks.
4. In Colab, select Runtime > Change runtime type > T4 GPU (or another available CUDA GPU). Each notebook mounts Drive and checks for a GPU.

The MobileNet preflight checks pinned SHA-256 values for all approved CSV manifests, exact relative-path inventories, image MD5 values and full decoding, six-class mapping, counts, duplicate-group isolation, and excluded cross-class groups. It rebuilds a new `/content/rice_classification_verified/` runtime copy and stops on any mismatch; it never silently skips corrupt files or removes an existing runtime folder.

## Run order

1. Open Rice_Disease_YOLO11_Training.ipynb and Rice_Disease_MobileNetV3_Training.ipynb in Google Colab. Run setup and preflight cells. Training is disabled by default; set START_TRAINING = True explicitly after checking the data and runtime. Each notebook uses at most 30 epochs and saves its best validation-selected checkpoint to Drive.
2. Optional exports are also disabled by default. Set RUN_EXPORTS = True in the relevant model notebook after its best checkpoint exists.
3. Only after both model checkpoints exist, open Rice_Model_Comparison.ipynb. Its test-evaluation flag is disabled by default. Set RUN_TEST_EVALUATION = True to evaluate the same held-out test.csv once for both models.

The MobileNet notebook reads test.csv only for manifest/image integrity preflight; test rows are excluded from its train/validation loaders. Its optional final test report is disabled by default and is for one frozen report only. The comparison notebook reads test.csv only after confirming both best checkpoints are present. Do not use test metrics to change hyperparameters and rerun the models.

## Outputs

Run artifacts are written beneath `MyDrive/Krishok_AI/`: YOLO and comparison outputs stay under `runs/rice_classification/`; MobileNet outputs go under `AI/experiments/MobileNetV3_Rice/`.

- yolo11n_cls/: best.pt, results.csv, Ultralytics plots, and environment.json
- `AI/experiments/MobileNetV3_Rice/`: integrity report, best_model.pt, last_model.pt, training history/curves, validation report/confusion matrix, CPU/GPU latency, model size, environment, and optional final-test metrics/confusion matrix
- YOLO exports are written by Ultralytics beside the YOLO best checkpoint; MobileNet ONNX and TorchScript exports are saved in `AI/experiments/MobileNetV3_Rice/`.
- comparison/: test metrics, per-class metrics, confusion matrices, predictions, loss curves, and model_comparison.csv

The comparison records the installed framework versions, GPU, preprocessing notes, parameter counts, checkpoint file sizes, and measured latency. It does not contain prefilled or invented accuracy values.

## Reproducibility notes

- Seed is fixed at 42 in the notebooks.
- Ultralytics is pinned to 8.4.215. PyTorch and torchvision are kept from the active Colab CUDA image; their exact versions are recorded because Colab GPU builds vary.
- YOLO uses the Ultralytics classification input pipeline and 224 px size. MobileNetV3-Large uses its ImageNet weight preset for evaluation (resize/center-crop and ImageNet mean/std); training adds a random resized crop and horizontal flip with the same normalization.
- Preprocessing differs by architecture and is recorded in the comparison outputs. Both models use identical manifest rows, class IDs, and test image paths.
- TorchScript is included because it was explicitly requested. Current PyTorch documentation marks TorchScript deprecated in favor of torch.export; use TorchScript only when the target runtime requires it.

## Official references

- Ultralytics classification and training: https://docs.ultralytics.com/tasks/classify
- Ultralytics YOLO11: https://docs.ultralytics.com/models/yolo11
- Ultralytics export formats: https://docs.ultralytics.com/modes/export
- Torchvision MobileNetV3-Large: https://docs.pytorch.org/vision/stable/models/mobilenetv3.html
- PyTorch ONNX export: https://docs.pytorch.org/docs/stable/onnx_export.html
- PyTorch TorchScript notice: https://docs.pytorch.org/docs/stable/notes/cpu_threading_torchscript_inference

