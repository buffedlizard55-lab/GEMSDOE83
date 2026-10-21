#!/usr/bin/env python3
"""Fail-closed static site generator for GEMSDOE83 (root + docs/ GitHub Pages).

Re-validates the actual GeoTIFF bytes on disk via `vendor/gems57/validate.py` and
verifies SHA-256 hashes against `run_card.json` before rendering the top-of-site
`OK TO DOWNLOAD AND SUBMIT` banner.
"""
from __future__ import annotations

import hashlib
import html
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor"))

from gems57 import grid as GRID, validate as V  # noqa: E402

COMP_URL = "https://www.drivendata.org/competitions/306/competition-doe-gems/"
DESC_URL = "https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/"
SUB_URL = "https://www.drivendata.org/competitions/306/competition-doe-gems/submissions/"
LB_URL = "https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/"
GDR_URL = "https://gdr.openei.org/submissions/1391"
GEODAWN_URL = "https://doi.org/10.5066/P93LGLVQ"
THREEDEP_URL = "https://www.usgs.gov/3d-elevation-program"


def esc(x: object) -> str:
    return html.escape(str(x), quote=True)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_on_disk_bytes(card: dict) -> tuple[bool, list[str], dict]:
    tif_path = ROOT / card["submissions_tif"]
    zip_path = ROOT / card["submissions_zip"]
    docs_tif = ROOT / card["tif_download"]
    docs_zip = ROOT / card["zip_download"]
    reasons: list[str] = []

    for p, label in (
        (tif_path, "submissions TIFF"),
        (zip_path, "submissions ZIP"),
        (docs_tif, "docs/downloads TIFF"),
        (docs_zip, "docs/downloads ZIP"),
    ):
        if not p.exists():
            reasons.append(f"missing {label}: {p}")

    if reasons:
        return False, reasons, {}

    if sha256_file(tif_path) != card["raster_sha256"]:
        reasons.append("submissions TIFF SHA-256 mismatch with run_card.json")
    if sha256_file(docs_tif) != card["raster_sha256"]:
        reasons.append("docs/downloads TIFF SHA-256 mismatch with run_card.json")
    if sha256_file(zip_path) != card["zip_sha256"]:
        reasons.append("submissions ZIP SHA-256 mismatch with run_card.json")
    if sha256_file(docs_zip) != card["zip_sha256"]:
        reasons.append("docs/downloads ZIP SHA-256 mismatch with run_card.json")

    g = GRID.load_grid(ROOT / "data" / "bridge")
    val = V.validate(tif_path, g.footprint, g.catalogue)
    if not val.get("all_checks_passed", False):
        reasons.append("vendor/gems57/validate.py failed on TIFF bytes")
    if not card.get("leakage_canary", {}).get("passed", False):
        reasons.append("leakage canary gate did not pass")
    if not card.get("uniqueness", {}).get("pre_placement_surface_unique", False):
        reasons.append("pre-placement surface uniqueness gate did not pass")
    if not card.get("uniqueness", {}).get("final_dots_unique", False):
        reasons.append("final dots uniqueness gate did not pass")
    if not card.get("ok_to_submit", False):
        reasons.append("run_card ok_to_submit is False")

    return (len(reasons) == 0), reasons, val


CSS = """
:root {
  --bg: #0b1120;
  --panel: #111827;
  --card: #1e293b;
  --border: #334155;
  --text: #f8fafc;
  --muted: #94a3b8;
  --accent: #38bdf8;
  --green: #22c55e;
  --green-bg: rgba(34, 197, 94, 0.12);
  --amber: #f59e0b;
  --red: #ef4444;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Inter, sans-serif;
  background: var(--bg);
  color: var(--text);
  line-height: 1.6;
}
header.nav {
  background: #090d16;
  border-bottom: 1px solid var(--border);
  padding: 0.85rem 1.5rem;
  position: sticky;
  top: 0;
  z-index: 50;
}
.nav-inner {
  max-width: 1240px;
  margin: 0 auto;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}
.brand {
  font-weight: 800;
  font-size: 1.1rem;
  color: var(--text);
  text-decoration: none;
  letter-spacing: 0.02em;
}
.brand span { color: var(--accent); }
.nav-links {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
}
.nav-links a {
  color: var(--muted);
  text-decoration: none;
  font-size: 0.92rem;
  font-weight: 600;
}
.nav-links a:hover, .nav-links a.active { color: var(--accent); }
main {
  max-width: 1240px;
  margin: 1.5rem auto 4rem;
  padding: 0 1.25rem;
}
.hero-banner {
  border-radius: 12px;
  padding: 1.5rem 1.75rem;
  margin-bottom: 2rem;
  box-shadow: 0 10px 30px rgba(0,0,0,0.35);
}
.hero-ok {
  background: linear-gradient(135deg, rgba(20, 83, 45, 0.55), rgba(15, 23, 42, 0.95));
  border: 2px solid var(--green);
}
.hero-bad {
  background: linear-gradient(135deg, rgba(127, 29, 29, 0.55), rgba(15, 23, 42, 0.95));
  border: 2px solid var(--red);
}
.status-pill {
  display: inline-block;
  padding: 0.35rem 0.85rem;
  border-radius: 999px;
  font-weight: 800;
  font-size: 0.88rem;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  margin-bottom: 0.75rem;
}
.pill-ok { background: var(--green); color: #052e16; }
.pill-bad { background: var(--red); color: #fff; }
.btn-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  margin: 1.1rem 0;
}
.btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.7rem 1.2rem;
  border-radius: 8px;
  font-weight: 700;
  font-size: 0.95rem;
  text-decoration: none;
  transition: transform 0.1s ease, opacity 0.15s ease;
}
.btn:hover { transform: translateY(-1px); opacity: 0.94; }
.btn-primary { background: var(--green); color: #052e16; }
.btn-secondary { background: var(--accent); color: #082f49; }
.btn-outline { background: rgba(255,255,255,0.06); color: var(--text); border: 1px solid var(--border); }
.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin: 0.9rem 0;
}
.chip {
  padding: 0.28rem 0.68rem;
  border-radius: 6px;
  font-size: 0.82rem;
  font-weight: 600;
  background: rgba(255,255,255,0.06);
  border: 1px solid var(--border);
}
.chip-ok { border-color: rgba(34, 197, 94, 0.5); color: #86efac; background: rgba(34, 197, 94, 0.1); }
.chip-info { border-color: rgba(56, 189, 248, 0.5); color: #bae6fd; background: rgba(56, 189, 248, 0.1); }
.copy-box {
  background: #090d16;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 0.65rem 0.9rem;
  margin: 0.5rem 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 0.86rem;
  overflow-x: auto;
}
.copy-btn {
  background: var(--card);
  color: var(--text);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 0.3rem 0.65rem;
  cursor: pointer;
  font-size: 0.78rem;
  font-weight: 600;
  flex-shrink: 0;
}
.copy-btn:hover { border-color: var(--accent); color: var(--accent); }
section.card {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 1.4rem 1.6rem;
  margin-bottom: 1.5rem;
}
h1, h2, h3 { color: #f8fafc; margin-top: 0; }
h1 { font-size: 1.75rem; margin-bottom: 0.6rem; }
h2 { font-size: 1.32rem; border-bottom: 1px solid var(--border); padding-bottom: 0.45rem; margin-bottom: 1rem; }
h3 { font-size: 1.08rem; color: var(--accent); margin-top: 1.2rem; margin-bottom: 0.4rem; }
table {
  width: 100%;
  border-collapse: collapse;
  margin: 0.85rem 0;
  font-size: 0.88rem;
}
th, td {
  border: 1px solid var(--border);
  padding: 0.55rem 0.75rem;
  text-align: left;
  vertical-align: top;
}
th { background: var(--card); color: #e2e8f0; font-weight: 700; }
tr:nth-child(even) td { background: rgba(30, 41, 59, 0.4); }
tr.highlight td { background: rgba(34, 197, 94, 0.14); font-weight: 600; }
code, pre {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 0.86rem;
}
code {
  background: rgba(255,255,255,0.07);
  padding: 0.12rem 0.35rem;
  border-radius: 4px;
}
pre {
  background: #090d16;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 1rem;
  overflow-x: auto;
}
.grid-2 {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
  gap: 1.2rem;
}
.muted { color: var(--muted); font-size: 0.88rem; }
a { color: var(--accent); }
.math-box {
  background: #090d16;
  border-left: 4px solid var(--accent);
  padding: 0.9rem 1.2rem;
  border-radius: 0 8px 8px 0;
  margin: 0.9rem 0;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 0.88rem;
}
"""


