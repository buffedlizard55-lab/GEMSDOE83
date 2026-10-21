import importlib.util
from pathlib import Path

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

spec = importlib.util.spec_from_file_location('validator', Path(__file__).parents[1] / 'scripts/validate_artifact.py')
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)


def write(path, a=None, **kw):
    if a is None:
        a = np.full((1, 4, 5), .25, dtype='float32')
    profile = dict(driver='GTiff', height=a.shape[1], width=a.shape[2], count=a.shape[0],
                   dtype=a.dtype, crs='EPSG:32611', transform=from_origin(200, 300, 100, 100))
    profile.update(kw)
    with rasterio.open(path, 'w', **profile) as dst:
        dst.write(a)
    return path


def test_valid_format_never_promotes(tmp_path):
    t = write(tmp_path / 't.tif')
    r = v.validate(t, t)
    assert r['format_valid'] and not r['submission_ready']


@pytest.mark.parametrize('value', [-1, 1.001, np.nan, np.inf, -np.inf])
def test_bad_value(tmp_path, value):
    t = write(tmp_path / 't.tif')
    a = np.zeros((1, 4, 5), dtype='float32'); a[0, 0, 0] = value
    c = write(tmp_path / 'c.tif', a)
    assert not v.validate(c, t)['format_valid']


@pytest.mark.parametrize('kw', [dict(crs='EPSG:4326'), dict(transform=from_origin(201, 300, 100, 100))])
def test_wrong_grid(tmp_path, kw):
    t = write(tmp_path / 't.tif'); c = write(tmp_path / 'c.tif', **kw)
    assert not v.validate(c, t)['format_valid']


def test_wrong_shape_and_bands(tmp_path):
    t = write(tmp_path / 't.tif')
    for shape in [(1, 3, 5), (2, 4, 5)]:
        c = write(tmp_path / 'c.tif', np.zeros(shape, dtype='float32'))
        assert not v.validate(c, t)['format_valid']


def test_hidden_negative_nodata_outside_footprint(tmp_path):
    a = np.zeros((1, 4, 5), dtype='float32'); a[0, 0, 0] = -1
    t = write(tmp_path / 't.tif', a, nodata=-1)
    c = write(tmp_path / 'c.tif', a, nodata=-1)
    assert not v.validate(c, t)['format_valid']


def test_mask_cannot_hide_inside_nan(tmp_path):
    t = write(tmp_path / 't.tif')
    a = np.zeros((1, 4, 5), dtype='float32'); a[0, 0, 0] = np.nan
    c = write(tmp_path / 'c.tif', a, nodata=np.nan)
    assert not v.validate(c, t)['format_valid']


def test_empty_footprint(tmp_path):
    t = write(tmp_path / 't.tif', np.zeros((1, 4, 5), dtype='float32'), nodata=0)
    c = write(tmp_path / 'c.tif')
    assert not v.validate(c, t)['format_valid']
