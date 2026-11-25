# Krishok AI - Dataset Audit Report

Audit date: 2026-11-19 (Asia/Dhaka). This audit reads archive listings and selected archive members directly. Nested ZIP payloads were streamed to temporary storage for indexing, then removed; dataset members were not extracted to the project, and no source archive was modified. No model was trained.

## Executive findings

- **RiceLeafDiseaseBD** is the best first rice-only classification candidate: the archive contains 9,769 decodable original images in six class folders. Use folder labels and a corrected explicit mapping. Before splitting, group exact duplicates; 39 duplicate groups include 8 cross-class groups that need label review. YOLO box files are a separate, inconsistent annotation layer and should not define classification labels.
- **Agri-Vision4** contains the documented 28 classes, but actual counts differ from its README. Original and augmented files have no exact byte duplicates across the two sets, yet the pHash screen finds substantial same-class similarity; split source groups first and keep packaged augmented data out of validation/test.
- **BCDD** has 19 actual image-folder classes and 8,992 readable JPGs, but the README class mapping does not match three of the folders. Exact duplicates cross the supplied train/val/test partitions. The root `metadata.json` is VegHealth14 metadata, not BCDD metadata.
- **VegHealth14** image records match its 27,282 original images and MD5 values. Its exact duplicate flags are confirmed. There are 59 exact-content identities assigned to multiple classes (157 image records), creating label-conflict risk. The archive also includes a separate augmented directory not described by the root metadata. No license is stated in its metadata.

## RiceLeafDiseaseBD

The outer ZIP contains a nested `RiceLeafDiseaseBD.zip`; it was inspected by staging the nested ZIP bytes only. Its index contains 26,158 files: 9,769 original JPGs, 8,194 annotated-overlay JPGs, 8,194 YOLO TXT files, and one XLSX metadata workbook. All 9,769 original JPGs decoded successfully. The class folders contain 1,575 Healthy, 1,326 Blast, 2,178 Brown spot, 724 Leaf smut, 2,244 Rice Tungro, and 1,722 Sheath blight original images (total 9,769).

All 8,194 TXT files pair to an original disease image by class folder and basename. Healthy images intentionally have no box labels. The TXT files contain **21,460 annotation rows**: Blast 4,844; Brown spot 9,352; Leaf smut 1,501; Rice Tungro 3,156; Sheath blight 2,607. This verifies the 21,460 summary figure. The README class table lists 2,605 Sheath blight boxes and states a 22,123 total; the per-class table values sum to 21,458, not 22,123. The v2 note also claims 22,123. Thus 22,123 is not supported by the released TXT files.

One Blast file (`blast_258.txt`) is empty. One box in `Rice Tungro_578.txt`, line 1, extends beyond normalized image bounds. All other parsed rows have five fields, finite normalized coordinates, positive width/height, and in-bounds boxes. Every disease class has non-empty valid boxes elsewhere; Healthy has no box annotations by design.

**Class ID mismatch:** the archive labels use `0=Blast, 1=Brown spot, 2=Leaf smut, 3=Rice Tungro, 4=Sheath blight`; Healthy has no box rows. The README instead documents `0=Brown Spot, 1=Blast, 2=Healthy, 3=Leaf Smut, 4=Rice Tungro, 5=Sheath Blight`. Do not consume detection IDs as classification labels without an explicit corrected mapping.

Exact SHA-256 checks on the original images found 39 duplicate-content groups (39 duplicate excess files), including 8 groups spanning multiple class folders. Group these before splitting and review the cross-class label assignments.

## Agri-Vision4

The outer archive contains `Orginal_Dataset.zip` and `Update_Aug_Dataset.zip`; the update archive contains four crop-specific ZIPs. The 28 documented classes are Tomato (5), Papaya (7), Zucchini (9), and Bottle Gourd (7). All scanned image files decoded successfully.

The 28 documented class names are: **Tomato**: Downy, Healthy, Mosaic, Spot, White_spot; **Papaya**: Bacterial_Blight, Carica_Insect_Hole, Curled_Yellow_Spot, Healthy_Leaf, Mosaic_Virus, Pathogen_Symptoms, Yellow_Necrotic_Spots_Holes; **Zucchini**: Angular_Leaf_Spot, Anthracnose, Downy_Mildew, Dry_Leaf, Healthy, Insect_Damage, Iron_Chlorosis_Damage, Xanthomonas_Leaf_Spot, Yellow_Mosaic_Virus; **Bottle Gourd**: Alternaria_Leaf_Blight, Anthracnose, Downy_Mildew, Early_Alternaria_Leaf_Blight, Fungal_Damage_Leaf, Healthy, Mosaic_Virus.

