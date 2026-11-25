# MobileNetV3 Rice experiment

This directory is the Colab Drive output target for `AI/notebooks/Rice_Disease_MobileNetV3_Training.ipynb`. Copy the complete approved `AI/data/processed/rice_classification/` directory (including all manifests) into `MyDrive/Krishok_AI/data/processed/rice_classification/`. Run the notebook in a Colab GPU runtime. Preflight rebuilds `/content/rice_classification_verified/`, checks the pinned manifest SHA-256 values and exact per-split paths, fully decodes every image, checks each file MD5, verifies the six-class mapping and duplicate exclusions, and stops at the first mismatch. It never deletes an existing runtime folder or skips a bad file.

Training, exports, and final test reporting are disabled by default. Set `START_TRAINING=True` only after the integrity report says PASS. Use train/validation only for fitting, checkpoint selection, scheduling, and early stopping. The optional test report is a single final frozen evaluation and must not guide tuning.

After training, validation metrics, confusion matrix, curves, model size, and separate CPU/GPU inference latency are written here. The test set is not used in those reports. Expected image counts: train 6,827; validation 1,463; test 1,463. Seed: 42. Image size: 224. Initial epochs: 30. Batch size: 32 (set 16 or 8 manually if Colab GPU OOM occurs).

## Completed CPU run

A CPU training run was completed after explicit request. See `cpu_training_summary.md` and `cpu_training.log` for configuration, validation-only results, and artifacts. The test split was not evaluated.

