# Dataset scan discrepancy investigation

## Verified project-side state

The approved processed dataset currently matches all three approved manifests exactly: train **6,827/6,827**, validation **1,463/1,463**, test **1,463/1,463**. The on-disk inventory has no missing or unmanifested files in any split. Hashes of the approved manifests at audit time: train `baf1004abaa44f3ddddd7bde3abc5cefc15d06904e4b441eb0dcf87ea41d0b0d`, validation `60706b05853801deb524ea078bccc7c62ef4a23029008d7b28a649afed2d0145`, test `91fdd26f22243861fcf1eea53b3312d1e1bcdb5800ffa822f56ab486b3d59d9f`.

The reported corrupt path `train/Sheath blight/Sheath blight_1022.jpg` exists locally (314,309 bytes) and successfully passes Pillow JPEG verification at 1024?1024. This contradicts the corruption claim for the project-side processed copy. It is present in the approved train manifest.

## What the discrepancy means

The stated training scan of 5,635 is **1,192 fewer** than the train manifest. The stated validation scan of 1,464 is **one more** than its manifest. Neither discrepancy is reproducible from the current project directory: all files match manifests. The preserved Ultralytics `args.yaml` records the training data path as `/content/rice_classification`, which is a Colab runtime path; no Colab-side file inventory, scan log, cache, or uploaded archive snapshot is present in this repository. Consequently, the precise missing filenames and exact runtime cause cannot be established from available evidence. A partial/stale Colab staging copy is consistent with the direction and scale of the discrepancy, but remains an inference, not a verified cause.

A single corrupt file cannot account for a 1,192-image shortfall, and the named image is valid in the local processed copy. The +1 validation scan likewise points to a different runtime inventory (for example, an extra unmanifested file), but the extra file cannot be identified without that runtime inventory.

## Safe resolution before another run

In Colab, compare the uploaded `train.csv`, `val.csv`, and `test.csv` against the approved SHA-256 values above; count actual supported image files recursively by split and compare each relative path set with its manifest. Clear only generated Ultralytics dataset cache files after preserving them for diagnosis, then rebuild the runtime folder from the approved processed dataset and rerun inventory validation. Do not alter manifests or labels. The local processed dataset, original archives, and checkpoints were not modified.
