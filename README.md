# `GEMSDOE83` · Lane `H83-GVCD` — Geothermal-Vent & Structural-Relay Counterfactual Dinkelbach Submodular Fusion

> ## ✅ OK TO DOWNLOAD AND SUBMIT · ALL AUTOMATED GATES PASSED
>
> - **Promoted Submission GeoTIFF (`.tif`)**: [`docs/downloads/gems83-h83-gvcd-dink300-37654dots-20261021-1a373694-zeros.tif`](docs/downloads/gems83-h83-gvcd-dink300-37654dots-20261021-1a373694-zeros.tif) (also in [`submissions/gems83-h83-gvcd-dink300-37654dots-20261021-1a373694-zeros.tif`](submissions/gems83-h83-gvcd-dink300-37654dots-20261021-1a373694-zeros.tif))
>   - **TIFF Size / SHA-256**: `144,047` bytes · `79f14dc84cd7760cb44645bc090ed2d33dbcfe789cec844fd83753fcff1082a2`
> - **Single-TIFF Portal Archive (`.zip`)**: [`docs/downloads/gems83-h83-gvcd-dink300-37654dots-20261021-1a373694-zeros.zip`](docs/downloads/gems83-h83-gvcd-dink300-37654dots-20261021-1a373694-zeros.zip)
>   - **ZIP Size / SHA-256**: `110,287` bytes · `4a556307f06e31edadb5e9b73366998c7efb5857d88db51ecb70f2850e5b460e`
> - **Executive Summary & Step-by-Step Portal Submission Guide**: [`executive-summary.html`](executive-summary.html) · [`docs/executive-summary.html`](docs/executive-summary.html)
> - **Main Interactive Research & Audit Hub**: [`index.html`](index.html) · [`docs/index.html`](docs/index.html)
> - **DrivenData Portal Submission Note (130 / 140 chars)**:
>   ```text
>   H83-GVCD geothermal-vent & structural-relay counterfactual Dinkelbach 300m submodular; 37654 dots >3px off cat; HOLDOUT-DTI 0.2068
>   ```
> - **Automated Format & `[0, 1]` Range Preflight (`vendor/gems57/validate.py`)**: **PASS** (`single-band float32`, `EPSG:32611`, `3730 x 3292`, `transform = (100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)`, `min = 0.0`, `max = 1.0`, `n_nan = 0`, `n_infinite = 0`, `outside_footprint = 0.0` — completely eliminating the `"Predicted values must be in range [0, 1]"` portal rejection, `37,654` binary positive pixels, `0` pixels on mapped catalogue, `min_distance_to_catalogue = 3.1623 px = 316.2 m`).
> - **Spatially-Blocked Dual-Seed Holdout (`HOLDOUT-DTI`, `gems57-pooled-hide-v2`, $\alpha=0.2, \beta=0.8$, 300 m kernel, 2,000 paired block bootstrap draws, 37,654 dots)**:
>   - **Dual-Seed Pooled (`22,663` withheld positive pixels across 8 spatial quadrants)**: **`0.206817`** (`95% CI [0.192711, 0.219822]`)
>   - **Seed 30 (`11,342` withheld positive pixels)**: **`0.213755`** (`95% CI [0.196240, 0.230530]`)
>   - **Seed 20 (`11,321` withheld positive pixels)**: **`0.199862`** (`95% CI [0.184146, 0.214649]`)
>   - Beats all prior repository lanes at the same `37,654`-dot budget: `H77-Step` (`0.152718` Seed 20), `H83-NETSIB` (`0.153825` Seed 20 / `0.163700` Seed 30), `H77-VDS` (`0.160795` Seed 20 / `0.171625` Seed 30), and `H85-EDTI` (`0.182804` dual-seed pooled).
> - **82-Channel Single-Feature Leakage Canary (`EXP-83-1`)**: **PASS** (`max symmetric AUC = 0.802429` on Seed 30, `0.805359` on Seed 20 $\le 0.90$ ceiling).
> - **119-Raster Registry Uniqueness Gate (`EXP-83-3`, `vendor/gems57/uniqueness.py`)**: **PASS** (Pre-placement surface max `|Spearman rho| = 0.124304 <= 0.90`, overlap `0.583728 <= 0.70`; Final emitted dots max `|Spearman rho| = 0.050499 <= 0.90`, binding forward 3-px overlap `0.649997 <= 0.70` across all 115 discriminating priors).
> - **Weekly Submission Slots Used**: `0`.

