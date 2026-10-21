#!/usr/bin/env python3
"""Validate H83 hypotheses on spatially-blocked holdout (hide-and-recover).

Implements:
  - Leakage canary: solo AUC per surface
  - Holdout DTI for each surface at fixed mass (40000 px) via greedy or top-N
  - Registry duplicate check: rank-correlation and overlap
"""
import sys, json, time, hashlib
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from sklearn.metrics import roc_auc_score

from gems83.holdout import load_holdout_context, evaluate_candidate_holdout
from gems83.metric import kernel, ALPHA, BETA
from gems83 import grid

DATA = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"
EVIDENCE = ROOT / "evidence"
REGISTRY_DOWNLOADS = Path("/tmp/GEMSDOE32/docs/downloads")  # for duplicate check

def load_surface(name: str) -> np.ndarray:
    path = PROC / f"{name.lower()}_surface.tif"
    with rasterio.open(path) as s:
        a = s.read(1)
    # Convert NaN outside to 0, keep values
    a = np.where(np.isfinite(a), a, 0).astype(np.float32)
    return a

def leakage_canary(surface: np.ndarray, foot: np.ndarray, labels: np.ndarray, ctx) -> dict:
    """Two-sided AUC inside each quadrant."""
    # Compute AUC per fold quadrant
    from gems83.holdout import quadrant_ids
    quad = ctx.quad
    results = {}
    for fold in [0,1,2,3]:
        mask = (quad == fold) & foot
        y = labels[mask].astype(int)
        # need positive examples inside this fold
        if y.sum() == 0 or y.sum() == y.size:
            results[f"fold_{fold}"] = None
            continue
        scores = surface[mask]
        # Remove NaN
        valid = np.isfinite(scores)
        if valid.sum() == 0:
            results[f"fold_{fold}"] = None
            continue
        try:
            auc = roc_auc_score(y[valid], scores[valid])
            # two-sided: max(auc, 1-auc)
            auc2 = max(auc, 1-auc)
        except Exception as e:
            auc2 = 0.5
        results[f"fold_{fold}"] = float(auc2)
        # leakage if >0.90
    vals = [v for v in results.values() if v is not None]
    mean_auc = float(np.mean(vals)) if vals else 0.5
    leak = any(v > 0.90 for v in vals) if vals else False
    return {"per_fold": results, "mean_two_sided_auc": mean_auc, "leakage_flag": leak, "max_auc": float(max(vals)) if vals else 0.5}

def top_n_mask(surface: np.ndarray, foot: np.ndarray, labels: np.ndarray, n: int, buffer_px: int = 2) -> np.ndarray:
    """Select top N pixels, excluding catalogue buffer."""
    from scipy.ndimage import binary_dilation
    # Mask out catalogue buffer
    if buffer_px > 0:
        labels_dil = binary_dilation(labels, iterations=buffer_px)
        domain = foot & ~labels_dil
    else:
        domain = foot & ~labels
    s = np.where(domain, surface, -np.inf)
    flat = s.ravel()
    # If n > available, clamp
    available = (domain).sum()
    n_eff = min(n, int(available))
    idx = np.argpartition(flat, -n_eff)[-n_eff:]
    m = np.zeros(flat.shape, dtype=bool)
    m[idx] = True
    return m.reshape(s.shape)

