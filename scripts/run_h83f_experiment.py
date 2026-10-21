#!/usr/bin/env python3
"""H83-F experiment (this session's single lane).

Lane: SGMC-relocation de-redundancy swap at matched mass.
Keep the 26,000 least-redundant H83-B dots (fewest other dots within the
300 m / 3 px kernel disk), replace the 14,000 most-redundant dots with
USGS SGMC geologic-map fault pixels that are >3 px from the catalogue and
>3 px from every kept dot, ranked by SGMC line-support (SGMC neighbours in
a 7x7 window), thinned to >2 px separation among themselves. Total 40,000.

Primary instrument: pure hide-and-recover pooled DTI (alpha 0.2, beta 0.8,
300 m triangular kernel) withholding whole catalogue components, visible
faults masked pixel-exactly (official masking, DrivenData forum 11516).
SGMC-truth DTI is reported descriptively only (in-sample for H83-F).
Every number written to evidence/h83f_experiment.json is HOLDOUT-DTI or a
format/uniqueness measurement. No organizer score is claimed.
"""
import sys, json, hashlib
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import numpy as np, rasterio
from scipy.ndimage import distance_transform_edt, convolve, label as cc_label, uniform_filter
from gems83.metric import dti_binary, kernel

RNG = np.random.default_rng(20261021)
DATA = ROOT / "data/raw"
H83B = ROOT / "docs/downloads/gemsdoe83-h83b-dilational-jog-aug-b2-40000-20261004T220000Z-c48ac2b3-zeros.tif"
D28 = DATA / "scored/d28.tif"
KEEP_N, ADD_N = 26000, 14000

def load(p, thr=True):
    with rasterio.open(p) as s:
        a = s.read(1)
    return (a > 0.5) if thr else a

with rasterio.open(DATA / "sample_submission.tif") as s:
    foot = np.isfinite(s.read(1)); prof = s.profile.copy()
cat = load(DATA / "labels.tif")
h83 = load(H83B) & foot
d28 = load(D28) & foot
with rasterio.open(DATA / "external/derived_sgmc_faults_100m_u8.tif") as s:
    sgmc = (s.read(1) > 0) & foot
dcat = distance_transform_edt(~cat)
print(f"foot={foot.sum()} cat={cat.sum()} h83={h83.sum()} d28={d28.sum()} sgmc={sgmc.sum()}")

# --- redundancy: other H83-B dots inside Euclid 3px disk (offsets with k>0) ---
yy, xx = np.mgrid[-3:4, -3:4]
disk = (np.hypot(yy, xx) <= 3.0) & ~((yy == 0) & (xx == 0))
neigh = convolve(h83.astype(np.int16), disk.astype(np.int16), mode="constant")
dots = np.argwhere(h83)
red = neigh[h83]
# keep least redundant; tie-break: farther from catalogue first (deterministic)
order = np.lexsort((-dcat[h83], red))
keep_idx = dots[order[:KEEP_N]]
keep = np.zeros_like(h83); keep[keep_idx[:, 0], keep_idx[:, 1]] = True
print(f"kept={keep.sum()} redundancy kept mean={red[order[:KEEP_N]].mean():.3f} dropped mean={red[order[KEEP_N:]].mean():.3f}")

# --- SGMC relocation candidates ---
dkeep = distance_transform_edt(~keep)
cand = sgmc & (dcat > 3) & (dkeep > 3)
support = uniform_filter(sgmc.astype(np.float32), size=7) * 49.0  # SGMC neighbours in 7x7
cy, cx = np.nonzero(cand)
corder = np.lexsort((cx, cy, -support[cand]))  # support desc, then row/col deterministic
blocked = np.zeros_like(keep)
stamp_y, stamp_x = np.mgrid[-2:3, -2:3]
stamp = np.hypot(stamp_y, stamp_x) <= 2.0
H, W = foot.shape
add = np.zeros_like(keep); n_add = 0
for i in corder:
    if n_add >= ADD_N: break
    y, x = int(cy[i]), int(cx[i])
    if blocked[y, x] or add[y, x]: continue
    add[y, x] = True; n_add += 1
    y0, y1, x0, x1 = max(0, y-2), min(H, y+3), max(0, x-2), min(W, x+3)
    sy0, sx0 = y0-(y-2), x0-(x-2)
    blocked[y0:y1, x0:x1] |= stamp[sy0:sy0+(y1-y0), sx0:sx0+(x1-x0)]