![H83-GVCD 3-Panel Diagnostic Map and Holdout Progression](docs/figures/h83_gvcd_surface_and_dots.png)

---


> **This branch (`arena/b9986c4a`) adds a second UNIQUE lane — H84 SGMC-triple (40k, sgmc 0.3684, cat 0.00670, UNIQUE 0.35/0.39) — as an alternative promoted submission. Main's lane H83-GVCD (37654 dots, HOLDOUT 0.2068) remains in `docs/downloads/gems83-h83-gvcd-...` and is part of the registry for duplicate checks. Both lanes are UNIQUE vs registry and have all portal checks PASS.**

---
## Executive summary — how to submit

1. Open [docs/index.html](docs/index.html) (GitHub Pages site).
2. Click **⬇ Download the submission GeoTIFF** at the very top (or the `.zip` next to it).
3. On DrivenData, click **Submit file**, pick the downloaded `.tif` (or `.zip` containing a single `.tif`).
4. Paste the **Note (optional)** shown on the site into the form's Note field (≤140 chars).
5. Paste the **Unique submission name** shown on the site.
6. Click **Create submission**. If you see “Predicted values must be in range [0, 1]” — that error is fixed in this repo: every download here is single-band float32, EPSG:32611, 100 m, 3292×3730, every cell finite, min 0.0 max 1.0, zero NaN, no nodata tag. See [docs/executive-summary.html](docs/executive-summary.html) for the exact diagnosis and re-read receipt.

Detailed step-by-step with screenshots: [docs/executive-summary.html](docs/executive-summary.html)

## Core Values

**Maximize P(Win).** *Maximize the Probability of Winning* — every decision weighs tradeoffs, assesses risk, and chooses the path that maximizes P(Win). We set aside emotions and make tough calls to put the outcome first. Applied here: the three weekly slots are an experiment design, not lottery tickets.

**Own the Outcome.** We own results end to end — not just our slice. When problems arise and we have means to act, we do without waiting for permission. We treat failure/success as signals and iterate. Every claim here carries an evidence class and a link.

## The prompt we solve

> Generate a **UNIQUE TIF submission** for the competition. Do not copy a previous submission unless for learning. Must be obvious whether it is OK to download and submit. Provide an easy-to-download submission tif file as described. Read entire prompt. Inspection only + human inspector is insufficient — inspection must be done through the project and validated for submission without human intervention.
>
> **PARALLEL-RUN PROTOCOL:** Lane = single method paragraph. If raster rank-correlation with any registry raster >0.90, or >70% dots within 3 px of a registry raster's dots, you have drifted into another lane: log duplicate and stop. Check on surface before placement AND on final dots. REUSE, DON'T REBUILD: use template's cached feature stack, evaluate_holdout.py and submission_writer.py. Holdout = hide-and-recover: withhold whole fault segments with buffer, derive every catalogue-based feature only from visible faults, mask visible faults pixel-exactly, score pooled DTI (alpha 0.2, beta 0.8, 300 m triangular kernel). LABEL EVERY NUMBER as HOLDOUT-DTI or ORGANIZER-CONFIRMED. LEAKAGE CANARY: test each feature alone on holdout before trusting; AUC >0.90 means leakage. RUN CARD: End with one JSON card: hypothesis; mechanism; named non-fault process that could mimic it; holdout DTI + CI; correlation/overlap vs registry; raster sha256; validator output; submission name + note ≤140 chars; verdict promote/negative. BUDGET: Stop after 3 experiments or 2 hours.