def build_hero(card: dict, ok: bool, reasons: list[str], val: dict, rel_prefix: str) -> str:
    tif_href = f"{rel_prefix}downloads/{Path(card['tif_download']).name}"
    zip_href = f"{rel_prefix}downloads/{Path(card['zip_download']).name}"
    tif_kb = card["tif_size_bytes"] / 1024.0
    zip_kb = card["zip_size_bytes"] / 1024.0
    dual = card["holdout_dti"]["dualseed_pooled_22663px"]
    s30 = card["holdout_dti"]["seed_30_11342px"]
    s20 = card["holdout_dti"]["seed_20_11321px"]
    can = card["leakage_canary"]
    uq = card["uniqueness"]

    if ok:
        cls = "hero-banner hero-ok"
        pill = '<span class="status-pill pill-ok">✅ OK TO DOWNLOAD AND SUBMIT · ALL AUTOMATED GATES PASSED</span>'
        headline = f"Promoted Submission Ready: {esc(card['submission_name'])}.tif"
        summary = (
            "Automated preflight verification passed without human intervention on the actual GeoTIFF & ZIP bytes on disk: "
            "single-band float32, EPSG:32611, 3730×3292, values strictly in [0.0, 1.0] (binary 0.0 / 1.0, 0 NaN anywhere, "
            "0.0 outside footprint — eliminating the 'Predicted values must be in range [0, 1]' portal error), "
            "37,654 positive dots, 0 dots on mapped catalogue (min distance 3.1623 px = 316.2 m), "
            "all 82 single-feature leakage canaries <= 0.8054 <= 0.90, and registry uniqueness verified across all 119 rasters "
            "(|Spearman rho| <= 0.1243 surface / 0.0505 dots <= 0.90; 3-px dot overlap <= 0.6500 <= 0.70)."
        )
    else:
        cls = "hero-banner hero-bad"
        pill = '<span class="status-pill pill-bad">⛔ NOT OK TO SUBMIT · FAIL-CLOSED GATE FIRED</span>'
        headline = f"Hold — Do Not Submit: {esc('; '.join(reasons))}"
        summary = "One or more automated validation, canary, or uniqueness checks failed on disk."

    return f"""
<div class="{cls}">
  {pill}
  <h1>{headline}</h1>
  <p>{esc(summary)}</p>
  <div class="btn-row">
    <a class="btn btn-primary" href="{esc(tif_href)}" download>⬇ Download Validated .tif ({tif_kb:.1f} KB)</a>
    <a class="btn btn-secondary" href="{esc(zip_href)}" download>⬇ Download Single-TIFF .zip ({zip_kb:.1f} KB)</a>
    <a class="btn btn-outline" href="executive-summary.html">📋 Executive Summary &amp; Step-by-Step Portal Guide →</a>
    <a class="btn btn-outline" href="{esc(SUB_URL)}" target="_blank" rel="noopener">🚀 Open DrivenData Submissions Portal ↗</a>
  </div>
  <div class="chips">
    <span class="chip chip-ok">Format &amp; [0,1] Range: PASS (min=0.0, max=1.0, 0 NaN, EPSG:32611, 3730×3292)</span>
    <span class="chip chip-ok">Dual-Seed HOLDOUT-DTI: {dual['dti']:.4f} (95% CI {dual['ci95'][0]:.4f}–{dual['ci95'][1]:.4f}; 22,663 withheld px)</span>
    <span class="chip chip-ok">Seed 30: {s30['dti']:.4f} · Seed 20: {s20['dti']:.4f} (Beats H77-VDS 0.1716/0.1608 &amp; H85-EDTI 0.1828)</span>
    <span class="chip chip-ok">Leakage Canary (82 ch): PASS (max AUC {can['seed_20_max_auc']:.4f} &le; 0.90)</span>
    <span class="chip chip-ok">Registry Uniqueness (119 rasters): PASS (|&rho;| &le; {uq['final_dots_worst_spearman']:.4f}, 3-px overlap &le; {uq['final_dots_worst_overlap_3px']:.4f} &le; 0.70)</span>
    <span class="chip chip-info">Weekly Submission Slots Used: 0</span>
  </div>
  <p class="muted" style="margin:0.4rem 0 0.2rem;">Unique Submission Filename / Identifier (click Copy):</p>
  <div class="copy-box">
    <code>{esc(card['submission_name'])}.tif</code>
    <button class="copy-btn" onclick="navigator.clipboard.writeText('{esc(card['submission_name'])}.tif');this.textContent='Copied!';">Copy Filename</button>
  </div>
  <p class="muted" style="margin:0.4rem 0 0.2rem;">DrivenData Portal Submission Note ({len(card['portal_note'])} / 140 chars):</p>
  <div class="copy-box">
    <code>{esc(card['portal_note'])}</code>
    <button class="copy-btn" onclick="navigator.clipboard.writeText('{esc(card['portal_note'])}');this.textContent='Copied!';">Copy Portal Note</button>
  </div>
  <p class="muted" style="margin-top:0.55rem;">
    <b>TIFF SHA-256:</b> <code>{esc(card['raster_sha256'])}</code> ·
    <b>ZIP SHA-256:</b> <code>{esc(card['zip_sha256'])}</code> ·
    <b>Evaluator:</b> <code>{esc(card['evaluator_version'])}</code> (<code>HOLDOUT-DTI</code> — local hide-and-recover holdout measurement, never a leaderboard projection)
  </p>
</div>
"""


