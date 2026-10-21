"""Regression tests for the negative submission state and evidence labels.

These intentionally do not depend on ignored organizer data or quarantined rasters
being submission candidates. Quarantined TIFFs are hashed only as audit history.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def test_run_card_fails_closed_without_candidate():
    card = read_json(DOCS / "run-card.json")
    assert card["verdict"] == "negative"
    assert card["submission_ready"] is False
    assert card["submission"]["submission_ready"] is False
    assert card["submission"]["name"] is None
    assert card["submission"]["note"] is None
    assert card["submission"]["file"] is None
    assert card["raster_sha256"] is None
    assert card["budget"]["experiments_run"] == 0
    assert card["budget"]["weekly_slots_used"] == 0
    assert card["method_lane"]["status"] == "UNASSIGNED"


def test_required_holdout_and_duplicate_measurements_stay_null():
    card = read_json(DOCS / "run-card.json")
    protocol = card["holdout_protocol"]
    assert protocol["status"] == "REQUIRED_NOT_RUN"
    assert protocol["hide_unit"] == "Whole fault segments with a spatial buffer"
    assert protocol["visible_fault_mask"] == "Pixel-exact"
    assert protocol["metric"] == {
        "pooling": "pooled", "alpha": 0.2, "beta": 0.8,
        "kernel": "triangular", "radius_m": 300
    }
    holdout = card["holdout"]
    assert holdout["label"] == "HOLDOUT-DTI"
    assert holdout["status"] == "NOT_RUN_BLOCKED"
    assert holdout["evaluator_version"] is None
    assert holdout["withheld_positive_count"] is None
    assert holdout["pooled_dti"] is None
    assert holdout["ci95"] is None
    assert holdout["feature_only_leakage_canary"]["status"] == "NOT_RUN"
    assert card["registry"]["surface"]["maximum_rank_correlation"] is None
    assert card["registry"]["final_dots"]["maximum_fraction_within_3px"] is None
    assert card["registry"]["unique_verified"] is False


def test_owner_grid_discrepancy_is_explicit_and_blocking():
    card = read_json(DOCS / "run-card.json")
    audit = card["template_audit"]
    assert audit["status"] == "UNRESOLVED_BLOCKER_OWNER_MIRROR_ONLY"
    assert audit["sample_template"]["finite_cells"] == 5_167_373
    assert audit["sample_template"]["rasterio_transform"] == [100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0]
    assert audit["legacy_feature_footprint_claim"] == 5_165_852
    assert audit["difference_cells"] == 1_521
    assert audit["official_template_authenticated"] is False
    assert audit["outside_mask_semantics_resolved"] is False
    issues = read_json(ROOT / "registry/irregularities.json")["items"]
    assert next(x for x in issues if x["id"] == "IR-83-GRID-01")["status"] == "open"
    landing = (DOCS / "index.html").read_text(encoding="utf-8")
    assert "5,167,373 vs 5,165,852" in landing


def test_score_context_keeps_evidence_classes_separate():
    context = read_json(DOCS / "run-card.json")["score_provenance_context"]
    reported = context["user_reported_gemsdoe32_h33_2_b2"]
    assert reported["value"] == 0.2778
    assert reported["evidence_class"] == "USER-REPORTED-UNVERIFIED"
    assert reported["organizer_submission_page_receipt"] is None
    assert reported["owner_manifest_status_at_snapshot"] == "UNSCORED; receipt null"

    proxy = context["owner_lm_calibrated_proxy_for_h33_2_b2"]
    assert proxy["evidence_class"] == "OWNER-REPORTED-PROXY-METRIC-NOT-A-SCORE"
    assert proxy["positive_quadrants"] == 4
    projection = context["owner_live_projection_for_h33_2_b2"]
    assert projection["evidence_class"] == "PROJECTION-NOT-A-SCORE"

    coincidence = context["owner_local_proxy_matching_rounded_user_claim"]
    assert coincidence["evidence_class"] == "OWNER-REPORTED-LOCAL-PROXY-METRIC-NOT-A-SCORE"
    assert round(coincidence["value"], 4) == coincidence["user_reported_current_leaderboard_value"]
    assert coincidence["organizer_receipt"] is None
    assert context["current_organizer_confirmed_score"] is None


def test_quarantined_format_receipts_match_archived_bytes():
    receipts = (
        DOCS.parent / "research/quarantine/prior-h83b/evidence/format-audit-zeros.json",
        DOCS.parent / "research/quarantine/prior-h83b/evidence/format-audit-nan.json",
    )
    for receipt_path in receipts:
        receipt = read_json(receipt_path)
        candidate = ROOT / receipt["candidate"]
        assert candidate.is_file()
        assert sha256(candidate) == receipt["sha256"]
        assert receipt["submission_ready"] is False
    zeros = read_json(receipts[0])
    nan = read_json(receipts[1])
    assert zeros["format_valid"] is True
    assert nan["format_valid"] is False


def test_published_data_copies_match_audit_registers():
    assert (DOCS / "data/sources.json").read_bytes() == (ROOT / "registry/sources.json").read_bytes()
    assert (DOCS / "data/user_supplied_score_ledger.csv").read_bytes() == (ROOT / "registry/user_supplied_score_ledger.csv").read_bytes()
    with (DOCS / "data/user_supplied_score_ledger.csv").open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 112
    assert all(row["evidence_class"] in {
        "USER_REPORTED_UNVERIFIED", "USER_REPORTED_CONFLICT", "NO_SCORE_SUPPLIED"
    } for row in rows)


def test_no_submission_binary_is_published():
    docs = list(DOCS.rglob("*.tif")) + list(DOCS.rglob("*.tiff")) + list(DOCS.rglob("*.zip"))
    assert docs == []
    landing = (DOCS / "index.html").read_text(encoding="utf-8")
    assert "Download disabled — NOT READY" in landing


def test_legacy_feed_uses_static_registry_without_network_or_writes(monkeypatch):
    import urllib.request
    from gems83 import feed

    def forbidden(*args, **kwargs):
        raise AssertionError("legacy feed helpers must never make network requests")

    monkeypatch.setattr(urllib.request, "urlopen", forbidden)
    status = feed.build(ROOT)
    assert status["schema"] == "gemsdoe83-status-feed-v2"
    sources = feed.refresh_sources(ROOT)
    assert sources["checked_utc"] is None
    assert sources["policy"].startswith("No automatic network probes")
    assert sources["results"]
    assert not (DOCS / "data/feed.json").exists()
    assert not (DOCS / "data/source_health.json").exists()


def test_historical_leaderboard_snapshot_is_not_a_submission_receipt():
    snapshot = read_json(ROOT / "registry/leaderboard_snapshot_2026-10-04.json")
    assert snapshot["evidence_class"] == "HISTORICAL_PUBLIC_PAGE_SNAPSHOT_METADATA_ONLY"
    assert snapshot["numeric_leaderboard_values_included"] is False
    assert snapshot["entries"] == []
    assert "not a submission-page receipt" in snapshot["verification_note"]
    assert "not current" in snapshot["verification_note"]


def test_pinned_owner_evidence_hash_receipt():
    receipt = read_json(ROOT / "evidence/upstream/GEMSDOE32_owner_evidence_receipt.json")
    assert receipt["repository_commit"] == "f62038b54dcb7767d4d997f80b033cdc3d42bef9"
    assert receipt["evidence_class"] == "OWNER_REPORTED_NOT_ORGANIZER_RECEIPT"
    assert "not ORGANIZER-CONFIRMED" in receipt["historical_score_ledger_interpretation"]
    for source in receipt["sources"]:
        if source.get("local_snapshot") and source.get("sha256"):
            assert sha256(ROOT / source["local_snapshot"]) == source["sha256"]
    excerpt = receipt["h33_2_b2_manifest_excerpt"]
    assert excerpt["candidate_id"] == "H33-2-B2"
    assert excerpt["receipt"] is None
    assert "UNSCORED" in excerpt["note"]
