# RiceLeafDiseaseBD Classification Preparation Report

Preparation completed without model training. Source ZIP files were read only; image bytes in the processed dataset are copied unchanged from the original-image folders.

## Inputs and method

- Outer archive: `RiceLeafDiseaseBD A Field-Based Annotated Smartpho.zip`
- Nested archive: `RiceLeafDiseaseBD A Field-Based Annotated Smartpho/RiceLeafDiseaseBD.zip`
- Included source tree: `RiceLeafDiseaseBD/Original images/<class>/<filename>` only.
- Classification labels: original folder names; YOLO class IDs were not used.
- Expected image dimensions: 1024x1024 pixels.
- Seed: `42`; target ratios: train 70%, validation 15%, test 15%.
- Exact duplicate groups use MD5 of the original image bytes. Groups containing more than one folder class are unresolved and excluded from every primary split.

## Preparation totals

- Original image members indexed: 9,769
- Primary benchmark images: 9,753
- Excluded images: 16 (16 cross-class duplicate members; 0 invalid images).
- MD5 groups total: 9,730; multi-image exact-duplicate groups: 39 (31 single-label groups retained, 8 cross-class groups excluded).
- Dimensions observed among valid indexed originals: {(1024, 1024): 9769}.

## Split counts

| Split | Images | Actual ratio | Target ratio |
|---|---:|---:|---:|
| train | 6827 | 70.00% | 70% |
| val | 1463 | 15.00% | 15% |
| test | 1463 | 15.00% | 15% |

## Per-class distribution

| Class folder | Train | Validation | Test | Total |
|---|---:|---:|---:|---:|
| Blast | 927 | 199 | 199 | 1325 |
| Brown spot | 1524 | 326 | 326 | 2176 |
| Healthy | 1102 | 236 | 236 | 1574 |
| Leaf smut | 506 | 108 | 109 | 723 |
| Rice Tungro | 1566 | 336 | 336 | 2238 |
| Sheath blight | 1202 | 258 | 257 | 1717 |

## Annotation files (reported separately; not classification labels)

- Disease original images: 8194; matching YOLO label files: 8194; missing disease label files: 0; orphan labels: 0.
- Healthy originals without box files (expected): 1575.
- Empty annotation files: 1.
- Box rows observed: 21,460; malformed rows: 0; out-of-bounds boxes: 1.
- Empty label path: `blast_258.txt`. Out-of-bounds annotation: `Rice Tungro_578.txt`, line 1.
- Known YOLO class-ID dispute remains documented in the dataset audit; the classification labels here come only from original folder names.

## Exclusions and review

- Unresolved cross-class duplicate groups excluded: 8. Each group and its member paths/classes/MD5 are listed in `manifests/cross_class_review.csv` with status `unresolved_excluded`.
- Other rejected images: 0.
- No labels were reassigned. Review decisions are intentionally left unresolved until a human verifies source images.

## Reproducibility and validation

- Recreate with `python AI/src/prepare_rice_classification.py --archive <outer-zip> --output-dir <output-dir> --seed 42`.
- Validate with `python AI/src/validate_rice_dataset.py --dataset-dir <output-dir>`.
- Manifests preserve source ZIP member paths and original basenames. Group assignment is deterministic for a fixed seed and ratios.
- Splits are assigned to whole MD5 groups. If actual ratios differ from targets, the table above is authoritative; groups are never divided to force a ratio.

## Validation results

The standalone validator completed successfully.

- Result: **PASS**; 9753 manifest-listed images across 6 classes.
- Split image counts exactly match the manifest and image files: train 6827, validation 1463, test 1463.
- Exact MD5 duplicate groups are split-safe: 9722 included groups, with no group crossing splits.
- Unresolved cross-class groups excluded: 8; none appears in a split manifest.
- Every listed image decodes at 1024x1024, has a matching MD5 and valid class label; unmanifested image files: 0.
- Per-split class distributions are listed above; the machine-readable validation result is `AI/data/processed/rice_classification/manifests/validation_report.json`.
