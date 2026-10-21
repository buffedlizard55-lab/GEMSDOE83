"""Feature engineering for Lane H83-GVCD (GEMSDOE83).

Strictly label-free physical / geothermal / radiometric / LiDAR channels +
fold-proper visible-catalogue structural-relay & geothermal-coupling channels.
Never reads `labels.tif`, `hidden`, `truth`, or `dist_known_fault_px`.
Memory-disciplined streaming implementation keeping peak RSS < 1.2 GB on a 3.9 GB container.
"""
from __future__ import annotations

import gc
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import rasterio
from scipy import ndimage as ndi
from scipy.signal import oaconvolve

TRAINING_BAND_NAMES: Tuple[str, ...] = (
    "mag_anomaly_deviation",
    "mag_reduced_to_pole",
    "tmi_horizontal_gradient",
    "geodetic_second_invariant",
    "iso_gravity_slope",
    "tilt_angle_total_curvature",
    "geodetic_shear_rate",
    "geodetic_dilatation_rate",
    "tmi_vertical_gradient",
    "distance_to_earthquake",
    "iso_gravity_vertical_gradient",
    "detrended_elevation",
    "iso_gravity_anomaly",
    "total_magnetic_intensity",
    "depth_to_basement",
    "earthquake_density",
    "conductivity_surface",
    "iso_gravity_horizontal_gradient",
    "detrended_elevation_slope",
)

GRAD_BAND_INDICES: Tuple[int, ...] = (0, 1, 3, 6, 7, 11, 12, 14, 15, 16, 17, 18)
STD5_BAND_INDICES: Tuple[int, ...] = (0, 6, 11, 12, 14, 16, 18)

EXTERNAL_PHYSICAL_NAMES: Tuple[str, ...] = (
    "geotherm_temp_excess_s8",
    "geotherm_temp_excess_s20",
    "geotherm_quartz_s10",
    "geotherm_quartz_s24",
    "geotherm_chalcedony_s12",
    "geotherm_cation_s12",
    "geotherm_composite_plume",
    "volcanic_vent_density_s25",
    "rad_K_z",
    "rad_Th_z",
    "rad_U_z",
    "rad_TC_z",
    "rad_ThK_z",
    "rad_UK_z",
    "rad_k_metasomatism",
    "mag_up150_shallow_residual",
    "lidar_scarp_max_z",
    "lidar_step_max_z",
    "lidar_relief_norm_scarp",
    "lidar_scarp_coherence",
)

INTERACTION_PHYSICAL_NAMES: Tuple[str, ...] = (
    "x_strain_transtension",
    "x_grav_basement_step",
    "mag_shallow_ridge",
    "geotherm_claycap_conduit",
)

STRUCTURAL_NETWORK_NAMES: Tuple[str, ...] = (
    "ns_logdist",
    "ns_den4",
    "ns_den12",
    "ns_den32",
    "ns_cont",
    "ns_gap",
    "ns_sib",
    "ns_cont_max",
    "ns_sib_max",
    "ns_coh",
    "net_beam_short",
    "net_beam_med",
    "net_beam_long",
    "net_bridge_med",
    "net_bridge_long",
    "net_tip_ray",
    "net_ann_near",
    "net_ann_far",
)

COUPLING_INTERACTION_NAMES: Tuple[str, ...] = (
    "coup_geotherm_tip",
    "coup_geotherm_gap",
    "coup_lidar_cont",
    "coup_strain_sib",
)

STRUCT8 = np.ones((3, 3), dtype=bool)
N_STRIKE_BINS = 12
R_KERNEL = 25


