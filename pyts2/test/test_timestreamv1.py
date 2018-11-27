from pyts2.timestream import TSv1Stream
from pyts2.utils import parse_date

import numpy as np
import datetime as dt

def test_read():

    expect_times = set([
        dt.datetime(2001, 2, 1,  9, 14, 15),
        dt.datetime(2001, 2, 1, 10, 14, 15),
        dt.datetime(2001, 2, 1, 11, 14, 15),
        dt.datetime(2001, 2, 1, 12, 14, 15),
        dt.datetime(2001, 2, 1, 13, 14, 15),
        dt.datetime(2001, 2, 2,  9, 14, 15),
        dt.datetime(2001, 2, 2, 10, 14, 15),
        dt.datetime(2001, 2, 2, 11, 14, 15),
        dt.datetime(2001, 2, 2, 12, 14, 15),
        dt.datetime(2001, 2, 2, 13, 14, 15),
    ])

    expect_pixels = np.array([[255,255]], dtype="u1")

    timestreams = [
        "testdata/timestreams/big-tarball.tar",
        "testdata/timestreams/flat",
        "testdata/timestreams/nested",
        "testdata/timestreams/tarball-day",
    ]

    for timestream in timestreams:
        for image in TSv1Stream(timestream):
            assert image.subsec_index == 0
            assert np.array_equal(image.pixels, expect_pixels)
            assert image.datetime in expect_times
