"""Fail-closed checks for the published site, status feed, and run card."""
from __future__ import annotations

import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
DOCS = (ROOT / "docs").resolve()


class LocalLinks(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        for key, value in attrs:
            if key in ("href", "src") and value:
                self.links.append(value)


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def check_run_card() -> None:
    card = _read_json(DOCS / "run-card.json")
    assert card["verdict"] == "negative"
    assert card["submission_ready"] is False
    assert card["submission"]["submission_ready"] is False
    assert card["submission"]["weekly_slot_used"] is False
    assert card["submission"]["name"] is None
    assert card["submission"]["note"] is None
    assert card["submission"]["file"] is None
    assert card["raster_sha256"] is None
    assert card["budget"]["experiments_run"] == 0
    assert card["budget"]["weekly_slots_used"] == 0
    assert card["holdout_protocol"]["status"] == "REQUIRED_NOT_RUN"
    assert card["holdout_protocol"]["metric"] == {
        "pooling": "pooled", "alpha": 0.2, "beta": 0.8,
        "kernel": "triangular", "radius_m": 300
    }
    assert card["holdout"]["label"] == "HOLDOUT-DTI"
    assert card["holdout"]["status"] == "NOT_RUN_BLOCKED"
    assert card["holdout"]["evaluator_version"] is None
    assert card["holdout"]["withheld_positive_count"] is None
    assert card["holdout"]["pooled_dti"] is None
    assert card["holdout"]["ci95"] is None
    assert card["holdout"]["feature_only_leakage_canary"]["status"] == "NOT_RUN"
    assert card["registry"]["surface"]["maximum_rank_correlation"] is None
    assert card["registry"]["final_dots"]["maximum_fraction_within_3px"] is None
    assert card["registry"]["unique_verified"] is False
    assert card["validator"]["status"] == "NOT_RUN_NO_CURRENT_CANDIDATE"
    assert all(card["validator"][k] is None for k in (
        "no_nan_inside_footprint", "values_in_0_1", "crs_match", "shape_match",
        "transform_match", "single_band", "reopened_written_bytes", "validator_output"
    ))


def check_site_links() -> int:
    html_files = sorted(DOCS.rglob("*.html"))
    assert html_files, "No published HTML pages found"
    checked = 0
    for file in html_files:
        text = file.read_text(encoding="utf-8")
        assert '<html lang="en">' in text, f"Missing language declaration: {file.relative_to(DOCS)}"
        parser = LocalLinks()
        parser.feed(text)
        for link in parser.links:
            url = urlsplit(link)
            if url.scheme or url.netloc or not url.path:
                continue
            target = (file.parent / unquote(url.path)).resolve()
            assert target.is_relative_to(DOCS), f"Link escapes published site in {file.relative_to(DOCS)}: {link}"
            assert target.exists(), f"Broken local target in {file.relative_to(DOCS)}: {link}"
            assert target.suffix.lower() not in (".tif", ".tiff", ".zip"), f"Unvalidated download link: {link}"
            checked += 1
    return checked


def main() -> None:
    check_run_card()
    status = _read_json(DOCS / "data/status.json")
    assert status["project_status"] == "BLOCKED_NOT_READY"
    assert status["submission_ready"] is False
    assert status["submission_file"] is None
    assert status["organizer_confirmed_score"] is None
    assert status["holdout_dti"] is None and status["holdout_ci95"] is None
    assert "not a live" in status["notice"].lower()

    assert (DOCS / ".nojekyll").exists(), "Pages artifact should be served as the prebuilt docs tree"
    pages_workflow = (ROOT / ".github/workflows/pages.yml").read_text(encoding="utf-8")
    assert "path: docs" in pages_workflow, "Pages workflow must upload the reviewed docs tree"
    assert not list(DOCS.rglob("*.tif")) and not list(DOCS.rglob("*.tiff")) and not list(DOCS.rglob("*.zip"))

    root_index = (ROOT / "index.html").read_text(encoding="utf-8")
    assert "url=docs/index.html" in root_index and "NOT READY" in root_index
    landing = (DOCS / "index.html").read_text(encoding="utf-8")
    assert "NOT READY — DO NOT SUBMIT" in landing
    assert "Download disabled — NOT READY" in landing

    links = check_site_links()
    print(f"PASS: fail-closed run card/status, {links} local page links, no unvalidated downloads")


if __name__ == "__main__":
    main()
