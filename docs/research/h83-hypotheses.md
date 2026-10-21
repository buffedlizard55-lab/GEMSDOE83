# H83 — Five candidate hypotheses, ranked by measured layer discrimination

**Status: [MODEL] + [MEASURED where noted]. Nothing here has been submitted; no slot requested by this document.** All figures from organiser's `training_features.tif` (19 bands, sha256 `4371c82e…`) and `labels.tif` (`7ba308cc…`), digest-verified against `registry/data_manifest.json`. Every band name quoted from GeoTIFF band descriptions.

For implementation cost: CPU seconds on 2-vCPU sandbox.

---

## How hypotheses were ranked

Two measurements drive ranking (reproducible via `scripts/run_holdout.py` and `scripts/band_auc.py`):

1. **Per-layer discrimination of held-out faults, spatially blocked** — two-sided AUC (fault vs background) inside 4 quadrants. From GEMSDOE32 round 3 (re-verified here):
   - tc (6) 0.5735 [0.539–0.610]
   - geod_shearrate (7) 0.5721
   - det_elev_slope (19) 0.5652
   - iso_grav_anom_slope (5) 0.5521
   - geod_2ndinv (4) 0.5488

2. **What line transforms buy:** curvature/zero-crossing helps `det_elev` +10.1% (0.5256→0.5786) and `depth_to_base_surf` +3.5%, but *hurts* tc, shearrate, 2ndinv. Rule: **transform only raw fields; don't re-differentiate derivatives.**

---

## H83-A — Dilational jog geothermal conduit (GEODETIC STRAIN + BASEMENT STEP) — RANK 1, PROMOTED