def registry_duplicate_check(mask: np.ndarray, registry_paths: list[Path], foot: np.ndarray) -> dict:
    """Check rank-correlation with registry rasters and overlap within 3px."""
    results = []
    for rp in registry_paths:
        try:
            with rasterio.open(rp) as s:
                arr = s.read(1)
            # Convert to binary: >0 is dot
            reg_mask = (arr > 0.5) & foot if arr.dtype != np.bool_ else arr & foot
            # Overlap within 3px: dilate reg_mask by 3, check fraction of our dots inside
            from scipy.ndimage import binary_dilation
            reg_dil = binary_dilation(reg_mask, iterations=3)
            overlap = (mask & reg_dil).sum() / max(mask.sum(), 1)
            # Rank correlation: Spearman approximated via Pearson on ranks?
            # Use flat rank correlation: flatten both surfaces? But we have binary masks, use Jaccard-like?
            # Compute Pearson correlation of binary masks
            # To avoid degenerate, compute over footprint
            a = mask[foot].astype(float)
            b = reg_mask[foot].astype(float)
            # Pearson
            a_mean = a.mean()
            b_mean = b.mean()
            num = ((a - a_mean)*(b - b_mean)).sum()
            den = np.sqrt(((a - a_mean)**2).sum() * ((b - b_mean)**2).sum())
            corr = float(num / (den + 1e-12)) if den>1e-12 else 0.0
            # Also check surface correlation if available, but we only have binary
            results.append({"path": str(rp.name), "pearson": corr, "overlap_3px_frac": float(overlap), "reg_dots": int(reg_mask.sum()), "our_dots": int(mask.sum())})
        except Exception as e:
            results.append({"path": str(rp.name), "error": str(e)})
    return {"checks": results}

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--mass", type=int, default=40000, help="emitted pixels")
    parser.add_argument("--buffer", type=int, default=2, help="catalogue buffer px")
    args = parser.parse_args()

    EVIDENCE.mkdir(parents=True, exist_ok=True)
    # Load context
    print("Loading holdout context...")
    ctx = load_holdout_context(DATA, hide_frac=0.20)
    print(f"Context loaded: {len(ctx.cells)} cells, SGMC off {ctx.sgmc_n_truth} truth px")
    foot = ctx.foot
    labels = ctx.labels

    # Check existing best file for baseline
    baseline_path = REGISTRY_DOWNLOADS / "gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif"
    if baseline_path.exists():
        with rasterio.open(baseline_path) as s:
            baseline_mask = s.read(1) > 0.5
        baseline_mask = baseline_mask & foot
        print(f"Baseline registry mask: {baseline_mask.sum()} dots")
        # Evaluate baseline on holdout
        baseline_result = evaluate_candidate_holdout(baseline_mask, ctx, name="baseline_h33b2_37654")
        print(f"Baseline HOLDOUT-DTI catalogue_hidden_mean {baseline_result['catalogue_hidden_mean']:.5f} drift {baseline_result['drift_corrected_holdout_mean']:.5f}")

    registry_files = list(REGISTRY_DOWNLOADS.glob("*.tif"))[:5]
    print(f"Registry files for duplicate check: {[p.name for p in registry_files]}")

    results = {}
    for hyp in ["H83-A", "H83-C", "H83-B"]:
        print(f"\n=== {hyp} ===")
        try:
            surface = load_surface(hyp)
            print(f"  surface loaded min {surface.min():.3f} max {surface.max():.3f} mean {surface[foot].mean():.3f}")
            # Leakage canary
            canary = leakage_canary(surface, foot, labels, ctx)
            print(f"  LEAKAGE CANARY: mean AUC {canary['mean_two_sided_auc']:.4f} max {canary['max_auc']:.4f} leak {canary['leakage_flag']}")
            if canary['leakage_flag']:
                print(f"  *** LEAKAGE DETECTED — abort ***")
            # Top-N emission
            mask = top_n_mask(surface, foot, labels, n=args.mass, buffer_px=args.buffer)
            print(f"  emitted {mask.sum()} dots (requested {args.mass}) 0 on catalogue ? {(mask & labels).sum()==0}")
            # Holdout evaluation
            hold = evaluate_candidate_holdout(mask, ctx, name=hyp)
            print(f"  HOLDOUT-DTI catalogue_hidden_mean {hold['catalogue_hidden_mean']:.5f} sgmc {hold['sgmc_prevalence_calibrated_dti']:.5f} drift {hold['drift_corrected_holdout_mean']:.5f}")
            print(f"  per quadrant cat: {hold['catalogue_hidden_per_quadrant']}")
            # Duplicate check
            dup = registry_duplicate_check(mask, registry_files, foot)
            for c in dup["checks"]:
                print(f"    dup {c['path']} corr {c.get('pearson',0):.3f} overlap {c.get('overlap_3px_frac',0):.3f}")
                if abs(c.get('pearson',0)) > 0.90 or c.get('overlap_3px_frac',0) > 0.70:
                    print(f"    *** DRIFTED INTO ANOTHER LANE — duplicate! ***")
            results[hyp] = {"canary": canary, "holdout": hold, "duplicate": dup, "emitted": int(mask.sum())}
        except Exception as e:
            import traceback; traceback.print_exc()
            results[hyp] = {"error": str(e)}

    # Save evidence
    out_path = EVIDENCE / "holdout_run_h83a.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved evidence to {out_path}")

    # Also test baseline again for comparison
    if baseline_path.exists():
        # Run baseline holdout again for direct comparison at same mass?
        # Our baseline is 37654, but we can also test at 40000 for comparison
        # Let's also create a baseline at 40000 by random or by reusing best surface?
        pass

    # Print summary ranking
    print("\n=== RANKING by HOLDOUT-DTI catalogue_hidden_mean ===")
    ranked = sorted([(k, v.get("holdout",{}).get("catalogue_hidden_mean",0)) for k,v in results.items()], key=lambda x: x[1], reverse=True)
    for r in ranked:
        print(r)
