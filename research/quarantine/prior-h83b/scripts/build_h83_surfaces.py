#!/usr/bin/env python3
"""Build H83 hypothesis surfaces and save as GeoTIFFs for holdout testing."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np
import rasterio
from gems83.h83 import build_h83a, build_h83c, build_h83b

DATA = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed"
OUT.mkdir(parents=True, exist_ok=True)

def get_footprint():
    with rasterio.open(DATA / "sample_submission.tif") as s:
        return np.isfinite(s.read(1))

if __name__ == "__main__":
    foot = get_footprint()
    print(f"footprint {foot.sum()} px, shape {foot.shape}")
    with rasterio.open(DATA / "sample_submission.tif") as s:
        profile = s.profile.copy()

    for name, builder in [("H83-A", build_h83a), ("H83-C", build_h83c)]:
        print(f"Building {name}...")
        if name == "H83-A":
            surface = builder(DATA / "training_features.tif", foot)
        else:
            surface = builder(DATA / "training_features.tif", foot)
        print(f"  {name} min {surface.min():.4f} max {surface.max():.4f} mean {surface[foot].mean():.4f} nonzero {(surface>0).sum()}")
        # Save as tiff for inspection
        out_path = OUT / f"{name.lower()}_surface.tif"
        profile_out = profile.copy()
        profile_out.update(dtype="float32", count=1, nodata=np.nan, compress="deflate")
        arr = np.where(foot, surface, np.nan).astype(np.float32)
        with rasterio.open(out_path, "w", **profile_out) as dst:
            dst.write(arr, 1)
        print(f"  saved to {out_path}")

    # H83-B needs rad path
    rad_path = DATA / "external" / "geodawn_rad_u8.tif"
    if rad_path.exists():
        print("Building H83-B...")
        surface = build_h83b(DATA / "training_features.tif", foot, rad_path)
        print(f"  H83-B min {surface.min():.4f} max {surface.max():.4f} mean {surface[foot].mean():.4f}")
        out_path = OUT / "h83-b_surface.tif"
        with rasterio.open(out_path, "w", **profile_out) as dst:
            dst.write(np.where(foot, surface, np.nan).astype(np.float32), 1)
        print(f"  saved to {out_path}")
    else:
        print(f"rad path {rad_path} missing, skip H83-B")

    print("done")
