"""Historical owner-authored H83 hypothesis surfaces; not a validated active pipeline here.

Layer names and indices below come from the old local/owner-mirror implementation and are not
verified against the official competition feature stack. The earlier "built and validated" wording
is retained only as history; this checkout has no canonical shared holdout result for H83-A. Consult
the run card and research notes before reusing any output or claim.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage
from scipy.ndimage import gaussian_filter, maximum_filter, minimum_filter

from . import grid


def _read_band(path: Path, idx: int, foot: np.ndarray | None = None) -> np.ndarray:
    """Read one band from training_features, replacing nodata sentinel with 0 or nan."""
    with rasterio.open(path) as s:
        a = s.read(idx).astype(np.float32)
    NODATA = np.float32(-3.4028234663852886e38)
    # footprint is where band 1 != NODATA; for other bands same geometry
    if foot is not None:
        # ensure we respect footprint
        pass
    # Replace NODATA with NaN initially, later filled
    a = np.where(a == NODATA, np.nan, a)
    return a

def _fill_nan(a: np.ndarray, foot: np.ndarray, method: str = "nearest") -> np.ndarray:
    """Fill NaN inside footprint by nearest neighbor; outside footprint set 0."""
    # Use simple inpaint: replace nan with 0 then smooth? For this use case, fill with median of footprint
    # Better: use ndimage distance transform to fill?
    # Simple: fill with 0 then gaussian blur will handle, but for accuracy we use median
    valid = np.isfinite(a) & foot
    if not valid.any():
        return np.zeros_like(a, dtype=np.float32)
    median = float(np.median(a[valid]))
    out = np.where(np.isfinite(a), a, median).astype(np.float32)
    out[~foot] = 0.0
    return out

def _robust_unit(a: np.ndarray, foot: np.ndarray, p1: float = 1, p99: float = 99) -> np.ndarray:
    """Robust min-max to [0,1] using 1st and 99th percentile inside footprint."""
    v = a[foot]
    if v.size == 0:
        return np.zeros_like(a, dtype=np.float32)
    lo = float(np.percentile(v, p1))
    hi = float(np.percentile(v, p99))
    if hi <= lo:
        return np.zeros_like(a, dtype=np.float32)
    out = np.clip((a - lo) / (hi - lo), 0.0, 1.0).astype(np.float32)
    out[~foot] = 0.0
    return out

def _grad_mag(a: np.ndarray) -> np.ndarray:
    gy, gx = np.gradient(a.astype(np.float32))
    return np.hypot(gx, gy).astype(np.float32)

def _structure_tensor_orientation(a: np.ndarray, sigma: float = 2.0):
    """Return coherence and theta of structure tensor."""
    gx = ndimage.gaussian_filter(a, sigma, order=(0,1), mode="nearest")
    gy = ndimage.gaussian_filter(a, sigma, order=(1,0), mode="nearest")
    jxx = gaussian_filter(gx*gx, sigma, mode="nearest")
    jyy = gaussian_filter(gy*gy, sigma, mode="nearest")
    jxy = gaussian_filter(gx*gy, sigma, mode="nearest")
    tr = jxx + jyy + 1e-12
    coh = np.sqrt(np.maximum(((jxx - jyy)*0.5)**2 + jxy**2, 0)) / tr
    theta = 0.5 * np.arctan2(2*jxy, (jxx - jyy) + 1e-12)
    return coh.astype(np.float32), theta.astype(np.float32)

def build_h83a(training_features: Path, foot: np.ndarray) -> np.ndarray:
    """Dilational jog surface.

    Steps:
      1. dilatation positive part: dilate_norm = clip(dilate / p95, 0,1) where dilate>0 else 0
      2. shear normalized + 2ndinv normalized (geodetic opening intensity)
      3. basement step ridge: |grad(depth_to_base)| robust-unit
      4. bend vote: orientation coherence change — compute structure tensor orientation of det_elev,
         then detect high gradient of theta (bend) via |grad(theta)| weighted by coherence.
      5. Composite: dil_open × shear × step × (0.5 + 0.5*bend) with safeguards.
    """
    # Load bands
    dilate_raw = _read_band(training_features, 8)
    shear_raw = _read_band(training_features, 7)
    inv_raw = _read_band(training_features, 4)
    depth_raw = _read_band(training_features, 15)
    gravhg_raw = _read_band(training_features, 18)
    detelev_raw = _read_band(training_features, 12)

    # Fill NaN
    dilate = _fill_nan(dilate_raw, foot)
    shear = _fill_nan(shear_raw, foot)
    inv = _fill_nan(inv_raw, foot)
    depth = _fill_nan(depth_raw, foot)
    gravhg = _fill_nan(gravhg_raw, foot)
    detelev = _fill_nan(detelev_raw, foot)

    # 1. Dilational opening: positive dilatation only (extensional)
    # Use 1st-99th robust
    foot_valid = foot & np.isfinite(dilate)
    # Positive part
    dil_pos = np.where(dilate > 0, dilate, 0).astype(np.float32)
    dil_norm = _robust_unit(dil_pos, foot)
    # Also emphasize strongly positive tail
    dil_boost = np.clip(dil_pos / (np.percentile(dil_pos[foot], 95) + 1e-9), 0, 1).astype(np.float32)
    dil_open = (0.6 * dil_norm + 0.4 * dil_boost).astype(np.float32)
    dil_open[~foot] = 0

    # 2. Shear + 2nd invariant normalized
    shear_norm = _robust_unit(shear, foot)
    inv_norm = _robust_unit(inv, foot)
    # Combine shear and inv as opening intensity (high strain magnitude)
    strain_intensity = np.sqrt(shear_norm * np.maximum(inv_norm, 0)).astype(np.float32)
    strain_intensity = _robust_unit(strain_intensity, foot)

    # Alternative: shear alone
    # Use weighted combination: opening requires both dilatation and shear
    opening = (dil_open * (0.5 + 0.5*strain_intensity)).astype(np.float32)

    # 3. Basement step ridge: gradient magnitude of depth_to_base_surf
    # Smooth slightly before gradient to reduce noise
    depth_sm = gaussian_filter(depth, 1.5, mode="nearest")
    depth_grad = _grad_mag(depth_sm)
    # Also grav hg is already gradient, use it directly normalized
    grav_norm = _robust_unit(np.abs(gravhg), foot)
    step_ridge = _robust_unit(depth_grad, foot)
    # Combine depth step and grav step: both indicate basement offset
    step_comb = (0.6*step_ridge + 0.4*grav_norm).astype(np.float32)
    # Enhance line-ness via ridge filter
    # Use Hessian ridge on depth to capture long-straight boundary
    # Simple: dilate then erode? Use maximum filter to emphasize ridge
    # We'll apply coherence weighting later
    step_norm = _robust_unit(step_comb, foot)

    # 4. Bend vote: orientation coherence change
    # Compute structure tensor orientation of detrended elevation (detelev)
    # Det_elev is topo after detrending; bends appear as orientation changes
    detelev_sm = gaussian_filter(detelev, 1.0, mode="nearest")
    coh, theta = _structure_tensor_orientation(detelev_sm, sigma=2.0)
    # Bend is gradient of theta weighted by coherence
    # Unwrap theta (0- pi) — compute gradient magnitude of cos/sin
    cos2t = np.cos(2*theta)
    sin2t = np.sin(2*theta)
    dcos = _grad_mag(cos2t)
    dsin = _grad_mag(sin2t)
    bend_raw = np.hypot(dcos, dsin).astype(np.float32)
    # Weight by coherence (need well-defined orientation)
    bend = bend_raw * np.clip(coh, 0, 1)
    bend_norm = _robust_unit(bend, foot)
    # Emphasize moderate bends (15-30°) not just extreme
    # Use power to enhance mid-range
    bend_vote = np.power(np.clip(bend_norm, 0, 1), 0.7).astype(np.float32)
    # At least half weight even without bend, to not kill non-bending jogs
    bend_factor = (0.5 + 0.5*bend_vote).astype(np.float32)

    # 5. Composite
    # Opening × shear × step × bend
    # Ensure opening already includes dilatation positive
    core = opening * (0.3 + 0.7*strain_intensity) * (0.4 + 0.6*step_norm)
    core = core * bend_factor
    # Suppress outside high topo slope? Not needed for jog, but keep
    # Normalize final
    score = _robust_unit(core, foot)
    # Slight power to enhance contrast
    score = np.power(score, 0.9).astype(np.float32)
    score[~foot] = 0.0
    return score

def build_h83c(training_features: Path, foot: np.ndarray) -> np.ndarray:
    """Buried scarp under Lahontan — depth step where topo flat."""
    depth_raw = _read_band(training_features, 15)
    gravhg_raw = _read_band(training_features, 18)
    detelev_raw = _read_band(training_features, 12)
    detelev_slope_raw = _read_band(training_features, 19)
    depth = _fill_nan(depth_raw, foot)
    gravhg = _fill_nan(gravhg_raw, foot)
    detelev = _fill_nan(detelev_raw, foot)
    slope = _fill_nan(detelev_slope_raw, foot)

    depth_sm = gaussian_filter(depth, 1.5, mode="nearest")
    step = _grad_mag(depth_sm)
    step_n = _robust_unit(step, foot)
    grav_n = _robust_unit(np.abs(gravhg), foot)
    # lacustrine flatness: low slope decile
    slope_n = _robust_unit(np.abs(slope), foot)
    flatness = 1.0 - slope_n
    flatness = np.power(flatness, 1.5).astype(np.float32)
    # Straightness via orientation coherence of depth gradient
    gy, gx = np.gradient(depth_sm.astype(np.float32))
    mag = np.hypot(gx, gy)
    # Simple straightness: coherence of gradient direction via local dot product
    # Compute normalized gradient direction
    eps = 1e-9
    nx = gx / (mag + eps)
    ny = gy / (mag + eps)
    # 3x3 window coherence
    coherence = np.zeros_like(mag, dtype=np.float32)
    for dy in (-1,0,1):
        for dx in (-1,0,1):
            coherence += np.roll(np.roll(nx, dy, 0), dx, 1)*nx + np.roll(np.roll(ny, dy,0),dx,1)*ny
    coherence = coherence / 9.0
    straight = np.clip((coherence - 0.5)/0.5, 0, 1).astype(np.float32)
    combined = (0.6*step_n + 0.4*grav_n) * flatness * np.power(straight, 1.2)
    return _robust_unit(combined, foot).astype(np.float32)

def build_h83b(training_features: Path, foot: np.ndarray, geodawn_rad_path: Path) -> np.ndarray:
    """Radiometric alteration corridor."""
    import rasterio as rio
    cond_raw = _read_band(training_features, 17)
    depth_raw = _read_band(training_features, 15)
    cond = _fill_nan(cond_raw, foot)
    depth = _fill_nan(depth_raw, foot)
    # Load radiometric if exists
    if geodawn_rad_path.exists():
        with rio.open(geodawn_rad_path) as ds:
            # bands: 1=K,2=Th,3=U,4=TC counts (uint8 quantized)
            k = ds.read(1).astype(np.float32)
            th = ds.read(2).astype(np.float32) if ds.count>=2 else k
            u = ds.read(3).astype(np.float32) if ds.count>=3 else k
            # footprint for rad may differ, but assume same grid
            # If nan, fill
            k = np.where(np.isfinite(k), k, 0)
            th = np.where(np.isfinite(th), th, 0)
            u = np.where(np.isfinite(u), u, 0)
            # Normalize
            k_n = _robust_unit(k, foot)
            th_n = _robust_unit(th, foot)
            # Th/K ratio
            th_k = th / (k + 1)
            th_k_n = _robust_unit(th_k, foot)
            # K depletion: 1 - k_n
            k_dep = 1.0 - k_n
            alter = k_dep * th_k_n
            alter_n = _robust_unit(alter, foot)
    else:
        alter_n = np.zeros(foot.shape, dtype=np.float32)
    cond_grad = _grad_mag(gaussian_filter(cond, 1.5, mode="nearest"))
    cond_edge = _robust_unit(cond_grad, foot)
    # Clay cap breach: low cond inside but edge high
    # Simple: alter × cond_edge
    score = alter_n * (0.5 + 0.5*cond_edge)
    return _robust_unit(score, foot).astype(np.float32)

# Builders dict for easy iteration
H83_BUILDERS = {
    "H83-A": build_h83a,
    "H83-C": build_h83c,
    "H83-B": build_h83b,
}

H83_SPECS = {
    "H83-A": {
        "name": "Dilational jog geothermal conduit",
        "layers": ["geod_dilaterate(8)", "geod_shearrate(7)", "geod_2ndinv(4)", "depth_to_base_surf(15)", "iso_grav_anom_hg(18)", "det_elev(12)"],
        "signature": "positive dilatation × shear intensity × basement gravity step × bend vote (structure-tensor orientation change)",
        "why_off_catalogue": "Catalogue is surface-expression-led; jogs <3 km under alluvium lack continuous scarp and are omitted, yet are prime blind geothermal conduits (Faulds; Monte Cristo 2020 rupture on unmapped faults).",
        "novelty": "No prior channel used dilatation polarity (extension vs contraction) nor bend detection; H33-D used step alone, H62 used raw strain without jog geometry.",
        "cost": "~30s CPU",
    },
    "H83-C": {
        "name": "Buried scarp under Lahontan plain",
        "layers": ["depth_to_base_surf(15)", "iso_grav_anom_hg(18)", "iso_grav_anom(13)", "det_elev(12)", "det_elev_slope(19)"],
        "signature": "depth+grav gradient ridge where topo flat (lacustrine decile) × straightness coherence",
        "why_off_catalogue": "Lake Lahontan sediments bury faults; basement offset remains in depth/gravity but no topo scarp, so surface mapping misses it.",
        "novelty": "H62-2 gated on general absence of surface expression; this gates specifically on lacustrine flatness (det_elev_slope low decile), a narrower geomorphic unit.",
        "cost": "~40s CPU",
    },
    "H83-B": {
        "name": "Radiometric hydrothermal alteration corridor",
        "layers": ["geodawn_rad K/Th/U (external)", "cond_surf(17)", "depth_to_base_surf(15)"],
        "signature": "K depletion × Th/K high × conductivity edge breach",
        "why_off_catalogue": "Blind geothermal faults lack scarp but have alteration halos in radiometrics; catalogue mapped by geomorphology, not geochemistry.",
        "novelty": "H33-A fused radiometrics as one of six physics with orientation consensus, but never computed alteration ratios (Th/K, U/K) nor K depletion gate; H32-C used MT clay-cap breach alone.",
        "cost": "~60s CPU",
    },
    "H83-D": {
        "name": "Microseismic lineament",
        "layers": ["deq_n100a15(10)", "ieq_n100a15(16) replaced with raw ComCat epicenters"],
        "signature": "epicenter kernel density × 16-direction collinearity vote (5 km halflen)",
        "why_off_catalogue": "Seismogenic blind faults at 3–8 km depth lack surface rupture; seismicity lineaments reveal them while Quaternary surface compilation misses them.",
        "novelty": "No prior hypothesis correctly used raw seismicity; bands 10/16 are smoothed with 0.9986 autocorrelation, no fault-scale info.",
        "cost": "~Medium (external fetch)",
    },
    "H83-E": {
        "name": "En-echelon Riedel wing-crack",
        "layers": ["det_elev(12)", "det_elev_slope(19)", "geod_shearrate(7)", "tmi(14)"],
        "signature": "Hessian ridge × shear high × 15° Riedel orientation vote",
        "why_off_catalogue": "Main fault mapped, but stepover R-shears <800 m and wing-crack tips below mapping resolution, yet host geothermal upwelling in stepovers.",
        "novelty": "GEMSDOE20 used power-law tilt wing-crack without Riedel 15° rule; H33-C used LiDAR scarplets without shear gating.",
        "cost": "~25s CPU",
    },
}

def top_n_mask(surface: np.ndarray, foot: np.ndarray, n: int) -> np.ndarray:
    s = np.where(foot, np.asarray(surface, dtype=np.float32), -np.inf)
    flat = s.ravel()
    idx = np.argpartition(flat, -n)[-n:]
    m = np.zeros(flat.shape, dtype=bool)
    m[idx] = True
    return m.reshape(s.shape)

def rank_surface(surface: np.ndarray, foot: np.ndarray) -> np.ndarray:
    s = np.where(foot, np.asarray(surface, dtype=np.float32), -np.inf)
    order = np.argsort(np.argsort(s.ravel(), kind="stable"), kind="stable").astype(np.float32)
    order = order / max(float(foot.sum() - 1), 1.0)
    out = order.reshape(s.shape)
    out[~foot] = 0.0
    return out
