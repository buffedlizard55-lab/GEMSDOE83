#!/usr/bin/env python3
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"src"))
import numpy as np, rasterio
from scipy.ndimage import distance_transform_edt
from gems83.holdout import load_holdout_context, evaluate_candidate_holdout
from gems83.live_mirror import load_live_mirror_context, evaluate_live_mirror
from gems83.live_anchor import invert_live_pair, removal_gain_bound

DATA=ROOT/"data/raw"
ctx=load_holdout_context(DATA)
foot=ctx.foot
labels=ctx.labels

# Load D28
p28=Path("/tmp/test_data/scored/gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif")
with rasterio.open(p28) as s:
    base=s.read(1)>0.5
base=base & foot
print(f"D28 base {base.sum()}")

# Distance to catalogue
dcat=distance_transform_edt(~labels)

# Load live mirror context
lm_ctx=load_live_mirror_context(DATA, foot, labels)

# Invert live pair to get budget
inv=invert_live_pair(hi="H27-4-R1-SOLO", lo="D2.8", g_assumed=12226.0)
print(f"Inversion: d_hi {inv.d_hi:.1f} s_hi {inv.s_hi:.1f} budget {inv.implied_credit_loss_budget:.1f}")

for B in [1,2,3,4]:
    mask=base & (dcat> B)
    n_removed=base.sum() - mask.sum()
    # Compute credit loss: need to compute TP_w for removed dots vs base?
    # For now use holdout evaluation as proxy for credit
    # Estimate credit loss as difference in weighted coverage?
    # Simpler: compute live-mirror delta
    res=evaluate_live_mirror(mask, lm_ctx, name=f"B={B}")
    res2=evaluate_candidate_holdout(mask, ctx, name=f"B={B}")
    print(f"B={B}: n {mask.sum()} removed {n_removed} LM {res['lm_mean']:.5f} LM_cal {res['lm_calibrated_mean']:.5f} holdout cat {res2['catalogue_hidden_mean']:.5f} drift {res2['drift_corrected_holdout_mean']:.5f}")
    # Compute removal gain bound using actual measured d_credit from live-mirror TP_w? Use holdout tp?
    # For live_anchor, need d_credit measured from field's TP_w
    # Let's approximate d_credit as n_removed * mean kernel credit per dot (use 0.1 as estimate)
    # But better compute actual TP_w difference using live_mirror's fold_detail
    # We can compute d_credit from holdout? Not accurate. Use live_mirror's tp_w
    # For now, use inverted budget to compute safety if d_credit ~ n_removed * 0.126 (mean credit per dot from earlier)
    mean_credit_per_dot=0.1262 # from docs
    d_credit_est=n_removed * mean_credit_per_dot * 0.2 # ??? Actually need weighted credit per dot
    # Let's compute more accurately: Use holdout's tp difference
    # We'll just print n_removed and let live_anchor compute bound with d_credit = n_removed * 0.05 (break-even)
    # Actually we can compute exact d_credit if we had truth field, but we don't. Use live_anchor's safety with measured d_credit from earlier B=2 (65.09 for 2545 dots => 0.0256 per dot)
    # For B=2, measured was 65.09/2545=0.0256 credit per removed dot
    # Use that to estimate for B=3
    if B==2:
        # Use known values from registry
        print(f"  known B2: dn 2545 d_credit 65.09 safety 2.08")
    # For B3, estimate
    # Let's compute actual credit loss via official DTI's tp_w for SGMC truth? Use lm_ctx's truth?
    # We can compute TP_w for removed dots vs SGMC truth? But SGMC truth is off-catalogue, so removed dots near catalogue earn ~0 credit, so d_credit ~0

# Test augmented: B2 base + H83 jog addition
PROC=ROOT/"data/processed"
with rasterio.open(PROC/"h83-a_surface.tif") as s:
    surf=np.where(np.isfinite(s.read(1)), s.read(1), 0)
# Top N addition not near base
base_b2=base & (dcat>2)
base_dist=distance_transform_edt(~base_b2)
available=foot & ~labels & (dcat>2) & (base_dist>3)
# Actually available = domain & base_dist>3
surf_avail=np.where(available, surf, -np.inf)
for add_n in [1000,2500]:
    flat=surf_avail.ravel()
    idx=np.argpartition(flat, -add_n)[-add_n:]
    add_mask=np.zeros(flat.shape,bool)
    add_mask[idx]=True
    add_mask=add_mask.reshape(surf.shape)
    combined=base_b2 | add_mask
    res=evaluate_live_mirror(combined, lm_ctx, name=f"B2+{add_n}H83A")
    res2=evaluate_candidate_holdout(combined, ctx, name=f"B2+{add_n}H83A")
    print(f"B2+{add_n}H83A: n {combined.sum()} LM {res['lm_mean']:.5f} LM_cal {res['lm_calibrated_mean']:.5f} holdout cat {res2['catalogue_hidden_mean']:.5f} sgmc {res2['sgmc_prevalence_calibrated_dti']:.5f}")

# Validate live mirror ordering
from gems83.live_mirror import validate_live_mirror
val=validate_live_mirror(DATA, lm_ctx)
print(f"Live mirror validation all_reproduced {val['all_reproduced']} n {val['n_orderings_reproduced']}/{val['n_orderings_checked']}")
for c in val['orderings']:
    print(c)
