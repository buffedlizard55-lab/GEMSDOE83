#!/usr/bin/env python3
"""End-to-end 3-experiment pipeline for Lane H83-GVCD (GEMSDOE83).

Executes:
  - EXP-83-1: 82-channel single-feature leakage canary audit (Seeds 30 & 20, gate <= 0.90)
              + pure label-free physical/geothermal/radiometric/LiDAR LOQO baseline.
  - EXP-83-2: Paired 6-arm dual-seed spatial-quadrant holdout (Seed 30 = 11,342 withheld,
              Seed 20 = 11,321 withheld, combined = 22,663 withheld positives) on the
              unmodified `vendor/gems57/evaluate_holdout.py` (`gems57-pooled-hide-v2`).
  - EXP-83-3: Full-catalogue 4-fold LOQO production surface, pre-placement surface
              uniqueness scan, Collar-Decoupled (excl_px=3.0) Quadrant-Calibrated
              Dinkelbach Submodular 300m Kernel + Uniqueness Cap (0.640 < 0.70) 37,654-dot
              emission, unmodified `vendor/gems57/submission_writer.py`, `validate.py`,
              and `uniqueness.py` audits.
"""
from __future__ import annotations

import gc
import glob
import hashlib
import json
import shutil
import sys
import time
import zipfile
from pathlib import Path
from typing import Dict, List, Tuple

import lightgbm as lgb
import numpy as np
import rasterio
from scipy import ndimage as ndi
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor"))
sys.path.insert(0, str(ROOT / "src"))

from gems57 import (  # noqa: E402
    evaluate_holdout as EH,
    grid as GRID,
    holdout as HO,
    metric as M,
    submission_writer as SW,
    uniqueness as U,
    validate as V,
)
from gems83 import dinkelbach_emitter as DE, features as F  # noqa: E402

RAW_DIR = ROOT / "data" / "raw"
BRIDGE_DIR = ROOT / "data" / "bridge"
PROC_DIR = ROOT / "data" / "processed"
EVID_DIR = ROOT / "evidence"
SUB_DIR = ROOT / "submissions"
DOCS_DL_DIR = ROOT / "docs" / "downloads"

BUDGET = 37_654
OVERLAP_CAP = 0.650


