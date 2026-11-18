"""Transparent screening of congestion observations (stdlib only).

Important: a traffic count by itself is *not* evidence of congestion.
The excess-vehicle-minutes proxy assumes observed/free-flow times and vehicle
counts describe the very same route, direction and observation window.
"""
from __future__ import annotations

import argparse
import csv
from datetime import date
import json
import math
from pathlib import Path

REQUIRED = {"site_id", "date", "period", "observed_minutes", "freeflow_minutes", "vehicles", "source"}


def _number(value: str, field: str) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid {field}: {value!r}") from exc
    if not math.isfinite(parsed):
        raise ValueError(f"Invalid {field}: must be finite")
    return parsed


def rank(rows: list[dict[str, str]]) -> list[dict]:
    """Calculate an illustrative *screening* metric per observation, not a causal estimate."""
    results = []
    seen = set()
    for line, row in enumerate(rows, start=2):
        if not isinstance(row, dict):
            raise ValueError(f"Row {line}: expected a CSV record")
        missing = REQUIRED - row.keys()
        if missing:
            raise ValueError(f"Row {line}: missing columns: {sorted(missing)}")
        for field in ("site_id", "date", "period", "source"):
            if not isinstance(row[field], str) or not row[field].strip():
                raise ValueError(f"Row {line}: {field} is required")
        try:
            date.fromisoformat(row["date"])
        except ValueError as exc:
            raise ValueError(f"Row {line}: date must be YYYY-MM-DD") from exc
        key = (row["site_id"], row["date"], row["period"])
        if key in seen:
            raise ValueError(f"Row {line}: duplicate site/date/period: {key}")
        seen.add(key)
        observed = _number(row["observed_minutes"], "observed_minutes")
        freeflow = _number(row["freeflow_minutes"], "freeflow_minutes")
        vehicles_float = _number(row["vehicles"], "vehicles")
        if not vehicles_float.is_integer():
            raise ValueError(f"Row {line}: vehicles must be an integer")
        vehicles = int(vehicles_float)
        if freeflow <= 0 or observed < freeflow or vehicles < 0:
            raise ValueError(f"Row {line}: inconsistent travel time or vehicle count")
        if vehicles > 0 and not row["source"].strip():
            raise ValueError(f"Row {line}: provenance is required")
        excess = (observed - freeflow) * vehicles
        results.append({
            "site_id": row["site_id"].strip(),
            "date": row["date"],
            "period": row["period"].strip(),
            "vehicles": vehicles,
            "observed_minutes": observed,
            "freeflow_minutes": freeflow,
            "excess_vehicle_minutes": round(excess, 2),
            "source": row["source"].strip(),
            "source_url": (row.get("source_url") or "").strip(),
            "measurement_method": (row.get("measurement_method") or "unspecified").strip(),
        })
    return sorted(results, key=lambda r: (-r["excess_vehicle_minutes"], r["site_id"], r["date"]))


def load_observations(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames is None:
            raise ValueError("CSV has no header")
        if len(reader.fieldnames) != len(set(reader.fieldnames)):
            raise ValueError("CSV contains duplicate columns")
        return rank(list(reader))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path)
    args = parser.parse_args()
    print(json.dumps(load_observations(args.csv), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
