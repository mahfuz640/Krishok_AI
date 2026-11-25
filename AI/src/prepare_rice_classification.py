#!/usr/bin/env python3
"""Prepare a group-safe RiceLeafDiseaseBD image-classification dataset.

Only Original images/ members are read from the nested RiceLeafDiseaseBD ZIP.
Original archives are never modified. Source image bytes are copied unchanged.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
import math
import random
import shutil
import tempfile
import zipfile
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath
from typing import Any

from PIL import Image, UnidentifiedImageError

LOGGER = logging.getLogger("prepare_rice_classification")
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = PROJECT_ROOT / "AI" / "data" / "processed" / "rice_classification"
SPLITS = ("train", "val", "test")
DEFAULT_RATIOS = {"train": 0.70, "val": 0.15, "test": 0.15}
HEALTHY_CLASS = "Healthy"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--archive",
        type=Path,
        help="Outer RiceLeafDiseaseBD ZIP. Defaults to the unique RiceLeafDiseaseBD*.zip in project root.",
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--train-ratio", type=float, default=0.70)
    parser.add_argument("--val-ratio", type=float, default=0.15)
    parser.add_argument("--test-ratio", type=float, default=0.15)
    parser.add_argument("--expected-width", type=int, default=1024)
    parser.add_argument("--expected-height", type=int, default=1024)
    parser.add_argument("--log-level", default="INFO", choices=("DEBUG", "INFO", "WARNING", "ERROR"))
    return parser.parse_args()


def resolve_archive(path: Path | None) -> Path:
    if path is not None:
        candidate = path.expanduser().resolve()
        if not candidate.is_file():
            raise FileNotFoundError(f"RiceLeafDiseaseBD outer ZIP does not exist: {candidate}")
        return candidate
    matches = sorted(PROJECT_ROOT.glob("RiceLeafDiseaseBD*.zip"))
    if len(matches) != 1:
        raise FileNotFoundError(
            "Expected exactly one RiceLeafDiseaseBD*.zip in project root; "
            f"found {len(matches)}. Pass --archive explicitly."
        )
    return matches[0].resolve()


def stage_inner_zip(outer_path: Path) -> tuple[Path, str]:
    """Stream only the nested ZIP bytes to a temporary file for random access."""
    temp_path: Path | None = None
    try:
        with zipfile.ZipFile(outer_path) as outer:
            candidates = [
                info for info in outer.infolist()
                if not info.is_dir() and PurePosixPath(info.filename).name == "RiceLeafDiseaseBD.zip"
            ]
            if len(candidates) != 1:
                raise RuntimeError(
                    "Expected exactly one nested RiceLeafDiseaseBD.zip in outer archive; "
                    f"found {len(candidates)}."
                )
            inner_info = candidates[0]
            temp = tempfile.NamedTemporaryFile(prefix="krishok_rice_inner_", suffix=".zip", delete=False)
            temp_path = Path(temp.name)
            with temp, outer.open(inner_info) as source:
                shutil.copyfileobj(source, temp, length=8 * 1024 * 1024)
        return temp_path, inner_info.filename
    except Exception:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
        raise


def image_validation(data: bytes, expected_size: tuple[int, int]) -> dict[str, Any]:
    result: dict[str, Any] = {
        "valid": False,
        "width": None,
        "height": None,
        "format": None,
        "error": "",
    }
    try:
        import io

        with Image.open(io.BytesIO(data)) as image:
            result["format"] = image.format
            result["width"], result["height"] = image.size
            image.verify()
        if (result["width"], result["height"]) != expected_size:
            result["error"] = (
                f"dimension mismatch: got {result['width']}x{result['height']}, "
                f"expected {expected_size[0]}x{expected_size[1]}"
            )
            return result
        result["valid"] = True
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        result["error"] = f"image decode failed: {exc}"
    return result


def parse_annotations(zip_file: zipfile.ZipFile, all_members: list[zipfile.ZipInfo], originals: list[dict[str, Any]]) -> dict[str, Any]:
    label_infos: dict[tuple[str, str], zipfile.ZipInfo] = {}
    for info in all_members:
        path = PurePosixPath(info.filename)
        if path.suffix.lower() != ".txt" or "labels" not in path.parts:
            continue
        label_infos[(path.parent.parent.name, path.stem.casefold())] = info

    disease_images = [row for row in originals if row["class_label"] != HEALTHY_CLASS]
    originals_by_key = {
        (row["class_label"], PurePosixPath(row["source_member_path"]).stem.casefold())
        for row in disease_images
    }
    missing_labels: list[str] = []
    empty_labels: list[str] = []
    orphan_labels: list[str] = []
    malformed_rows: list[dict[str, Any]] = []
    out_of_bounds: list[dict[str, Any]] = []
    row_counts: Counter[str] = Counter()

    for row in disease_images:
        key = (row["class_label"], PurePosixPath(row["source_member_path"]).stem.casefold())
        if key not in label_infos:
            missing_labels.append(row["source_member_path"])

    for key, info in label_infos.items():
        if key not in originals_by_key:
            orphan_labels.append(info.filename)
        text = zip_file.read(info).decode("utf-8", errors="replace")
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if not lines:
            empty_labels.append(info.filename)
            continue
        for line_number, line in enumerate(lines, start=1):
            fields = line.split()
            if len(fields) != 5:
                malformed_rows.append({"path": info.filename, "line": line_number, "reason": f"expected 5 fields, got {len(fields)}"})
                continue
            try:
                class_id = int(fields[0])
                x, y, width, height = (float(value) for value in fields[1:])
                if not all(math.isfinite(value) for value in (x, y, width, height)):
                    raise ValueError("non-finite coordinate")
                if not 0 <= class_id <= 5:
                    malformed_rows.append({"path": info.filename, "line": line_number, "reason": f"class ID outside 0..5: {class_id}"})
                row_counts[key[0]] += 1
                if not all(0 <= value <= 1 for value in (x, y, width, height)) or width <= 0 or height <= 0:
                    malformed_rows.append({"path": info.filename, "line": line_number, "reason": "invalid normalized values or nonpositive box size"})
                elif x - width / 2 < -1e-6 or x + width / 2 > 1 + 1e-6 or y - height / 2 < -1e-6 or y + height / 2 > 1 + 1e-6:
                    out_of_bounds.append({"path": info.filename, "line": line_number, "box": [x, y, width, height]})
            except ValueError as exc:
                malformed_rows.append({"path": info.filename, "line": line_number, "reason": str(exc)})

    return {
        "disease_original_image_count": len(disease_images),
        "healthy_images_without_annotation_expected": sum(row["class_label"] == HEALTHY_CLASS for row in originals),
        "annotation_file_count": len(label_infos),
        "missing_disease_annotation_files": missing_labels,
        "empty_annotation_files": empty_labels,
        "orphan_annotation_files": orphan_labels,
        "box_row_count": sum(row_counts.values()),
        "box_rows_by_class_folder": dict(sorted(row_counts.items())),
        "malformed_box_rows": malformed_rows,
        "out_of_bounds_box_rows": out_of_bounds,
        "classification_uses_yolo_annotation_ids": False,
    }


def assign_groups_by_class(
    groups: list[dict[str, Any]], ratios: dict[str, float], seed: int
) -> dict[str, str]:
    """Greedy deterministic group assignment minimizing per-class image-count error."""
    assignments: dict[str, str] = {}
    by_class: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for group in groups:
        labels = group["class_labels"]
        if len(labels) != 1:
            raise ValueError(f"Cross-class group reached split assignment: {group['group_id']}")
        by_class[next(iter(labels))].append(group)

    for class_index, class_label in enumerate(sorted(by_class)):
        rng = random.Random(seed + class_index * 1009)
        class_groups = by_class[class_label]
        rng.shuffle(class_groups)
        class_groups.sort(key=lambda group: len(group["members"]), reverse=True)
        total_images = sum(len(group["members"]) for group in class_groups)
        targets = {split: total_images * ratios[split] for split in SPLITS}
        counts = {split: 0 for split in SPLITS}

        # Seed each split with one group when possible so every class is represented.
        start = min(len(class_groups), len(SPLITS))
        for index, split in enumerate(SPLITS[:start]):
            group = class_groups[index]
            assignments[group["group_id"]] = split
            counts[split] += len(group["members"])

        for group in class_groups[start:]:
            size = len(group["members"])
            scores: list[tuple[float, float, str]] = []
            for split in SPLITS:
                score = 0.0
                for candidate in SPLITS:
                    count = counts[candidate] + (size if candidate == split else 0)
                    target = targets[candidate]
                    score += ((count - target) ** 2) / max(target, 1.0)
                scores.append((score, rng.random(), split))
            chosen = min(scores)[2]
            assignments[group["group_id"]] = chosen
            counts[chosen] += size
    return assignments


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def make_report(
    report_path: Path,
    archive_path: Path,
    nested_path: str,
    seed: int,
    ratios: dict[str, float],
    expected_size: tuple[int, int],
    class_map: dict[str, int],
    split_rows: dict[str, list[dict[str, Any]]],
    group_rows: list[dict[str, Any]],
    cross_rows: list[dict[str, Any]],
    rejected_rows: list[dict[str, Any]],
    annotation_status: dict[str, Any],
    dimensions: Counter[tuple[int, int]],
) -> None:
    total = sum(len(rows) for rows in split_rows.values())
    split_counts = {split: len(split_rows[split]) for split in SPLITS}
    duplicate_groups = [row for row in group_rows if int(row["member_count"]) > 1]
    retained_duplicate_groups = [row for row in duplicate_groups if row["benchmark_status"] == "included"]
    empty_annotation_names = ", ".join(
        PurePosixPath(path).name for path in annotation_status["empty_annotation_files"]
    ) or "none"
    out_of_bounds_names = ", ".join(
        f"{PurePosixPath(item['path']).name}:line {item['line']}"
        for item in annotation_status["out_of_bounds_box_rows"]
    ) or "none"
    lines = [
        "# RiceLeafDiseaseBD Classification Preparation Report",
        "",
        "Preparation completed without model training. Source ZIP files were read only; image bytes in the processed dataset are copied unchanged from the original-image folders.",
        "",
        "## Inputs and method",
        "",
        f"- Outer archive: `{archive_path.name}`",
        f"- Nested archive: `{nested_path}`",
        "- Included source tree: `RiceLeafDiseaseBD/Original images/<class>/<filename>` only.",
        "- Classification labels: original folder names; YOLO class IDs were not used.",
        f"- Expected image dimensions: {expected_size[0]}x{expected_size[1]} pixels.",
        f"- Seed: `{seed}`; target ratios: train {ratios['train']:.0%}, validation {ratios['val']:.0%}, test {ratios['test']:.0%}.",
        "- Exact duplicate groups use MD5 of the original image bytes. Groups containing more than one folder class are unresolved and excluded from every primary split.",
        "",
        "## Preparation totals",
        "",
        f"- Original image members indexed: {sum(split_counts.values()) + len(rejected_rows)}",
        f"- Primary benchmark images: {total}",
        f"- Excluded images: {len(rejected_rows)} ({sum(1 for row in rejected_rows if row['exclusion_reason'] == 'unresolved_cross_class_duplicate')} cross-class duplicate members; {sum(1 for row in rejected_rows if row['exclusion_reason'] == 'invalid_image')} invalid images).",
        f"- MD5 groups total: {len(group_rows)}; multi-image exact-duplicate groups: {len(duplicate_groups)} ({len(retained_duplicate_groups)} single-label groups retained, {len(cross_rows)} cross-class groups excluded).",
        f"- Dimensions observed among valid indexed originals: {dict(sorted(dimensions.items()))}.",
        "",
        "## Split counts",
        "",
        "| Split | Images | Actual ratio | Target ratio |",
        "|---|---:|---:|---:|",
    ]
    for split in SPLITS:
        ratio = split_counts[split] / total if total else 0.0
        lines.append(f"| {split} | {split_counts[split]} | {ratio:.2%} | {ratios[split]:.0%} |")
    lines.extend(["", "## Per-class distribution", "", "| Class folder | Train | Validation | Test | Total |", "|---|---:|---:|---:|---:|"])
    for class_label in sorted(class_map):
        counts = [sum(row["class_label"] == class_label for row in split_rows[split]) for split in SPLITS]
        lines.append(f"| {class_label} | {counts[0]} | {counts[1]} | {counts[2]} | {sum(counts)} |")
    lines.extend(
        [
            "",
            "## Annotation files (reported separately; not classification labels)",
            "",
            f"- Disease original images: {annotation_status['disease_original_image_count']}; matching YOLO label files: {annotation_status['annotation_file_count']}; missing disease label files: {len(annotation_status['missing_disease_annotation_files'])}; orphan labels: {len(annotation_status['orphan_annotation_files'])}.",
            f"- Healthy originals without box files (expected): {annotation_status['healthy_images_without_annotation_expected']}.",
            f"- Empty annotation files: {len(annotation_status['empty_annotation_files'])}.",
            f"- Box rows observed: {annotation_status['box_row_count']}; malformed rows: {len(annotation_status['malformed_box_rows'])}; out-of-bounds boxes: {len(annotation_status['out_of_bounds_box_rows'])}.",
            f"- Empty label path(s): {empty_annotation_names}.",
            f"- Out-of-bounds annotation path(s): {out_of_bounds_names}.",
            "- Known YOLO class-ID dispute remains documented in the dataset audit; the classification labels here come only from original folder names.",
            "",
            "## Exclusions and review",
            "",
            f"- Unresolved cross-class duplicate groups excluded: {len(cross_rows)}. Each group and its member paths/classes/MD5 are listed in `manifests/cross_class_review.csv` with status `unresolved_excluded`.",
            f"- Other rejected images: {sum(1 for row in rejected_rows if row['exclusion_reason'] != 'unresolved_cross_class_duplicate')}.",
            "- No labels were reassigned. Review decisions are intentionally left unresolved until a human verifies source images.",
            "",
            "## Reproducibility and validation",
            "",
            f"- Recreate with `python AI/src/prepare_rice_classification.py --archive <outer-zip> --output-dir <output-dir> --seed {seed}`.",
            "- Validate with `python AI/src/validate_rice_dataset.py --dataset-dir <output-dir>`.",
            "- Manifests preserve source ZIP member paths and original basenames. Group assignment is deterministic for a fixed seed and ratios.",
            "- Splits are assigned to whole MD5 groups. If actual ratios differ from targets, the table above is authoritative; groups are never divided to force a ratio.",
            "",
        ]
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level), format="%(levelname)s: %(message)s")
    ratios = {"train": args.train_ratio, "val": args.val_ratio, "test": args.test_ratio}
    if any(value <= 0 for value in ratios.values()) or not math.isclose(sum(ratios.values()), 1.0, abs_tol=1e-8):
        raise SystemExit("ERROR: train/val/test ratios must be positive and sum to 1.0.")
    if args.expected_width <= 0 or args.expected_height <= 0:
        raise SystemExit("ERROR: expected image width and height must be positive.")
    archive_path = resolve_archive(args.archive)
    output_dir = args.output_dir.expanduser().resolve()
    if output_dir.exists() and any(output_dir.iterdir()):
        raise SystemExit(f"ERROR: output directory is not empty; refusing to overwrite existing data: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    expected_size = (args.expected_width, args.expected_height)
    LOGGER.info("Opening outer archive: %s", archive_path)

    inner_path, nested_member_name = stage_inner_zip(archive_path)
    try:
        with zipfile.ZipFile(inner_path) as dataset_zip:
            members = [info for info in dataset_zip.infolist() if not info.is_dir()]
            original_infos = [
                info for info in members
                if "Original images" in PurePosixPath(info.filename).parts
                and PurePosixPath(info.filename).suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
            ]
            if not original_infos:
                raise RuntimeError("No decodable image members found under Original images/.")

            indexed: list[dict[str, Any]] = []
            invalid_records: list[dict[str, Any]] = []
            dimensions: Counter[tuple[int, int]] = Counter()
            for index, info in enumerate(original_infos, start=1):
                path = PurePosixPath(info.filename)
                if len(path.parts) < 4:
                    LOGGER.warning("Ignoring image with unexpected original path: %s", info.filename)
                    continue
                class_label = path.parts[-2]
                data = dataset_zip.read(info)
                digest = hashlib.md5(data).hexdigest()
                validation = image_validation(data, expected_size)
                if validation["width"] is not None and validation["height"] is not None:
                    dimensions[(validation["width"], validation["height"])] += 1
                row = {
                    "source_member_path": info.filename,
                    "filename": path.name,
                    "class_label": class_label,
                    "md5": digest,
                    "group_id": f"md5_{digest}",
                    "zip_info": info,
                    "valid_image": validation["valid"],
                    "width": validation["width"],
                    "height": validation["height"],
                    "image_format": validation["format"],
                    "validation_error": validation["error"],
                }
                indexed.append(row)
                if not validation["valid"]:
                    invalid_records.append(row)
                if index % 1000 == 0:
                    LOGGER.info("Indexed %d/%d original images", index, len(original_infos))

            annotation_status = parse_annotations(dataset_zip, members, indexed)
            by_digest: dict[str, list[dict[str, Any]]] = defaultdict(list)
            for row in indexed:
                by_digest[row["md5"]].append(row)
            groups: list[dict[str, Any]] = []
            cross_groups: list[dict[str, Any]] = []
            for digest, group_members in sorted(by_digest.items()):
                labels = sorted({row["class_label"] for row in group_members})
                group = {
                    "group_id": f"md5_{digest}",
                    "md5": digest,
                    "members": group_members,
                    "class_labels": set(labels),
                    "is_cross_class": len(labels) > 1,
                    "has_invalid_image": any(not row["valid_image"] for row in group_members),
                }
                groups.append(group)
                if group["is_cross_class"]:
                    cross_groups.append(group)

            if len(cross_groups) != 8:
                LOGGER.warning(
                    "Audit previously found 8 cross-class groups; current MD5 scan found %d. Check source archive/version.",
                    len(cross_groups),
                )

            included_groups = [
                group for group in groups
                if not group["is_cross_class"] and not group["has_invalid_image"]
            ]
            class_labels = sorted({row["class_label"] for group in included_groups for row in group["members"]})
            if not class_labels:
                raise RuntimeError("No valid single-label original images remain for classification.")
            class_to_id = {label: index for index, label in enumerate(class_labels)}
            assignments = assign_groups_by_class(included_groups, ratios, args.seed)

            group_rows: list[dict[str, Any]] = []
            split_rows: dict[str, list[dict[str, Any]]] = {split: [] for split in SPLITS}
            rejected_rows: list[dict[str, Any]] = []
            for group in groups:
                split = assignments.get(group["group_id"], "")
                if group["is_cross_class"]:
                    reason = "unresolved_cross_class_duplicate"
                    status = "unresolved_excluded"
                elif group["has_invalid_image"]:
                    reason = "invalid_image"
                    status = "invalid_excluded"
                else:
                    reason = ""
                    status = "included"
                labels = sorted(group["class_labels"])
                member_outputs: list[str] = []
                for row in group["members"]:
                    if reason:
                        rejected_rows.append({
                            "source_archive": archive_path.name,
                            "source_member_path": row["source_member_path"],
                            "filename": row["filename"],
                            "class_label": row["class_label"],
                            "md5": row["md5"],
                            "duplicate_group_id": group["group_id"],
                            "exclusion_reason": reason,
                            "validation_error": row["validation_error"],
                        })
                        continue
                    relative_path = PurePosixPath(split, row["class_label"], row["filename"]).as_posix()
                    member_outputs.append(relative_path)
                    split_rows[split].append({
                        "image_path": relative_path,
                        "source_archive": archive_path.name,
                        "nested_archive_member": nested_member_name,
                        "source_member_path": row["source_member_path"],
                        "filename": row["filename"],
                        "class_label": row["class_label"],
                        "class_id": class_to_id[row["class_label"]],
                        "md5": row["md5"],
                        "duplicate_group_id": group["group_id"],
                        "width": row["width"],
                        "height": row["height"],
                    })
                group_rows.append({
                    "group_id": group["group_id"],
                    "md5": group["md5"],
                    "member_count": len(group["members"]),
                    "class_labels": json.dumps(labels, ensure_ascii=False),
                    "split": split,
                    "benchmark_status": status,
                    "exclusion_reason": reason,
                    "source_paths": json.dumps([row["source_member_path"] for row in group["members"]], ensure_ascii=False),
                    "output_paths": json.dumps(member_outputs, ensure_ascii=False),
                })

            # Copy selected source bytes unchanged into split/class/original_filename.
            LOGGER.info("Copying %d selected images into %s", sum(map(len, split_rows.values())), output_dir)
            copied_targets: set[str] = set()
            for group in included_groups:
                split = assignments[group["group_id"]]
                for row in group["members"]:
                    relative_path = PurePosixPath(split, row["class_label"], row["filename"]).as_posix()
                    if relative_path in copied_targets:
                        raise RuntimeError(f"Output filename collision would overwrite an image: {relative_path}")
                    copied_targets.add(relative_path)
                    target = output_dir.joinpath(*PurePosixPath(relative_path).parts)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with dataset_zip.open(row["zip_info"]) as source, target.open("wb") as destination:
                        shutil.copyfileobj(source, destination, length=1024 * 1024)

            manifests = output_dir / "manifests"
            image_fields = [
                "image_path", "source_archive", "nested_archive_member", "source_member_path", "filename",
                "class_label", "class_id", "md5", "duplicate_group_id", "width", "height",
            ]
            for split in SPLITS:
                split_rows[split].sort(key=lambda row: (row["class_label"], row["source_member_path"]))
                write_csv(manifests / f"{split}.csv", image_fields, split_rows[split])
            write_csv(
                manifests / "duplicate_groups.csv",
                ["group_id", "md5", "member_count", "class_labels", "split", "benchmark_status", "exclusion_reason", "source_paths", "output_paths"],
                group_rows,
            )
            review_rows = []
            for group in cross_groups:
                review_rows.append({
                    "group_id": group["group_id"],
                    "image_paths": json.dumps([row["source_member_path"] for row in group["members"]], ensure_ascii=False),
                    "folder_class_labels": json.dumps([row["class_label"] for row in group["members"]], ensure_ascii=False),
                    "md5": group["md5"],
                    "review_status": "unresolved_excluded",
                })
            write_csv(manifests / "cross_class_review.csv", ["group_id", "image_paths", "folder_class_labels", "md5", "review_status"], review_rows)
            write_csv(
                manifests / "rejected_images.csv",
                ["source_archive", "source_member_path", "filename", "class_label", "md5", "duplicate_group_id", "exclusion_reason", "validation_error"],
                rejected_rows,
            )
            (manifests / "class_mapping.json").write_text(
                json.dumps({
                    "dataset": "RiceLeafDiseaseBD",
                    "label_source": "folder name under Original images/",
                    "uses_yolo_annotation_class_ids": False,
                    "classes": [
                        {"class_id": class_to_id[label], "class_label": label, "source_folder": label}
                        for label in class_labels
                    ],
                    "expected_image_size": {"width": expected_size[0], "height": expected_size[1]},
                    "seed": args.seed,
                    "split_ratios": ratios,
                }, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            (manifests / "annotation_status.json").write_text(
                json.dumps(annotation_status, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            make_report(
                PROJECT_ROOT / "documentation" / "rice_classification_preparation_report.md",
                archive_path, nested_member_name, args.seed, ratios, expected_size, class_to_id,
                split_rows, group_rows, review_rows, rejected_rows, annotation_status, dimensions,
            )
            LOGGER.info(
                "Prepared %d images (train=%d, val=%d, test=%d); excluded %d",
                sum(map(len, split_rows.values())), *(len(split_rows[s]) for s in SPLITS), len(rejected_rows),
            )
    finally:
        inner_path.unlink(missing_ok=True)

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, zipfile.BadZipFile, RuntimeError, ValueError) as exc:
        LOGGER.error("Preparation failed: %s", exc)
        raise SystemExit(2)
