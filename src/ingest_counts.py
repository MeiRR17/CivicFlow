"""Offline, provenance-gated import of aggregate traffic count CSVs.

This adapter intentionally never infers travel speed, delay or congestion
from traffic volumes. It does not access the network or publish the result.
"""
from __future__ import annotations

import argparse
import csv
from datetime import date, datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from urllib.parse import urlparse

MAX_INPUT_BYTES = 25 * 1024 * 1024
MAX_RECORDS = 200_000
COLUMNS = ("site_id", "date", "period", "direction", "vehicles")
PROVENANCE_FIELDS = (
    "provider", "canonical_source_url", "dataset_title", "release_date",
    "accessed_at_utc", "license", "collection_method",
    "geographical_extent", "time_extent", "update_frequency", "known_gaps",
    "transformation_version", "source_checksum",
)
PERIOD = re.compile(r"^([01][0-9]|2[0-3]):[0-5][0-9]-([01][0-9]|2[0-3]):[0-5][0-9]$")
HASH = re.compile(r"^[a-fA-F0-9]{64}$")


def nonblank(value: object, field: str, limit: int = 500) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be text")
    clean = value.strip()
    if not clean or len(clean) > limit or any(ord(char) < 32 for char in clean):
        raise ValueError(f"{field} must contain 1-{limit} printable characters")
    return clean


