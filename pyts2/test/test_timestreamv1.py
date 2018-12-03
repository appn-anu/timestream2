from pyts2.timestream import TSv1Stream
from pyts2.utils import parse_date

from .data import SMALL_TIMESTREAMS

import numpy as np
import datetime as dt

def test_read():
    timestreams = [
        "testdata/timestreams/flat",
        "testdata/timestreams/flat.zip",
        "testdata/timestreams/flat.tar",
        "testdata/timestreams/nested",
        "testdata/timestreams/nested.zip",
        "testdata/timestreams/nested.tar",
        "testdata/timestreams/tarball-day",
        "testdata/timestreams/zipball-day",
    ]

    for timestream in timestreams:
        for image in TSv1Stream(timestream):
            assert image.subsec_index == 0
            assert np.array_equal(image.pixels, SMALL_TIMESTREAMS["expect_pixels"])
            assert image.datetime in SMALL_TIMESTREAMS["expect_times"]
