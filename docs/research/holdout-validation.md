# Holdout validation — H83-B top candidate

**Evaluator:** `src/gems83/holdout.py` v2026-10-04, 4 quadrants ×2 draws =8 cells, collar 15 px (1.5 km), domain erosion 12 px (1.2 km), hide 20% of fault segments, derive features only from visible faults, mask visible faults pixel-exactly, pool DTI α0.2 β0.8 R300m.

**Leakage canary:** Solo two-sided AUC per quadrant for H83-B surface: NW 0.6058, NE 0.588, SW 0.545, SE 0.588 → mean 0.588, max 0.6058 (<0.90 PASS, no leakage).

**Results at matched mass 40000 px, 0 on catalogue, buffer 2 px:**

| Candidate | catalogue_hidden_mean | sgmc_prevalence_calibrated_dti | drift_corrected_holdout_mean | LM off-catalogue |
|-----------|----------------------|--------------------------------|------------------------------|------------------|
| B2 baseline 37654 (0.2778 claim) | 0.00460 HOLDOUT-DTI | 0.06412 | 0.04504 | 0.07404 |
| H83-B+2500 (40154, 93% overlap duplicate) | 0.00461 | **0.06646** | 0.04532 | 0.07834 |
| **GEMSDOE83-H83B-JOG-AUG-B2-40K 40000 (UNIQUE, 0.683 overlap)** | 0.00442 | **0.06811** (+0.0040 vs B2) | 0.04166 | **0.07771** |
| Random 40000 | 0.03211 | 0.04718 | 0.06962 | — |
| Pure H83-B 40000 | 0.00222 | 0.03414 | 0.01475 | 0.05002 |

**Verdict:** H83-B augmented beats B2 on SGMC (best live predictor ρ0.54) and LM, but slightly below on catalogue_hidden (0.00442 vs 0.00460, Δ -0.00018 within 95% CI ±0.00102, not significant). Promotion to slot requires SGMC instrument trust; otherwise negative result (deliverable).

See `evidence/holdout_run_h83a.json` and `evidence/submission_*.json`.
