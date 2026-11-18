"""Validate reviewable civic investigation records; do not infer official facts."""
from __future__ import annotations

from datetime import date
import json
from pathlib import Path
from urllib.parse import urlsplit

STATUSES = (
    "reported", "investigating", "proposed", "in_progress", "evaluating", "resolved"
)
EVIDENCE_STATES = ("synthetic", "unverified", "documented")


def safe_url(value: str) -> str:
    if not isinstance(value, str) or not value:
        return ""
    parsed = urlsplit(value)
    return value if parsed.scheme in ("https", "http") and parsed.netloc and not any(c.isspace() for c in value) else ""


def load_cases(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("dataset_type") not in ("synthetic", "real"):
        raise ValueError("dataset_type must be 'synthetic' or 'real'")
    cases = data.get("cases")
    if not isinstance(cases, list):
        raise ValueError("cases must be an array")
    ids = set()
    for record in cases:
        if not isinstance(record, dict):
            raise ValueError("Each case must be an object")
        for field in ("id", "domain", "site_id", "title", "location", "problem", "next_action"):
            if not isinstance(record.get(field), str) or not record[field].strip():
                raise ValueError(f"Case missing {field}")
        if record["id"] in ids:
            raise ValueError(f"Duplicate case id: {record['id']}")
        ids.add(record["id"])
        if record.get("status") not in STATUSES:
            raise ValueError(f"Invalid status for {record['id']}")
        if record.get("evidence_status") not in EVIDENCE_STATES:
            raise ValueError(f"Invalid evidence_status for {record['id']}")
        if data["dataset_type"] == "real" and record["evidence_status"] == "synthetic":
            raise ValueError("Real datasets cannot include synthetic cases")
        sources = record.get("sources", [])
        if not isinstance(sources, list) or any(not safe_url(link) for link in sources):
            raise ValueError(f"Case {record['id']}: sources must be valid HTTP(S) links")
        if record["evidence_status"] == "documented" and not sources:
            raise ValueError(f"Case {record['id']}: documented cases need cited sources")
        for field in ("hypotheses", "interventions"):
            if not isinstance(record.get(field), list) or any(not isinstance(x, str) for x in record[field]):
                raise ValueError(f"Case {record['id']}: {field} must be a string array")
        for update in record.get("updates", []):
            if not isinstance(update, dict) or not update.get("date") or not update.get("note"):
                raise ValueError(f"Case {record['id']}: invalid audit update")
            try:
                date.fromisoformat(update["date"])
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Case {record['id']}: update date must be ISO") from exc
    return data