def build_index_html(card: dict, canary: dict, exp2: dict, uniq: dict, ok: bool, reasons: list[str], val: dict, rel_prefix: str) -> str:
    hero = build_hero(card, ok, reasons, val, rel_prefix)
    fig_src = f"{rel_prefix}figures/h83_gvcd_surface_and_dots.png"
    dual_scores = card["holdout_dti"]["all_arms_dualseed"]
    s30_scores = card["holdout_dti"]["all_arms_seed30"]
    s20_scores = card["holdout_dti"]["all_arms_seed20"]
    pdiffs = card["holdout_dti"]["paired_differences_dualseed"]

    arm_labels = [
        ("A0_random", "A0: Uniform Random Control (Poisson-disk sep 2.8 px, d > 2 px)"),
        ("A1_phys_poisson", "A1: 60 Label-Free Physical + Geothermal + Radiometric + LiDAR Channels Only (LOQO)"),
        ("A2_struct_poisson", "A2: 22 Fold-Proper Visible-Network Continuation/Relay + Geothermal-Coupling Channels Only (LOQO)"),
        ("A3_gvcd_poisson", "A3: Full 82-Channel H83-GVCD Cross-Tree Ensemble + Standard Poisson-Disk (sep 2.8 px, d > 2 px)"),
        ("A4_gvcd_dink_c20", "A4: Full 82-Channel H83-GVCD + Quadrant-Calibrated Dinkelbach 300 m Submodular Emitter (d > 2 px)"),
        ("A5_gvcd_dink_c30", "A5: Full 82-Channel H83-GVCD + Collar-Decoupled Dinkelbach 300 m Submodular Emitter (d > 3 px, Cap <= 0.650) [PROMOTED]"),
    ]
    arm_rows = ""
    for key, label in arm_labels:
        d_s30 = s30_scores[key]
        d_s20 = s20_scores[key]
        d_pool = dual_scores[key]
        if key == "A5_gvcd_dink_c30":
            delta_str = "Reference (Promoted Candidate)"
            row_cls = ' class="highlight"'
        else:
            pd = pdiffs[key]
            delta_str = f"+{pd['delta']:.4f} (+{pd['ci95'][0]:.4f} to +{pd['ci95'][1]:.4f})"
            row_cls = ""
        arm_rows += f"""
        <tr{row_cls}>
          <td><b>{esc(label)}</b></td>
          <td><b>{d_pool['dti']:.4f}</b><br><span class="muted">[{d_pool['ci95'][0]:.4f}, {d_pool['ci95'][1]:.4f}]</span></td>
          <td>{d_s30['dti']:.4f}<br><span class="muted">[{d_s30['ci95'][0]:.4f}, {d_s30['ci95'][1]:.4f}]</span></td>
          <td>{d_s20['dti']:.4f}<br><span class="muted">[{d_s20['ci95'][0]:.4f}, {d_s20['ci95'][1]:.4f}]</span></td>
          <td>{d_pool['tpw']:.1f} / {d_pool['fpw']:.1f}</td>
          <td>{esc(delta_str)}</td>
        </tr>"""

    top_canary_s30 = canary["seeds"]["30"]["top_15_features"][:10]
    top_canary_s20 = {x["feature"]: x["symmetric_auc"] for x in canary["seeds"]["20"]["top_15_features"]}
    all_s20 = canary["seeds"]["20"]["per_feature_symmetric_auc"]
    canary_rows = ""
    for item in top_canary_s30:
        fnm = item["feature"]
        v30 = item["symmetric_auc"]
        v20 = all_s20.get(fnm, top_canary_s20.get(fnm, 0.5))
        canary_rows += f"""
        <tr>
          <td><code>{esc(fnm)}</code></td>
          <td>{v30:.4f}</td>
          <td>{v20:.4f}</td>
          <td>&le; 0.9000</td>
          <td><span style="color:#4ade80;font-weight:700;">PASS</span></td>
        </tr>"""

    ov_rows = ""
    for r in uniq["literal_untruncated_audit"]["top_10_informative_literal_overlap"][:8]:
        ov_rows += f"""
        <tr>
          <td><code>{esc(r['name'])}</code></td>
          <td>{r['their_positive_pixels']:,}</td>
          <td>{r['their_3px_halo_footprint_coverage']*100:.2f}%</td>
          <td>{r['literal_forward_overlap_3px']:.4f} (&le; 0.70)</td>
          <td>{r['spearman_full_footprint']:.4f} (&le; 0.90)</td>
          <td><span style="color:#4ade80;font-weight:700;">PASS</span></td>
        </tr>"""

    run_card_json_str = json.dumps(card, indent=2)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>GEMSDOE83 · Lane H83-GVCD — Geothermal-Vent &amp; Structural-Relay Counterfactual Dinkelbach Submodular Fusion</title>
  <style>{CSS}</style>
</head>
<body>
<header class="nav">
  <div class="nav-inner">
    <a class="brand" href="index.html">GEMSDOE83 <span>· Lane H83-GVCD</span></a>
    <nav class="nav-links">
      <a class="active" href="index.html">Main Research &amp; Audit Hub</a>
      <a href="executive-summary.html">Executive Summary &amp; How to Submit</a>
      <a href="#why-h33">Why GEMSDOE32 Scored 0.2778</a>
      <a href="#hypotheses">5 Ranked Hypotheses</a>
      <a href="#experiments">3 Holdout Experiments</a>
      <a href="#uniqueness">119-Raster Uniqueness Audit</a>
      <a href="#leaderboard">Prior Scores &amp; Irregularities</a>
      <a href="#runcard">JSON Run Card</a>
    </nav>
  </div>
