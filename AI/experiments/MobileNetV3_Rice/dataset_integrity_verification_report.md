# Dataset Integrity Verification Report

**Current project-side status: PASS.** These facts come from the completed local dataset validation and reconciliation. The notebook generates a separate runtime verification report after rebuilding and checking the Colab copy.

| Split | Approved manifest rows | Project image files |
|---|---:|---:|
| Train | 6,827 | 6,827 |
| Validation | 1,463 | 1,463 |
| Test | 1,463 | 1,463 |

Approved manifest SHA-256:

- `train.csv`: `baf1004abaa44f3ddddd7bde3abc5cefc15d06904e4b441eb0dcf87ea41d0b0d`
- `val.csv`: `60706b05853801deb524ea078bccc7c62ef4a23029008d7b28a649afed2d0145`
- `test.csv`: `91fdd26f22243861fcf1eea53b3312d1e1bcdb5800ffa822f56ab486b3d59d9f`

Class mapping: Blast=0, Brown spot=1, Healthy=2, Leaf smut=3, Rice Tungro=4, Sheath blight=5. Labels derive from approved classification folders, not YOLO annotation IDs. The preparation validator reported all approved images decode at 1024?1024, exact duplicate groups are split-safe, and all eight unresolved cross-class exact-duplicate groups are excluded. The previously reported Colab inventory discrepancy is unresolved; this local PASS does not certify any historical Colab runtime.
