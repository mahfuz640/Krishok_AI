# AI integration plan

## Model identity

- Architecture: MobileNetV3-Large, six rice classes.
- Source checkpoint: `AI/experiments/MobileNetV3_Rice/best_model.pt` (SHA-256 `99bd70c5fa8ee99c1d578c44e6099cd8133499ddfdaf1609180cf6530846e5b0`). The file was inspected in place and not copied or modified.
- Approved class IDs: 0 Blast, 1 Brown spot, 2 Healthy, 3 Leaf smut, 4 Rice Tungro, 5 Sheath blight.
- Selected artifact for a future LiteRT Android path: `AI/experiments/MobileNetV3_Rice/deployment/tflite_fp32/mobilenetv3_large_fp32_float32.tflite`.
- The checkpoint and deployment report remain outside this app directory. No model copy is bundled or referenced with a static `require()`.
- The exported LiteRT FP32 file was exercised with a TensorFlow Lite interpreter on Windows. It has not been run through `react-native-fast-tflite` on Android or iOS; compatibility is not claimed.

## Input contract

- Input tensor: `[1, 224, 224, 3]`, NHWC, float32.
- Decode to oriented RGB; resize shorter edge to 232 with bilinear antialiasing; center crop 224 x 224; scale RGB bytes by 1/255; normalize each channel using mean `[0.485, 0.456, 0.406]` and standard deviation `[0.229, 0.224, 0.225]`.
- Output contains six logits in approved ID order. The service applies stable softmax and validates confidence before creating a domain result.

## Integration sequence

1. Confirm the chosen `.tflite` SHA-256 against `AI/experiments/MobileNetV3_Rice/deployment/model_checksums.txt`.
2. Select an Android/iOS pixel decoder that handles orientation, exact resize/crop, bilinear antialiasing, and RGB extraction. Validate tensors against the Python reference pipeline on an agreed image corpus.
3. Copy the verified artifact into a versioned app model asset only after the product owner approves the mobile artifact. Do not alter the source experiment artifact.
4. Supply its app-local URI to `FastTfliteModelRunner`, build a fresh development client, and check model input/output metadata on device.
5. Compare native outputs to PyTorch and TensorFlow Lite reference outputs on the same validation samples. Keep the frozen test split out of tuning.
6. Measure startup, memory, latency, battery impact, and output agreement on representative Android and iOS devices before enabling detection in the UI.
7. Configure `EXPO_PUBLIC_API_URL` (or the matching app config extra) only after a real, authenticated server contract exists. Validate server responses against the same class and confidence constraints.

## Current runtime behavior

`OfflineDiseaseDetectionService` and `OnlineDiseaseDetectionService` expose the production interfaces, but current defaults deliberately fail with clear unavailable errors. The result screen shows that no prediction was made. It never inserts placeholder predictions into SQLite.