def log(*a) -> None:
    print(f"[{time.strftime('%H:%M:%S')}]", *a, flush=True)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def draw_training_parts(
    foot: np.ndarray,
    cat_known: np.ndarray,
    tr_reg: np.ndarray,
    sets: List[Tuple[np.ndarray, np.ndarray]],
    lut: np.ndarray,
    rng: np.random.Generator,
    pos_cap: int = 44_000,
) -> List[Tuple[np.ndarray, np.ndarray, int]]:
    d_cat = ndi.distance_transform_edt(~cat_known).astype(np.float32)
    neg_base = foot & tr_reg & (d_cat > 3.0)
    hard = lut[np.flatnonzero(neg_base & (d_cat <= 15.0))]
    easy = lut[np.flatnonzero(neg_base & (d_cat > 15.0))]
    out = []
    per_set = pos_cap // len(sets)
    for sid, (hid, _M) in enumerate(sets):
        pos = lut[np.flatnonzero(hid & tr_reg & foot)]
        if pos.size > per_set:
            pos = rng.choice(pos, per_set, replace=False)
        n_neg = 2 * pos.size
        nh = min(hard.size, n_neg // 2)
        ne = min(easy.size, n_neg - nh)
        neg = np.concatenate([rng.choice(hard, nh, replace=False), rng.choice(easy, ne, replace=False)])
        rows = np.concatenate([pos, neg])
        y = np.concatenate([np.ones(pos.size, np.int8), np.zeros(neg.size, np.int8)])
        out.append((rows, y, sid))
    return out


def gather_cols(
    X_phys: np.ndarray, rows: np.ndarray, M_sc: np.ndarray | None, mode: str = "full"
) -> np.ndarray:
    s_idx = np.sort(rows)
    inv = np.argsort(np.argsort(rows))
    if mode == "phys":
        return np.asarray(X_phys[s_idx], np.float32)[inv]
    assert M_sc is not None
    if mode == "struct":
        return np.asarray(M_sc[s_idx], np.float32)[inv]
    b = np.asarray(X_phys[s_idx], np.float32)[inv]
    n = np.asarray(M_sc[s_idx], np.float32)[inv]
    return np.hstack([b, n])


def fit_and_predict_fold(
    X_phys: np.ndarray,
    parts: List[Tuple[np.ndarray, np.ndarray, int]],
    sets: List[Tuple[np.ndarray, np.ndarray]],
    te_rows: np.ndarray,
    M_vis: np.ndarray,
    mode: str,
    seed_offset: int,
) -> np.ndarray:
    Xs, ys = [], []
    for rows, y, sid in parts:
        Xs.append(gather_cols(X_phys, rows, sets[sid][1], mode))
        ys.append(y)
    Xtr, ytr = np.vstack(Xs), np.concatenate(ys)
    del Xs, ys

    m1 = lgb.LGBMClassifier(
        n_estimators=180,
        learning_rate=0.065,
        num_leaves=45,
        min_child_samples=55,
        colsample_bytree=0.70,
        subsample=0.80,
        subsample_freq=1,
        reg_alpha=1.5,
        reg_lambda=4.0,
        n_jobs=-1,
        random_state=8301 + seed_offset,
        verbose=-1,
    )
    m1.fit(Xtr, ytr)

    m2 = None
    if mode == "full":
        m2 = lgb.LGBMClassifier(
            n_estimators=200,
            learning_rate=0.055,
            num_leaves=31,
            min_child_samples=80,
            colsample_bytree=0.85,
            subsample=0.85,
            subsample_freq=1,
            extra_trees=True,
            reg_alpha=2.5,
            reg_lambda=8.0,
            n_jobs=-1,
            random_state=8302 + seed_offset,
            verbose=-1,
        )
        m2.fit(Xtr, ytr)
    del Xtr, ytr

    preds = np.empty(te_rows.size, np.float32)
    for s in range(0, te_rows.size, 300_000):
        r = te_rows[s : s + 300_000]
        Xte = gather_cols(X_phys, r, M_vis, mode)
        p1 = m1.predict_proba(Xte)[:, 1].astype(np.float32)
        if m2 is not None:
            p2 = m2.predict_proba(Xte)[:, 1].astype(np.float32)
            preds[s : s + 300_000] = 0.55 * p1 + 0.45 * p2
        else:
            preds[s : s + 300_000] = p1
    return preds


def run_exp1_canary(
    g: GRID.Grid,
    X_phys: np.ndarray,
    phys_names: List[str],
    lut: np.ndarray,
) -> dict:
    exp1_path = EVID_DIR / "h83_exp1_canary_and_surface.json"
    if exp1_path.exists():
        log("Loading cached EXP-83-1 canary report from h83_exp1_canary_and_surface.json")
        return json.loads(exp1_path.read_text())
    log("=== EXP-83-1: Single-Feature Leakage Canary Audit (82 channels, Seeds 30 & 20) ===")
    foot, cat = g.footprint, g.catalogue
    d_cat = ndi.distance_transform_edt(~cat).astype(np.float32)
    sc_names = list(F.STRUCTURAL_NETWORK_NAMES) + list(F.COUPLING_INTERACTION_NAMES)
    all_names = phys_names + sc_names

    canary_by_seed = {}
    for seed in (30, 20):
        folds, _ = HO.buffered_component_draw(g, seed=seed, hide_frac=0.20, buffer_px=3)
        hidden = folds[0]["hidden_all"]
        visible = folds[0]["visible"]
        M_vis = F.compute_structural_and_coupling_fp(
            visible, foot, X_phys, phys_names, PROC_DIR / f"h83_sc_s{seed}_vis.npy"
        )
        rng = np.random.default_rng(8300 + seed)
        pos_fp = lut[np.flatnonzero(hidden & foot)]
        neg_pool = lut[np.flatnonzero(foot & (~cat) & (d_cat > 3.0))]
        neg_fp = rng.choice(neg_pool, size=min(160_000, neg_pool.size), replace=False)
        eval_rows = np.concatenate([pos_fp, neg_fp])
        y = np.concatenate([np.ones(pos_fp.size, dtype=np.int8), np.zeros(neg_fp.size, dtype=np.int8)])

        X_ev = gather_cols(X_phys, eval_rows, M_vis, mode="full")
        aucs: Dict[str, float] = {}
        for j, nm in enumerate(all_names):
            v = X_ev[:, j]
            ok = np.isfinite(v)
            if ok.sum() > 100 and np.ptp(v[ok]) > 0:
                a = float(roc_auc_score(y[ok], v[ok]))
                aucs[nm] = round(max(a, 1.0 - a), 6)
            else:
                aucs[nm] = 0.5
        del X_ev
        gc.collect()
        max_nm = max(aucs, key=aucs.get)
        max_val = aucs[max_nm]
        log(f"Seed {seed}: {len(aucs)} channels audited, max symmetric AUC = {max_val:.4f} ({max_nm}) <= 0.90")
        if max_val > 0.90:
            raise RuntimeError(f"LEAKAGE CANARY FAILED on seed {seed}: {max_nm} = {max_val}")
        top15 = sorted(aucs.items(), key=lambda kv: kv[1], reverse=True)[:15]
        canary_by_seed[str(seed)] = {
            "withheld_positive_pixels": int(pos_fp.size),
            "negative_pixels_sampled": int(neg_fp.size),
            "n_features_tested": len(aucs),
            "max_symmetric_auc": max_val,
            "max_feature": max_nm,
            "all_below_090": bool(max_val <= 0.90),
            "top_15_features": [{"feature": k, "symmetric_auc": v} for k, v in top15],
            "per_feature_symmetric_auc": aucs,
        }

    report = {
        "experiment": "EXP-83-1",
        "evidence_class": "LEAKAGE-CANARY",
        "evaluator_version": EH.VERSION,
        "gate_ceiling_symmetric_auc": 0.90,
        "all_seeds_passed": True,
        "n_total_channels": len(all_names),
        "n_physical_channels": len(phys_names),
        "n_structural_and_coupling_channels": len(sc_names),
        "seeds": canary_by_seed,
    }
    EVID_DIR.mkdir(parents=True, exist_ok=True)
    (EVID_DIR / "h83_leakage_canary.json").write_text(json.dumps(report, indent=2) + "\n")
    (EVID_DIR / "h83_exp1_canary_and_surface.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def get_or_fit_seed_surfaces(
    seed: int,
    g: GRID.Grid,
    X_phys: np.ndarray,
    phys_names: List[str],
    flat_fp: np.ndarray,
    lut: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, List[dict]]:
    foot, cat = g.footprint, g.catalogue
    quad = HO.quadrant_ids(foot)
    folds, _ = HO.buffered_component_draw(g, seed=seed, hide_frac=0.20, buffer_px=3)
    cache_npz = PROC_DIR / f"h83_surfs_seed{seed}.npz"
    if cache_npz.exists():
        log(f"Loading cached OOF surfaces for Seed {seed} from {cache_npz.name}")
        npz = np.load(cache_npz)
        return (
            npz["phys"].astype(np.float32),
            npz["struct"].astype(np.float32),
            npz["gvcd"].astype(np.float32),
            folds,
        )

    visible = folds[0]["visible"]
    M_vis = F.compute_structural_and_coupling_fp(
        visible, foot, X_phys, phys_names, PROC_DIR / f"h83_sc_s{seed}_vis.npy"
    )
    sets = []
    for r in range(2):
        syn_hid, syn_st = F.synthetic_withhold(visible, foot, quad, seed=seed * 10 + r)
        M_syn = F.compute_structural_and_coupling_fp(
            syn_st, foot, X_phys, phys_names, PROC_DIR / f"h83_sc_s{seed}_syn{r}.npy"
        )
        sets.append((syn_hid, M_syn))

    surf_phys = np.zeros(foot.shape, np.float32)
    surf_struct = np.zeros(foot.shape, np.float32)
    surf_gvcd = np.zeros(foot.shape, np.float32)

    for k, fold in enumerate(folds):
        tf = time.time()
        tr_reg = np.zeros_like(foot)
        for j, f2 in enumerate(folds):
            if j != k:
                tr_reg |= f2["region"]
        rng = np.random.default_rng(8300 + 10 * seed + k)
        parts = draw_training_parts(foot, (cat & tr_reg) | visible, tr_reg, sets, lut, rng)
        te_rows = lut[np.flatnonzero(fold["region"] & foot)]

        for mode, target_surf in (("phys", surf_phys), ("struct", surf_struct), ("full", surf_gvcd)):
            preds = fit_and_predict_fold(X_phys, parts, sets, te_rows, M_vis, mode, seed_offset=10 * seed + k)
            target_surf.ravel()[flat_fp[te_rows]] = preds
        gc.collect()
        log(f"Seed {seed} Fold {fold['name']} trained & predicted in {time.time() - tf:.1f}s")

    np.savez_compressed(
        cache_npz,
        phys=surf_phys.astype(np.float16),
        struct=surf_struct.astype(np.float16),
        gvcd=surf_gvcd.astype(np.float16),
    )
    return surf_phys, surf_struct, surf_gvcd, folds


def run_exp2_dualseed_holdout(
    g: GRID.Grid,
    X_phys: np.ndarray,
    phys_names: List[str],
    flat_fp: np.ndarray,
    lut: np.ndarray,
    packed_halos: np.ndarray,
    n_halos: int,
) -> dict:
    exp2_path = EVID_DIR / "h83_exp2_dualseed_holdout.json"
    if exp2_path.exists():
        log("Loading cached EXP-83-2 dual-seed holdout report from h83_exp2_dualseed_holdout.json")
        return json.loads(exp2_path.read_text())
    log("=== EXP-83-2: Paired 6-Arm Dual-Seed Spatial-Quadrant Holdout (Seeds 30 & 20) ===")
    foot = g.footprint
    arm_names = (
        "A0_random",
        "A1_phys_poisson",
        "A2_struct_poisson",
        "A3_gvcd_poisson",
        "A4_gvcd_dink_c20",
        "A5_gvcd_dink_c30",
    )
    combined_terms: Dict[str, np.ndarray] = {}
    per_seed_out = {}

    for seed in (30, 20):
        surf_phys, surf_struct, surf_gvcd, folds = get_or_fit_seed_surfaces(
            seed, g, X_phys, phys_names, flat_fp, lut
        )
        dist_known = ndi.distance_transform_edt(~folds[0]["masked_known"]).astype(np.float32)
        allow_20 = foot & (dist_known > 2.0)
        allow_30 = foot & (dist_known > 3.0)

        rng_rand = np.random.default_rng(999 + seed)
        surf_rand = (rng_rand.random(foot.shape, dtype=np.float32) * foot).astype(np.float32)

        dots_by_arm = {
            "A0_random": DE.emit_poisson_disk(surf_rand, allow_20, BUDGET, 2.8),
            "A1_phys_poisson": DE.emit_poisson_disk(surf_phys, allow_20, BUDGET, 2.8),
            "A2_struct_poisson": DE.emit_poisson_disk(surf_struct, allow_20, BUDGET, 2.8),
            "A3_gvcd_poisson": DE.emit_poisson_disk(surf_gvcd, allow_20, BUDGET, 2.8),
            "A4_gvcd_dink_c20": DE.emit_dinkelbach_submodular(
                surf_gvcd,
                allow_20,
                BUDGET,
                min_sep_px=2.45,
                packed_halos_fp=packed_halos,
                fp_lut=lut,
                n_halos=n_halos,
                overlap_cap=OVERLAP_CAP,
            )[0],
            "A5_gvcd_dink_c30": DE.emit_dinkelbach_submodular(
                surf_gvcd,
                allow_30,
                BUDGET,
                min_sep_px=2.40,
                packed_halos_fp=packed_halos,
                fp_lut=lut,
                n_halos=n_halos,
                overlap_cap=OVERLAP_CAP,
            )[0],
        }

        seed_terms: Dict[str, np.ndarray] = {}
        fold_details: Dict[str, dict] = {}
        for arm in arm_names:
            d = dots_by_arm[arm].astype(np.float32)
            acc = None
            pf = {}
            for fold in folds:
                res, t = EH.evaluate(d, fold, foot)
                pf[fold["name"]] = {
                    "dti": round(float(res["dti"]), 6),
                    "tpw": round(float(res["tpw"]), 4),
                    "fpw": round(float(res["fpw"]), 4),
                    "fnw": round(float(res["fnw"]), 4),
                    "n_truth": int(res["n_truth"]),
                    "n_emitted": int(res["n_emitted"]),
                    "coverage": round(float(res["coverage"]), 6),
                }
                acc = t if acc is None else acc + t
            seed_terms[arm] = acc
            combined_terms[arm] = acc if arm not in combined_terms else combined_terms[arm] + acc
            fold_details[arm] = pf
            dti_val = float(EH.from_terms(acc.sum(axis=0)))
            log(f"[Seed {seed}] {arm:18s} -> HOLDOUT-DTI = {dti_val:.6f}")

        summ = EH.pooled_summary(seed_terms, draws=2000, seed=520810 + seed, candidate="A5_gvcd_dink_c30")
        per_seed_out[str(seed)] = {
            "withheld_positive_pixels": int(folds[0]["hidden_all"].sum()),
            "budget_dots": BUDGET,
            "summary": summ,
            "per_fold": fold_details,
            "fold_receipts": [f["receipt"] for f in folds],
        }

    dualseed_summary = EH.pooled_summary(
        combined_terms, draws=2000, seed=830830, candidate="A5_gvcd_dink_c30"
    )
    for arm in arm_names:
        sc = dualseed_summary["scores"][arm]
        log(
            f"[DUAL-SEED POOLED 22,663 px] {arm:18s} -> HOLDOUT-DTI = {sc['dti']:.6f} "
            f"(95% CI [{sc['ci95'][0]:.6f}, {sc['ci95'][1]:.6f}])"
        )

    out = {
        "experiment": "EXP-83-2",
        "evidence_class": "HOLDOUT-DTI",
        "evaluator_version": EH.VERSION,
        "implementation_hashes": EH.implementation_hashes(),
        "alpha": M.ALPHA,
        "beta": M.BETA,
        "kernel_radius_m": M.R_M,
        "budget_dots": BUDGET,
        "enforced_overlap_cap": OVERLAP_CAP,
        "dualseed_pooled_summary": dualseed_summary,
        "seeds": per_seed_out,
    }
    (EVID_DIR / "h83_exp2_dualseed_holdout.json").write_text(json.dumps(out, indent=2) + "\n")
    return out


def audit_uniqueness_full(
    surf: np.ndarray,
    dots: np.ndarray,
    g: GRID.Grid,
    scored_dir: Path,
) -> dict:
    uniq_path = EVID_DIR / "h83_uniqueness.json"
    if uniq_path.exists():
        log("Loading cached uniqueness audit from h83_uniqueness.json")
        return json.loads(uniq_path.read_text())
    foot = g.footprint
    allowed = foot & (~g.catalogue)
    paths = sorted(glob.glob(str(scored_dir / "*.tif")))
    records = [
        {
            "repo_first": "scored_registry",
            "sources": [Path(p).name],
            "cache_file": str(Path(p).resolve()),
            "sha256": sha256_file(Path(p)),
        }
        for p in paths
    ]
    registry_index = {
        "complete_accessible_scan": True,
        "rasters": records,
    }
    expected_grid = (foot.shape, g.crs, GRID.TRANSFORM)

    # Pre-compute halo coverage of allowed domain for each registry file
    halo_cov_by_sha: Dict[str, float] = {}
    for rec in records:
        with rasterio.open(rec["cache_file"]) as ds:
            if ds.shape != foot.shape:
                continue
            arr = ds.read(1).astype(np.float32)
        sup = np.isfinite(arr) & (arr > 0) & foot
        halo_cov_by_sha[rec["sha256"]] = U.halo_coverage(sup, allowed)

    log(f"Running vendor/gems57/uniqueness.py on pre-placement surface across {len(records)} rasters...")
    surf_rep = U.compare_array_to_registry(
        surf.astype(np.float32),
        registry_index,
        foot,
        file_sha256=hashlib.sha256(surf.astype(np.float32).tobytes()).hexdigest(),
        expected_grid=expected_grid,
    )
    for r in surf_rep["rows"]:
        if "error" not in r:
            r["halo_coverage"] = round(halo_cov_by_sha.get(r["sha256"], 0.0), 6)
            r["forward_overlap"] = r["my_dots_within_3px_of_theirs"]
    surf_binding = U.binding_duplicate_decision(surf_rep["rows"])
    log(
        f"Surface uniqueness (binding like-for-like): duplicate={surf_binding['duplicate']}, "
        f"worst_spearman={surf_binding['worst_abs_spearman']:.4f}, "
        f"worst_forward_overlap={surf_binding['worst_forward_overlap']:.4f}"
    )

    log(f"Running vendor/gems57/uniqueness.py on final emitted dots across {len(records)} rasters...")
    dots_rep = U.compare_array_to_registry(
        dots.astype(np.float32),
        registry_index,
        foot,
        file_sha256=hashlib.sha256(dots.astype(np.float32).tobytes()).hexdigest(),
        expected_grid=expected_grid,
    )
    for r in dots_rep["rows"]:
        if "error" not in r:
            r["halo_coverage"] = round(halo_cov_by_sha.get(r["sha256"], 0.0), 6)
            r["forward_overlap"] = r["my_dots_within_3px_of_theirs"]
    dots_binding = U.binding_duplicate_decision(dots_rep["rows"])
    dots_two_phase = U.two_phase_summary(dots_rep["rows"], int(foot.sum()))
    log(
        f"Final dots uniqueness (binding like-for-like): duplicate={dots_binding['duplicate']}, "
        f"worst_spearman={dots_binding['worst_abs_spearman']:.4f}, "
        f"worst_forward_overlap={dots_binding['worst_forward_overlap']:.4f}"
    )

    disc_rows = [
        r for r in dots_rep["rows"]
        if "error" not in r and float(r.get("halo_coverage", 0.0)) < U.DENSE_HALO_FRACTION
    ]
    space_rows = [
        r for r in dots_rep["rows"]
        if "error" not in r and float(r.get("halo_coverage", 0.0)) >= U.DENSE_HALO_FRACTION
    ]
    disc_rows.sort(key=lambda r: r["my_dots_within_3px_of_theirs"], reverse=True)
    space_rows.sort(key=lambda r: r["my_dots_within_3px_of_theirs"], reverse=True)

    out = {
        "evidence_class": "UNIQUENESS-AUDIT",
        "policy": "vendor/gems57/uniqueness.py binding_duplicate_decision (IR-H85-01 like-for-like + literal full report)",
        "gate_thresholds": {
            "spearman_rho_limit": U.RHO_LIMIT,
            "dot_overlap_3px_limit": U.OVERLAP_LIMIT,
            "enforced_dinkelbach_overlap_cap": OVERLAP_CAP,
        },
        "rasters_checked": len(records),
        "pre_placement_surface": {
            "unique": not bool(surf_binding["duplicate"]),
            "binding_decision": surf_binding,
            "literal_duplicate_count": int(surf_rep["duplicate_count"]),
            "worst_spearman_full_footprint": round(float(surf_binding["worst_abs_spearman"]), 6),
            "worst_dot_overlap_3px": round(float(surf_binding["worst_forward_overlap"]), 6),
            "top_5_spearman": sorted(
                [r for r in surf_rep["rows"] if "error" not in r],
                key=lambda r: abs(r.get("spearman_full_footprint") or 0.0),
                reverse=True,
            )[:5],
            "top_5_discriminating_overlap": sorted(
                [r for r in surf_rep["rows"] if "error" not in r and float(r.get("halo_coverage", 0.0)) < U.DENSE_HALO_FRACTION],
                key=lambda r: r.get("my_dots_within_3px_of_theirs") or 0.0,
                reverse=True,
            )[:5],
        },
        "final_emitted_dots": {
            "unique": not bool(dots_binding["duplicate"]),
            "binding_decision": dots_binding,
            "two_phase_summary": dots_two_phase,
            "literal_duplicate_count": int(dots_rep["duplicate_count"]),
            "worst_spearman_full_footprint": round(float(dots_binding["worst_abs_spearman"]), 6),
            "worst_dot_overlap_3px": round(float(dots_binding["worst_forward_overlap"]), 6),
            "top_10_overlap": disc_rows[:10],
            "top_5_spearman": sorted(
                [r for r in dots_rep["rows"] if "error" not in r],
                key=lambda r: abs(r.get("spearman_full_footprint") or 0.0),
                reverse=True,
            )[:5],
        },
        "literal_untruncated_audit": {
            "informative_rasters_count": len(disc_rows),
            "informative_max_forward_overlap_3px": round(float(disc_rows[0]["my_dots_within_3px_of_theirs"]), 6) if disc_rows else 0.0,
            "informative_all_below_070": not bool(dots_binding["duplicate"]),
            "top_10_informative_literal_overlap": [
                {
                    "name": r["submission"],
                    "their_positive_pixels": r["their_dots"],
                    "their_3px_halo_footprint_coverage": r["halo_coverage"],
                    "literal_forward_overlap_3px": round(float(r["my_dots_within_3px_of_theirs"]), 6),
                    "spearman_full_footprint": round(float(r["spearman_full_footprint"]), 6) if r.get("spearman_full_footprint") is not None else None,
                }
                for r in disc_rows[:10]
            ],
            "space_filling_or_whole_grid_lattice_rasters": [
                {
                    "name": r["submission"],
                    "their_positive_pixels": r["their_dots"],
                    "their_3px_halo_footprint_coverage": r["halo_coverage"],
                    "literal_forward_overlap_3px": round(float(r["my_dots_within_3px_of_theirs"]), 6),
                    "spearman_full_footprint": round(float(r["spearman_full_footprint"]), 6) if r.get("spearman_full_footprint") is not None else None,
                }
                for r in space_rows
            ],
        },
    }
    (EVID_DIR / "h83_uniqueness.json").write_text(json.dumps(out, indent=2) + "\n")
    return out


def run_exp3_build_and_audit(
    g: GRID.Grid,
    X_phys: np.ndarray,
    phys_names: List[str],
    flat_fp: np.ndarray,
    lut: np.ndarray,
    packed_halos: np.ndarray,
    n_halos: int,
) -> Tuple[dict, dict, Path, Path]:
    log("=== EXP-83-3: Full-Catalogue 4-Fold LOQO Production Surface & Submission Build ===")
    foot, cat = g.footprint, g.catalogue
    quad = HO.quadrant_ids(foot)
    surf_path = PROC_DIR / "h83_final_surface.npy"

    if surf_path.exists():
        log(f"Loading cached production surface from {surf_path.name}")
        surf = np.load(surf_path).astype(np.float32)
    else:
        M_full = F.compute_structural_and_coupling_fp(
            cat, foot, X_phys, phys_names, PROC_DIR / "h83_sc_full_vis.npy"
        )
        sets = []
        for r in range(2):
            syn_hid, syn_st = F.synthetic_withhold(cat, foot, quad, seed=9000 + r)
            M_syn = F.compute_structural_and_coupling_fp(
                syn_st, foot, X_phys, phys_names, PROC_DIR / f"h83_sc_full_syn{r}.npy"
            )
            sets.append((syn_hid, M_syn))

        regions = [ndi.binary_erosion(quad == q, iterations=HO.DOMAIN_ERODE) & foot for q in range(4)]
        surf = np.zeros(foot.shape, np.float32)
        for k in range(4):
            tf = time.time()
            tr_reg = np.zeros_like(foot)
            for j in range(4):
                if j != k:
                    tr_reg |= regions[j]
            rng = np.random.default_rng(9900 + k)
            parts = draw_training_parts(foot, cat, tr_reg, sets, lut, rng)
            te_rows = lut[np.flatnonzero((quad == k) & foot)]
            preds = fit_and_predict_fold(X_phys, parts, sets, te_rows, M_full, "full", seed_offset=900 + k)
            surf.ravel()[flat_fp[te_rows]] = preds
            gc.collect()
            log(f"Production LOQO fold {k} done in {time.time() - tf:.1f}s")
        surf = np.where(foot, np.clip(surf, 0.0, 1.0), 0.0).astype(np.float32)
        np.save(surf_path, surf)

    d_cat = ndi.distance_transform_edt(~cat).astype(np.float32)
    allow_full = foot & (~cat) & (d_cat > 3.0)
    dots, dink_stats = DE.emit_dinkelbach_submodular(
        surf,
        allow_full,
        budget=BUDGET,
        min_sep_px=2.40,
        packed_halos_fp=packed_halos,
        fp_lut=lut,
        n_halos=n_halos,
        overlap_cap=OVERLAP_CAP,
    )
    log(f"Emitted {int(dots.sum()):,} binary dots: {dink_stats}")

    # Scale pre-placement surface inside allow_full so its top values match emitted priority for surface audit
    surf_for_audit = np.where(allow_full, surf, 0.0).astype(np.float32)
    uniq_out = audit_uniqueness_full(surf_for_audit, dots, g, RAW_DIR / "scored")

    # Write official GeoTIFF + single-TIFF ZIP via unmodified vendor/gems57/submission_writer.py
    SUB_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DL_DIR.mkdir(parents=True, exist_ok=True)
    pred_f32 = dots.astype(np.float32)
    pix_sha8 = hashlib.sha256(np.ascontiguousarray(pred_f32).tobytes()).hexdigest()[:8]
    sub_stem = f"gems83-h83-gvcd-dink300-37654dots-20261021-{pix_sha8}-zeros"
    final_tif = SUB_DIR / f"{sub_stem}.tif"
    final_zip = SUB_DIR / f"{sub_stem}.zip"
    final_rec = SUB_DIR / f"{sub_stem}.json"
    for p in (final_tif, final_zip, final_rec):
        if p.exists():
            p.unlink()

    note_str = (
        "H83-GVCD geothermal-vent & structural-relay counterfactual Dinkelbach 300m submodular; "
        "37654 dots >3px off cat; overlap<=0.650"
    )[:140]
    receipt = SW.write_submission(
        final_tif,
        pred_f32,
        BRIDGE_DIR / "sample_submission.tif",
        g.footprint,
        note=note_str,
        name=sub_stem,
        catalogue=g.catalogue,
    )
    sha = receipt["sha256"]

    # Mirror to docs/downloads/ for GitHub Pages download buttons
    shutil.copy2(final_tif, DOCS_DL_DIR / final_tif.name)
    shutil.copy2(final_zip, DOCS_DL_DIR / final_zip.name)
    shutil.copy2(final_rec, DOCS_DL_DIR / final_rec.name)

    val_report = V.validate(final_tif, g.footprint, g.catalogue)
    log(f"Validator on {final_tif.name}: all_checks_passed={val_report['all_checks_passed']}")
    if not val_report["all_checks_passed"]:
        raise RuntimeError(f"Submission validator failed: {val_report}")

    d_emitted = d_cat[dots]
    dist_breakdown = {
        "total_binary_dots": int(dots.sum()),
        "min_distance_to_catalogue_px": round(float(d_emitted.min()), 4),
        "median_distance_to_catalogue_px": round(float(np.median(d_emitted)), 4),
        "mean_distance_to_catalogue_px": round(float(d_emitted.mean()), 4),
        "near_continuation_300m_to_1p2km_dots": int(((d_emitted > 3.0) & (d_emitted <= 12.0)).sum()),
        "step_over_and_piedmont_1p2km_to_5km_dots": int(((d_emitted > 12.0) & (d_emitted <= 50.0)).sum()),
        "blind_intrabasin_gt_5km_dots": int((d_emitted > 50.0).sum()),
    }

    exp3_report = {
        "experiment": "EXP-83-3",
        "evidence_class": "BUILD-AND-VALIDATION",
        "submission_name": sub_stem,
        "tif_path": f"submissions/{final_tif.name}",
        "zip_path": f"submissions/{final_zip.name}",
        "docs_tif_path": f"docs/downloads/{final_tif.name}",
        "docs_zip_path": f"docs/downloads/{final_zip.name}",
        "raster_sha256": sha,
        "zip_sha256": sha256_file(final_zip),
        "tif_size_bytes": final_tif.stat().st_size,
        "zip_size_bytes": final_zip.stat().st_size,
        "dinkelbach_stats": dink_stats,
        "distance_breakdown": dist_breakdown,
        "validator_output": val_report,
    }
    (EVID_DIR / "h83_exp3_build_and_uniqueness.json").write_text(json.dumps(exp3_report, indent=2) + "\n")
    return exp3_report, uniq_out, final_tif, final_zip


def main() -> int:
    t0 = time.time()
    g = GRID.load_grid(BRIDGE_DIR)
    foot = g.footprint
    phys_names, X_phys = F.load_or_build_rowmajor_f16(RAW_DIR, foot, PROC_DIR)
    flat_fp = np.flatnonzero(foot.ravel())
    lut = np.full(foot.size, -1, dtype=np.int64)
    lut[flat_fp] = np.arange(flat_fp.size)

    packed_halos, n_halos, _ = DE.build_or_load_registry_halos(
        RAW_DIR / "scored", foot, PROC_DIR, budget=BUDGET
    )

    exp1 = run_exp1_canary(g, X_phys, phys_names, lut)
    exp2 = run_exp2_dualseed_holdout(g, X_phys, phys_names, flat_fp, lut, packed_halos, n_halos)
    exp3, uniq, final_tif, final_zip = run_exp3_build_and_audit(
        g, X_phys, phys_names, flat_fp, lut, packed_halos, n_halos
    )

    s30_dti = exp2["seeds"]["30"]["summary"]["scores"]["A5_gvcd_dink_c30"]
    s20_dti = exp2["seeds"]["20"]["summary"]["scores"]["A5_gvcd_dink_c30"]
    dual_dti = exp2["dualseed_pooled_summary"]["scores"]["A5_gvcd_dink_c30"]

    beats_all = (
        s30_dti["dti"] > 0.171625
        and s20_dti["dti"] > 0.160795
        and dual_dti["dti"] > 0.182804
        and exp1["all_seeds_passed"]
        and uniq["pre_placement_surface"]["unique"]
        and uniq["final_emitted_dots"]["unique"]
        and exp3["validator_output"]["all_checks_passed"]
    )

    run_card = {
        "lane_id": "H83-GVCD",
        "repo": "buffedlizard55-lab/GEMSDOE83",
        "branch": "arena/a27c329b-gemsdoe83",
        "date_utc": "2026-10-21",
        "submission_name": exp3["submission_name"],
        "portal_note": (
            f"H83-GVCD geothermal-vent & structural-relay counterfactual Dinkelbach 300m submodular; "
            f"37654 dots >3px off cat; HOLDOUT-DTI {dual_dti['dti']:.4f}"
        )[:140],
        "tif_download": exp3["docs_tif_path"],
        "zip_download": exp3["docs_zip_path"],
        "submissions_tif": exp3["tif_path"],
        "submissions_zip": exp3["zip_path"],
        "raster_sha256": exp3["raster_sha256"],
        "zip_sha256": exp3["zip_sha256"],
        "tif_size_bytes": exp3["tif_size_bytes"],
        "zip_size_bytes": exp3["zip_size_bytes"],
        "ok_to_download": bool(exp3["validator_output"]["all_checks_passed"]),
        "ok_to_submit": bool(beats_all),
        "verdict": "PROMOTE — OK TO DOWNLOAD AND SUBMIT" if beats_all else "HOLD — DO NOT SUBMIT",
        "evidence_class": "HOLDOUT-DTI",
        "evaluator_version": EH.VERSION,
        "organizer_confirmed_score": None,
        "weekly_slots_used": 0,
        "holdout_dti": {
            "dualseed_pooled_22663px": dual_dti,
            "seed_30_11342px": s30_dti,
            "seed_20_11321px": s20_dti,
            "all_arms_dualseed": exp2["dualseed_pooled_summary"]["scores"],
            "all_arms_seed30": exp2["seeds"]["30"]["summary"]["scores"],
            "all_arms_seed20": exp2["seeds"]["20"]["summary"]["scores"],
            "paired_differences_dualseed": exp2["dualseed_pooled_summary"]["paired_differences"],
        },
        "incumbent_comparisons": {
            "vs_H77_Step_seed20_0152718": round(s20_dti["dti"] - 0.152718, 6),
            "vs_H83_NETSIB_seed20_0153825": round(s20_dti["dti"] - 0.153825, 6),
            "vs_H83_NETSIB_seed30_0163700": round(s30_dti["dti"] - 0.163700, 6),
            "vs_H77_VDS_seed20_0160795": round(s20_dti["dti"] - 0.160795, 6),
            "vs_H77_VDS_seed30_0171625": round(s30_dti["dti"] - 0.171625, 6),
            "vs_H85_EDTI_dualseed_0182804": round(dual_dti["dti"] - 0.182804, 6),
        },
        "leakage_canary": {
            "passed": exp1["all_seeds_passed"],
            "gate_limit": 0.90,
            "seed_30_max_auc": exp1["seeds"]["30"]["max_symmetric_auc"],
            "seed_30_max_feature": exp1["seeds"]["30"]["max_feature"],
            "seed_20_max_auc": exp1["seeds"]["20"]["max_symmetric_auc"],
            "seed_20_max_feature": exp1["seeds"]["20"]["max_feature"],
        },
        "uniqueness": {
            "pre_placement_surface_unique": uniq["pre_placement_surface"]["unique"],
            "pre_placement_worst_spearman": uniq["pre_placement_surface"]["worst_spearman_full_footprint"],
            "pre_placement_worst_overlap_3px": uniq["pre_placement_surface"]["worst_dot_overlap_3px"],
            "final_dots_unique": uniq["final_emitted_dots"]["unique"],
            "final_dots_worst_spearman": uniq["final_emitted_dots"]["worst_spearman_full_footprint"],
            "final_dots_worst_overlap_3px": uniq["final_emitted_dots"]["worst_dot_overlap_3px"],
            "informative_literal_max_overlap_3px": uniq["literal_untruncated_audit"]["informative_max_forward_overlap_3px"],
            "rasters_checked": uniq["rasters_checked"],
        },
        "validator": exp3["validator_output"],
        "distance_breakdown": exp3["distance_breakdown"],
        "dinkelbach_stats": exp3["dinkelbach_stats"],
        "elapsed_s": round(time.time() - t0, 1),
    }
    (EVID_DIR / "h83_run_card.json").write_text(json.dumps(run_card, indent=2) + "\n")
    (ROOT / "run_card.json").write_text(json.dumps(run_card, indent=2) + "\n")
    log(f"=== PIPELINE COMPLETE in {run_card['elapsed_s']}s: verdict={run_card['verdict']} ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
