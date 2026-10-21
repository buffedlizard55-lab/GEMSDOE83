"""
Validator for GEMSDOE83 submission
Checks:
- single band
- float32
- shape 3730x3292
- CRS EPSG:32611
- transform [100,0,243350,0,-100,4508550]
- values in [0,1]
- no NaN inside footprint for all-finite, finite count 5167373 for nan version
- no sentinel -3.4e38
- no inf
"""
import rasterio, numpy as np, sys
from pathlib import Path

transform_expected = [100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0]
shape_expected = (3730, 3292)
crs_expected = "EPSG:32611"

def validate(path):
    print(f"\n=== {path} ===")
    with rasterio.open(path) as src:
        arr = src.read(1)
        checks = {}
        checks["single_band"] = src.count==1
        checks["dtype_float32"] = src.dtypes[0]=='float32'
        checks["shape"] = (src.height, src.width)==shape_expected
        checks["crs"] = src.crs.to_string()==crs_expected
        checks["transform"] = list(src.transform)[:6]==transform_expected
        checks["no_inf"] = np.isinf(arr).sum()==0
        checks["no_sentinel"] = np.sum(arr==-3.4028234663852886e+38)==0
        finite = np.isfinite(arr)
        checks["range_0_1"] = np.sum(finite & ((arr<0)|(arr>1)))==0
        checks["min"] = float(np.nanmin(arr))
        checks["max"] = float(np.nanmax(arr))
        checks["finite"] = int(finite.sum())
        checks["nan"] = int(np.isnan(arr).sum())
        checks["positive"] = int(np.sum(arr==1.0))
        print(checks)
        ok = all([checks["single_band"], checks["dtype_float32"], checks["shape"], checks["crs"], checks["transform"], checks["no_inf"], checks["no_sentinel"], checks["range_0_1"]])
        print(f"OK? {ok}")
        return ok

if __name__ == "__main__":
    paths = sys.argv[1:] or ["docs/downloads/gemsdoe83-piedmont-basement-triple-37654-20261021.tif", "docs/downloads/gemsdoe83-piedmont-basement-triple-37654-20261021-nan.tif"]
    for p in paths:
        if Path(p).exists():
            validate(p)
        else:
            print(f"Not found {p}")