PHYSICAL_CHANNEL_NAMES: Tuple[str, ...] = (
    "z_mag_anomaly_deviation",
    "z_mag_reduced_to_pole",
    "z_tmi_horizontal_gradient",
    "z_geodetic_second_invariant",
    "z_iso_gravity_slope",
    "z_tilt_angle_total_curvature",
    "z_geodetic_shear_rate",
    "z_geodetic_dilatation_rate",
    "z_tmi_vertical_gradient",
    "z_distance_to_earthquake",
    "z_iso_gravity_vertical_gradient",
    "z_detrended_elevation",
    "z_iso_gravity_anomaly",
    "z_total_magnetic_intensity",
    "z_depth_to_basement",
    "z_earthquake_density",
    "z_conductivity_surface",
    "z_iso_gravity_horizontal_gradient",
    "z_detrended_elevation_slope",
    "grad_mag_reduced_to_pole",
    "grad_tilt_angle_total_curvature",
    "grad_detrended_elevation",
    "grad_iso_gravity_anomaly",
    "grad_total_magnetic_intensity",
    "grad_depth_to_basement",
    "grad_conductivity_surface",
    "grad_detrended_elevation_slope",
    "lap_tilt_angle_total_curvature",
    "lap_detrended_elevation",
    "lap_iso_gravity_anomaly",
    "lap_total_magnetic_intensity",
    "lap_depth_to_basement",
    "lap_conductivity_surface",
    "ridge_mag_reduced_to_pole",
    "ridge_tilt_angle_total_curvature",
    "ridge_detrended_elevation",
    "ridge_iso_gravity_anomaly",
    "ridge_total_magnetic_intensity",
    "ridge_depth_to_basement",
    "ridge_conductivity_surface",
    "ridge_detrended_elevation_slope",
    "std5_tilt_angle_total_curvature",
    "std5_detrended_elevation",
    "std5_total_magnetic_intensity",
    "std5_conductivity_surface",
    "x_couple_tmi_dem",
    "x_couple_tmi_grav",
    "x_ridge_dem_slope",
    "x_strain_transtension",
    "geotherm_vent_plume_s6",
    "geotherm_vent_plume_s18",
    "geotherm_reservoir_enthalpy",
    "geotherm_claycap_conduit",
    "rad_k_metasomatism",
    "rad_u_redox_halo",
    "rad_tc_grad",
    "mag_shallow_residual",
    "mag_shallow_ridge",
    "lidar_relief_norm_scarp",
    "lidar_scarp_coherence",
)


def physical_channel_names() -> List[str]:
    return list(PHYSICAL_CHANNEL_NAMES)


def all_channel_names() -> List[str]:
    return physical_channel_names() + list(STRUCTURAL_NETWORK_NAMES) + list(COUPLING_INTERACTION_NAMES)


def _robust_z_flat(vec: np.ndarray) -> np.ndarray:
    med = float(np.median(vec))
    mad = float(np.median(np.abs(vec - med)))
    scale = max(1.4826 * mad, float(np.std(vec)), 1e-6)
    return np.clip((vec - med) / scale, -8.0, 8.0).astype(np.float32)


def _fill_band(arr: np.ndarray, footprint: np.ndarray) -> np.ndarray:
    out = arr.astype(np.float32, copy=True)
    bad = ~np.isfinite(out) | (np.abs(out) > 1e20)
    valid_fp = footprint & ~bad
    med = float(np.median(out[valid_fp])) if valid_fp.any() else 0.0
    out[bad] = med
    out[~footprint] = med
    return out