The archive contains **5,247 original** and **22,875 augmented** image files. README claims are 5,266 and 22,734. The original total is 19 below the README: Zucchini Healthy has 88 vs 108 claimed (-20), offset by a valid PNG named `.jpg` in Bottle Gourd Alternaria (304 vs 303, +1). The augmented excess of 141 is Tomato Healthy (853 found vs 712 claimed). Other documented per-class counts agree after accounting for folder-name aliases such as Tomato `Downy Mildew`/`Downy` and White spot/`white_spot`. The original ZIP has a valid PNG image named `.jpg` with no basename; it is included in the 5,247 total and is an exact cross-class duplicate of a Bottle Gourd Mosaic Virus image.

Raw-byte SHA-256 found 864 duplicate groups (1,256 excess files); 362 groups span multiple class labels. No raw-byte exact duplicate group spans Original and Augmented sets. A 64-bit DCT perceptual-hash screen found 13,785 **same-class image pairs** at Hamming distance <=4, including distance-zero pairs; 3,857 augmented images had a same-class original nearest neighbour at distance <=6. These are candidate visual matches, not proof of source lineage, and should be reviewed before forming groups. The pHash scan used regular image extensions and excluded the single `.jpg`-named PNG; the exact-hash scan included it. It also kept the original Tomato `Downy Mildew` and augmented `Downy` folder names separate, so cross-alias comparisons are not included in the pHash counts. Treat these pHash totals as a partial screening result and normalize aliases before final grouping.

Leakage-safe plan: form groups across all exact-hash copies and candidate near-duplicate links without regard to split; inspect cross-class exact groups for label conflict. Split the original images by those groups first. Use packaged augmentation for training only after the split, or regenerate augmentation from training originals only. Keep validation and test on untouched originals.

## BCDD

`BCDD.zip` contains 8,992 JPGs, split into `train`, `val`, and `test`, with class names represented by directories (no separate sidecar labels). There are 19 actual archive class folders; all 8,992 images decoded successfully. Four `.DS_Store` files are non-image extras. Split totals are train 6,744, validation 1,348, test 900.

The README/Hugging Face class list has 19 names, but three listed classes are absent from the ZIP: Rice Leaf Scald, Rice Narrow Brown Spot, Tomato Leaf Mold. The ZIP has three different classes in their place: Tomato Early blight, Wheat Loose Smut, and Wheat Yellow rust. The count remains 19, but the class semantics do not match. The root `metadata.json` describes VegHealth14 and cannot validate BCDD classes.

Exact SHA-256 found 90 duplicate groups / 180 records, of which 33 groups cross the supplied split boundaries. The existing splits are therefore unsafe for an unbiased evaluation until groups are kept together and class names are reconciled.

## VegHealth14

Root `metadata.json` describes 53 folders and 27,282 image records. The ZIP has exactly 27,282 JPGs under `Commonly_cultivated_vegetables_224/`; every metadata path exists, there are no extra original JPGs, and all 27,282 file MD5 checksums match. Metadata class folder and label ID fields also match their paths (0 mismatches). All 11,421 `duplicate_of` references resolve to a same-class image with the same MD5; per-class duplicate counts match the metadata.

The reported 157 multi-class images are **157 file records across 59 exact-hash groups**, not 15. The group records assign the identical bytes to more than one class across eight affected classes: Cabbage Alternaria Spot, Cabbage Black Rot, Chilli Bacterial Spot, Chilli Cercospora Leaf Spot, Eggplant Healthy, Eggplant Leaf Spot Disease, Eggplant Mosaic Virus Disease, and Eggplant Wilt Disease. These need group-safe splitting and label review.

The nested ZIP additionally contains 53,000 JPGs under `Commonly_cultivated_vegetables_224_aug/` and 80,282 `__MACOSX/` AppleDouble sidecar entries whose filenames also end in `.jpg`. Those are not part of the 27,282 metadata records; do not count sidecars as images. Metadata says no augmentation, so use the base directory for experiments unless the augmented subset is independently documented and audited.

## First rice classification experiment

Use RiceLeafDiseaseBD **Original images** with class labels taken from the six folder names. The images are Bangladesh field photos, have no predefined split, and all decoded successfully. Create a manifest from exact archive paths, use a fixed seed, and split hash groups (not files) so duplicates stay together. Review the 8 cross-class exact groups and either resolve their labels or keep each entire ambiguous group out of evaluation. Ignore overlay JPGs and YOLO detection IDs for the initial image-level classifier. The annotation discrepancy does not prevent folder-based classification, but the corrected six-class names and a documented duplicate policy must be fixed before training.

Detailed counts and per-class mappings are in [`dataset_class_mapping.csv`](dataset_class_mapping.csv). License evidence and integrity issues are recorded in the companion reports.
