# Copyright (c) 2018 Kevin Murray <kdmfoss@gmail.com>
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from pyts2.tsformats import TSv1Stream,  TSv2Stream
from .data import SMALL_TIMESTREAMS


import numpy as np
import datetime as dt

def test_roundtrip_v1_to_v2(tmpdir):
    outpath = tmpdir.join("test.ts2")
    out = TSv2Stream(outpath, "w")
    for image in TSv1Stream("testdata/timestreams/flat/"):
        assert image.datetime in SMALL_TIMESTREAMS["expect_times"]
        assert image.subsec_index == 0
        assert np.array_equal(image.pixels, SMALL_TIMESTREAMS["expect_pixels"])
        out.write(image)
    out.close()

    for image in TSv2Stream(outpath, "r"):
        assert image.subsec_index == 0
        assert np.array_equal(image.pixels, SMALL_TIMESTREAMS["expect_pixels"])
        assert image.datetime in SMALL_TIMESTREAMS["expect_times"]

