#!/usr/bin/env python3
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"src"))
import numpy as np, rasterio
from scipy.ndimage import binary_dilation, distance_transform_edt
from gems83.holdout import load_holdout_context, evaluate_candidate_holdout
from gems83.metric import kernel

DATA=ROOT/"data/raw"
PROC=ROOT/"data/processed"
REG=Path("/tmp/GEMSDOE32/docs/downloads")

ctx=load_holdout_context(DATA)
foot=ctx.foot
labels=ctx.labels

# Load baseline
baseline_path=REG/"gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif"
with rasterio.open(baseline_path) as s:
    base_mask=s.read(1)>0.5
base_mask=base_mask & foot
print(f"base {base_mask.sum()}")

# Load H83-A surface
with rasterio.open(PROC/"h83-a_surface.tif") as s:
    surf=np.where(np.isfinite(s.read(1)), s.read(1), 0).astype(np.float32)
# Mask catalogue buffer
from scipy.ndimage import binary_dilation as dil
labels_dil=dil(labels, iterations=2)
domain=foot & ~labels_dil
surf=np.where(domain, surf, -np.inf)

# Evaluate base
res_base=evaluate_candidate_holdout(base_mask, ctx, name="base_B2")
print(f"base HOLDOUT cat {res_base['catalogue_hidden_mean']:.5f} sgmc {res_base['sgmc_prevalence_calibrated_dti']:.5f} drift {res_base['drift_corrected_holdout_mean']:.5f}")

# Now augment: add top N from surf where not near base (3px)
# Create distance to base
base_dist=distance_transform_edt(~base_mask)
# Only add where base_dist >3
available = domain & (base_dist>3)
print(f"available for addition {available.sum()}")
surf_avail=np.where(available, surf, -np.inf)
for add_n in [1000, 2500, 5000, 10000]:
    # select top add_n
    flat=surf_avail.ravel()
    # Filter finite
    idx=np.argpartition(flat, -add_n)[-add_n:]
    add_mask=np.zeros(flat.shape, bool)
    add_mask[idx]=True
    add_mask=add_mask.reshape(surf.shape)
    combined=base_mask | add_mask
    print(f"add_n {add_n}: combined {combined.sum()} cat check {(combined & labels).sum()}")
    res=evaluate_candidate_holdout(combined, ctx, name=f"aug_{add_n}")
    print(f"  cat {res['catalogue_hidden_mean']:.5f} (+{res['catalogue_hidden_mean']-res_base['catalogue_hidden_mean']:.5f}) sgmc {res['sgmc_prevalence_calibrated_dti']:.5f} (+{res['sgmc_prevalence_calibrated_dti']-res_base['sgmc_prevalence_calibrated_dti']:.5f}) drift {res['drift_corrected_holdout_mean']:.5f} (+{res['drift_corrected_holdout_mean']-res_base['drift_corrected_holdout_mean']:.5f})")
    # Also check overlap vs registry
    # Compare to incumbent D2.8
    inc_path=REG/"gemsdoe32-d28-ref02600-repro-44090-20261004T183200Z-426073b6-zeros.tif"
    if inc_path.exists():
        with rasterio.open(inc_path) as s:
            inc=s.read(1)>0.5
        # overlap
        from scipy.ndimage import binary_dilation
        inc_dil=binary_dilation(inc, iterations=3)
        overlap=(combined & inc_dil).sum()/combined.sum()
        print(f"    overlap with incumbent 3px {overlap:.3f}")