def _rasterize_geothermal_and_vents(
    raw_dir: Path, shape: Tuple[int, int], transform, footprint: np.ndarray
) -> Dict[str, np.ndarray]:
    import csv

    H, W = shape
    x0 = float(transform.c)
    dx = float(transform.a)
    y0 = float(transform.f)
    dy = float(transform.e)

    temp_grid = np.zeros((H, W), dtype=np.float32)
    qtz_grid = np.zeros((H, W), dtype=np.float32)
    chal_grid = np.zeros((H, W), dtype=np.float32)
    cat_grid = np.zeros((H, W), dtype=np.float32)

    ws_path = raw_dir / "external" / "gdr_wellspring_in_footprint.csv"
    with ws_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                ux = float(row["utm_e"])
                uy = float(row["utm_n"])
            except (KeyError, ValueError):
                continue
            col = int((ux - x0) / dx)
            r = int((uy - y0) / dy)
            if not (0 <= r < H and 0 <= col < W):
                continue
            try:
                tc = float(row.get("temp_c", "") or "nan")
                if np.isfinite(tc) and 15.0 < tc < 400.0:
                    excess = max(0.0, tc - 15.0)
                    if excess > temp_grid[r, col]:
                        temp_grid[r, col] = excess
            except ValueError:
                pass
            for key, grid_arr in (
                ("gt_quartz_c", qtz_grid),
                ("gt_chalcedony_c", chal_grid),
                ("gt_na_k_ca_c", cat_grid),
            ):
                try:
                    val = float(row.get(key, "") or "nan")
                    if np.isfinite(val) and 25.0 < val < 450.0:
                        ex = max(0.0, val - 25.0)
                        if ex > grid_arr[r, col]:
                            grid_arr[r, col] = ex
                except ValueError:
                    pass

    vent_grid = np.zeros((H, W), dtype=np.float32)
    vv_path = raw_dir / "external" / "gdr_volcanic_vents_in_footprint.csv"
    with vv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                ux = float(row["utm_e"])
                uy = float(row["utm_n"])
            except (KeyError, ValueError):
                continue
            col = int((ux - x0) / dx)
            r = int((uy - y0) / dy)
            if 0 <= r < H and 0 <= col < W:
                vent_grid[r, col] += 1.0

    t_s8 = _robust_z_flat(np.log1p(ndi.gaussian_filter(temp_grid, sigma=8.0)[footprint]))
    t_s20 = _robust_z_flat(np.log1p(ndi.gaussian_filter(temp_grid, sigma=20.0)[footprint]))
    del temp_grid
    q_s10 = _robust_z_flat(np.log1p(ndi.gaussian_filter(qtz_grid, sigma=10.0)[footprint]))
    q_s24 = _robust_z_flat(np.log1p(ndi.gaussian_filter(qtz_grid, sigma=24.0)[footprint]))
    del qtz_grid
    ch_s12 = _robust_z_flat(np.log1p(ndi.gaussian_filter(chal_grid, sigma=12.0)[footprint]))
    del chal_grid
    ca_s12 = _robust_z_flat(np.log1p(ndi.gaussian_filter(cat_grid, sigma=12.0)[footprint]))
    del cat_grid
    vv_s25 = _robust_z_flat(np.log1p(ndi.gaussian_filter(vent_grid, sigma=25.0)[footprint]))
    del vent_grid
    comp = _robust_z_flat(0.35 * t_s8 + 0.25 * t_s20 + 0.20 * q_s10 + 0.10 * ch_s12 + 0.10 * ca_s12)

    return {
        "geotherm_temp_excess_s8": t_s8,
        "geotherm_temp_excess_s20": t_s20,
        "geotherm_quartz_s10": q_s10,
        "geotherm_quartz_s24": q_s24,
        "geotherm_chalcedony_s12": ch_s12,
        "geotherm_cation_s12": ca_s12,
        "geotherm_composite_plume": comp,
        "volcanic_vent_density_s25": vv_s25,
    }


def build_or_load_physical_stack(
    raw_dir: Path, footprint: np.ndarray, cache_path: Path
) -> Tuple[List[str], np.ndarray]:
    """Stream or load the 60 label-free physical channels over `footprint`."""
    names = physical_channel_names()
    n_ch = len(names)
    n_px = int(footprint.sum())
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    meta_path = cache_path.with_suffix(".names.txt")

    if cache_path.exists() and meta_path.exists():
        cached_names = [line.strip() for line in meta_path.read_text().splitlines() if line.strip()]
        if cached_names == names:
            mm = np.load(cache_path, mmap_mode="r")
            if mm.shape == (n_ch, n_px):
                return names, mm

    raise RuntimeError("Physical stack cache missing or mismatched; run build script first.")


