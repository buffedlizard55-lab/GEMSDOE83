"""Independent format audit, NOT the missing shared competition writer/evaluator.

Reject rather than repair predictions. Audit the complete TIFF, including masked
pixels: a nodata declaration must not hide out-of-range values from this check.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import rasterio


def validate(candidate, template):
    checks = {}
    with rasterio.open(template) as ref, rasterio.open(candidate) as src:
        checks['single_band'] = src.count == 1
        checks['shape_match'] = src.shape == ref.shape
        checks['crs_match'] = src.crs is not None and src.crs == ref.crs
        checks['transform_match'] = src.transform == ref.transform
        checks['nonempty_footprint'] = False
        checks['no_nan_inside_footprint'] = True
        checks['no_masked_predictions_inside_footprint'] = True
        checks['all_pixels_finite'] = True
        checks['all_values_in_0_1'] = True
        checks['real_numeric_dtype'] = np.dtype(src.dtypes[0]).kind in 'uif'
        if checks['shape_match'] and checks['single_band'] and checks['real_numeric_dtype']:
            for _, window in ref.block_windows(1):
                foot = ref.dataset_mask(window=window) > 0
                a = src.read(1, window=window)
                checks['nonempty_footprint'] |= bool(foot.any())
                checks['no_nan_inside_footprint'] &= bool(np.isfinite(a[foot]).all())
                checks['no_masked_predictions_inside_footprint'] &= bool((src.read_masks(1, window=window)[foot] > 0).all())
                checks['all_pixels_finite'] &= bool(np.isfinite(a).all())
                checks['all_values_in_0_1'] &= bool(((a >= 0) & (a <= 1)).all())
        else:
            for key in ['all_pixels_finite', 'all_values_in_0_1', 'no_nan_inside_footprint', 'no_masked_predictions_inside_footprint']:
                checks[key] = False
    h = hashlib.sha256()
    with open(candidate, 'rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return {'schema': 'gems83-format-audit-v1', 'candidate': str(candidate),
            'template': str(template), 'sha256': h.hexdigest(), 'checks': checks,
            'format_valid': all(checks.values()),
            'submission_ready': False,
            'scope': 'Format only. No holdout, uniqueness, official template authentication, or slot authorization implied.'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('candidate', type=Path)
    p.add_argument('template', type=Path)
    p.add_argument('--output', type=Path)
    args = p.parse_args()
    try:
        result = validate(args.candidate, args.template)
    except (OSError, rasterio.errors.RasterioError, ValueError) as exc:
        result = {'format_valid': False, 'submission_ready': False, 'error': str(exc)}
    text = json.dumps(result, indent=2, allow_nan=False) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
    print(text, end='')
    return 0 if result['format_valid'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
