# Dataset Integrity Report

All counts below were measured from archive members; README/metadata numbers are explicitly marked as claims. Archives were not modified. Nested ZIP bytes were staged temporarily to inspect the central directory and selected members; complete dataset folders were not extracted into the project.

| Dataset | Verified archive contents | Integrity results |
|---|---|---|
| RiceLeafDiseaseBD | 9,769 original JPG; 8,194 overlay JPG; 8,194 TXT; 1 XLSX. | 9,769/9,769 originals decode; 8,194/8,194 disease labels map to original files. 21,460 annotation rows. 1 empty disease label; 1 out-of-bounds box. 39 exact duplicate groups among originals; 8 cross-class groups. README claims 22,123 in one section; file rows verify 21,460. Label IDs conflict with README. |
| Agri-Vision4 | 5,247 original images; 22,875 augmented images; four crop-specific augmented archives; 28 documented classes. | All scanned images decode. README says 5,266 original and 22,734 augmented (actual deltas -19/+141). 864 exact duplicate groups / 1,256 excess files; 362 groups span classes. No exact duplicate bridges original/augmented sets. Same-class 64-bit pHash pairs <=4: 13,785 candidate pairs (the pHash pass excluded one PNG named `.jpg`; exact-hash audit included it). |
| BCDD | 8,992 JPG, 19 actual class folders, train 6,744 / val 1,348 / test 900; four `.DS_Store` files. | All JPGs decode. README class names differ from three archive folders. 90 exact duplicate groups / 180 records; 33 groups cross supplied split boundaries. The ZIP has no separate label files; class is directory path. |
| VegHealth14 | 27,282 metadata-listed original JPG; 53 classes; also 53,000 augmented JPG and 80,282 `__MACOSX` `.jpg` sidecar records. | All metadata paths exist, no extra/missing base JPG, all 27,282 MD5 checksums match; metadata class/path/ID fields have 0 mismatches. 11,421 duplicate references verified against same-class hashes. 59 cross-class exact-hash groups involve 157 records across 8 classes. No license field in metadata. |

## Integrity details

### RiceLeafDiseaseBD

- Original image counts by class: Healthy 1,575; Blast 1,326; Brown spot 2,178; Leaf smut 724; Rice Tungro 2,244; Sheath blight 1,722.
- Annotation rows by disease folder: Blast 4,844; Brown spot 9,352; Leaf smut 1,501; Rice Tungro 3,156; Sheath blight 2,607. Healthy has no box labels.
- Invalid annotation: `Rice Tungro_578.txt`, line 1, box extends beyond normalized image bounds. Empty annotation file: `Blast/labels/blast_258.txt`. All remaining rows pass field-count, finite-value, normalized-coordinate, positive-size, and image-bound checks.
- Actual annotation IDs: Blast 0, Brown spot 1, Leaf smut 2, Rice Tungro 3, Sheath blight 4. These disagree with the README mapping; Healthy has no annotation ID in the actual TXT rows.
- Exact duplicates: 39 SHA-256 groups / 39 excess files; 8 groups cross class folders. Group exact hashes before assigning train/validation/test.

### Agri-Vision4

- README-vs-archive class count deltas: Zucchini Healthy original 108 claimed / 88 found; Bottle Gourd Alternaria 303 claimed / 304 found (one PNG named `.jpg`); Tomato Healthy augmented 712 claimed / 853 found. Total original 5,266 claimed / 5,247 found; augmented 22,734 claimed / 22,875 found. One valid PNG is named `.jpg` and is included in the actual original count.
- Exact raw SHA-256 repeats: 864 groups, 1,256 excess files; 362 groups contain multiple class names. No byte-identical pair crosses original and augmented sets.
- Near duplicate method: 64-bit DCT pHash on decoded grayscale images; report counts are same-class pairs at Hamming distance <=4. It finds 13,785 pairs, including 6,024 at distance 0. This is a conservative review signal, not proof of shared source. The pHash screen excluded the `.jpg`-named PNG and did not merge the original `Downy Mildew` / augmented `Downy` aliases; normalize that class and rerun the comparison before using the candidate count as a final split manifest.
- Leakage-safe strategy: group exact duplicates globally, review cross-class duplicate labels, group pHash-near candidates, split originals by groups, then augment training-only data. Keep validation/test original-only.

### BCDD

- Archive path format: `<split>/<class_folder>/<image>.jpg`; labels are class-directory names. No JSON/CSV sidecar class mapping is in the root ZIP.
- README class metadata and archive folder disagreement: README-only Rice Leaf Scald, Rice Narrow Brown Spot, Tomato Leaf Mold; archive-only Tomato Early blight, Wheat Loose Smut, Wheat Yellow rust.
- Exact SHA-256 duplicate groups: 90, with 33 crossing train/validation/test. Keep each duplicate group within a single split before evaluation.
- License: BCDD.zip has no embedded license file; local README and publisher dataset card document CC BY-SA 4.0. See `dataset_license_report.md`.

### VegHealth14

- Root metadata describes the base image directory only. All 27,282 record paths and MD5 values match its base folder. The `duplicate_of` targets and each class's declared duplicate count match the file hashes.
- Multi-class exact duplicate identities: 59 SHA-256/MD5 content groups across more than one class, involving 157 files. A content group may contain multiple copies within one class plus another class; use connected exact-hash components across all class folders and review conflicting labels.
- `Commonly_cultivated_vegetables_224_aug/` has 53,000 additional JPGs, absent from the metadata records. `__MACOSX/` contains 80,282 AppleDouble companion files with `.jpg` names; these are metadata sidecars, not image files.
- No license field was found. Do not assign or assume one.