def load_or_build_rowmajor_f16(
    raw_dir: Path, footprint: np.ndarray, proc_dir: Path
) -> Tuple[List[str], np.ndarray]:
    """Return `(names, X_rm_f16)` where `X_rm_f16` has shape `(n_fp, 60)`."""
    names = physical_channel_names()
    rm_path = proc_dir / "h83_phys_rm.f16"
    if rm_path.exists():
        mm = np.load(rm_path, mmap_mode="r")
        if mm.shape == (int(footprint.sum()), len(names)):
            return names, mm
    _, col_mm = build_or_load_physical_stack(raw_dir, footprint, proc_dir / "h83_phys_stack.f32")
    n_ch, n_px = col_mm.shape
    mm_rm = np.lib.format.open_memmap(rm_path, mode="w+", dtype=np.float16, shape=(n_px, n_ch))
    step = 500_000
    for a in range(0, n_px, step):
        b = min(a + step, n_px)
        mm_rm[a:b, :] = np.asarray(col_mm[:, a:b], dtype=np.float16).T
    mm_rm.flush()
    del mm_rm, col_mm
    gc.collect()
    return names, np.load(rm_path, mmap_mode="r")


def _strike_field(mask: np.ndarray) -> np.ndarray:
    """Line direction theta in [0, pi) from structure tensor of smoothed mask."""
    i = ndi.gaussian_filter(mask.astype(np.float32), 1.0)
    gy = ndi.sobel(i, axis=0)
    gx = ndi.sobel(i, axis=1)
    jxx = ndi.gaussian_filter(gx * gx, 3.0)
    jyy = ndi.gaussian_filter(gy * gy, 3.0)
    jxy = ndi.gaussian_filter(gx * gy, 3.0)
    phi = 0.5 * np.arctan2(2.0 * jxy, jxx - jyy)
    theta = np.mod(phi + np.pi / 2.0, np.pi)
    return theta.astype(np.float32)


def _oriented_kernels(theta: float, r: int = R_KERNEL) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    dy, dx = np.mgrid[-r : r + 1, -r : r + 1].astype(np.float32)
    ux, uy = np.cos(theta), np.sin(theta)
    along = dx * ux + dy * uy
    across = -dx * uy + dy * ux
    lat = np.exp(-0.5 * (across / 1.5) ** 2) * np.exp(-np.abs(along) / 12.0) * (np.abs(along) <= 25)
    kf = (lat * (along > 0.5)).astype(np.float32)
    kb = (lat * (along < -0.5)).astype(np.float32)
    ks = ((np.abs(across) >= 4) & (np.abs(across) <= 20) & (np.abs(along) <= 15)).astype(np.float32)
    ks *= np.exp(-0.5 * (along / 8.0) ** 2).astype(np.float32)
    kf /= kf.sum()
    kb /= kb.sum()
    ks /= ks.sum()
    return kf, kb, ks


