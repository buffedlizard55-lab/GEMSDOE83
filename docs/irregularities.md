# Data Sources, Limitations, and Discovered Irregularities (`GEMSDOE83` / `Lane H83-GVCD`)

## 1. Official Data Sources & SHA-256 Provenance

All 23 input files in `data/raw/` were restored and SHA-256-verified against `registry/data_manifest.json` (`data/restore_receipt.json`, `verified: 23/23`):

1. **DrivenData DOE GEMS Competition Bundle** ([Competition #306](https://www.drivendata.org/competitions/306/competition-doe-gems/), [Problem Description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)):
   - `training_features.tif` (`4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5`, `935,768,539` bytes): 19-band `float32` stack on `EPSG:32611` (`3730 x 3292`, 100 m pixel size, transform `(100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)`).
   - `existing_faults.tif` (`d9eb4fb5ad5fbbe6dfdc8f5fe4ade2be16ba3e8f669fd2d0dc7f1de406f863d1`, `200,829` bytes): Published USGS/INGENIOUS fault catalogue (`60,988` positive cells inside the `5,167,373`-cell valid footprint).
   - `sample_submission.tif` (`c8f3b2bd02bed83ba3fb2fa2cdcef61fa04ab0ac419ebffae1bd3fd3eb3a7a69`, `9,108,828` bytes): Reference submission template (`float32`, `0.0` inside footprint, `NaN` outside footprint).
2. **DOE Geothermal Data Repository (GDR) Submission #1391 — INGENIOUS Great Basin Geothermal Play Fairway** ([https://gdr.openei.org/submissions/1391](https://gdr.openei.org/submissions/1391)):
   - `external/gdr_wellspring_in_footprint.csv` (`e4ed0a6195fd70fd25d497f79a3ab0576bf690d4bc112b385a3a9cf9b86c5718`, `27,092` in-footprint wells and thermal springs; `7,170` with $T > 20^\circ\text{C}$, `3,944` with $T > 35^\circ\text{C}$, max $296.5^\circ\text{C}$; `740` quartz geothermometer $>80^\circ\text{C}$, `567` chalcedony $>60^\circ\text{C}$, `499` Na-K-Ca cation $>80^\circ\text{C}$).
   - `external/gdr_volcanic_vents_in_footprint.csv` (`7b2d18e89e4b304f4d87d39df22cf8df376f2a6277e4ebcb8f5961775a8e5cd7`, `21` Quaternary volcanic vents).
3. **USGS GeoDAWN Airborne Radiometric & Magnetic Survey** ([https://doi.org/10.5066/P93LGLVQ](https://doi.org/10.5066/P93LGLVQ)):
   - `external/geodawn_rad_u8.tif` (`c22420f75999030d7cc65c9e31e50d232ea6158423bca051613a18a8b20ba682`): 4 bands (`K`, `Th`, `U`, `TC`).
   - `external/geodawn_extensions_u8.tif` (`a35a9c6d2a14786f4dab85481ee59769213072f5dab5b2535ea82ae4d9bb7d9b`): 4 bands (`Th/K`, `U/K`, `U/Th`, `TMI_up150`).
4. **USGS 3DEP 1 m Digital Elevation Model Breakline / Scarp Stack** ([https://www.usgs.gov/3d-elevation-program](https://www.usgs.gov/3d-elevation-program)):
   - `external/lidar_scarp_features_u8.tif` (`d580bb8bdcdb941e32fefb8b38044bc5bf04e199bf2e83498c31576e6fc465568`): 12 directional scarp step, Laplacian, relief, coherence, strike, and tile-validity bands.

---

## 2. Dataset Limitations & Required Preprocessing Safeguards

1. **Extreme Negative Float32 Sentinel Values (`-3.4028235e+38`) Inside `training_features.tif`**:
   - Bands 1–19 of `training_features.tif` contain `-3.4028235e+38` (`-FLT_MAX`) sentinel values both outside the footprint and on edge cells inside the footprint. Any unguarded spatial convolution or gradient filter propagates `-3.4e38` across neighboring pixels. `src/gems83/features.py` masks `~np.isfinite(arr) | (np.abs(arr) > 1e20)` and imputes the in-footprint median before computing spatial derivatives.
2. **Band 6 (`tilt_angle_total_curvature`) Units**:
   - Band 6 of `training_features.tif` is stored in **radians in $[0, \pi/2] \approx [0, 1.5707963]$**, not degrees. Robust median/MAD standardization in `src/gems83/features.py` is scale-invariant.
3. **Leaky Column `dist_known_fault_px` in `gdr_wellspring_in_footprint.csv`**:
   - The CSV `external/gdr_wellspring_in_footprint.csv` contains a precomputed column `dist_known_fault_px` (distance to the full `existing_faults.tif` catalogue, which includes withheld holdout faults!). `src/gems83/features.py` **never reads `dist_known_fault_px`**; it reads only `utm_e`, `utm_n`, `temp_c`, `gt_quartz_c`, `gt_chalcedony_c`, and `gt_na_k_ca_c`.
4. **Partial Spatial Coverage of 1 m 3DEP LiDAR Tiles (`lidar_valid`)**:
   - 1 m 3DEP LiDAR tiles cover ~64% of the Great Basin footprint (heavier in NW/SW than NE/SE). To prevent missing LiDAR tiles from biasing cross-quadrant probability tails, `src/gems83/dinkelbach_emitter.py` applies quadrant-specific Bayes prior-shift calibration (`bayes_prior_calibrate(..., quadrant_calibrate=True)`).
5. **Outside-Footprint `NaN` vs `0.0` Portal Range Error (`"Predicted values must be in range [0, 1]"`)**:
   - While `sample_submission.tif` has `NaN` outside the valid footprint, the DrivenData submission portal's range validator checks `0 <= x <= 1` on raster arrays where `NaN` comparisons evaluate to `False`, triggering `"Predicted values must be in range [0, 1]"` on `NaN`-outside files. `vendor/gems57/submission_writer.py` writes `0.0` outside the footprint (`nodata = None`, `n_nan = 0`, `min = 0.0`, `max = 1.0`).

---

## 3. Code-Verified Irregularities in Prior Lanes & How `GEMSDOE83` Fixes Them

| ID | Affected Prior Lane / File | Exact Code-Verified Irregularity | Impact on Reported Metrics | Resolution in `GEMSDOE83` (`Lane H83-GVCD`) |
| :--- | :--- | :--- | :--- | :--- |
| **`IR-83-01`** | `GEMSDOE77` `scripts/h85_edti_pipeline.py` (line 138) | `stage_sweep` called `train_surface(X, f["region"], f["visible"], dv, seed=...)`, passing the **test quadrant `f["region"]`** as the training mask instead of out-of-fold quadrants `foot & ~f["region"]`. | Trained the `HistGradientBoostingClassifier` inside the evaluated test quadrant (using `visible` vs `~visible` in that same quadrant). | `scripts/run_h83_gvcd_pipeline.py` trains strictly Leave-One-Quadrant-Out (`tr_reg` = union of the 3 non-test quadrants `j != k`), with 0 test-quadrant pixels in training. |
| **`IR-83-02`** | `GEMSDOE77` `scripts/h85_edti_pipeline.py` (line 161) | `stage_ablation` computed `dist_cat = ndi.distance_transform_edt(~grid.catalogue)` on the **full** catalogue (including withheld `hidden` truth) and passed it to `train_surface` to filter negative training samples (`dist > 3.5`). | Excluded hidden test fault collars from negative sampling during Stage-2 training. | `scripts/run_h83_gvcd_pipeline.py` computes negative exclusion strictly from `(cat & tr_reg) \| visible`, never touching `hidden` in test quadrant `k`. |
| **`IR-83-03`** | `GEMSDOE77` `scripts/h85_edti_pipeline.py` (line 214) | `stage_build` computed `n_emit = int(round(3.3 * int(cat.sum()))) = 201,260` dots on the full grid (`3.3 * 60,988`), emitting **5.34x** the optimal `37,654` budget because `3.3` was calibrated on `~11,330` fold-hidden positives ($3.3 \times 11,330 \approx 37,390$), not on all `60,988` full-catalogue pixels. | Produced an over-emitted `201,260`-dot file whose 3-px halo covers `55.37%` of the entire footprint. | `scripts/run_h83_gvcd_pipeline.py` emits the exact `37,654`-dot budget in both holdout evaluation (`EXP-83-2`) and production build (`EXP-83-3`). |
| **`IR-83-04` (`IR-H85-01`)** | `vendor/gems57/uniqueness.py` & `data/raw/scored/` | Out of `119` registry rasters in `data/raw/scored/`, `4` files (`13gems_20261001_r13-lattice-s5_v2_nan-outside.tif` — a uniform 5-px whole-grid lattice — and 3 continuous `-RESEARCH-ONLY` / `-research` probability surfaces with $1.88\text{M}$–$5.01\text{M}$ positive cells) have 3-px halos covering **`98.04%` to `99.87%` of the entire footprint**, making literal $>0$ support overlap $\ge 0.98$ for *any* nonempty submission (including uniform random dots). | Under an unfiltered literal $>0$ reading on continuous surfaces, no candidate can ever pass $\le 0.70$. | `vendor/gems57/uniqueness.py` (`binding_duplicate_decision`, `IR-H85-01`) classifies priors by `halo_coverage < 0.70` (`115` discriminating priors vs `4` space-filling priors) and reports **both** the binding like-for-like reading (`duplicate = False`, max overlap `0.6500 <= 0.70` across all 115 discriminating priors, max `|Spearman rho| = 0.0505 <= 0.90` across all 119 priors) and the literal all-119 table side by side in `evidence/h83_uniqueness.json`. |
