from pyts2.pipeline import *
from pyts2.pipeline.resize import geom2rowcol
from pyts2 import *

from .data import *
from .utils import *

import pytest
import numpy as np
from PIL import Image
from io import BytesIO
from os import path as op


def test_geom2rowcol():
    assert geom2rowcol("200x100") == (200, 100)
    assert geom2rowcol("x100") == (None, 100)
    assert geom2rowcol("100x") == (100, None)
    with pytest.raises(ValueError):
        geom2rowcol("x")
    with pytest.raises(ValueError):
        geom2rowcol("not a geometry")


def test_resize(data):
    img = TimestreamImage.from_path(data("images/GC37L~320_2019_04_01_00_00_00.jpg"))
    orows, ocols, odepth = img.pixels.shape

    downsized = ResizeImageStep(cols=100).process_file(img)
    rows, cols, depth = downsized.pixels.shape
    assert cols == 100
    assert depth == odepth
    assert rows < orows