def compute_structural_network_features(
    visible_mask: np.ndarray, footprint: np.ndarray
) -> Dict[str, np.ndarray]:
    """Compute all 18 fold-proper visible-catalogue structural-relay features.

    Strictly derived from `visible_mask` ONLY — never touches withheld truth!
    Combines:
      1. 10 continuous 2D FFT (`oaconvolve`) oriented continuation/gap/sibling/coherence fields
      2. 8 hollow-core ($s >= 4$ px) directional ray/tip/bridge/annular fields
    """
    m = np.asarray(visible_mask, dtype=bool) & np.asarray(footprint, dtype=bool)
    fp = np.asarray(footprint, dtype=bool)
    out: Dict[str, np.ndarray] = {}

    # Part A: 10 continuous 2D FFT oriented network fields
    out["ns_logdist"] = np.log1p(ndi.distance_transform_edt(~m)).astype(np.float32)
    mf = m.astype(np.float32)
    for s in (4, 12, 32):
        out[f"ns_den{s}"] = ndi.gaussian_filter(mf, float(s)).astype(np.float32)

    theta = _strike_field(m)
    bins = np.minimum((theta / np.pi * N_STRIKE_BINS).astype(np.int16), N_STRIKE_BINS - 1)
    cont = np.zeros(m.shape, np.float32)
    gap = np.zeros(m.shape, np.float32)
    sib = np.zeros(m.shape, np.float32)
    cont_max = np.zeros(m.shape, np.float32)
    sib_max = np.zeros(m.shape, np.float32)
    for k in range(N_STRIKE_BINS):
        mk = (m & (bins == k)).astype(np.float32)
        if not mk.any():
            continue
        kf, kb, ks = _oriented_kernels((k + 0.5) * np.pi / N_STRIKE_BINS)
        f = np.maximum(oaconvolve(mk, kf, mode="same"), 0.0).astype(np.float32)
        b = np.maximum(oaconvolve(mk, kb, mode="same"), 0.0).astype(np.float32)
        s = np.maximum(oaconvolve(mk, ks, mode="same"), 0.0).astype(np.float32)
        c = f + b
        cont += c
        gap += np.sqrt(f * b)
        sib += s
        np.maximum(cont_max, c, out=cont_max)
        np.maximum(sib_max, s, out=sib_max)
        del f, b, s, c, mk
    out.update(ns_cont=cont, ns_gap=gap, ns_sib=sib, ns_cont_max=cont_max, ns_sib_max=sib_max)

    c2 = ndi.gaussian_filter(mf * np.cos(2 * theta), 20.0)
    s2 = ndi.gaussian_filter(mf * np.sin(2 * theta), 20.0)
    den = ndi.gaussian_filter(mf, 20.0)
    out["ns_coh"] = (np.hypot(c2, s2) / (den + 1e-6) * (den > 1e-4)).astype(np.float32)
    del theta, bins, c2, s2, den
    gc.collect()

    # Part B: 8 hollow-core (s >= 4 px) directional tip/beam/bridge/annular fields
    gy = ndi.sobel(mf, axis=0)
    gx = ndi.sobel(mf, axis=1)
    strike = np.arctan2(-gx, gy)
    del gy, gx
    nb_count = ndi.convolve(mf, np.ones((3, 3), dtype=np.float32), mode="constant", cval=0.0)
    tips = m & (nb_count >= 1.5) & (nb_count <= 3.5)
    del nb_count

    beam_short = np.zeros(m.shape, dtype=np.float32)
    beam_med = np.zeros(m.shape, dtype=np.float32)
    beam_long = np.zeros(m.shape, dtype=np.float32)
    bridge_med = np.zeros(m.shape, dtype=np.float32)
    bridge_long = np.zeros(m.shape, dtype=np.float32)
    tip_ray = np.zeros(m.shape, dtype=np.float32)

    for k in range(8):
        ang = k * (np.pi / 8.0)
        align = np.abs(np.cos(strike - ang))
        oriented = np.where(m & (align > 0.78), mf, 0.0).astype(np.float32)
        oriented_tips = np.where(tips & (align > 0.72), 1.0, 0.0).astype(np.float32)
        del align
        dy, dx = np.sin(ang), np.cos(ang)

        f_s = np.zeros(m.shape, dtype=np.float32)
        b_s = np.zeros(m.shape, dtype=np.float32)
        f_m = np.zeros(m.shape, dtype=np.float32)
        b_m = np.zeros(m.shape, dtype=np.float32)
        f_l = np.zeros(m.shape, dtype=np.float32)
        b_l = np.zeros(m.shape, dtype=np.float32)
        t_r = np.zeros(m.shape, dtype=np.float32)

        for s in (4, 6, 8, 10, 12, 16, 20, 26, 32, 40):
            r_off = int(round(s * dy))
            c_off = int(round(s * dx))
            sh_f = np.roll(oriented, (r_off, c_off), axis=(0, 1))
            sh_b = np.roll(oriented, (-r_off, -c_off), axis=(0, 1))
            if s <= 12:
                ws = float(np.exp(-s / 8.0))
                f_s += ws * sh_f
                b_s += ws * sh_b
            if s <= 26:
                wm = float(np.exp(-s / 16.0))
                f_m += wm * sh_f
                b_m += wm * sh_b
            wl = float(np.exp(-s / 28.0))
            f_l += wl * sh_f
            b_l += wl * sh_b
            if s <= 26:
                wt = float(np.exp(-s / 14.0))
                t_r += wt * (
                    np.roll(oriented_tips, (r_off, c_off), axis=(0, 1))
                    + np.roll(oriented_tips, (-r_off, -c_off), axis=(0, 1))
                )

        del oriented, oriented_tips
        f_s = ndi.gaussian_filter(f_s, sigma=1.2)
        b_s = ndi.gaussian_filter(b_s, sigma=1.2)
        f_m = ndi.gaussian_filter(f_m, sigma=1.8)
        b_m = ndi.gaussian_filter(b_m, sigma=1.8)
        f_l = ndi.gaussian_filter(f_l, sigma=2.5)
        b_l = ndi.gaussian_filter(b_l, sigma=2.5)
        t_r = ndi.gaussian_filter(t_r, sigma=1.8)

        np.maximum(beam_short, f_s + b_s, out=beam_short)
        np.maximum(beam_med, f_m + b_m, out=beam_med)
        np.maximum(beam_long, f_l + b_l, out=beam_long)
        np.maximum(bridge_med, np.sqrt(f_m * b_m), out=bridge_med)
        np.maximum(bridge_long, np.sqrt(f_l * b_l), out=bridge_long)
        np.maximum(tip_ray, t_r, out=tip_ray)
        del f_s, b_s, f_m, b_m, f_l, b_l, t_r

    del strike, tips
    ann_near = np.maximum(
        0.0, ndi.gaussian_filter(mf, sigma=7.0) - 0.85 * ndi.gaussian_filter(mf, sigma=2.0)
    ).astype(np.float32)
    ann_far = np.maximum(
        0.0, ndi.gaussian_filter(mf, sigma=18.0) - 0.85 * ndi.gaussian_filter(mf, sigma=4.0)
    ).astype(np.float32)

    raw_hollow = {
        "net_beam_short": beam_short,
        "net_beam_med": beam_med,
        "net_beam_long": beam_long,
        "net_bridge_med": bridge_med,
        "net_bridge_long": bridge_long,
        "net_tip_ray": tip_ray,
        "net_ann_near": ann_near,
        "net_ann_far": ann_far,
    }
    for k, arr in raw_hollow.items():
        z_arr = np.zeros(m.shape, dtype=np.float32)
        z_arr[fp] = _robust_z_flat(arr[fp])
        out[k] = z_arr
    for k in ("ns_logdist", "ns_den4", "ns_den12", "ns_den32", "ns_cont", "ns_gap", "ns_sib", "ns_cont_max", "ns_sib_max", "ns_coh"):
        out[k] = np.where(fp, out[k], 0.0).astype(np.float32)
    del raw_hollow
    gc.collect()
    return out


