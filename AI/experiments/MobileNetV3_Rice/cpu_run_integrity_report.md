# CPU Run Dataset Integrity Verification

**Status: PASS.** Exact approved manifests, folder path inventories, image decoding, image MD5 hashes, class mapping, counts, duplicate group isolation, and cross-class exclusions all passed before training.

| Split | Manifest rows | Files | Manifest SHA-256 |
|---|---:|---:|---|
| train | 6827 | 6827 | `baf1004abaa44f3ddddd7bde3abc5cefc15d06904e4b441eb0dcf87ea41d0b0d` |
| val | 1463 | 1463 | `60706b05853801deb524ea078bccc7c62ef4a23029008d7b28a649afed2d0145` |
| test | 1463 | 1463 | `91fdd26f22243861fcf1eea53b3312d1e1bcdb5800ffa822f56ab486b3d59d9f` |

Class mapping: Blast=0, Brown spot=1, Healthy=2, Leaf smut=3, Rice Tungro=4, Sheath blight=5

Test images were decoded and integrity-checked only; no test image was loaded by a model, optimizer, scheduler, or tuning process.