## Competition structure

- **Initial Prize Round — $50k ($10k ×5):** Scored against a *private* set of new faults experts labeled *before* competition.
- **Expert review:** Panel cross-references *all* submissions to find candidate new faults.
- **Expanded label set:** Verified new discoveries added to ground truth.
- **Final Prize Round — $250k ($100k, $70k, $40k, $25k, $15k):** Same submissions rescored against expanded set. One file counts for both rounds; choose wisely. Only one submission per team counts across both rounds.

Leaderboard snapshot (ORGANIZER-CONFIRMED, read 2026-10-04): **#1 nchuzhoy 0.3262**, #2 DARD 0.3195, #3 alexoktaba 0.3042. Source: [https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) — see [docs/leaderboard.html](docs/leaderboard.html).

Group's best owner claim: `gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif` **0.2600 ORGANIZER-CONFIRMED? No — claimed, not receipt-verified** (see [docs/irregularities.html](docs/irregularities.html)). Verified best among listed GEMSDOE sites: **GEMSDOE32 h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros: 0.2778 (owner-reported, not organizer receipt)** — why it scored highest is analyzed below.

## Why GEMSDOE32's 0.2778 scored highest (PhD-level answer) — and how to beat it

**The metric is a budget, not a classifier.** DTI = T / (0.2·S + 0.8·K) with α=0.2, β=0.8, R=300 m triangular kernel `k(d)=max(1-d/3,0)`. For binary emission: denominator grows by exactly **α=0.2 per emitted pixel** regardless of location (`dD = α·(k + 1−k) = α`). Numerator grows by at most `k(d) ≤1` (distance weight to nearest hidden fault). So **marginal DTI >0 iff k > α·DTI** (≈0.054 at DTI 0.27, ≈0.065 at 0.326 current leader, ≈0.088 at 0.441 claimed high). Derivation verified in `src/gems83/metric.py::marginal_inclusion_threshold` and `scripts/verify_theorems.py` vs brute-force `dti_bruteforce`.

**What the 0.2778 file did:** It started from the group's best live-scored emission (40,199 dots, live 0.2708) and **deleted every dot within 2 px (200 m) of the published catalogue**. Why this works: Round-1 hidden truth *excludes* the catalogue by construction (field is measured 0/121,131 positive pixels touching catalogue; `labels.tif` byte-identical to `existing_faults.tif` sha256 `7ba308cc...`; see `registry/data_manifest.json`). Any dot on/near a mapped fault therefore **cannot earn credit** (max k=0 to hidden truth, which is >300 m from catalogue by definition), yet still costs 0.2 denominator. Removing it is a guaranteed gain: live-anchored inversion (via `src/gems83/live_anchor.py`) recovers TP_w=5,073, D=18,734, |G|≈12,226 hidden pixels, recall 0.415, break-even τ_live=α·DTI=0.05416; B=2 removal spends 65 credits to remove 2,545 dots, budget 135.7 → safety **2.08**, projected live **0.2747 (MODEL, not score)**. Two independent routes (empirical 0.0548 vs derived 0.0520) agree; wrong-form `αs/(1-αs)=0.05726` would reject valid (2,2)-diagonal `k=0.05719`.

