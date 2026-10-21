"""Deprecated status-feed compatibility helpers; no network probes or dynamic board data.

The current site consumes the reviewed static snapshot at ``docs/data/status.json`` and the
registered source statuses at ``registry/sources.json``. This historical module must not scrape
a leaderboard, probe external sources, synthesize evidence, or write a competing feed.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read_json(path: Path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def sha256(path: Path, limit: int | None = None) -> str | None:
    """Historical file-hash helper retained for compatibility; does not access the network."""
    if not path.exists():
        return None
    digest = hashlib.sha256()
    remaining = limit
    with path.open("rb") as file:
        while remaining is None or remaining > 0:
            block = file.read(1 << 20 if remaining is None else min(1 << 20, remaining))
            if not block:
                break
            digest.update(block)
            if remaining is not None:
                remaining -= len(block)
    return digest.hexdigest()


def build(root: Path = ROOT) -> dict:
    """Return the checked-in static status; do not assemble or write a second feed."""
    status_path = root / "docs" / "data" / "status.json"
    status = _read_json(status_path)
    if not isinstance(status, dict) or status.get("schema") != "gemsdoe83-status-feed-v2":
        raise RuntimeError(f"Reviewed static status feed missing or invalid: {status_path}")
    return status


def refresh_sources(root: Path = ROOT, timeout: float = 15.0) -> dict:
    """Return the recorded source register without probing hosts or changing files.

    ``timeout`` remains in the signature for compatibility but is intentionally unused. Source
    availability must be verified explicitly and recorded by a reviewed session; this helper
    cannot claim live availability.
    """
    del timeout
    register = _read_json(root / "registry" / "sources.json", {"sources": []})
    results = [
        {
            "id": source.get("id"),
            "url": source.get("url"),
            "status": source.get("status", "UNKNOWN_NOT_PROBED"),
            "evidence_class": source.get("evidence_class", "NOT_RECORDED"),
            "note": "Registered status only; no network request was made by this helper.",
        }
        for source in register.get("sources", [])
    ]
    return {
        "checked_utc": None,
        "results": results,
        "policy": "No automatic network probes or leaderboard scraping; use reviewed source statuses.",
    }