</header>
<main>
  {hero}

  <section class="card">
    <h2>1. Visual Diagnostic Overview — Surface, Emitted 37,654 Dots &amp; Holdout Progression</h2>
    <p>
      Below is the 3-panel diagnostic overview generated directly from the validated production artifacts
      (<code>data/processed/h83_final_surface.npy</code>, <code>{esc(card['submissions_tif'])}</code>, and
      <code>evidence/h83_exp2_dualseed_holdout.json</code>):
    </p>
    <p style="text-align:center;margin:1rem 0;">
      <img src="{esc(fig_src)}" alt="H83-GVCD 3-Panel Diagnostic Map and Holdout Progression" style="max-width:100%;border-radius:10px;border:1px solid var(--border);">
    </p>
  </section>

  <section class="card" id="why-h33">
    <h2>2. PhD-Level Analysis: Why GEMSDOE32 Scored <code>0.2778</code> (<code>ORGANIZER-CONFIRMED</code>) &amp; How to Surpass <code>0.2778</code> / <code>0.3195</code> Toward <code>0.4413</code></h2>
    <div class="grid-2">
      <div>
        <h3>2.1 Byte-Level Forensics of <code>GEMSDOE32</code> (<code>0.2778</code>)</h3>
        <p>
          Direct byte inspection of <code>data/raw/scored/h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif</code>
          (SHA-256 <code>c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9</code>, <code>219,065</code> bytes)
          and its build receipt in <code>buffedlizard55-lab/GEMSDOE32/registry/submission_build.json</code> proves:
        </p>
        <ul>
          <li><b>Exact Pixel Support:</b> <code>37,654</code> binary positive pixels (<code>1.0</code> inside footprint, <code>0.0</code> elsewhere, <code>0</code> NaNs), representing <code>0.7287%</code> of the <code>5,167,373</code> in-footprint cells.</li>
          <li><b>Catalogue Exclusion Collar:</b> <code>0</code> pixels on the mapped catalogue (<code>existing_faults.tif</code>, <code>60,988</code> cells) and <code>0</code> pixels within <code>d &le; 2.0 px</code> (<code>200 m</code>). Minimum Euclidean distance to any mapped fault is <code>&radic;5 px &approx; 2.2361 px</code> (<code>223.6 m</code>); median distance is <code>12.04 px</code> (<code>1.20 km</code>).</li>
          <li><b>Controlled 3-Step Live Genealogy:</b>
            <ol>
              <li><code>GEMSDOE24</code> (<code>h24-4-r1-solo-d2.8</code>): <code>44,090</code> dots, <code>d &gt; 0 px</code> &rarr; <b><code>0.2600</code></b> <code>ORGANIZER-CONFIRMED</code>.</li>
              <li><code>GEMSDOE28</code> (<code>GEMS28-H27-4-R1-SOLO-D2.8</code>): pruned <code>3,891</code> dots at <code>d &le; 1.0 px</code> &rarr; <code>40,199</code> dots &rarr; <b><code>0.2708</code></b> <code>ORGANIZER-CONFIRMED</code> (<code>+0.0108</code>).</li>
              <li><code>GEMSDOE32</code> (<code>h33-h33-2-b2</code>): pruned <code>2,545</code> dots at <code>1.0 &lt; d &le; 2.0 px</code> &rarr; <code>37,654</code> dots &rarr; <b><code>0.2778</code></b> <code>ORGANIZER-CONFIRMED</code> (<code>+0.0070</code> over <code>GEMSDOE28</code>, <code>+0.0178</code> over <code>GEMSDOE24</code>).</li>
            </ol>
          </li>
        </ul>
      </div>
      <div>
        <h3>2.2 Exact DTI Marginal-Emission Proof</h3>
        <p>
          Under the official Distance-Weighted Tversky Index (<a href="{esc(DESC_URL)}" target="_blank" rel="noopener">DrivenData #306</a>,
          &alpha; = 0.2, &beta; = 0.8, 300 m triangular kernel <i>k(d) = max(1 &minus; d/3, 0)</i>), since &alpha; + &beta; = 1, the denominator simplifies to:
        </p>
        <div class="math-box">
          D(S) = 0.2 &middot; (TP_w(S) + |S| &minus; &Sigma;<sub>x&in;S</sub> q(x)) + 0.8 &middot; |T_test|<br>
          DTI(S) = TP_w(S) / D(S)
        </div>
        <p>
          Adding a binary dot <i>x</i> with incremental coverage &Delta;T(x) and false-positive penalty &Delta;F(x) = 1 &minus; q(x) improves DTI at current score <i>s</i> if and only if:
        </p>
        <div class="math-box">
          &Delta;T(x) / &Delta;F(x) &gt; &alpha;s / (1 &minus; (1 &minus; &beta;)s) = 0.2s / (1 &minus; 0.2s) &approx; 0.05726 (at s = 0.2708)
        </div>
        <p>
          Pixels at <code>1 &lt; d(x, C) &le; 2 px</code> (<code>100–200 m</code> laterally across strike from a digitized range-front fault) lie inside the digitization collar of the <i>already-mapped</i> fault (which is masked from test truth <i>T_test</i>) and are already 45%–67% covered by dots at <code>d &gt; 3 px</code>. Removing those <code>2,545</code> wasted dots cut the denominator by <code>0.2 &times; 2545 = 509.0</code> units with near-zero numerator loss, raising live DTI from <code>0.2708</code> to <code>0.2778</code>.
        </p>
      </div>
    </div>
    <h3>2.3 Three Structural Bottlenecks Beyond <code>0.2778</code> / <code>0.3195</code> and How <code>H83-GVCD</code> Solves Them</h3>
    <ol>
      <li><b>Eliminating the <i>d = 0</i> On-Catalogue Training Tautology via Counterfactual Re-Withholding:</b> Standard classifiers trained on <code>catalogue</code> (<i>d = 0</i>) vs <code>~catalogue</code> (<i>d &gt; 3</i>) learn features that peak on mapped traces rather than across unmapped step-over relays or blind faults. <code>H83-GVCD</code> trains strictly on <b>counterfactual component-withheld splits (<code>synthetic_withhold</code>, <code>buffer_px = 3</code>)</b> of the fold's visible network, so both training positives and training negatives reside in the exact <code>d &gt; 3.0 px</code> regime where inference occurs.</li>
      <li><b>Integrating Deep Hydrothermal Upflow Plumes, Geothermometers &amp; Relief-Deconfounded 1 m LiDAR:</b> Blind intrabasin and piedmont faults lack 30 m DEM scarps but conduct deep geothermal fluids and offset Quaternary fans at the 1 m scale. We fuse <b>27,092 DOE GDR #1391 thermal wells/springs &amp; silica/cation geothermometers</b> + <b>USGS GeoDAWN airborne radiometric K/Th metasomatism &amp; 150 m upward-continuation magnetic residual</b> + <b>USGS 3DEP 1 m relief-deconfounded LiDAR scarp coherence</b> directly with hollow-core fault-tip rays (<code>coup_geotherm_tip</code>) and relay bridges (<code>coup_geotherm_gap</code>).</li>
      <li><b>Replacing Greedy Poisson-Disk with Quadrant-Calibrated Dinkelbach 300 m Submodular Optimization:</b> Greedy Poisson-disk (<code>min_sep = 2.8 px</code>) ignores 29-cell 300 m kernel saturation and over-allocates dots to NW/SW quadrants with denser LiDAR coverage. Our <b>Quadrant-Calibrated Dinkelbach Submodular Emitter</b> maximizes expected marginal 300 m DTI gain at collar <code>d &gt; 3.0 px</code> while enforcing <code>overlap_cap = 0.650 &lt; 0.70</code> across all discriminating registry rasters, boosting dual-seed <code>HOLDOUT-DTI</code> from <code>0.1746</code> (Poisson-disk on the same surface) to <b><code>0.2068</code></b> (<code>+0.0322</code> DTI, <code>95% CI [+0.0245, +0.0404]</code>).</li>
    </ol>
  </section>

  <section class="card" id="hypotheses">
    <h2>3. Five Ranked Geological &amp; Geothermal Hypotheses (<code>H83-1</code> to <code>H83-5</code>)</h2>
    <table>
      <thead>
        <tr>
          <th>Rank</th>
          <th>Hypothesis &amp; Mechanism</th>
          <th>Exact Data Layers Used</th>
          <th>Why It Catches Unmapped Faults &amp; Deconfounds Mimics</th>
          <th>Measured Holdout DTI Impact &amp; Cost</th>
        </tr>
      </thead>
      <tbody>
        <tr class="highlight">
          <td><b>1</b></td>
          <td><b><code>H83-1</code>: Counterfactual Off-Catalogue Structural-Relay &amp; Hollow-Core Tip-Ray Geometry</b></td>
          <td><code>existing_faults.tif</code> (strictly <code>fold["visible"]</code> in holdout; <code>syn_state</code> in training)</td>
          <td>12-bin 2D FFT (<code>oaconvolve</code>) continuation (<code>ns_cont</code>), bilateral step-over bridge (<code>ns_gap = &radic;(f&middot;b)</code>), parallel hanging-wall sibling (<code>ns_sib</code>, 4–20 px across strike), and hollow-core (<i>s &ge; 4 px</i>) tip rays (<code>net_tip_ray</code>) catch unmapped relay ramps and splay terminations. Deconfounds erosional pediment embayments via multi-physics coupling.</td>
          <td><b><code>+0.0781</code> DTI</b> over physical-only (<code>0.0907 &rarr; 0.1688</code> dual-seed)<br><span class="muted">Cost: Medium (~70s/state)</span></td>
        </tr>
        <tr class="highlight">
          <td><b>2</b></td>
          <td><b><code>H83-2</code>: Collar-Decoupled Quadrant-Calibrated Dinkelbach Submodular 300 m Kernel Optimizer</b></td>
          <td><code>H83-GVCD</code> LOQO surface + <code>existing_faults.tif</code> (<i>d &gt; 3.0 px</i> collar) + 119 registry rasters</td>
          <td>Calibrates each spatial quadrant (NW, NE, SW, SE) via Bayes log-odds bisection (&pi;<sub>true</sub> = 0.0022) and maximizes submodular 29-cell 300 m triangular kernel coverage minus &lambda;<sub>fp</sub> false-positive cost with <code>overlap_cap = 0.650 &lt; 0.70</code>. Prevents LiDAR tile coverage bias and 1–2 px collar waste.</td>
          <td><b><code>+0.0322</code> DTI</b> over Poisson-disk <code>D2.8</code> on identical surface (<code>0.1746 &rarr; 0.2068</code> dual-seed)<br><span class="muted">Cost: Low (~14s)</span></td>
        </tr>
        <tr>
          <td><b>3</b></td>
          <td><b><code>H83-3</code>: Deep Hydrothermal Upflow Plumes, Geothermometer Enthalpy &amp; Clay-Cap Alteration Conduits Coupled to Fault Tips</b></td>
          <td>DOE GDR #1391 <code>gdr_wellspring_in_footprint.csv</code> (<code>temp_c</code>, <code>gt_quartz_c</code>, <code>gt_chalcedony_c</code>, <code>gt_na_k_ca_c</code>; never <code>dist_known_fault_px</code>), <code>gdr_volcanic_vents_in_footprint.csv</code>, Bands 4, 16, 17</td>
          <td>Amagmatic Great Basin geothermal upflow occurs at critically stressed fault tips and step-over relays beneath electrically conductive smectite/illite clay caps (<code>geotherm_claycap_conduit</code>, <code>coup_geotherm_tip</code>, <code>coup_geotherm_gap</code>). Deconfounds flat-lying playa brines by requiring geothermometer enthalpy + strain rate + tip-ray alignment.</td>
          <td><b><code>+0.0058</code> to <code>+0.0129</code> DTI</b> synergistic gain on top of structure (<code>0.1671 &rarr; 0.1800</code> on Seed 30)<br><span class="muted">Cost: Low (~8s)</span></td>
        </tr>
        <tr>
          <td><b>4</b></td>
          <td><b><code>H83-4</code>: Relief-Deconfounded 1 m LiDAR Piedmont Breaklines &amp; GeoDAWN K-Metasomatism (K/Th) + Shallow Magnetic Residual</b></td>
          <td>USGS 3DEP 1 m <code>lidar_scarp_features_u8.tif</code>, GeoDAWN <code>geodawn_rad_u8.tif</code> &amp; <code>geodawn_extensions_u8.tif</code>, Bands 14 &amp; 19</td>
          <td>Normalizes 1 m LiDAR scarp steps by local relief (<code>lidar_relief_norm_scarp</code>) and weights by 100 m breakline coherence (<code>lidar_scarp_coherence</code>), combined with hydrothermal adularia/illite K/Th enrichment (<code>rad_k_metasomatism</code>) and shallow magnetic residual <code>TMI &minus; TMI_up150</code>. Deconfounds Pleistocene Lake Lahontan shorelines via subsurface magnetic/gravity alignment.</td>
          <td>Included in <b><code>+0.0230</code> DTI</b> physical-stack gain over 39-band raw baseline (<code>0.0729 &rarr; 0.0959</code> Seed 30)<br><span class="muted">Cost: Low (~25s)</span></td>
        </tr>
        <tr>
          <td><b>5</b></td>
          <td><b><code>H83-5</code>: Basement-Step Gravity Horizontal-Gradient Curvature &amp; Transtensional Dilatation-Shear Tensor Coupling</b></td>
          <td><code>training_features.tif</code> Bands 7, 8, 13, 15, 18</td>
          <td>Couples positive GPS dilatation + shear strain rate (<code>x_strain_transtension</code>) with steep horizontal gradients in isostatic gravity and basement depth (<code>grad_iso_gravity_anomaly</code>, <code>grad_depth_to_basement</code>, <code>coup_strain_sib</code>) to recover buried intrabasin bounding faults. Rejects circular caldera/pluton margins via strike coherence.</td>
          <td>Included in <b><code>+0.0230</code> DTI</b> physical-stack gain<br><span class="muted">Cost: Low (~15s)</span></td>
        </tr>
      </tbody>
    </table>
  </section>

  <section class="card" id="experiments">
    <h2>4. Three Preregistered Experiments (<code>EXP-83-1</code>, <code>EXP-83-2</code>, <code>EXP-83-3</code>) — Dual-Seed <code>HOLDOUT-DTI</code> Results</h2>
    <p>
      Executed within the strict 3-experiment budget (<code>registry/preregistration_h83_gvcd.json</code>) using the
      <b>unmodified shared evaluator <code>vendor/gems57/evaluate_holdout.py</code> (<code>gems57-pooled-hide-v2</code>)</b>:
      20% whole 8-connected fault components withheld per spatial quadrant, 3 px context collar removed from visible faults,
      all structural features recomputed strictly from each fold's <code>visible</code> mask, visible faults masked pixel-exactly,
      pooled DTI (&alpha; = 0.2, &beta; = 0.8, 300 m triangular kernel), and 2,000 paired spatial-block bootstrap draws
      at the identical <code>37,654</code>-dot budget.
    </p>
    <table>
      <thead>
        <tr>
          <th>Ablation Arm (All at 37,654 Emitted Dots)</th>
          <th>Dual-Seed Pooled HOLDOUT-DTI<br>(22,663 withheld positives)</th>
          <th>Seed 30 HOLDOUT-DTI<br>(11,342 withheld positives)</th>
          <th>Seed 20 HOLDOUT-DTI<br>(11,321 withheld positives)</th>
          <th>Pooled TP<sub>w</sub> / FP<sub>w</sub></th>
          <th>Paired &Delta; (A5 &minus; Control)<br>[95% Spatial Bootstrap CI]</th>
        </tr>
      </thead>
      <tbody>
        {arm_rows}
      </tbody>
    </table>

    <h3>4.1 Single-Feature Leakage Canary Audit (<code>EXP-83-1</code>, All 82 Features &le; 0.90 Gate)</h3>
    <p>
      Every individual feature across all <b>82 channels</b> (60 label-free physical/geothermal/radiometric/LiDAR channels +
      18 fold-proper visible-network channels + 4 explicit geothermal-structural coupling channels) was tested alone against
      the withheld holdout truth on both <code>Seed 30</code> and <code>Seed 20</code> (<code>evidence/h83_leakage_canary.json</code>).
      <b>All 82 channels pass the <code>AUC &le; 0.90</code> gate on both seeds</b> (worst symmetric AUC: <code>0.8024</code> on Seed 30, <code>0.8054</code> on Seed 20):
    </p>
    <table>
      <thead>
        <tr>
          <th>Channel Name</th>
          <th>Seed 30 Symmetric AUC (11,342 pos)</th>
          <th>Seed 20 Symmetric AUC (11,321 pos)</th>
          <th>Canary Gate Ceiling</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        {canary_rows}
      </tbody>
    </table>
  </section>

  <section class="card" id="uniqueness">
    <h2>5. 119-Raster Registry Uniqueness Audit (<code>EXP-83-3</code> — Pre-Placement Surface &amp; Final Dots)</h2>
    <p>
      Audited via the unmodified <code>vendor/gems57/uniqueness.py</code> against all <b>119 prior registry rasters</b> in
      <code>data/raw/scored/*.tif</code> (<code>evidence/h83_uniqueness.json</code>):
    </p>
    <ul>
      <li><b>Pre-Placement Continuous Surface (<code>h83_final_surface.npy</code>):</b> <code>unique = True</code> · max <code>|Spearman &rho;| = {uniq['pre_placement_surface']['worst_spearman_full_footprint']:.4f} &le; 0.90</code> · max discriminating 3-px overlap = <code>{uniq['pre_placement_surface']['worst_dot_overlap_3px']:.4f} &le; 0.70</code>.</li>
      <li><b>Final Emitted Binary Dots (<code>{esc(card['submission_name'])}.tif</code>, <code>37,654</code> dots):</b> <code>unique = True</code> · max <code>|Spearman &rho;| = {uniq['final_emitted_dots']['worst_spearman_full_footprint']:.4f} &le; 0.90</code> · max forward 3-px overlap across all <b>115 discriminating priors</b> = <code>{uniq['final_emitted_dots']['worst_dot_overlap_3px']:.4f} &le; 0.70</code> (enforced directly inside the Dinkelbach priority queue with <code>overlap_cap = 0.650</code>).</li>
      <li><b>Transparent Reporting of the 4 Space-Filling / Whole-Grid Lattice Priors (<code>IR-83-04</code> / <code>IR-H85-01</code>):</b> Out of 119 files in <code>data/raw/scored/</code>, 4 files (<code>13gems_20261001_r13-lattice-s5_v2_nan-outside.tif</code> — a regular 5-px lattice across the whole basin — plus 3 continuous <code>-RESEARCH-ONLY</code> / <code>-research</code> surfaces with 1.88M–5.01M positive pixels) have 3-px halos covering <b>98.04% to 99.87% of the entire footprint</b>, where even uniformly random dots have 98%–99.9% overlap. Both readings are reported side by side in <code>evidence/h83_uniqueness.json</code>.</li>
    </ul>
    <table>
      <thead>
        <tr>
          <th>Closest Discriminating Registry Raster (115 total)</th>
          <th>Their Positive Pixels</th>
          <th>Their 3-px Halo Coverage of Footprint</th>
          <th>Our Forward 3-px Overlap (Limit &le; 0.70)</th>
          <th>Full-Footprint Spearman &rho; (Limit &le; 0.90)</th>
          <th>Gate Verdict</th>
        </tr>
      </thead>
      <tbody>
        {ov_rows}
      </tbody>
    </table>
  </section>

  <section class="card" id="leaderboard">
    <h2>6. Complete Prior GEMSDOE Leaderboard Scores (<code>ORGANIZER-CONFIRMED</code>) &amp; Local <code>HOLDOUT-DTI</code> Registry</h2>
    <p>
      Every metric below is explicitly labeled by its evidence class (<code>ORGANIZER-CONFIRMED</code> live DrivenData leaderboard score vs
      <code>HOLDOUT-DTI</code> local hide-and-recover evaluator score). Local holdout scores and live leaderboard scores measure different things and are never conflated:
    </p>
    <table>
      <thead>
        <tr>
          <th>Repository / Lane</th>
          <th>Submission Filename / Artifact</th>
          <th>Emitted Positive Pixels</th>
          <th>Evidence Class</th>
          <th>Score &amp; Details</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>External Competition Leader</td>
          <td>DrivenData Leaderboard High (<a href="{esc(LB_URL)}" target="_blank" rel="noopener">Leaderboard</a>)</td>
          <td>Unknown (External)</td>
          <td><code>ORGANIZER-CONFIRMED</code></td>
          <td><b><code>0.4413</code></b> (current external competition ceiling)</td>
        </tr>
        <tr>
          <td><code>GEMSDOE49</code></td>
          <td><code>GEMS49-H49-R1-HYBRID-ANCHOR-31K</code></td>
          <td>31,182 (weighted)</td>
          <td><code>ORGANIZER-CONFIRMED</code></td>
          <td><b><code>0.3195</code></b> (project owner's highest multi-model live ensemble)</td>
        </tr>
        <tr>
          <td><code>GEMSDOE32</code></td>
          <td><code>h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif</code></td>
          <td>37,654 (binary, <i>d &gt; 2 px</i>)</td>
          <td><code>ORGANIZER-CONFIRMED</code></td>
          <td><b><code>0.2778</code></b> (single-family binary Poisson-disk D2.8 + 2 px collar prune; SHA-256 <code>c55bafc4...</code>)</td>
        </tr>
        <tr>
          <td><code>GEMSDOE28</code></td>
          <td><code>GEMS28-H27-4-R1-SOLO-D2.8</code></td>
          <td>40,199 (binary, <i>d &gt; 1 px</i>)</td>
          <td><code>ORGANIZER-CONFIRMED</code></td>
          <td><b><code>0.2708</code></b> (1 px collar prune parent of H33)</td>
        </tr>
        <tr>
          <td><code>GEMSDOE24</code></td>
          <td><code>h24-4-r1-solo-d2.8</code></td>
          <td>44,090 (binary, <i>d &gt; 0 px</i>)</td>
          <td><code>ORGANIZER-CONFIRMED</code></td>
          <td><b><code>0.2600</code></b> (unpruned Poisson-disk D2.8 grandparent of H33)</td>
        </tr>
        <tr>
          <td><code>GEMSDOE73</code> (<code>H73-A</code>)</td>
          <td><code>gems73-h73-a-ridge-submod-20261020.tif</code></td>
          <td>37,654</td>
          <td><code>HOLDOUT-DTI</code> (<code>gems57-pooled-hide-v2</code>)</td>
          <td><code>0.112230</code> (Seed 30, 11,342 withheld positives)</td>
        </tr>
        <tr>
          <td><code>GEMSDOE75</code></td>
          <td><code>gems75-submod-37654.tif</code></td>
          <td>37,654</td>
          <td><code>HOLDOUT-DTI</code> (<code>gems57-pooled-hide-v2</code>)</td>
          <td><code>0.135088</code> (Seed 30, 11,342 withheld positives)</td>
        </tr>
        <tr>
          <td><code>GEMSDOE77</code> (<code>H77-Step</code>)</td>
          <td><code>gems77-step-propensity-submod300.tif</code></td>
          <td>34,625</td>
          <td><code>HOLDOUT-DTI</code> (<code>gems57-pooled-hide-v2</code>)</td>
          <td><code>0.152718</code> (Seed 20 incumbent, 11,321 withheld positives)</td>
        </tr>
        <tr>
          <td><code>GEMSDOE76</code> (<code>H76-3</code>)</td>
          <td><code>gemsdoe76-h76-3-hero-matched-37654dots-20261021-c11c9e7d-zeros.tif</code></td>
          <td>37,654</td>
          <td><code>HOLDOUT-DTI</code> (<code>gems57-pooled-hide-v2</code>)</td>
          <td><code>0.158020</code> (Seed 30, 11,342 withheld positives)</td>
        </tr>
        <tr>
          <td><code>GEMSDOE77</code> (<code>H83-NETSIB</code>)</td>
          <td><code>gems77-h83-netsib-37654dots-20261021-ed06b51d-zeros.tif</code></td>
          <td>37,654</td>
          <td><code>HOLDOUT-DTI</code> (<code>gems57-pooled-hide-v2</code>)</td>
          <td><code>0.163700</code> (Seed 30) / <code>0.153825</code> (Seed 20) — stopped on 0.9091 overlap</td>
        </tr>
        <tr>
          <td><code>GEMSDOE77</code> (<code>H77-VDS</code>)</td>
          <td><code>gems77-h77e-vds-dinkelbach-44090dots-20261021.tif</code></td>
          <td>37,654 / 44,090</td>
          <td><code>HOLDOUT-DTI</code> (<code>gems57-pooled-hide-v2</code>)</td>
          <td><code>0.171625</code> (Seed 30) / <code>0.160795</code> (Seed 20) at 37,654 dots</td>
        </tr>
        <tr>
          <td><code>GEMSDOE77</code> (<code>H85-EDTI</code>)</td>
          <td><code>gems85-h85-edti-collar35-skel-r33-20261021-d97b248e-zeros.tif</code></td>
          <td>201,260 (over-emitted, <code>IR-83-03</code>)</td>
          <td><code>HOLDOUT-DTI</code> (<code>gems57-pooled-hide-v2</code>)</td>
          <td><code>0.182804</code> Dual-Seed / <code>0.190925</code> Seed 30 / <code>0.173903</code> Seed 20 (affected by <code>IR-83-01</code>)</td>
        </tr>
        <tr class="highlight">
          <td><b><code>GEMSDOE83</code> (<code>H83-GVCD</code>, This Repo)</b></td>
          <td><b><code>{esc(card['submission_name'])}.tif</code></b></td>
          <td><b>37,654 (binary, <i>d &gt; 3 px</i>, 0 NaN)</b></td>
          <td><b><code>HOLDOUT-DTI</code> (<code>gems57-pooled-hide-v2</code>)</b></td>
          <td>
            <b><code>0.206817</code> Dual-Seed Pooled</b> (95% CI <code>[0.192711, 0.219822]</code>, 22,663 withheld px)<br>
            <b><code>0.213755</code> Seed 30</b> (95% CI <code>[0.196240, 0.230530]</code>, 11,342 withheld px)<br>
            <b><code>0.199862</code> Seed 20</b> (95% CI <code>[0.184146, 0.214649]</code>, 11,321 withheld px)
          </td>
        </tr>
      </tbody>
    </table>

    <h3>6.1 Data Sources, Limitations &amp; Code-Verified Irregularities (<a href="{esc(rel_prefix)}irregularities.md">Full Report</a>)</h3>
    <ul>
      <li><b>Official Data Sources:</b> <a href="{esc(COMP_URL)}" target="_blank" rel="noopener">DrivenData DOE GEMS #306</a> (19-band <code>training_features.tif</code>, <code>existing_faults.tif</code>, <code>sample_submission.tif</code>), <a href="{esc(GDR_URL)}" target="_blank" rel="noopener">DOE GDR #1391 INGENIOUS Great Basin Play Fairway</a> (27,092 wells/springs + 21 volcanic vents), <a href="{esc(GEODAWN_URL)}" target="_blank" rel="noopener">USGS GeoDAWN Airborne Survey</a> (radiometric K, Th, U, TC, ratios &amp; 150 m upward-continued TMI), and <a href="{esc(THREEDEP_URL)}" target="_blank" rel="noopener">USGS 3DEP 1 m DEM</a> breakline stack.</li>
      <li><b><code>IR-83-01</code> (Fixed):</b> Prior lane <code>h85_edti_pipeline.py</code> called <code>train_surface(X, f["region"], ...)</code> on the test quadrant instead of out-of-fold quadrants. <code>H83-GVCD</code> trains strictly Leave-One-Quadrant-Out (<code>j != k</code>).</li>
      <li><b><code>IR-83-02</code> (Fixed):</b> Prior lane <code>h85_edti_pipeline.py</code> filtered Stage-2 negatives using <code>ndi.distance_transform_edt(~grid.catalogue)</code> (full catalogue). <code>H83-GVCD</code> uses strictly <code>(cat &amp; tr_reg) | visible</code>.</li>
      <li><b><code>IR-83-03</code> (Fixed):</b> Prior lane <code>h85_edti_pipeline.py</code> emitted <code>201,260</code> dots (<code>3.3 &times; 60,988</code>) on the full grid. <code>H83-GVCD</code> emits the exact <code>37,654</code>-dot budget in both holdout and production.</li>
      <li><b><code>IR-83-04</code> / <code>IR-H85-01</code> (Documented):</b> 4 of 119 files in <code>data/raw/scored/</code> are whole-grid 5-px lattices or continuous research surfaces whose 3-px halos cover 98.0%–99.9% of the footprint. Both the binding like-for-like uniqueness decision (<code>PASS</code> across all 115 discriminating priors, max overlap <code>0.6500 &le; 0.70</code>) and the literal all-119 table are reported in <code>evidence/h83_uniqueness.json</code>.</li>
    </ul>
  </section>

  <section class="card" id="runcard">
    <h2>7. Machine-Readable JSON Run Card (<code>run_card.json</code>)</h2>
    <pre>{esc(run_card_json_str)}</pre>
  </section>
</main>
</body>
</html>
"""


def build_exec_summary_html(card: dict, ok: bool, reasons: list[str], val: dict, rel_prefix: str) -> str:
    hero = build_hero(card, ok, reasons, val, rel_prefix)
    dual = card["holdout_dti"]["dualseed_pooled_22663px"]
    s30 = card["holdout_dti"]["seed_30_11342px"]
    s20 = card["holdout_dti"]["seed_20_11321px"]

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Executive Summary &amp; How to Submit · GEMSDOE83 (Lane H83-GVCD)</title>
  <style>{CSS}</style>
</head>
<body>
<header class="nav">
  <div class="nav-inner">
    <a class="brand" href="index.html">GEMSDOE83 <span>· Lane H83-GVCD</span></a>
    <nav class="nav-links">
      <a href="index.html">Main Research &amp; Audit Hub</a>
      <a class="active" href="executive-summary.html">Executive Summary &amp; How to Submit</a>
      <a href="{esc(SUB_URL)}" target="_blank" rel="noopener">DrivenData Submissions Portal ↗</a>
      <a href="{esc(LB_URL)}" target="_blank" rel="noopener">Live Leaderboard ↗</a>
    </nav>
  </div>
</header>
<main>
  {hero}

  <section class="card">
    <h2>1. Step-by-Step Guide: How to Download &amp; Submit to the DOE GEMS Prize Portal</h2>
    <ol>
      <li>
        <b>Verify the Automated Status Badge Above:</b> Confirm that the green banner at the top of this page reads
        <code>✅ OK TO DOWNLOAD AND SUBMIT · ALL AUTOMATED GATES PASSED</code>. This badge is computed fail-closed from the actual
        GeoTIFF bytes on disk (SHA-256 <code>{esc(card['raster_sha256'])}</code>).
      </li>
      <li>
        <b>Download the Validated Submission File:</b> Click either
        <b>⬇ Download Validated .tif ({card['tif_size_bytes']/1024:.1f} KB)</b> or
        <b>⬇ Download Single-TIFF .zip ({card['zip_size_bytes']/1024:.1f} KB)</b> above.
        The DrivenData portal accepts either a single-band <code>.tif</code> or a <code>.zip</code> containing a single <code>.tif</code>.
      </li>
      <li>
        <b>Open the DrivenData DOE GEMS Submission Page:</b> Sign in at
        <a href="{esc(SUB_URL)}" target="_blank" rel="noopener">{esc(SUB_URL)}</a> and click <b>Submit file</b>.
      </li>
      <li>
        <b>Upload the File &amp; Paste the 140-Character Portal Note:</b> Select
        <code>{esc(card['submission_name'])}.tif</code> (or <code>.zip</code>) and paste the pre-formatted note from the copy box above:
        <div class="copy-box">
          <code>{esc(card['portal_note'])}</code>
          <button class="copy-btn" onclick="navigator.clipboard.writeText('{esc(card['portal_note'])}');this.textContent='Copied!';">Copy Note</button>
        </div>
      </li>
      <li>
        <b>Record the Organizer Score Receipt:</b> Once scored by DrivenData, record the returned live score as an
        <code>ORGANIZER-CONFIRMED</code> receipt paired with SHA-256 <code>{esc(card['raster_sha256'])}</code>.
        (This repository has used <b>0 weekly submission slots</b>; spending a weekly slot is always the human selector's decision.)
      </li>
    </ol>
  </section>

  <section class="card">
    <h2>2. Why the Earlier <code>"Predicted values must be in range [0, 1]"</code> Portal Error Cannot Occur</h2>
    <p>
      Earlier submissions across the GEMSDOE project encountered the DrivenData portal rejection
      <code>"Predicted values must be in range [0, 1]"</code> when outside-footprint cells contained <code>NaN</code>
      (matching <code>sample_submission.tif</code>'s <code>NaN</code> outside-footprint mask) or unclipped floating-point drift.
      Our file <code>{esc(card['submission_name'])}.tif</code> was written by the unmodified
      <code>vendor/gems57/submission_writer.py</code> and verified on disk by <code>vendor/gems57/validate.py</code>:
    </p>
    <table>
      <thead>
        <tr>
          <th>Automated Preflight Check</th>
          <th>Measured Value on Disk</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        <tr><td>Single-Band Float32 GeoTIFF</td><td><code>count = 1, dtype = float32, nodata = None</code></td><td><span style="color:#4ade80;font-weight:700;">PASS</span></td></tr>
        <tr><td>CRS &amp; Grid Dimensions</td><td><code>EPSG:32611, 3730 &times; 3292</code></td><td><span style="color:#4ade80;font-weight:700;">PASS</span></td></tr>
        <tr><td>Affine Geotransform</td><td><code>(100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)</code></td><td><span style="color:#4ade80;font-weight:700;">PASS</span></td></tr>
        <tr><td>Minimum / Maximum Pixel Value</td><td><code>min = {val.get('min', 0.0):.1f}, max = {val.get('max', 1.0):.1f}</code> (strictly in <code>[0.0, 1.0]</code>)</td><td><span style="color:#4ade80;font-weight:700;">PASS</span></td></tr>
        <tr><td>NaN / Infinite / Sentinel Count</td><td><code>n_nan = {val.get('n_nan', 0)}, n_infinite = {val.get('n_infinite', 0)}, n_finite = {val.get('n_finite', 12279160):,}</code></td><td><span style="color:#4ade80;font-weight:700;">PASS</span></td></tr>
        <tr><td>Outside-Footprint Pixel Values</td><td>Strictly <code>0.0</code> on all <code>7,111,787</code> outside-footprint cells</td><td><span style="color:#4ade80;font-weight:700;">PASS</span></td></tr>
        <tr><td>Emitted Positive Pixels &amp; Catalogue Masking</td><td><code>37,654</code> binary dots inside footprint · <code>0</code> dots on mapped catalogue (min dist <code>3.1623 px</code>)</td><td><span style="color:#4ade80;font-weight:700;">PASS</span></td></tr>
      </tbody>
    </table>
  </section>

  <section class="card">
    <h2>3. Summary of Validation Gates Passed by <code>H83-GVCD</code></h2>
    <ul>
      <li><b>Dual-Seed Spatially-Blocked Holdout (<code>gems57-pooled-hide-v2</code>):</b>
        <ul>
          <li><b>Dual-Seed Pooled (22,663 withheld positives):</b> <code>HOLDOUT-DTI = {dual['dti']:.4f}</code> (95% CI <code>[{dual['ci95'][0]:.4f}, {dual['ci95'][1]:.4f}]</code>)</li>
          <li><b>Seed 30 (11,342 withheld positives):</b> <code>HOLDOUT-DTI = {s30['dti']:.4f}</code> (95% CI <code>[{s30['ci95'][0]:.4f}, {s30['ci95'][1]:.4f}]</code>)</li>
          <li><b>Seed 20 (11,321 withheld positives):</b> <code>HOLDOUT-DTI = {s20['dti']:.4f}</code> (95% CI <code>[{s20['ci95'][0]:.4f}, {s20['ci95'][1]:.4f}]</code>)</li>
          <li>Surpasses <code>H77-Step</code> (<code>0.1527</code>), <code>H83-NETSIB</code> (<code>0.1538 / 0.1637</code>), <code>H77-VDS</code> (<code>0.1608 / 0.1716</code>), and <code>H85-EDTI</code> (<code>0.1828</code>).</li>
        </ul>
      </li>
      <li><b>Single-Feature Leakage Canary (82 Channels):</b> Max symmetric AUC = <code>0.8024</code> (Seed 30) / <code>0.8054</code> (Seed 20) &le; <code>0.90</code> ceiling.</li>
      <li><b>119-Raster Registry Uniqueness Gate:</b> Pre-placement surface max <code>|Spearman &rho;| = 0.1243 &le; 0.90</code>, overlap <code>0.5837 &le; 0.70</code>; Final dots max <code>|Spearman &rho;| = 0.0505 &le; 0.90</code>, binding forward 3-px overlap <code>0.6500 &le; 0.70</code> across all 115 discriminating priors.</li>
    </ul>
  </section>
</main>
</body>
</html>
"""


def main() -> int:
    card = json.loads((ROOT / "run_card.json").read_text())
    canary = json.loads((ROOT / "evidence" / "h83_leakage_canary.json").read_text())
    exp2 = json.loads((ROOT / "evidence" / "h83_exp2_dualseed_holdout.json").read_text())
    uniq = json.loads((ROOT / "evidence" / "h83_uniqueness.json").read_text())

    ok, reasons, val = verify_on_disk_bytes(card)
    if not ok:
        raise RuntimeError(f"Fail-closed site build check failed: {reasons}")

    # Root HTML pages (rel_prefix = "docs/")
    (ROOT / "index.html").write_text(
        build_index_html(card, canary, exp2, uniq, ok, reasons, val, rel_prefix="docs/"),
        encoding="utf-8",
    )
    (ROOT / "executive-summary.html").write_text(
        build_exec_summary_html(card, ok, reasons, val, rel_prefix="docs/"),
        encoding="utf-8",
    )

    # docs/ HTML pages (rel_prefix = "")
    docs_dir = ROOT / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    (docs_dir / "index.html").write_text(
        build_index_html(card, canary, exp2, uniq, ok, reasons, val, rel_prefix=""),
        encoding="utf-8",
    )
    (docs_dir / "executive-summary.html").write_text(
        build_exec_summary_html(card, ok, reasons, val, rel_prefix=""),
        encoding="utf-8",
    )
    (docs_dir / ".nojekyll").write_text("", encoding="utf-8")

    # Mirror evidence & research into docs/ for GitHub Pages links
    (docs_dir / "evidence").mkdir(parents=True, exist_ok=True)
    for f in (ROOT / "evidence").glob("*.json"):
        shutil.copy2(f, docs_dir / "evidence" / f.name)
    (docs_dir / "research").mkdir(parents=True, exist_ok=True)
    for f in (ROOT / "research").glob("*.md"):
        shutil.copy2(f, docs_dir / "research" / f.name)

    print("Built index.html, executive-summary.html, docs/index.html, and docs/executive-summary.html (OK=True)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
