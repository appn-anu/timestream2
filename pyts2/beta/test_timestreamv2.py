# Copyright (c) 2018 Kevin Murray <kdmfoss@gmail.com>
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from pyts2 import TimeStream, TSInstant
from .tsv2_msgpack import TSv2Stream
from pyts2.test.data import SMALL_TIMESTREAMS


import numpy as np
import datetime as dt

def test_roundtrip_v1_to_v2(tmpdir):
    outpath = tmpdir.join("test.ts2")
    out = TSv2Stream(outpath, "w")
    for i, image in enumerate(TimeStream("testdata/timestreams/flat/")):
        out.write(image)
    out.close()

    stream = TSv2Stream(outpath, "r")
    for image in stream:
        # Instant
        expect_inst = TSInstant(SMALL_TIMESTREAMS["expect_times"][i],
                                subsecond=0, index=None)
        assert isinstance(image.instant, TSInstant)
        if stream.sorted:
            assert image.instant == expect_inst
        else:
            assert image.instant.datetime in SMALL_TIMESTREAMS["expect_times"]
            assert image.instant.subsecond == 0
            assert image.instant.index is None
        assert np.array_equal(image.pixels, SMALL_TIMESTREAMS["expect_pixels"])

