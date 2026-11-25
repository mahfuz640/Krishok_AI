#!/usr/bin/env python3
"""Validate a prepared RiceLeafDiseaseBD classification dataset and manifests."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath
from typing import Any

from PIL import Image, UnidentifiedImageError

LOGGER = logging.getLogger("validate_rice_dataset")
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATASET = PROJECT_ROOT / "AI" / "data" / "processed" / "rice_classification"
SPLITS = ("train", "val", "test")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-dir", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--expected-width", type=int)
    parser.add_argument("--expected-height", type=int)
    parser.add_argument("--log-level", default="INFO", choices=("DEBUG", "INFO", "WARNING", "ERROR"))
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise FileNotFoundError(f"Required manifest is missing: {path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    args = parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level), format="%(levelname)s: %(message)s")
    dataset_dir = args.dataset_dir.expanduser().resolve()
    manifests = dataset_dir / "manifests"
    if not dataset_dir.is_dir():
        raise SystemExit(f"ERROR: prepared dataset directory does not exist: {dataset_dir}")

    errors: list[str] = []
    mapping_path = manifests / "class_mapping.json"
    if not mapping_path.is_file():
        raise SystemExit(f"ERROR: class mapping is missing: {mapping_path}")
    mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
    classes = mapping.get("classes", [])
    class_to_id = {item["class_label"]: int(item["class_id"]) for item in classes}
    if len(class_to_id) != len(classes):
        errors.append("class_mapping.json contains duplicate class labels")
    if mapping.get("uses_yolo_annotation_class_ids") is not False:
        errors.append("class mapping must explicitly state that YOLO annotation IDs are not used")
    expected_width = args.expected_width or int(mapping.get("expected_image_size", {}).get("width", 1024))
    expected_height = args.expected_height or int(mapping.get("expected_image_size", {}).get("height", 1024))

    split_rows: dict[str, list[dict[str, str]]] = {}
    all_rows: list[dict[str, str]] = []
    for split in SPLITS:
        rows = read_csv(manifests / f"{split}.csv")
        split_rows[split] = rows
        all_rows.extend(rows)

    duplicate_rows = read_csv(manifests / "duplicate_groups.csv")
    duplicate_by_id = {row["group_id"]: row for row in duplicate_rows}
    cross_rows = read_csv(manifests / "cross_class_review.csv")
    cross_ids = {row["group_id"] for row in cross_rows}
    if any(row["review_status"] != "unresolved_excluded" for row in cross_rows):
        errors.append("cross_class_review.csv contains a row not marked unresolved_excluded")

    seen_image_paths: set[str] = set()
    group_splits: dict[str, set[str]] = defaultdict(set)
    group_counts: Counter[str] = Counter()
    distributions: dict[str, Counter[str]] = {split: Counter() for split in SPLITS}
    md5_by_group: dict[str, str] = {}
    for split, rows in split_rows.items():
        for row in rows:
            image_path = PurePosixPath(row["image_path"]).as_posix()
            if image_path in seen_image_paths:
                errors.append(f"image path appears more than once in manifests: {image_path}")
            seen_image_paths.add(image_path)
            if PurePosixPath(image_path).parts[0] != split:
                errors.append(f"manifest split/path mismatch: {split} row points to {image_path}")
            label = row["class_label"]
            if label not in class_to_id:
                errors.append(f"unknown class label in manifest: {label} ({image_path})")
            elif int(row["class_id"]) != class_to_id[label]:
                errors.append(f"class ID mismatch for {image_path}: {row['class_id']} != {class_to_id[label]}")
            class_parts = PurePosixPath(image_path).parts
            if len(class_parts) < 3 or class_parts[1] != label:
                errors.append(f"class folder/path mismatch for {image_path}; expected folder {label}")
            group_id = row["duplicate_group_id"]
            group_splits[group_id].add(split)
            group_counts[group_id] += 1
            distributions[split][label] += 1
            md5_by_group.setdefault(group_id, row["md5"])
            if md5_by_group[group_id] != row["md5"]:
                errors.append(f"one duplicate group has more than one MD5: {group_id}")
            if group_id in cross_ids:
                errors.append(f"unresolved cross-class group entered primary benchmark: {group_id}")
            group_record = duplicate_by_id.get(group_id)
            if group_record is None:
                errors.append(f"split manifest group missing from duplicate_groups.csv: {group_id}")
            elif group_record["benchmark_status"] != "included" or group_record["split"] != split:
                errors.append(f"duplicate group status/split mismatch: {group_id}")

            absolute_path = dataset_dir.joinpath(*PurePosixPath(image_path).parts)
            if not absolute_path.is_file():
                errors.append(f"manifest image does not exist: {absolute_path}")
                continue
            try:
                digest = hashlib.md5(absolute_path.read_bytes()).hexdigest()
                if digest != row["md5"]:
                    errors.append(f"MD5 mismatch for {image_path}: manifest {row['md5']}, file {digest}")
                with Image.open(absolute_path) as image:
                    width, height = image.size
                    image.verify()
                if (width, height) != (expected_width, expected_height):
                    errors.append(
                        f"unexpected dimensions for {image_path}: {width}x{height}; "
                        f"expected {expected_width}x{expected_height}"
                    )
                if int(row["width"]) != width or int(row["height"]) != height:
                    errors.append(f"dimension metadata mismatch for {image_path}")
            except (UnidentifiedImageError, OSError, ValueError) as exc:
                errors.append(f"corrupted or undecodable image {image_path}: {exc}")

    for group_id, splits in group_splits.items():
        if len(splits) != 1:
            errors.append(f"duplicate group crosses splits: {group_id} -> {sorted(splits)}")
        if md5_by_group.get(group_id) and group_id != f"md5_{md5_by_group[group_id]}":
            errors.append(f"duplicate group ID is not derived from its MD5: {group_id}")
    for group_id, group_row in duplicate_by_id.items():
        if group_row["benchmark_status"] == "included":
            if group_id not in group_splits:
                errors.append(f"included duplicate group has no split manifest rows: {group_id}")
            if group_counts[group_id] != int(group_row["member_count"]):
                errors.append(
                    f"image count differs from duplicate group manifest for {group_id}: "
                    f"{group_counts[group_id]} != {group_row['member_count']}"
                )
        elif group_id in group_splits:
            errors.append(f"excluded group appears in a split: {group_id}")
    for review in cross_rows:
        group_id = review["group_id"]
        group_record = duplicate_by_id.get(group_id)
        if group_record is None:
            errors.append(f"cross-class review group is missing from duplicate_groups.csv: {group_id}")
        else:
            try:
                labels = json.loads(group_record["class_labels"])
            except json.JSONDecodeError:
                labels = []
            if len(labels) < 2:
                errors.append(f"cross-class review group does not contain multiple labels: {group_id}")
            if group_record["benchmark_status"] != "unresolved_excluded" or group_record["split"]:
                errors.append(f"cross-class review group is not excluded from splits: {group_id}")
    if cross_ids & set(group_splits):
        errors.append("one or more unresolved cross-class groups are present in split manifests")

    disk_paths: set[str] = set()
    for split in SPLITS:
        split_dir = dataset_dir / split
        if not split_dir.is_dir():
            errors.append(f"split directory is missing: {split_dir}")
            continue
        for file_path in split_dir.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}:
                disk_paths.add(file_path.relative_to(dataset_dir).as_posix())
    if disk_paths != seen_image_paths:
        extra = sorted(disk_paths - seen_image_paths)
        missing = sorted(seen_image_paths - disk_paths)
        if extra:
            errors.append(f"unmanifested image files are present: {extra[:10]}")
        if missing:
            errors.append(f"manifest rows have no corresponding image files: {missing[:10]}")

    if errors:
        for error in errors:
            LOGGER.error(error)
        LOGGER.error("Validation failed with %d issue(s).", len(errors))
        return 1

    total = len(all_rows)
    summary: dict[str, Any] = {
        "dataset": "RiceLeafDiseaseBD classification",
        "status": "passed",
        "expected_dimensions": {"width": expected_width, "height": expected_height},
        "class_mapping": class_to_id,
        "split_counts": {},
        "duplicate_groups_included": len(group_splits),
        "cross_class_groups_excluded": len(cross_ids),
        "total_images": total,
        "class_distribution": {},
    }
    for split in SPLITS:
        summary["split_counts"][split] = {
            "images": len(split_rows[split]),
            "ratio": round(len(split_rows[split]) / total, 6) if total else 0.0,
            "classes": dict(sorted(distributions[split].items())),
        }
    summary["class_distribution"] = {
        label: {split: distributions[split][label] for split in SPLITS}
        for label in sorted(class_to_id)
    }
    (manifests / "validation_report.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    report_path = PROJECT_ROOT / "documentation" / "rice_classification_preparation_report.md"
    if report_path.is_file():
        current = report_path.read_text(encoding="utf-8")
        marker = "## Validation results"
        if marker in current:
            current = current.split(marker, 1)[0].rstrip() + "\n\n"
        lines = [
            marker,
            "",
            "The standalone validator completed successfully.",
            "",
            f"- Result: **PASS**; {total} manifest-listed images across {len(class_to_id)} classes.",
            f"- Split image counts exactly match the manifest and image files: train {len(split_rows['train'])}, validation {len(split_rows['val'])}, test {len(split_rows['test'])}.",
            f"- Exact MD5 duplicate groups are split-safe: {len(group_splits)} included groups, with no group crossing splits.",
            f"- Unresolved cross-class groups excluded: {len(cross_ids)}; none appears in a split manifest.",
            f"- Every listed image decodes at {expected_width}x{expected_height}, has a matching MD5 and valid class label; unmanifested image files: 0.",
            "- Per-split class distributions are listed above; the machine-readable validation result is `AI/data/processed/rice_classification/manifests/validation_report.json`.",
            "",
        ]
        report_path.write_text(current + "\n".join(lines), encoding="utf-8")
    LOGGER.info("Validation passed: %d images, %d classes, %d included duplicate groups, %d excluded cross-class groups.", total, len(class_to_id), len(group_splits), len(cross_ids))
    for split in SPLITS:
        split_summary = summary["split_counts"][split]
        LOGGER.info("%s: %d images (%.2f%%); classes=%s", split, split_summary["images"], split_summary["ratio"] * 100, split_summary["classes"])
    LOGGER.info("Validation report written to %s", manifests / "validation_report.json")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, json.JSONDecodeError, KeyError, ValueError) as exc:
        LOGGER.error("Validation could not complete: %s", exc)
        raise SystemExit(2)