def compute_structural_and_coupling_fp(
    visible_mask: np.ndarray,
    footprint: np.ndarray,
    X_phys_rm: np.ndarray,
    phys_names: List[str],
    cache_path: Path | None = None,
) -> np.ndarray:
    """Compute or load the `(n_fp, 22)` float16 matrix of 18 structural + 4 geothermal/physical coupling features."""
    n_fp = int(footprint.sum())
    n_cols = len(STRUCTURAL_NETWORK_NAMES) + len(COUPLING_INTERACTION_NAMES)
    if cache_path is not None and cache_path.exists():
        mm = np.load(cache_path, mmap_mode="r")
        if mm.shape == (n_fp, n_cols):
            return mm

    net = compute_structural_network_features(visible_mask, footprint)
    mat = np.empty((n_fp, n_cols), dtype=np.float16)
    for j, nm in enumerate(STRUCTURAL_NETWORK_NAMES):
        mat[:, j] = net[nm][footprint].astype(np.float16)

    # 4 explicit Geothermal-Structural & Piedmont-Relay coupling interactions
    idx_claycap = phys_names.index("geotherm_claycap_conduit")
    idx_plume = phys_names.index("geotherm_reservoir_enthalpy")
    idx_lidar = phys_names.index("lidar_relief_norm_scarp")
    idx_strain = phys_names.index("x_strain_transtension")

    claycap = np.asarray(X_phys_rm[:, idx_claycap], dtype=np.float32)
    plume = np.asarray(X_phys_rm[:, idx_plume], dtype=np.float32)
    lidar = np.asarray(X_phys_rm[:, idx_lidar], dtype=np.float32)
    strain = np.asarray(X_phys_rm[:, idx_strain], dtype=np.float32)

    tip_fp = net["net_tip_ray"][footprint]
    gap_fp = _robust_z_flat(net["ns_gap"][footprint])
    cont_fp = _robust_z_flat(net["ns_cont"][footprint])
    sib_fp = _robust_z_flat(net["ns_sib"][footprint])

    base_j = len(STRUCTURAL_NETWORK_NAMES)
    mat[:, base_j + 0] = _robust_z_flat(np.maximum(claycap, 0.0) * np.maximum(tip_fp, 0.0)).astype(np.float16)
    mat[:, base_j + 1] = _robust_z_flat(np.maximum(plume, 0.0) * np.maximum(gap_fp, 0.0)).astype(np.float16)
    mat[:, base_j + 2] = _robust_z_flat(np.maximum(lidar, 0.0) * np.maximum(cont_fp, 0.0)).astype(np.float16)
    mat[:, base_j + 3] = _robust_z_flat(np.maximum(strain, 0.0) * np.maximum(sib_fp, 0.0)).astype(np.float16)

    del net, claycap, plume, lidar, strain, tip_fp, gap_fp, cont_fp, sib_fp
    gc.collect()

    if cache_path is not None:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        np.save(cache_path, mat)
        del mat
        gc.collect()
        return np.load(cache_path, mmap_mode="r")
    return mat


