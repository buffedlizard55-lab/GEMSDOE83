# GEMSDOE83 — Five candidate hypotheses for the 2026-10-21 session (ranked)

Rules applied: each names layer(s), physical signature/transform, why it should catch a fault
*missing* from the USGS/INGENIOUS catalogue, difference from this repo, mimic, cost, falsifier.
Top candidate validated on spatially-blocked pure hide-and-recover before any slot spend.
Budget: 1 of 3 experiments used (H83-F, negative). Numbers are HOLDOUT-DTI unless labelled.

## Rank 1 — H83-F: SGMC-relocation de-redundancy swap — TESTED, NEGATIVE
- **Layers:** derived SGMC faults 100 m uint8 (USGS SGMC-derived, manifest sha256 `643cbe99…`, re-fetched/hashed this session) + existing H83-B emission + catalogue distance.
- **Signature:** kernel-redundancy count (other dots in Euclid 3 px disk); SGMC 7×7 line-support. Keep 26k least-redundant, add 14k SGMC pixels >3 px from catalogue/kept, >2 px self-separated.
- **Why off-catalogue:** state geologic-map compilation (SGMC) carries map-unit-bounding faults absent from the Quaternary-fault catalogue, which requires Quaternary surface evidence.
- **Novelty vs repo:** prior SGMC use was pure emission (live ~0.05 claims) or holdout truth only; never a redundancy-budgeted relocation at matched mass.
- **Mimic:** SGMC inferred contacts / pre-Quaternary structures, compilation seams.
- **Cost:** LOW (24 s CPU measured). **Canary:** SGMC-support AUC 0.739 <0.90 PASS.
- **Result (HOLDOUT-DTI, pooled, 11,790 withheld positives):** H83-F 0.00321 vs H83-B 0.00384, Δ −0.00063 [−0.00104,−0.00036]. **Falsified; DO NOT SUBMIT.** Uniqueness passed (overlap 0.672/0.640 <0.70).

## Rank 2 — H83-G: Scatter-blurred re-centring (NOT RUN — needs belief surface)
- **Layers:** H83-B continuous surface `data/processed/h83-b_surface.tif` (not in checkout; rebuild needs 419 MB `training_features.tif` mirror, obtainable via `bash scripts/fetch_mirrors.sh` on GitHub egress — verified small-file path this session, large file not re-fetched).
- **Signature:** Gaussian blur σ≈1.85 px (group's inferred hidden-set scatter) + greedy max-coverage packing, catalogue pixels excluded.
- **Why off-catalogue:** hidden expert faults scatter around geophysical lineaments; centring on the raw ridge wastes kernel credit.
- **Novelty:** GEMSDOE32 truth-model reports +0.0247 for this family but no GEMSDOE83 surface implements blur-then-pack.
- **Mimic:** survey line-spacing artefacts blurred into false trends. **Cost:** MEDIUM. **Falsifier:** pure holdout Δ≤0 vs H83-B.

## Rank 3 — H83-C: Buried basement scarp under Lahontan plain (NOT RUN this session)
- **Layers:** bands 15 `depth_to_base_surf`, 18 `iso_grav_anom_hg`, 19 `det_elev_slope` (flat gate).
- **Signature:** coincident long-straight gradient ridges in basement depth + gravity where surface slope is in the lowest decile (lacustrine plain).
- **Why off-catalogue:** basement offset under lake clays yields no scarp for field mappers.
- **Novelty:** lacustrine-flatness gate unused in repo surfaces. **Mimic:** paleo-shoreline notches, terrace risers. **Cost:** LOW–MED. Prior pure-surface record in repo: below random on catalogue holdout — augmentation-only if retried.

## Rank 4 — H83-D: Microseismic lineament (DATA CHECKED, NOT RUN)
- **Layers:** raw USGS ANSS ComCat epicenters via FDSNWS — free official source `https://earthquake.usgs.gov/fdsnws/event/1/` (competition allows licensed external data, page 967). Sandbox bash egress cannot reach it (allowlist: GitHub/PyPI/npm only) — obtainable on an unrestricted machine, NOT claimed fetched here.
- **Signature:** 16-direction collinearity vote (5 km half-length) on epicentre density, gated to low relief.
- **Why off-catalogue:** seismogenic blind faults at 3–8 km need not rupture the surface.
- **Novelty:** repo bands 10/16 are smoothed fields (no lineament transform). **Mimic:** quarry blasts, induced seismicity, location error. **Cost:** MEDIUM.

## Rank 5 — H83-H: Cross-contact magnetic phase displacement (NOT RUN)
- **Layers:** RTP/TMI + isostatic gravity bands of `training_features.tif`.
- **Signature:** matched magnetic contact pair laterally offset across an independent gravity edge (phase correlation of opposite flanks), not co-located edge strength.
- **Why off-catalogue:** buried strike-slip offset of a magnetic unit has no scarp.
- **Novelty:** displaced-pair object vs repo's per-pixel ridges/votes. **Mimic:** intrusive geometry, survey stitching. **Cost:** HIGH. Ranked last on cost/identifiability.

**Selector rule:** no Rank 2–5 idea may spend a weekly slot until it beats H83-B on the pure
hide-and-recover instrument (`scripts/run_h83f_experiment.py` harness) with canary AUC ≤0.90
and registry overlap <0.70 / correlation <0.90.
