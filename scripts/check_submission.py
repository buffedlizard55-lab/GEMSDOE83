#!/usr/bin/env python3
"""Validate a submission GeoTIFF against the competition template."""
import argparse, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"src"))
from gems83.grid import open_template
import rasterio, numpy as np

def validate(geotiff: Path, template: Path, strict_finite: bool=False):
    geotiff=Path(geotiff); template=Path(template)
    with rasterio.open(template) as tpl:
        exp_crs=str(tpl.crs); exp_width=tpl.width; exp_height=tpl.height; exp_transform=tpl.transform; exp_dtype="float32"
    with rasterio.open(geotiff) as s:
        arr=s.read(1)
        out={
            "filename": geotiff.name,
            "crs": str(s.crs), "width": s.width, "height": s.height, "transform": list(s.transform)[:6],
            "dtype": s.dtypes[0], "nodata": s.nodata,
            "crs_match": str(s.crs)==exp_crs,
            "shape_match": (s.width==exp_width and s.height==exp_height),
            "transform_match": s.transform==exp_transform,
            "dtype_ok": s.dtypes[0]=="float32",
            "count_ok": s.count==1,
        }
        finite=np.isfinite(arr)
        in_range=np.isfinite(arr) & (arr>=0) & (arr<=1)
        # For strict, require all cells finite and in [0,1]
        if strict_finite:
            out["all_finite"]=bool(finite.all())
            out["all_in_range"]=bool(in_range.all() and finite.all())
            out["min"]=float(np.nanmin(arr)) if finite.any() else None
            out["max"]=float(np.nanmax(arr)) if finite.any() else None
            out["nan_count"]=int((~finite).sum())
            out["outside_range"]=int((~in_range & finite).sum())
            out["passed"]=bool(out["crs_match"] and out["shape_match"] and out["transform_match"] and out["dtype_ok"] and out["all_finite"] and out["all_in_range"])
        else:
            # Check only inside footprint (finite in template)
            with rasterio.open(template) as tpl:
                foot=np.isfinite(tpl.read(1))
            in_vals=arr[foot]
            out["finite_inside"]=int(np.isfinite(in_vals).sum())
            out["min_inside"]=float(np.nanmin(in_vals)) if np.isfinite(in_vals).any() else None
            out["max_inside"]=float(np.nanmax(in_vals)) if np.isfinite(in_vals).any() else None
            out["passed"]=bool(out["crs_match"] and out["shape_match"] and out["transform_match"] and np.isfinite(in_vals).all() and ((in_vals>=0)&(in_vals<=1)).all())
        return out

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("geotiff", type=Path)
    p.add_argument("--template", type=Path, default=Path("data/raw/sample_submission.tif"))
    p.add_argument("--strict-finite", action="store_true")
    args=p.parse_args()
    rep=validate(args.geotiff, args.template, args.strict_finite)
    print(json.dumps(rep, indent=2))
    sys.exit(0 if rep["passed"] else 2)
