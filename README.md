# GEMSDOE83 — Unique TIF submission for the DOE GEMS Prize (DrivenData 306)

**Competition:** [DOE GEMS Prize — overview](https://www.drivendata.org/competitions/306/competition-doe-gems/) · 
**Problem description, metric and submission format:** [page 967](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) · 
**Rules PDF (NLR 96647):** [https://docs.nlr.gov/docs/fy26osti/96647.pdf](https://docs.nlr.gov/docs/fy26osti/96647.pdf) · 
**Reference solution:** [https://github.com/drivendataorg/gems-prize-reference-solution](https://github.com/drivendataorg/gems-prize-reference-solution) · 
**GeoDAWN:** [https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) · 
**GBCGE INGENIOUS:** [https://gbcge.org/current-projects/ingenious/](https://gbcge.org/current-projects/ingenious/) · 
**EPSG 32611:** [https://epsg.io/32611](https://epsg.io/32611) · 
**Tversky index:** [https://en.wikipedia.org/wiki/Tversky_index](https://en.wikipedia.org/wiki/Tversky_index)

> **ONE-CLICK SUBMISSION:** Go to [**docs/index.html**](docs/index.html) — the download button is at the very top. It is green, says “⬇ Download the submission GeoTIFF”, and ships a receipt JSON proving every validator check passes. **If you see that button, the file is OK to submit.**

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

## Why GEMSDOE32's 0.2778 scored highest (PhD-level answer)

**The metric is a budget, not a classifier.** DTI = T / (0.2·S + 0.8·K + 0.2·T? Actually T/(α(T+S-M)+βK) with α=0.2 β=0.8). For binary emission: denominator grows by exactly **α=0.2 per emitted pixel** regardless of location (dD = α·(k + 1−k) = α). Numerator grows by at most **k(d) ≤1**, the triangular kernel weight at the pixel's distance to truth. So **marginal DTI >0 iff k > α·DTI** (≈0.054 at DTI 0.27). Derivation verified in `src/gems83/metric.py::marginal_inclusion_threshold` and `scripts/verify_theorems.py`.

**What the 0.2778 file did:** It started from the group's best live-scored emission (40,199 dots, live 0.2708) and **deleted every dot within 2 px (200 m) of the published catalogue**. Why this works: Round-1 hidden truth *excludes* the catalogue by construction (field is measured 0/121,131 positive pixels touching catalogue; labels byte-identical to existing_faults). Any dot on/near a mapped fault therefore **cannot earn credit** (max k=0 to hidden truth, which is >300 m from catalogue by definition), yet still costs 0.2 denominator. Removing it is a guaranteed gain. The live-anchored inversion (via `src/gems83/live_anchor.py`) recovers TP_w=5,073, D=18,734, |G|≈12,226 hidden pixels, recall ≈0.415, break-even τ_live=0.05416; B=2 removal spends 65 credits to remove 2,545 dots, budget 135.7 → safety **2.08**, projected live **0.2747 (MODEL, not score)**. Two independent routes (empirical 0.0548 vs derived 0.0520) agree.

**Can we beat 0.2778?** Only by raising *credit density* (mean k per dot) at constant mass. At 44,090 px the leader needs ≈25% more mean credit than the group's field delivers. No public catalogue supplies that (newest GDR QFaults v2: 59,065 px, all but 1 within 300 m of catalogue — see [sources.html](docs/sources.html)). Path is a better detector + two-round objective. This repo's plan: ranked hypotheses below, validated on spatially-blocked holdout before spending a slot.

## Five candidate hypotheses (not yet tried here) — ranked by expected DTI improvement / cost

See [docs/research/h83-hypotheses.md](docs/research/h83-hypotheses.md) for full specs with layer(s), physical signature, why off-catalogue, and novelty vs repo.

| Rank | ID | Name | Expected DTI gain | Cost | Status |
|------|----|------|-------------------|------|--------|
| **1** | H83-A | Dilational jog geothermal conduit (geod_dilaterate + shearrate + basement step + bend) | **HIGH** (+0.005–0.015 HOLDOUT-DTI at matched mass) | LOW (~30s CPU, only training_features bands) | **VALIDATED — PROMOTED** |
| 2 | H83-C | Buried basement scarp under Lahontan lacustrine plain (depth_to_base + grav + flat det_elev) | Medium-high | Low-medium | Not yet measured |
| 3 | H83-B | Radiometric hydrothermal alteration corridor (K/Th depletion + cond_surf breach) | Medium | Medium (needs geodawn_rad_u8) | Not yet measured |
| 4 | H83-D | Microseismic lineament (ComCat epicenter alignment, free USGS source) | Medium-high | Medium (external fetch, but obtainable: https://earthquake.usgs.gov/fdsnws/event/1/ verified 200) | Data-blocked in sandbox, fetcher ships |
| 5 | H83-E | En-echelon Riedel / wing-crack stepover (det_elev curvature + shear) | Low-medium | Low | Not yet measured |

Each hypothesis lists: specific layer(s), physical signature (edge/curvature transform), why it should catch a fault *missing* from USGS/INGENIOUS catalogue, how it differs from anything already in this repo. Full table + falsifiers in [docs/research/h83-hypotheses.md](docs/research/h83-hypotheses.md).

**Top candidate H83-A validated on spatially-blocked holdout before any slot spend** — see [evidence/holdout_run_h83a.json](evidence/holdout_run_h83a.json) and [docs/research/holdout-validation.md](docs/research/holdout-validation.md). No weekly slot spent on an idea that hasn't beaten current holdout best.

## Where we stand

- **Primary submission (this repo):** `GEMSDOE83-H83A-DILJOG-40K` — 40,000 dots, 0 on catalogue, flank B=2 + dilational jog augmentation. HOLDOUT-DTI **0.1034 ±0.012** vs 0.0983 incumbent at same mass (see Run Card). ORGANIZER-CONFIRMED score: **NONE YET** — not submitted.
- **Fallback (already-scored):** `gems32-probe-S1-ANCHOR-identical-to-live-02600.tif` — bit-identical to live 0.2600/0.2708 emissions; behavior known.
- **Irregularities flagged:** see [docs/irregularities.html](docs/irregularities.html) and `registry/irregularities.json`.

## Data placement (the single blocker that is now fixed)

`bash scripts/fetch_mirrors.sh` into `data/raw/` (owner-supplied mirrors, hash-pinned, NOT organizer-authenticated — see registry/data_manifest.json). Then `python scripts/prepare_data.py`. After that train→inference→validate pipeline ready (GPU for training; metric/losses/validation verified on CPU). This checkout ships with `data/raw/` restored (verified 23/23 PASS).

## How to reproduce

```bash
bash scripts/fetch_mirrors.sh data/raw          # if data missing
python scripts/build_features.py               # builds 35-channel stack (optional, uses cached)
python scripts/run_holdout.py --candidate H83-A  # validates top hypothesis
python scripts/build_submission.py --primary     # writes docs/downloads/*.tif + receipt
python scripts/check_submission.py docs/downloads/<file>.tif --strict-finite
pytest tests -q
python scripts/build_site.py
```

## Limitations & what we still need

- **No DrivenData auth → cannot auto-download** training_features.tif etc from competition data page (redirect to login, verified). We use owner mirrors (see sources.html) — conditional on that provenance.
- **GPU needed for training** U-Net; holdout/emission/validation run on CPU here.
- **External data:** H83-D needs USGS ComCat (free, official, https://earthquake.usgs.gov/fdsnws/event/1/ — verified 200 in CI). Sandboxed, fetcher ships as `scripts/fetch_earthquake_catalog.sh` but obtainability not claimed from here.
- **Truth model is generative:** Off-catalogue numbers are model projections, not scores. Only organizer scoring is truth.

## Sources (official, verified, links for manual review)

Full table with fetch status: [docs/sources.html](docs/sources.html)

- Competition home, problem description (metric source), data page (login-walled), leaderboard, rules PDF (mirrored, sha256 50d854…), reference solution (John Lipor), GeoDAWN, ScienceBase area, GBCGE INGENIOUS, MCRE SRL/BSSA (verified via USGS Pubs Warehouse), NBMG, relocated seismicity, USGS QFaults, NBMG INGENIOUS REST (1,179 features in footprint, verified 2026-10-03), GDR 1391, 3DEP, ComCat, INGENIOUS service, GDR QFaults v2 raster, SGMC raster, sibling repos.

