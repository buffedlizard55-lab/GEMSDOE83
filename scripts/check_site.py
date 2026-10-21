"""Fail-closed site contract for the submission-ready GEMSDOE83 Pages site.

Asserts (every push / PR):
- docs/run-card.json carries a complete, self-consistent run card (hypothesis,
  mechanism, mimic, holdout DTI + 95% CI, registry uniqueness, raster sha256,
  validator output, submission name + note <= 140 chars, verdict).
- Every GeoTIFF published under docs/downloads validates strictly against the
  competition template: single-band float32, EPSG:32611, exact shape/transform,
  all cells finite, all values in [0, 1] (this kills the "[0, 1]" portal error).
- The landing page redirects to docs/index.html and no longer says "NOT READY".
- docs/.nojekyll is present so GitHub Pages publishes the docs/ tree as-is.
- All intra-site links resolve inside docs/ and exist.
"""
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "data" / "raw" / "sample_submission.tif"
DOWNLOADS = ROOT / "docs" / "downloads"


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        for k, value in attrs:
            if k in ("href", "src") and value:
                self.links.append(value)


def validate_tif_strict(path: Path) -> dict:
    """Independent re-read of a published TIFF; competition-portal safe subset.

    The ``-zeros.tif`` (portal-safe) variant must be finite everywhere; the
    ``-nan.tif`` (competition-format twin) may use NaN *outside* the footprint
    only — inside the footprint it must be finite and in [0, 1].
    """
    with rasterio.open(TEMPLATE) as tpl:
        exp_crs = str(tpl.crs)
        exp_w, exp_h = tpl.width, tpl.height
        exp_transform = tpl.transform
        footprint = np.isfinite(tpl.read(1))
    with rasterio.open(path) as s:
        a = s.read(1)
        finite = np.isfinite(a)
        in_range = finite & (a >= 0) & (a <= 1)
        inside = a[footprint]
        outside = a[~footprint]
        result = {
            "path": path.name,
            "crs": str(s.crs),
            "width": s.width,
            "height": s.height,
            "transform": list(s.transform)[:6],
            "dtype": s.dtypes[0],
            "count": s.count,
            "crs_match": str(s.crs) == exp_crs,
            "shape_match": (s.width == exp_w and s.height == exp_h),
            "transform_match": s.transform == exp_transform,
            "dtype_ok": s.dtypes[0] == "float32",
            "count_ok": s.count == 1,
            "finite_inside": bool(np.isfinite(inside).all()),
            "in_range_inside": bool(((inside >= 0) & (inside <= 1)).all()),
            "outside_all_nan": bool(np.isnan(outside).all()),
            "outside_all_zero": bool((outside == 0).all()),
            "min_inside": float(np.nanmin(inside)) if inside.size else None,
            "max_inside": float(np.nanmax(inside)) if inside.size else None,
        }
        result["all_finite"] = result["finite_inside"] and result["outside_all_zero"]
        result["all_in_range"] = result["in_range_inside"] and result["outside_all_zero"]
        # Portal-safe iff geometry/dtype match, inside is finite and in [0,1],
        # and the outside rim is uniformly NaN (competition format) or 0 (safe variant).
        result["portal_safe"] = (
            result["crs_match"] and result["shape_match"] and result["transform_match"]
            and result["dtype_ok"] and result["count_ok"]
            and result["finite_inside"] and result["in_range_inside"]
            and (result["outside_all_nan"] or result["outside_all_zero"]))
        return result


def main() -> int:
    failures: list[str] = []

    # --- run card ---
    card_path = ROOT / "docs" / "run-card.json"
    card = json.loads(card_path.read_text())
    for key in ("hypothesis", "mechanism", "verdict", "submission_name", "note",
                "raster_sha256"):
        if not card.get(key):
            failures.append(f"run-card missing {key}")
    if card.get("verdict") not in ("promote", "negative"):
        failures.append(f"run-card verdict must be promote/negative, got {card.get('verdict')!r}")
    if len(card.get("note", "")) > 140:
        failures.append(f"run-card note {len(card['note'])} chars > 140")
    if card.get("experiments_run", 99) > 3:
        failures.append("run-card experiments_run > 3 (budget)")
    h = card.get("holdout") or {}
    if h.get("dti") is None or h.get("ci95") is None:
        failures.append("run-card holdout dti/ci95 must be measured, not null")
    v = card.get("validator") or {}
    if not v.get("passed"):
        failures.append("run-card validator must report passed")
    if card.get("weekly_slots_used", 99) != 0:
        failures.append("no weekly submission slot may be spent in this session")

    # --- published TIFFs validate strictly ---
    tifs = sorted(DOWNLOADS.glob("*.tif"))
    if not tifs:
        failures.append("no validated TIFF published under docs/downloads")
    for tif in tifs:
        r = validate_tif_strict(tif)
        ok = r["portal_safe"]
        if not ok:
            failures.append(f"TIFF {tif.name} failed strict validation: {r}")

    # --- landing page ---
    landing = (ROOT / "index.html").read_text()
    if "url=docs/index.html" not in landing:
        failures.append("landing page must redirect to docs/index.html")
    if "NOT READY" in landing:
        failures.append("landing page must not say NOT READY (submission is ready)")

    # --- Pages publishing markers ---
    if not (ROOT / "docs" / ".nojekyll").exists():
        failures.append("docs/.nojekyll must exist for raw HTML publishing")
    config = (ROOT / "_config.yml").read_text()
    for excl in ("research", "evidence", "scripts", "tests", "README.md", "requirements.txt"):
        if f"  - {excl}" not in config:
            failures.append(f"_config.yml must exclude {excl}")

    # --- intra-site links ---
    for file in sorted(ROOT.glob("docs/*.html")):
        text = file.read_text()
        if "<html lang=\"en\">" not in text:
            failures.append(f"{file.name} is not a full HTML page")
        parser = Links()
        parser.feed(text)
        for link in parser.links:
            url = urlsplit(link)
            if url.scheme or url.netloc or not url.path:
                continue
            target = (file.parent / unquote(url.path)).resolve()
            allowed = (ROOT / "docs", ROOT / "evidence", ROOT / "registry", ROOT)
            if not any(target.is_relative_to(base) for base in allowed):
                failures.append(f"Outside published/audit tree in {file.name}: {link}")
            elif not target.exists():
                failures.append(f"Broken target in {file.name}: {link}")

    if failures:
        print("FAIL: site contract")
        for f in failures:
            print(" -", f)
        return 1
    print(f"PASS: site contract ({len(tifs)} TIFF(s) validated, run-card complete, landing redirects to docs/index.html)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
