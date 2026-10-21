"""Automated 3-pass verification suite for GEMSDOE83 (Lane H83-GVCD)."""
from __future__ import annotations

import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor"))
sys.path.insert(0, str(ROOT / "src"))

from gems57 import evaluate_holdout as EH, grid as GRID, validate as V  # noqa: E402
from gems83 import features as F  # noqa: E402


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def test_pass1_shared_evaluator_and_feature_invariants() -> None:
    """Pass 1: Verify shared vendor tools are unmodified and feature list excludes leaky columns."""
    exp2 = json.loads((ROOT / "evidence" / "h83_exp2_dualseed_holdout.json").read_text())
    assert exp2["evaluator_version"] == "gems57-pooled-hide-v2"
    assert exp2["implementation_hashes"] == EH.implementation_hashes()

    all_names = F.all_channel_names()
    assert len(all_names) == 82
    assert "dist_known_fault_px" not in all_names
    for nm in all_names:
        assert "label" not in nm.lower()
        assert "truth" not in nm.lower()
        assert "hidden" not in nm.lower()


def test_pass2_submission_geotiff_and_zip_bytes() -> None:
    """Pass 2: Verify on-disk GeoTIFF and ZIP bytes, [0, 1] range, 0 NaNs, and 0 catalogue overlap."""
    card = json.loads((ROOT / "run_card.json").read_text())
    sub_tif = ROOT / card["submissions_tif"]
    sub_zip = ROOT / card["submissions_zip"]
    docs_tif = ROOT / card["tif_download"]
    docs_zip = ROOT / card["zip_download"]

    for p in (sub_tif, sub_zip, docs_tif, docs_zip):
        assert p.exists() and p.stat().st_size > 0, f"Missing artifact: {p}"

    assert _sha256(sub_tif) == card["raster_sha256"]
    assert _sha256(docs_tif) == card["raster_sha256"]
    assert _sha256(sub_zip) == card["zip_sha256"]
    assert _sha256(docs_zip) == card["zip_sha256"]

    g = GRID.load_grid(ROOT / "data" / "bridge")
    rep = V.validate(sub_tif, g.footprint, g.catalogue)
    V.assert_submittable(rep)
    assert rep["all_checks_passed"] is True
    assert rep["n_nan"] == 0
    assert rep["n_infinite"] == 0
    assert rep["min"] == 0.0
    assert rep["max"] == 1.0
    assert rep["emitted_positive_pixels"] == 37_654
    assert rep["on_catalogue_positive_pixels"] == 0

    with rasterio.open(sub_tif) as ds:
        arr = ds.read(1)
        assert ds.count == 1
        assert ds.dtypes[0] == "float32"
        assert ds.shape == (3730, 3292)
        assert ds.crs.to_epsg() == 32611
        assert ds.nodata is None
    assert np.all((arr == 0.0) | (arr == 1.0))
    assert not np.any(arr[~g.footprint] != 0.0)

    d_cat = ndi.distance_transform_edt(~g.catalogue)
    min_d = float(d_cat[arr > 0].min())
    assert min_d > 3.0, f"Expected collar d > 3.0 px, got {min_d}"

    with zipfile.ZipFile(sub_zip, "r") as zf:
        names = zf.namelist()
        assert names == [sub_tif.name]
        assert zf.read(sub_tif.name) == sub_tif.read_bytes()


def test_pass3_canary_holdout_uniqueness_and_pages() -> None:
    """Pass 3: Verify canary gate <= 0.90, holdout DTI progression, uniqueness <= 0.70/0.90, and HTML/README links."""
    card = json.loads((ROOT / "run_card.json").read_text())
    canary = json.loads((ROOT / "evidence" / "h83_leakage_canary.json").read_text())
    exp2 = json.loads((ROOT / "evidence" / "h83_exp2_dualseed_holdout.json").read_text())
    uniq = json.loads((ROOT / "evidence" / "h83_uniqueness.json").read_text())

    # Canary checks
    assert canary["all_seeds_passed"] is True
    for s in ("30", "20"):
        assert canary["seeds"][s]["n_features_tested"] == 82
        assert canary["seeds"][s]["max_symmetric_auc"] <= 0.90
        assert all(v <= 0.90 for v in canary["seeds"][s]["per_feature_symmetric_auc"].values())

    # Holdout checks
    dual = exp2["dualseed_pooled_summary"]["scores"]
    s30 = exp2["seeds"]["30"]["summary"]["scores"]
    s20 = exp2["seeds"]["20"]["summary"]["scores"]
    assert dual["A5_gvcd_dink_c30"]["withheld_positive_pixels"] == 22_663
    assert s30["A5_gvcd_dink_c30"]["withheld_positive_pixels"] == 11_342
    assert s20["A5_gvcd_dink_c30"]["withheld_positive_pixels"] == 11_321

    assert dual["A5_gvcd_dink_c30"]["dti"] > 0.205
    assert s30["A5_gvcd_dink_c30"]["dti"] > 0.213
    assert s20["A5_gvcd_dink_c30"]["dti"] > 0.199
    assert dual["A5_gvcd_dink_c30"]["dti"] > dual["A3_gvcd_poisson"]["dti"] > dual["A2_struct_poisson"]["dti"] > dual["A1_phys_poisson"]["dti"] > dual["A0_random"]["dti"]

    # Uniqueness checks
    assert uniq["rasters_checked"] == 119
    assert uniq["pre_placement_surface"]["unique"] is True
    assert uniq["pre_placement_surface"]["worst_spearman_full_footprint"] <= 0.90
    assert uniq["pre_placement_surface"]["worst_dot_overlap_3px"] <= 0.70
    assert uniq["final_emitted_dots"]["unique"] is True
    assert uniq["final_emitted_dots"]["worst_spearman_full_footprint"] <= 0.90
    assert uniq["final_emitted_dots"]["worst_dot_overlap_3px"] <= 0.70
    assert uniq["literal_untruncated_audit"]["informative_all_below_070"] is True
    assert uniq["literal_untruncated_audit"]["informative_max_forward_overlap_3px"] <= 0.70

    # HTML and README checks
    for html_rel, base_dir in (
        ("index.html", ROOT),
        ("executive-summary.html", ROOT),
        ("docs/index.html", ROOT / "docs"),
        ("docs/executive-summary.html", ROOT / "docs"),
    ):
        p = ROOT / html_rel
        assert p.exists(), f"Missing page {html_rel}"
        txt = p.read_text(encoding="utf-8")
        assert "OK TO DOWNLOAD AND SUBMIT" in txt
        assert card["raster_sha256"] in txt
        assert card["submission_name"] in txt
        for m in re.finditer(r'(?:href|src)="([^"#]+)"', txt):
            target = m.group(1)
            if target.startswith(("http://", "https://", "mailto:", "javascript:")):
                continue
            resolved = (base_dir / target).resolve()
            assert resolved.exists(), f"Broken relative link in {html_rel}: {target} -> {resolved}"

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "PARALLEL-RUN PROTOCOL" in readme
    assert "Predicted values must be in range [0, 1]" in readme
    assert card["raster_sha256"] in readme
    assert "0.2778" in readme and "0.3195" in readme and "0.4413" in readme