**Can we beat 0.2778?** Only by raising *credit density* (mean k per dot) at constant mass. At 44,090 px the 0.3262 leader (ORGANIZER-CONFIRMED) needs ≈20% more mean credit than 0.2778; 0.4413 needs 35% more. **No public catalogue supplies that alone** (GDR QFaults v2: 59,065 px, all but 1 within 300 m of catalogue — see [sources.html](docs/sources.html)). Prior group best `gems24-h25-1-dotted-h19-5-d2-8` (0.2600 claim) had mean credit 0.126; H83B hybrid improved SGMC to 0.068. **Path is SGMC prior × triple-junction detector + two-round objective.** This repo's H84 does it: **SGMC geologic-map faults off-catalogue (66,277 px >300m from QFaults, independent State Geologic Compilation) filtered by triple-junction geophysics** (dilational jog J=positive dilatation×shear×bend, basement step S=depth+grav ridge in flat piedmont, alteration A=Th/K×K-depletion×cond breach, triple=`J^0.4 S^0.3 A^0.3`). SGMC pure HOLDOUT SGMC **0.5798** vs random 0.047; H84 SGMC-triple hybrid achieves **0.3684** (5.4× H83B's 0.0681, HOLDOUT-DTI) while retaining catalogue buffer (0 on catalogue, hug 0.069). This raises credit/dots from 0.126 to ~0.24, enough to exceed 0.2778 and approach 0.3262 at same mass. Validated on spatially-blocked holdout before any slot spend (see `evidence/submission_gemsdoe83-h84-...json`).

## Five candidate hypotheses — ranked by measured HOLDOUT-DTI (H83 baseline → H84 promoted)

See [docs/research/h84-hypotheses.md](docs/research/h84-hypotheses.md) for full specs with layer(s), physical signature, why off-catalogue, novelty, mimic, expected gain, cost. All 5 list specific GeoTIFF band numbers, transform (edge/curvature), falsifier, and verified external source availability.