def load_manifest(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        document = json.load(handle)
    if not isinstance(document, dict):
        raise ValueError("Provenance manifest must be a JSON object")
    if document.get("source_kind") != "traffic_counts":
        raise ValueError("source_kind must be 'traffic_counts'")
    for field in PROVENANCE_FIELDS:
        nonblank(document.get(field), field, 1500 if field == "known_gaps" else 500)
    source_url = urlparse(document["canonical_source_url"])
    if source_url.scheme != "https" or not source_url.hostname or source_url.username:
        raise ValueError("canonical_source_url must be an HTTPS URL without credentials")
    if not HASH.fullmatch(document["source_checksum"]):
        raise ValueError("source_checksum must be the 64-digit SHA-256 hex digest")
    try:
        date.fromisoformat(document["release_date"])
    except ValueError as exc:
        raise ValueError("release_date must be an ISO date") from exc
    try:
        accessed = datetime.fromisoformat(
            document["accessed_at_utc"].replace("Z", "+00:00")
        )
        if accessed.tzinfo is None or accessed.utcoffset() != timedelta(0):
            raise ValueError("accessed_at_utc needs an explicit UTC offset")
    except ValueError as exc:
        raise ValueError("accessed_at_utc must be an ISO-8601 UTC timestamp") from exc
    mapping = document.get("column_map")
    if not isinstance(mapping, dict) or set(mapping) != set(COLUMNS):
        raise ValueError(f"column_map must define exactly: {', '.join(COLUMNS)}")
    names = [nonblank(mapping[key], f"column_map.{key}", 100) for key in COLUMNS]
    if len(set(names)) != len(names):
        raise ValueError("column_map must map each field to a distinct CSV column")
    return document


def sha256_file(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            sha.update(chunk)
    return sha.hexdigest()


def parse_row(row: dict, mapping: dict, line: int) -> dict:
    values = {field: nonblank(row.get(mapping[field]), f"Row {line} {field}", 120)
              for field in COLUMNS}
    try:
        day = date.fromisoformat(values["date"]).isoformat()
    except ValueError as exc:
        raise ValueError(f"Row {line}: date must be YYYY-MM-DD") from exc
    if not PERIOD.fullmatch(values["period"]):
        raise ValueError(f"Row {line}: period must be HH:MM-HH:MM (24h)")
    begin, end = values["period"].split("-", 1)
    if begin >= end:
        raise ValueError(f"Row {line}: period end must follow start (same day)")
    if not values["vehicles"].isascii() or not values["vehicles"].isdecimal():
        raise ValueError(f"Row {line}: vehicles must be a nonnegative integer")
    count = int(values["vehicles"])
    if count > 100_000_000:
        raise ValueError(f"Row {line}: implausible volume; review the unit")
    return {
        "site_id": values["site_id"],
        "date": day,
        "period": values["period"],
        "direction": values["direction"],
        "vehicles": count,
    }


def load_counts(csv_path: Path, mapping: dict) -> tuple[list[dict], dict]:
    records = []
    keys = set()
    days = set()
    sites = set()
    directions = set()
    with csv_path.open("r", encoding="utf-8-sig", newline="") as stream:
        csv.field_size_limit(10_000)
        reader = csv.DictReader(stream)
        if reader.fieldnames is None or len(set(reader.fieldnames)) != len(reader.fieldnames):
            raise ValueError("CSV must have a header with no duplicate column names")
        missing = set(mapping.values()) - set(reader.fieldnames)
        if missing:
            raise ValueError(f"CSV lacks mapped columns: {sorted(missing)}")
        for line, raw in enumerate(reader, start=2):
            if len(records) >= MAX_RECORDS:
                raise ValueError(f"CSV contains more than {MAX_RECORDS} records")
            if None in raw:
                raise ValueError(f"Row {line}: too many fields")
            record = parse_row(raw, mapping, line)
            key = tuple(record[field] for field in ("site_id", "date", "period", "direction"))
            if key in keys:
                raise ValueError(f"Row {line}: duplicate site/date/period/direction")
            keys.add(key)
            records.append(record)
            days.add(record["date"])
            sites.add(record["site_id"])
            directions.add(record["direction"])
    if not records:
        raise ValueError("CSV must contain at least one aggregate count row")
    records.sort(key=lambda r: (r["site_id"], r["date"], r["period"], r["direction"]))
    return records, {
        "record_count": len(records),
        "unique_site_count": len(sites),
        "unique_direction_count": len(directions),
        "earliest_observation": min(days),
        "latest_observation": max(days),
        "zero_volume_rows": sum(row["vehicles"] == 0 for row in records),
        "rows_rejected": 0,
        "original_columns_dropped": "all except explicitly mapped aggregate columns",
        "checks": [
            "source_sha256", "manifest_completeness", "column_mapping",
            "unique_observation_key", "ISO_dates", "daily_time_windows",
            "nonnegative_integer_counts", "nonempty_aggregate_dimensions"
        ],
    }


def write_atomic(output: Path, content: dict, replace: bool) -> None:
    if output.is_symlink() or output.is_dir():
        raise ValueError("Output cannot be a symlink or directory")
    if output.exists() and not replace:
        raise ValueError("Output exists; specify --replace for explicit overwrite")
    if not output.parent.is_dir():
        raise ValueError("Output parent directory does not exist")
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=output.parent,
            prefix=".counts-import-", suffix=".json.tmp", delete=False
        ) as handle:
            temporary = Path(handle.name)
            json.dump(content, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        if output.exists() and not replace:
            raise ValueError("Output appeared during import; retry with --replace")
        os.replace(temporary, output)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def ingest(csv_path: Path, manifest_path: Path, output: Path, replace: bool = False) -> dict:
    for source in (csv_path, manifest_path):
        if source.is_symlink() or not source.is_file():
            raise ValueError(f"Input must be a regular non-symlink file: {source}")
    if output.resolve() in (csv_path.resolve(), manifest_path.resolve()):
        raise ValueError("Output must not overwrite an input")
    if csv_path.stat().st_size > MAX_INPUT_BYTES:
        raise ValueError("Source CSV exceeds the 25 MiB local import limit")
    manifest = load_manifest(manifest_path)
    actual = sha256_file(csv_path)
    if actual.lower() != manifest["source_checksum"].lower():
        raise ValueError("Source SHA-256 does not match the provenance manifest")
    records, quality = load_counts(csv_path, manifest["column_map"])
    source = {field: manifest[field] for field in PROVENANCE_FIELDS}
    source["source_checksum"] = actual
    result = {
        "schema_version": 1,
        "data_kind": "aggregate_traffic_counts_only",
        "review_status": "candidate_unverified",  # never auto-publish
        "claim_limits": [
            "Traffic counts alone do not establish congestion or delay.",
            "Provider, license, geographic extent and field methodology must be reviewed independently.",
            "This file is not approved evidence for any public civic case.",
        ],
        "provenance": source,
        "mapping": {field: manifest["column_map"][field] for field in COLUMNS},
        "quality": quality,
        "records": records,
    }
    write_atomic(output, result, replace)
    return quality


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args(argv)
    try:
        quality = ingest(args.csv, args.manifest, args.output, args.replace)
    except (OSError, ValueError, json.JSONDecodeError, UnicodeError, csv.Error) as exc:
        print(f"Import rejected: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({"output": str(args.output), "quality": quality,
                      "review_status": "candidate_unverified"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