def synthetic_withhold(
    mask: np.ndarray,
    footprint: np.ndarray,
    quad: np.ndarray,
    seed: int,
    frac: float = 0.20,
    collar_px: int = 3,
) -> Tuple[np.ndarray, np.ndarray]:
    """Re-withhold whole 8-connected components of `mask` per quadrant with a `collar_px` buffer.

    Returns `(syn_hidden, syn_state)` where `syn_state` is the reduced catalogue mask
    from which features are computed during training. Never touches outer withheld truth.
    """
    m = np.asarray(mask, dtype=bool) & np.asarray(footprint, dtype=bool)
    comp, n = ndi.label(m, STRUCT8)
    sizes = np.bincount(comp.ravel(), minlength=n + 1)
    hidden = np.zeros(m.shape, dtype=bool)
    for q in range(4):
        inq = quad == q
        cand = np.unique(comp[m & inq])
        clipped = np.unique(comp[m & ~inq])
        elig = np.setdiff1d(cand[cand > 0], clipped)
        if elig.size == 0:
            continue
        rng = np.random.default_rng(830_000 + 97 * seed + q)
        perm = rng.permutation(elig)
        cum = np.cumsum(sizes[perm])
        k = int(np.searchsorted(cum, frac * float((m & inq).sum()))) + 1
        hidden |= np.isin(comp, perm[: min(k, perm.size)]) & m
    collar = ndi.distance_transform_edt(~hidden) <= collar_px
    state = m & ~collar
    assert not (state & hidden).any()
    return hidden, state
