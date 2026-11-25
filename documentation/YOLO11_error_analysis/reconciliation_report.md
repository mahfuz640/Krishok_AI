# Dataset Reconciliation Report

**Project:** Krishok AI — Phase 1, Task 05  
**Scope:** Approved RiceLeafDiseaseBD classification manifests versus the processed project dataset and reported Colab training scans  
**Conclusion:** Project-side dataset reconciles with the approved manifests. The historical Colab scan counts do not reconcile from the evidence currently in the project.

## Reconciled project-side inventory

Each processed split was compared by relative image path against its approved CSV manifest. No missing or extra paths were found.

| Split | Manifest rows | Files on disk | Difference |
|---|---:|---:|---:|
| Train | 6,827 | 6,827 | 0 |
| Validation | 1,463 | 1,463 | 0 |
| Test | 1,463 | 1,463 | 0 |

Manifest SHA-256 fingerprints at reconciliation time:

| Manifest | SHA-256 |
|---|---|
| `train.csv` | `baf1004abaa44f3ddddd7bde3abc5cefc15d06904e4b441eb0dcf87ea41d0b0d` |
| `val.csv` | `60706b05853801deb524ea078bccc7c62ef4a23029008d7b28a649afed2d0145` |
| `test.csv` | `91fdd26f22243861fcf1eea53b3312d1e1bcdb5800ffa822f56ab486b3d59d9f` |

The hashes above are full SHA-256 values. Compare them against the uploaded Colab manifests before any future training run.

## Reconciliation of the reported scan counts

| Split | Approved manifest | Reported scan | Difference (scan − manifest) |
|---|---:|---:|---:|
| Train | 6,827 | 5,635 | −1,192 |
| Validation | 1,463 | 1,464 | +1 |

These differences were **not reproduced** in the current project dataset. The training arguments saved with the model record `/content/rice_classification` as the data path, indicating that Ultralytics read a Colab runtime directory. The repository does not contain that runtime's file listing, scan log, or exact uploaded dataset snapshot, so the missing train filenames and extra validation filename cannot be identified conclusively.

A partial or stale Colab staging copy could explain the train shortfall, but that is an inference, not a verified cause. The saved evidence does not support attributing the 1,192-file train shortfall to one corrupt image.

## Check of the reported corrupt image

The approved train manifest lists `train/Sheath blight/Sheath blight_1022.jpg`. The current processed file exists, is 314,309 bytes, fully decodes as a 1024 × 1024 JPEG, and its MD5 (`298dee9117cb5fd34ea0378f8799c172`) matches the manifest. Therefore the reported corruption does not apply to the current project-side copy. It may describe a different Colab copy, but that cannot be verified without that copy or its scan diagnostics.

## Leakage and label integrity checks

- Train, validation, and test paths reconcile exactly to their approved manifests.
- Exact-duplicate groups do not cross splits.
- All 8 unresolved cross-class duplicate groups are excluded from the primary benchmark manifests.
- Test labels were read from the approved test manifest and were not edited.
- The approved manifests, processed dataset, source archives, and model checkpoints were left unchanged during this reconciliation.

These checks cover exact duplicates (MD5). They do not establish absence of visually similar near-duplicates.

## Evidence needed to resolve the Colab-side cause

Before a future training run, preserve the Colab runtime inventory and compare it to the approved manifests:

1. Hash the three uploaded manifest CSVs and compare full SHA-256 values to the approved files.
2. Recursively inventory image paths under each runtime split and compare the path sets to `train.csv`, `val.csv`, and `test.csv`.
3. Record the Ultralytics scan output, including corrupt/unsupported file counts and the path of any cache used.
4. For any reported invalid file, compare its bytes and MD5 to the approved manifest/source copy; do not silently replace it or edit labels.
5. Rebuild the runtime dataset from the approved processed dataset if the path inventory differs, then rerun a read-only inventory check before training.

## Related artifacts

- `dataset_discrepancy_report.md` — investigation of the scan-count discrepancy.
- `error_analysis_summary.md` — evaluation and leakage summary.
- `AI/data/processed/rice_classification/manifests/{train,val,test}.csv` — approved split manifests.
- `rice/KrishokAI_results_archive/YOLO11_Rice_v1_local/args.yaml` — saved training data path and run settings.