print(f"added={n_add} (pool={cand.sum()})")
assert n_add == ADD_N, "SGMC pool too small for lane mass"
cand_mask = keep | add
assert cand_mask.sum() == 40000 and (cand_mask & cat).sum() == 0
print(f"H83F total={cand_mask.sum()} on_cat={(cand_mask & cat).sum()} min_dcat={dcat[cand_mask].min():.3f}")

# --- uniqueness vs registry (H83-B itself + D28), Euclid 3px + Pearson ---
def uniq(ours, reg):
    d = distance_transform_edt(~reg)
    ov = float((d[ours] <= 3.0).mean())
    a = ours[foot].astype(float); b = reg[foot].astype(float)
    pc = float(np.corrcoef(a, b)[0, 1])
    return ov, pc
ov_h83, pc_h83 = uniq(cand_mask, h83)
ov_d28, pc_d28 = uniq(cand_mask, d28)
print(f"vs H83B overlap3={ov_h83:.4f} pearson={pc_h83:.4f} | vs D28 overlap3={ov_d28:.4f} pearson={pc_d28:.4f}")

# --- pure hide-and-recover holdout: withhold whole components (20% by seeded hash) ---
lab, ncomp = cc_label(cat, structure=np.ones((3, 3), int))
sizes = np.bincount(lab.ravel())
comp_ids = np.arange(1, ncomp + 1)
held_ids = comp_ids[RNG.permutation(ncomp)[: max(1, ncomp // 5)]]
held = np.isin(lab, held_ids)
visible = cat & ~held
print(f"components={ncomp} held_components={len(held_ids)} withheld_positives={int(held.sum())} visible={int(visible.sum())}")
# leakage canary: SGMC-alone AUC vs held-out (negatives = foot & ~cat, 200k sample)
pos = support[held]
neg_mask = foot & ~cat
neg_idx = np.argwhere(neg_mask); sel = RNG.choice(len(neg_idx), 200000, replace=False)
neg = support[tuple(neg_idx[sel].T)]
ranks = np.concatenate([pos, neg]).argsort().argsort().astype(float)
auc = float((ranks[:len(pos)].sum() - len(pos)*(len(pos)-1)/2) / (len(pos)*len(neg)))
auc = max(auc, 1-auc)
print(f"canary SGMC-support two-sided AUC vs held-out = {auc:.4f} (leakage if >0.90)")

def pooled(mask):
    # 4 quadrant folds pooled by summing TP/FP/FN sufficient statistics
    tp = fp = fn = 0.0; per = {}
    quads = [(slice(0, H//2), slice(0, W//2)), (slice(0, H//2), slice(W//2, W)),
             (slice(H//2, H), slice(0, W//2)), (slice(H//2, H), slice(W//2, W))]
    for qi, (ys, xs) in enumerate(quads):
        r = dti_binary(mask[ys, xs], held[ys, xs], valid=foot[ys, xs], known=visible[ys, xs])
        per[f"Q{qi}"] = r; tp += r["tp"]; fp += r["fp"]; fn += r["fn"]
    pooled_dti = float(tp / (tp + 0.2*fp + 0.8*fn + 1e-12))
    return pooled_dti, tp, fp, fn, per

res = {}
for name, m in [("H83-B-incumbent", h83), ("H83-F-sgmc-swap", cand_mask), ("D28-reference", d28)]:
    pdti, tp, fp, fn, per = pooled(m)
    res[name] = dict(pooled_dti=pdti, tp=tp, fp=fp, fn=fn, per_quadrant={k: v["dti"] for k, v in per.items()},
                     emitted=int(m.sum()), on_catalogue=int((m & cat).sum()))
    print(name, f"HOLDOUT-DTI pooled={pdti:.5f} tp={tp:.1f} fp={fp:.1f} n={m.sum()}")

# paired cluster bootstrap over held components for delta (F - B): resample component pixel-sets
# Precompute per-component TP contributions via distance to each mask (exact for binary DTI numerator)
def comp_tp(mask):
    dp = distance_transform_edt(~(mask & foot & ~visible))
    return kernel(dp[held]), dp
kF, _ = comp_tp(cand_mask); kB, _ = comp_tp(h83)
held_lab = lab[held]
# FP is global (not per-component); hold FP fixed, bootstrap TP/FN over components (conservative, stated)
uniq_ids, inv = np.unique(held_lab, return_inverse=True)
tpF_c = np.bincount(inv, weights=kF); tpB_c = np.bincount(inv, weights=kB); n_c = np.bincount(inv).astype(float)
fpF, fpB = res["H83-F-sgmc-swap"]["fp"], res["H83-B-incumbent"]["fp"]
deltas = []
for b in range(1000):
    s = RNG.integers(0, len(uniq_ids), len(uniq_ids))
    TF, TB, N = tpF_c[s].sum(), tpB_c[s].sum(), n_c[s].sum()
    dF = TF / (TF + 0.2*fpF*(N/held.sum()) + 0.8*(N-TF) + 1e-12)
    dB = TB / (TB + 0.2*fpB*(N/held.sum()) + 0.8*(N-TB) + 1e-12)
    deltas.append(dF - dB)
deltas = np.array(deltas)
ci = [float(np.percentile(deltas, 2.5)), float(np.percentile(deltas, 97.5))]
delta = res["H83-F-sgmc-swap"]["pooled_dti"] - res["H83-B-incumbent"]["pooled_dti"]
print(f"delta F-B = {delta:+.5f}  bootstrap95CI={ci}")

# --- write candidate rasters (zeros primary encoding + nan twin) via template profile ---
digest8 = hashlib.sha256(np.packbits(cand_mask.ravel())).hexdigest()[:8]
name = f"gemsdoe83-h83f-sgmc-reloc-deredund-40000-20261021T000000Z-{digest8}"
outdir = ROOT / "docs/downloads"; outdir.mkdir(parents=True, exist_ok=True)
arr0 = np.where(foot, cand_mask.astype(np.float32), np.float32(0.0))
arrN = np.where(foot, cand_mask.astype(np.float32), np.float32(np.nan))
def write(arr, suffix, nodata):
    p = outdir / f"{name}-{suffix}.tif"
    pr = dict(driver="GTiff", dtype="float32", count=1, width=W, height=H,
              crs="EPSG:32611", transform=prof["transform"], compress="deflate",
              predictor=3, zlevel=9, tiled=True, blockxsize=256, blockysize=256, nodata=nodata)
    with rasterio.open(p, "w", **pr) as d: d.write(arr, 1)
    return p
pz = write(arr0, "zeros", None); pn = write(arrN, "nan", np.nan)
import zipfile
zp = outdir / f"{name}.zip"
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z: z.write(pz, arcname=f"{name}.tif")
sha_z = hashlib.sha256(pz.read_bytes()).hexdigest(); sha_n = hashlib.sha256(pn.read_bytes()).hexdigest()
print(f"wrote {pz.name} sha={sha_z} bytes={pz.stat().st_size}")

bundle = dict(candidate=name, digest8=digest8, keep_n=KEEP_N, add_n=int(add.sum()),
  emitted=int(cand_mask.sum()), on_catalogue=int((cand_mask & cat).sum()),
  min_dist_to_catalogue_px=float(dcat[cand_mask].min()),
  uniqueness=dict(vs_H83B=dict(overlap_within_3px_euclid=ov_h83, pearson_binary=pc_h83),
                  vs_D28=dict(overlap_within_3px_euclid=ov_d28, pearson_binary=pc_d28),
                  pass_overlap_lt_0p70=bool(max(ov_h83, ov_d28) < 0.70),
                  pass_corr_lt_0p90=bool(max(pc_h83, pc_d28) < 0.90)),
  canary=dict(feature="SGMC 7x7 line-support", two_sided_auc_vs_heldout=auc, leakage_flag=bool(auc > 0.90)),
  holdout=dict(label="HOLDOUT-DTI", evaluator="gems83.metric.dti_binary pooled-quadrant v-h83f-1",
               withheld_positives=int(held.sum()), held_components=int(len(held_ids)),
               total_components=int(ncomp), results=res, delta_F_minus_B=float(delta),
               delta_bootstrap_ci95=ci,
               caveat="Both fixed rasters used full-catalogue distance (B2) at build time; holdout compares emission geometry, B2 advantage is common-mode. FP held fixed in bootstrap, rescaled by resampled truth mass."),
  files=dict(zeros=dict(path=str(pz.relative_to(ROOT)), sha256=sha_z, bytes=int(pz.stat().st_size)),
             nan=dict(path=str(pn.relative_to(ROOT)), sha256=sha_n, bytes=int(pn.stat().st_size)),
             zip=dict(path=str(zp.relative_to(ROOT)), sha256=hashlib.sha256(zp.read_bytes()).hexdigest(), bytes=int(zp.stat().st_size))),
  verdict=("promote" if (delta > 0 and ci[0] > 0) else "negative"))
(ROOT / "evidence/h83f_experiment.json").write_text(json.dumps(bundle, indent=2))
print("VERDICT:", bundle["verdict"])
