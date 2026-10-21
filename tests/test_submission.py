import rasterio, numpy as np, pytest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
TIF=ROOT/"docs/downloads/gemsdoe83-h83b-dilational-jog-aug-b2-40000-20261004T220000Z-c48ac2b3-zeros.tif"
TEMPLATE=ROOT/"data/raw/sample_submission.tif"

def test_all_finite_and_range():
    with rasterio.open(TIF) as s:
        arr=s.read(1)
        assert np.isfinite(arr).all(), "all cells must be finite"
        assert (arr>=0).all() and (arr<=1).all(), "all in [0,1]"
        assert s.crs.to_string()=="EPSG:32611"
        assert s.width==3292 and s.height==3730
        assert s.dtypes[0]=="float32"

def test_no_nan_inside_footprint():
    if not TEMPLATE.exists(): pytest.skip('competition mirrors not fetched (CI)')
    with rasterio.open(TEMPLATE) as t:
        foot=np.isfinite(t.read(1))
    with rasterio.open(TIF) as s:
        arr=s.read(1)
        assert np.isfinite(arr[foot]).all()

def test_positive_pixels():
    with rasterio.open(TIF) as s:
        arr=s.read(1)
        assert int((arr>0).sum())==40000

def test_on_catalogue_zero():
    labels=ROOT/"data/raw/labels.tif"
    if not labels.exists(): pytest.skip('competition mirrors not fetched (CI)')
    with rasterio.open(labels) as l:
        lab=l.read(1)==1
    with rasterio.open(TIF) as s:
        arr=s.read(1)>0.5
    assert int((arr & lab).sum())==0

def test_duplicate_thresholds():
    import json
    run=json.loads((ROOT/"evidence/run_card.json").read_text())
    reg=run["correlation_overlap_vs_registry"]
    for k in ("H83-B_vs_D28","H83-F_vs_H83-B","H83-F_vs_D28"):
        assert reg[k]["pass"] and reg[k]["pearson_binary"]<0.90
    assert len(run["submission_note"])<=140
    assert run["negative_candidate"]["verdict"].startswith("negative")
