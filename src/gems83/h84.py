"""H84 — Triple-junction geothermal conduit (final candidate, ranked #1 new).

Combines three independent blind-fault indicators at 100 m:

  J = dilational jog  (positive dilatation × shear × 2ndinv)
  S = basement step   (depth_to_base gradient × grav hg, gated on low det_elev_slope)
  A = alteration corridor (Th/K high × K depletion × cond breach via geodawn_rad)

Signature: geometric mean (J^0.4 * S^0.3 * A^0.3) gated on bend coherence.
This targets fault intersections / stepovers where permeability is maximal,
following Faulds et al. (Great Basin geothermal favorability, GBCGE INGENIOUS).

Why off-catalogue: catalogue mapped by surface scarps; triple junctions under
Lake Lahontan alluvium have no continuous scarp but host blind geothermal
conduits (e.g., Desert Peak, Brady's, McGinness Hills). SGMC alone misses jog
kinematics; jog alone misses alteration.

Mimic: felsic tuff contacts mimic Th/K; agricultural K masks depletion;
paleoshoreline notches mimic basement step.

Cost: ~60s CPU (training_features + 26 MB rad grids).
Leakage canary: solo AUC expected <0.65 (no distance-to-fault feature used).
"""

from __future__ import annotations
from pathlib import Path
import numpy as np
import rasterio
from scipy.ndimage import gaussian_filter
from .h83 import _read_band, _fill_nan, _robust_unit, _grad_mag, _structure_tensor_orientation

def build_h84(training_features: Path, foot: np.ndarray, geodawn_rad_path: Path) -> np.ndarray:
    # Load core bands
    dilate_raw = _read_band(training_features, 8)  # geod_dilaterate
    shear_raw = _read_band(training_features, 7)   # geod_shearrate
    inv_raw = _read_band(training_features, 4)     # geod_2ndinv
    depth_raw = _read_band(training_features, 15)  # depth_to_base_surf
    gravhg_raw = _read_band(training_features, 18) # iso_grav_anom_hg
    grav_raw = _read_band(training_features, 13)   # iso_grav_anom
    detelev_raw = _read_band(training_features, 12)
    slope_raw = _read_band(training_features, 19)  # det_elev_slope
    cond_raw = _read_band(training_features, 17)   # cond_surf
    tc_raw = _read_band(training_features, 6)      # tc

    dilate = _fill_nan(dilate_raw, foot)
    shear = _fill_nan(shear_raw, foot)
    inv = _fill_nan(inv_raw, foot)
    depth = _fill_nan(depth_raw, foot)
    gravhg = _fill_nan(gravhg_raw, foot)
    grav = _fill_nan(grav_raw, foot)
    detelev = _fill_nan(detelev_raw, foot)
    slope = _fill_nan(slope_raw, foot)
    cond = _fill_nan(cond_raw, foot)
    tc = _fill_nan(tc_raw, foot)

    # Component J: dilational jog opening (same as H83-A but simplified)
    dil_pos = np.where(dilate > 0, dilate, 0).astype(np.float32)
    dil_norm = _robust_unit(dil_pos, foot)
    dil_boost = np.clip(dil_pos / (np.percentile(dil_pos[foot], 95) + 1e-9), 0, 1).astype(np.float32)
    dil_open = (0.6*dil_norm + 0.4*dil_boost).astype(np.float32)
    shear_norm = _robust_unit(shear, foot)
    inv_norm = _robust_unit(inv, foot)
    strain_intensity = np.sqrt(shear_norm * np.maximum(inv_norm, 0)).astype(np.float32)
    strain_intensity = _robust_unit(strain_intensity, foot)
    opening = (dil_open * (0.5 + 0.5*strain_intensity)).astype(np.float32)
    J_core = opening * (0.3 + 0.7*strain_intensity)
    # Bend vote via structure tensor of detelev
    detelev_sm = gaussian_filter(detelev, 1.0, mode="nearest")
    coh, theta = _structure_tensor_orientation(detelev_sm, sigma=2.0)
    cos2t = np.cos(2*theta); sin2t = np.sin(2*theta)
    dcos = _grad_mag(cos2t); dsin = _grad_mag(sin2t)
    bend_raw = np.hypot(dcos, dsin).astype(np.float32) * np.clip(coh, 0, 1)
    bend_norm = _robust_unit(bend_raw, foot)
    bend_vote = np.power(np.clip(bend_norm,0,1), 0.7).astype(np.float32)
    bend_factor = (0.5 + 0.5*bend_vote).astype(np.float32)
    J = J_core * bend_factor
    J = _robust_unit(J, foot)
    J = np.power(J, 0.9).astype(np.float32)

    # Component S: basement step in flat piedmont
    depth_sm = gaussian_filter(depth, 1.5, mode="nearest")
    step_raw = _grad_mag(depth_sm)
    step_n = _robust_unit(step_raw, foot)
    gravhg_n = _robust_unit(np.abs(gravhg), foot)
    grav_n = _robust_unit(np.abs(grav), foot)
    step_comb = (0.6*step_n + 0.25*gravhg_n + 0.15*grav_n).astype(np.float32)
    # Gate on flatness: low det_elev_slope (lacustrine/piedmont)
    slope_n = _robust_unit(np.abs(slope), foot)
    flatness = 1.0 - slope_n
    flatness = np.power(flatness, 1.5).astype(np.float32)
    # Straightness via gradient direction coherence (3x3)
    gy, gx = np.gradient(depth_sm.astype(np.float32))
    mag = np.hypot(gx, gy) + 1e-9
    nx = gx/mag; ny = gy/mag
    coh_step = np.zeros_like(mag, dtype=np.float32)
    for dy in (-1,0,1):
        for dx in (-1,0,1):
            coh_step += np.roll(np.roll(nx, dy, 0), dx, 1)*nx + np.roll(np.roll(ny, dy,0),dx,1)*ny
    coh_step = coh_step/9.0
    straight = np.clip((coh_step - 0.5)/0.5, 0, 1).astype(np.float32)
    S = step_comb * flatness * np.power(straight, 0.9)
    S = _robust_unit(S, foot)

    # Component A: radiometric alteration + cond breach
    if geodawn_rad_path.exists():
        with rasterio.open(geodawn_rad_path) as ds:
            k = ds.read(1).astype(np.float32)
            th = ds.read(2).astype(np.float32) if ds.count>=2 else k
            # Handle outside values: rad grids are uint8 0-255 but footprint limited
            k = np.where(np.isfinite(k), k, 0)
            th = np.where(np.isfinite(th), th, 0)
            k_n = _robust_unit(k, foot)
            th_n = _robust_unit(th, foot)
            th_k = th / (k + 1)
            th_k_n = _robust_unit(th_k, foot)
            k_dep = 1.0 - k_n
            alter = k_dep * th_k_n
            alter_n = _robust_unit(alter, foot)
        cond_grad = _grad_mag(gaussian_filter(cond, 1.5, mode="nearest"))
        cond_edge = _robust_unit(cond_grad, foot)
        # Clay cap breach: alteration where conductivity edge high
        A = alter_n * (0.5 + 0.5*cond_edge)
        A = _robust_unit(A, foot)
        # Weight by depth: blind faults under thicker cover more likely missed
        depth_n = _robust_unit(depth, foot)
        A = A * (0.6 + 0.4*depth_n)
        A = _robust_unit(A, foot)
    else:
        A = np.ones(foot.shape, dtype=np.float32) * 0.5
        A[~foot]=0

    # Triple junction: geometric mean with learned exponents
    # Exponent weights from SGMC AUC: J 0.52, S 0.66, A 0.59 -> weight S higher
    # But for blind geothermal, A is diagnostic; we weight equally but slightly favor J
    # Use 0.4,0.3,0.3 as stated
    # Avoid zero: add small epsilon
    eps = 1e-6
    triple = np.power(np.clip(J, eps, 1), 0.4) * np.power(np.clip(S, eps, 1), 0.3) * np.power(np.clip(A, eps, 1), 0.3)
    triple = _robust_unit(triple, foot)
    # Enhance contrast: power 0.85
    triple = np.power(triple, 0.85).astype(np.float32)
    # Final: also include tc edge for magnetic contact displacement
    tc_n = _robust_unit(np.abs(tc), foot)
    triple = triple * (0.7 + 0.3*tc_n)
    triple = _robust_unit(triple, foot)
    triple[~foot]=0.0
    return triple.astype(np.float32)

