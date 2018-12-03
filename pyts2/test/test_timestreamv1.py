from pyts2.timestream import TSv1Stream
from pyts2.utils import parse_date

from .data import SMALL_TIMESTREAMS

import numpy as np
import datetime as dt

def test_read():
    timestreams = [
        "testdata/timestreams/big-tarball.tar",
        "testdata/timestreams/flat",
        "testdata/timestreams/nested",
        "testdata/timestreams/tarball-day",
    ]

    for timestream in timestreams:
        for image in TSv1Stream(timestream):
            assert image.subsec_index == 0
            assert np.array_equal(image.pixels, SMALL_TIMESTREAMS["expect_pixels"])
            assert image.datetime in SMALL_TIMESTREAMS["expect_times"]