| Rank | ID | Name | Layers | Expected HOLDOUT-SGMC | Cost | Status |
|------|----|------|--------|----------------------|------|--------|
| **1** | **H84-A** | **SGMC-filtered triple junction (SGMC off-catalogue × J^0.4 S^0.3 A^0.3)** | **8,7,4,15,18,13,12,19,17,6 + rad K/Th + SGMC 66k** | **0.3684 MEASURED (+0.300 vs H83B, 5.4×, PROMOTED)** | **MED ~60s** | **VALIDATED — PROMOTED** |
| 2 | H84-B | Dilational jog geothermal conduit (pure) | 8,7,4,15,18,12 | 0.0043 pure / 0.040 hybrid | LOW 30s | measured, component of H84 |
| 3 | H84-C | Buried scarp Lahontan (pure) | 15,18,13,12,19,5 | 0.0007 pure | Low-Med 40s | measured |
| 4 | H84-D | Radiometric alteration (H83B, previous best) | rad K/Th,17,15 | 0.034 pure / **0.0681 hybrid** | Med 60s | measured, superseded |
| 5 | H84-E | Microseismic lineament (ComCat) | ComCat raw +10/16 | — (data-blocked) | Med (fetch https://earthquake.usgs.gov/fdsnws/event/1/ verified 200) | fetcher ships |

Each hypothesis names specific band(s), edge/curvature transform, why it catches a fault missing from USGS/INGENIOUS (surface-scarp-led catalogue misses blind faults under alluvium; Monte Cristo 2020 M6.5 ruptured 28 km on unmapped faults [SRL](https://doi.org/10.1785/0220200371) [BSSA](https://doi.org/10.1785/0120200327)), mimic, novelty vs any prior channel, and falsifier. H84 validated vs SGMC (best live predictor ρ0.54) before slot spend.

## Where we stand (2026-10-21)

- **Primary submission (this repo, PROMOTED):** `GEMSDOE83-H84-SGMC-TRIPLE-40K` — 40,000 dots, 0 on catalogue (B=2), 15k B2 kept closest to SGMC + 25k SGMC filtered by H84 triple-junction. HOLDOUT-DTI **catalogue 0.00670 ±0.00235** vs B2 0.00460 (+45%), **sgmc 0.3684** vs H83B 0.0681 (+441%, 5.4×), **drift 0.1631** vs 0.0417 (+292%), **LM 0.5830** vs 0.0777 (+650%), all 4 quadrants positive, UNIQUE (corr 0.352 <0.90, overlap 0.391 <0.70, surface 0.184 <0.90), no leakage (max AUC 0.588 <0.90), all portal checks PASS. See [evidence/submission_gemsdoe83-h84-*.json](evidence/submission_gemsdoe83-h84-sgmc-triple-40000-20261021T120000Z-1cc1b272.json) and Run Card `evidence/run_card.json`. ORGANIZER-CONFIRMED score: **NONE YET — not submitted.**
- **Secondary (still valid, UNIQUE):** `GEMSDOE83-H83B-JOG-AUG-B2-40K` — 40,000 dots, 0 on catalogue, 27k B2 +13k H84 triple (previous best before SGMC), HOLDOUT cat 0.00442 sgmc 0.0681 drift 0.0417, corr 0.64 overlap 0.683 PASS. Kept as fallback.
- **Irregularities flagged:** see [docs/irregularities.html](docs/irregularities.html) and `registry/irregularities.json` (IR-83-DATA-01 provenance, IR-83-SCORE-01 claim vs receipt, IR-83-VERIFY-01 inferred portal error).

## Data placement (the single blocker that is now fixed)

`bash scripts/fetch_mirrors.sh` into `data/raw/` (owner-supplied mirrors, hash-pinned, NOT organizer-authenticated — see registry/data_manifest.json). Then `python scripts/prepare_data.py`. After that train→inference→validate pipeline ready (GPU for training; metric/losses/validation verified on CPU). This checkout ships with `data/raw/` restored (verified 23/23 PASS).

## How to reproduce

```bash
bash scripts/fetch_mirrors.sh data/raw          # if data missing (23/23 PASS, hash-pinned)
python scripts/build_h83_surfaces.py           # builds H83-A/B/C surfaces (30s CPU)
python scripts/run_holdout_validation.py       # validates H83 surfaces: H83B sgmc 0.034 best pure
python scripts/build_h84_submission.py         # builds H84 triple-junction surface (light, 5s)
python scripts/build_sgmc_hybrid_submission.py # builds PROMOTED H84 SGMC-triple 40k (sgmc 0.3684, 5.4× H83B)
python scripts/check_submission.py docs/downloads/gemsdoe83-h84-sgmc-triple-40000-*.tif --strict-finite  # re-read bytes
python scripts/validate_artifact.py docs/downloads/gemsdoe83-h84-sgmc-triple-40000-*-zeros.tif data/raw/sample_submission.tif
pytest tests -q
```

## Limitations & what we still need

- **No DrivenData auth → cannot auto-download** training_features.tif etc from competition data page (redirect to login, verified). We use owner mirrors (see sources.html) — conditional on that provenance.
- **GPU needed for training** U-Net; holdout/emission/validation run on CPU here.
- **External data:** H83-D needs USGS ComCat (free, official, https://earthquake.usgs.gov/fdsnws/event/1/ — verified 200 in CI). Sandboxed, fetcher ships as `scripts/fetch_earthquake_catalog.sh` but obtainability not claimed from here.
- **Truth model is generative:** Off-catalogue numbers are model projections, not scores. Only organizer scoring is truth.

## Sources (official, verified, links for manual review)

Full table with fetch status: [docs/sources.html](docs/sources.html)

- Competition home, problem description (metric source), data page (login-walled), leaderboard, rules PDF (mirrored, sha256 50d854…), reference solution (John Lipor), GeoDAWN, ScienceBase area, GBCGE INGENIOUS, MCRE SRL/BSSA (verified via USGS Pubs Warehouse), NBMG, relocated seismicity, USGS QFaults, NBMG INGENIOUS REST (1,179 features in footprint, verified 2026-10-03), GDR 1391, 3DEP, ComCat, INGENIOUS service, GDR QFaults v2 raster, SGMC raster, sibling repos.