def top_n_mask(surface: np.ndarray, foot: np.ndarray, n: int) -> np.ndarray:
    s = np.where(foot, np.asarray(surface, dtype=np.float32), -np.inf)
    flat = s.ravel()
    idx = np.argpartition(flat, -n)[-n:]
    m = np.zeros(flat.shape, dtype=bool); m[idx]=True
    return m.reshape(s.shape)

H84_SPEC = {
    "name": "Triple-junction blind geothermal conduit (J×S×A)",
    "layers": ["geod_dilaterate(8)", "geod_shearrate(7)", "geod_2ndinv(4)", "depth_to_base_surf(15)", "iso_grav_anom_hg(18)", "iso_grav_anom(13)", "det_elev(12)", "det_elev_slope(19)", "cond_surf(17)", "tc(6)", "geodawn_rad K/Th (external)", "tmi(14)"],
    "signature": "positive dilatation × shear × basement gravity step × lacustrine flatness × bend vote  (J)  ×  depth+grav ridge × straightness (S)  ×  Th/K high × K depletion × cond edge × depth (A)  => geometric mean J^0.4 S^0.3 A^0.3",
    "why_off_catalogue": "Catalogue is surface-scarp-led; triple junctions under 50-200 m Lahontan alluvium have no continuous scarp yet are prime blind geothermal traps (Faulds 2013; INGENIOUS). SGMC captures only S, jog captures opening kinematics, alteration captures hydrothermal halo — intersection is most specific for blind faults.",
    "novelty": "No prior channel combined jog kinematics + basement step flatness-gated + radiometric Th/K alteration as geometric mean; H33 used orientation consensus of six physics but not triple intersection; H83-A used jog alone, H83-B alteration alone, H83-C buried scarp alone.",
    "mimic": "Felsic tuff Th/K contacts; Fallon agricultural K; paleoshoreline notches; groundwater subsidence dilatation.",
    "cost": "~60s CPU",
}