- **Layers:** Band 8 `geod_dilaterate` (volumetric expansion rate), Band 7 `geod_shearrate` (angular deformation), Band 4 `geod_2ndinv` (tensor magnitude), Band 15 `depth_to_base_surf` (sediment thickness), Band 18 `iso_grav_anom_hg` (gravity gradient), Band 12 `det_elev` (topo for bend detection).
- **Physical signature:** Normal-fault jog where extension opens a dilational quadrant: **positive dilatation (>0) + high shear + high 2nd invariant** co-located with a **basement step ridge** (|∇ depth_to_base| > percentile) and a **strike bend** (change in structure-tensor orientation >15° over 500 m). The composite is `dil_open × shear_norm × step_ridge × bend_vote`. Dilational jogs are the primary geothermal permeability structures in the Great Basin (Faulds et al. 2010, GBCGE structural framework; see [gbcge.org/current-projects/ingenious/](https://gbcge.org/current-projects/ingenious/)).
- **Why it catches a fault *missing from catalogue*:** USGS/INGENIOUS compilation is surface-expression-led (field mapping, LiDAR scarps). A jog/bend is <3 km long, often under alluvium, with **no continuous scarp** — mappers trace the main fault but omit the jog. Yet the jog is where fluids ascend (e.g., 2020 M6.5 Monte Cristo Range earthquake ruptured 28 km on *largely unmapped* Candelaria faults — [Koehler et al. 2021, SRL](https://doi.org/10.1785/0220200371); [Liu et al. 2021, BSSA](https://doi.org/10.1785/0120200327) — proving hidden faults exist exactly where strain is high).
- **How it differs from anything in repo:** `features.py` has raw band07/08/04 as values with no jog logic; `src/gems32/h33.py` used basement step *alone* (H33-D) and drainage chains, but never **dilatation polarity** (extension vs contraction) nor **bend detection**. H62 hypotheses used strain raw or tilt, not jog geometry. No prior channel computes *positive dilatation gated by shear + bend + step*.
- **Mimic (non-fault process):** Axial volcanic vent alignment or anthropogenic groundwater pumping-induced subsidence can produce extensional strain with no fault; also Lahontan lake loading/unloading creates dilatation signals.
- **Expected DTI gain:** HIGH (+0.005–0.015 HOLDOUT-DTI at matched 40k mass). Rationale: jogs host blind geothermal faults by definition, and current best file spends 57% mass off-belief surface (IR-32-SHIP-01) — replacing that mass with jog-targeted mass should raise credit/dots from 0.126 to ~0.15.
- **Implementation cost:** LOW (~30s CPU, only training_features bands, no external data).
- **Falsifier:** Build jog surface; if its blocked holdout AUC does not beat raw det_elev (0.5256) on ≥3/4 quadrants, FAIL.
- **Leakage canary:** Test jog surface alone — if AUC >0.90 → leakage, abort (measured: raw bands 0.54–0.57, far from leakage).

**VALIDATED:** Holdout DTI 0.1034 vs incumbent 0.0983 at 40k mass, +0.0051 in 4/4 quadrants (see evidence/holdout_run_h83a.json). Leakage canary: solo AUC 0.567, PASS.

---

## H83-C — Buried basement scarp under Lahontan lacustrine plain — RANK 2

- **Layers:** Band 15 `depth_to_base_surf`, Band 18 `iso_grav_anom_hg`, Band 13 `iso_grav_anom`, Band 12 `det_elev`, Band 19 `det_elev_slope` (flat = lake plain), Band 5 `iso_grav_anom_slope`.
- **Physical signature:** Long-straight **gradient ridge** in depth_to_base *and* iso_grav_anom_hg where det_elev_slope is *lowest decile* (lacustrine terrace, not a mountain front). Score = (|∇ depth| × |∇ grav|) × (1 − slope_norm) × straightness_vote (directional coherence of gradient over 3×3). Threshold: depth gradient >80th pct + lacustrine flatness gate.
- **Why off-catalogue:** NW Nevada is 60% Quaternary alluvium/lacustrine (Lake Lahontan, ~12.7 ka highstand). A normal fault offsetting basement under 100 m of lake clays produces **no topo scarp**, so field mappers miss it, but the basement step remains in depth_to_base and grav. Proven: GEMSDOE30's GDR QFaults v2 adds 59k px but all but 1 within 300 m of catalogue — meaning next faults are *under cover*, not along scarps.
- **Novelty:** H62-2 proposed basement step + grav gated by *general* absence of surface expression; this hypothesis gates specifically on **lacustrine flatness** (det_elev_slope decile), a narrower, testable geomorphic unit. No prior surface used lake-plain detection.
- **Mimic:** Paleo-shoreline erosional notches, fluvial terrace risers, or anthropogenic grading (e.g., Fallon farmland) can mimic a step without a fault.
- **Expected DTI:** Medium-high (+0.003–0.010).
- **Cost:** Low-medium (~40s CPU).
- **Falsifier:** If lacustrine-gated step does not beat raw depth_to_base_surf AUC (0.5246) in 3/4 quadrants, FAIL.

---

## H83-B — Radiometric hydrothermal alteration corridor — RANK 3

- **Layers:** `geodawn_rad_u8.tif` bands 1–4 (K, Th, U, TC counts, from GeoDAWN DOI 10.5066/P93LGLVQ), Band 17 `cond_surf`, Band 15 `depth_to_base_surf`, plus `gdr_wellspring_in_footprint.csv` well temps (GDR 1391 DOI 10.15121/1881483, CC BY 4.0).
- **Physical signature:** **K depletion + Th/K high + conductivity low** along a lineament: hydrothermal alteration bleaches K (K <20th pct) while Th/K >80th pct, coincident with a conductive clay-cap breach (cond_surf gradient ridge + conductivity low inside). Corroborated where spring temps >30°C align along structure (GDR wellsprings 2,146 pts inside footprint). Score = alteration_index × clay_breach × spring_proximity.
- **Why off-catalogue:** Blind geothermal faults lack scarp but have **alteration halos** (silicification, K-metasomatism loss) detectable in radiometrics; catalogue faults are mapped by geomorphology, not geochemistry. Geothermal vents cluster on altered corridors, not on every mapped fault (Great Basin geothermal favorability models, INGENIOUS 2023).
- **Novelty:** H33-A fused radiometrics as *one of six physics* with orientation consensus, but never computed **alteration ratios** (Th/K, U/K) nor gated on **K depletion**; H32-C used MT clay-cap breach alone without radiometric corroboration. No prior channel used U/Th ratio grids (`geodawn_extensions_u8.tif` bands Th/K, U/K, U/Th).
- **Mimic:** Lithologic contacts (e.g., felsic tuff vs basalt) produce K/Th steps with no fault; agricultural fertilizer K enrichment masks depletion.
- **Expected DTI:** Medium (+0.002–0.008).
- **Cost:** Medium (~60s CPU + 26 MB radiometric grids).
- **Falsifier:** If alteration corridor AUC <0.55 (barely better than chance) in blocked quadrants, FAIL.

---

## H83-D — Microseismic lineament (ComCat epicenter alignment) — RANK 4, DATA-BLOCKED IN SANDBOX

- **Layers:** Band 10 `deq_n100a15` (distance to earthquake), Band 16 `ieq_n100a15` (earthquake density, autocorrelation 0.9986 useless), but **replaced with raw USGS ComCat epicenters** (free, official: [https://earthquake.usgs.gov/fdsnws/event/1/](https://earthquake.usgs.gov/fdsnws/event/1/) — verified HTTP 200 in CI, see sources.html). Transform: epicenter kernel density → 16-direction collinearity vote (halflen 5 km = 50 px) → lineament strength. Gated by low detrended-elevation relief (blind fault, not range front).
- **Physical signature:** **Alignments of M1.5+ epicenters** over 2010–2024 along a 5–15 km trend; b-value low anomaly along trend (stress concentration). Blind faults creep/seismically slip under cover, producing lineaments invisible at surface but visible in relocated catalogs (Ruhl et al. Monte Cristo relocations [Zenodo 5302368](https://zenodo.org/records/5302368) show lineaments along unmapped 2020 ruptures).
- **Why off-catalogue:** Seismogenic faults at depth (3–8 km) may not propagate to surface; they appear as seismicity lineaments, not scarps. Catalogue is Quaternary surface rupture compilation — it systematically lacks seismogenic blind faults.
- **Novelty:** No prior hypothesis used *raw seismicity* correctly; repo's bands 10/16 are smoothed fields with no fault-scale information (measured autocorrelation 0.9986 at 1 km, 0.9935 at 3 km). Proposed raw catalog fetch is novel and needed (named source required).
- **Mimic:** Quarry blasts, induced seismicity from geothermal plants (e.g., Dixie Valley), or poorly located epicenters (rms >1 km) align artifactually.
- **Expected DTI:** Medium-high (+0.004–0.012) if seismicity is correlative, but noisy.
- **Cost:** Medium (requires free external fetch; sandbox egress to earthquake.usgs.gov returns HTTP 000 in prior sessions — **obtainability NOT claimed here**, fetcher ships as `scripts/fetch_earthquake_catalog.sh` for unrestricted machine).
- **Falsifier:** If seismic lineament density AUC <0.53 in blocked holdout, FAIL.
- **External source needed:** USGS ANSS ComCat via FDSNWS — free, official, no auth. Check: `curl -I https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime=2020-01-01` returns 200 from GitHub Actions runner (see evidence/probe_comcat.json). From this sandbox, HTTP 000 — so data not reachable here, script provided.

---

## H83-E — En-echelon Riedel / wing-crack stepover — RANK 5

- **Layers:** Band 12 `det_elev` (curvature), Band 19 `det_elev_slope`, Band 7 `geod_shearrate`, Band 14 `tmi` (for basement fabric orientation).
- **Physical signature:** **En-echelon tension gashes** (Riedel R-shears) at ~15° to main fault, plus **wing-crack tips** at fault terminations: small (300–800 m) curvilinear ridges/scarplets in det_elev curvature that form in stepovers. Detected via Hessian ridge at σ=1.0–2.0 px + structure-tensor orientation + shear alignment: ridge strength × shear_high × R-orientation_vote (15° to regional strike from TMI fabric).
- **Why off-catalogue:** Main fault cataloged, but stepover internal fractures are an order of magnitude shorter and below typical mapping resolution; yet they host geothermal upwelling (stepovers are known blind geothermal targets, e.g., Brady's, Desert Peak).
- **Novelty:** GEMSDOE20 H20 used power-law wing-crack scoring but with *power-law tilting* and thermal-pop, not Riedel geometry + shear gating; H33-C used LiDAR scarplet chains but not Riedel orientation rule. No prior channel enforced **15° Riedel orientation** constraint.
- **Mimic:** Eolian dunes, fluvial braid bars, or anthropogenic linear features (roads/canals) produce en-echelon patterns.
- **Expected DTI:** Low-medium (+0.001–0.005) — short features pay high FP per TP due to many isolated dots.
- **Cost:** Low (~25s CPU).
- **Falsifier:** If Riedel surface's top-40k dots have <2× overlap with SGMC off-catalogue faults vs random (i.e., no enrichment), FAIL.

---

## Summary ranking table

| Rank | ID | Name | Layers | Signature | Expected HOLDOUT-DTI gain | Cost |
|------|----|------|--------|-----------|---------------------------|------|
| 1 | H83-A | Dilational jog | 8,7,4,15,18,12 | positive dilatation × shear × basement step × bend | HIGH +0.005–0.015 | LOW 30s |
| 2 | H83-C | Buried scarp under Lahontan | 15,18,13,12,19,5 | depth+grav step where topo flat | Med-High +0.003–0.010 | Low-Med 40s |
| 3 | H83-B | Radiometric alteration | rad K/Th/U, 17,15 + wellsprings | K dep × Th/K high × clay breach | Med +0.002–0.008 | Med 60s |
| 4 | H83-D | Microseismic lineament | ComCat raw +10/16 | epicenter collinearity | Med-High +0.004–0.012 | Med (fetch) |
| 5 | H83-E | Riedel wing-crack | 12,19,7,14 | ridge × shear ×15° vote | Low-Med +0.001–0.005 | Low 25s |

Only **H83-A** validated in this session (budget 3 experiments/2h). Others are specified for next session.

