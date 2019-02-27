from pyts2.time import *
from pyts2.timestream import TimeStream
from pyts2.utils import find_files

from .data import *

import numpy as np
import datetime as dt

def test_read():
    timestreams = [
        "testdata/timestreams/flat",
        "testdata/timestreams/flat.zip",
        "testdata/timestreams/flat.tar",
        "testdata/timestreams/nested/", # with trailing slash
        "testdata/timestreams/nested",
        "testdata/timestreams/nested.zip",
        "testdata/timestreams/nested.tar",
        "testdata/timestreams/tarball-day",
        "testdata/timestreams/zipball-day",
    ]

    for timestream in timestreams:
        stream = TimeStream(timestream)
        for i, image in enumerate(stream):
            assert stream.sorted == ('tar' not in timestream)
            assert np.array_equal(image.pixels, SMALL_TIMESTREAMS["expect_pixels"])
            # Instant
            expect_inst = TSInstant(SMALL_TIMESTREAMS["expect_times"][i],
                                    subsecond=0, index=None)
            assert isinstance(image.instant, TSInstant)
            if stream.sorted:
                assert image.instant == expect_inst
            else:
                assert image.instant.datetime in SMALL_TIMESTREAMS["expect_times"]

        stream = TimeStream(timestream)
        for i, inst in enumerate(stream.iter_instants()):
            assert isinstance(inst, TSInstant)
            expect_inst = TSInstant(SMALL_TIMESTREAMS["expect_times"][i],
                                    subsecond=0, index=None)
            if stream.sorted:
                assert inst == expect_inst
            else:
                assert image.instant.datetime in SMALL_TIMESTREAMS["expect_times"]
                assert inst.subsecond == 0
                assert inst.index is None


def test_gvlike():
    for i, image in enumerate(TimeStream("testdata/timestreams/gvlike")):
        expect_inst = TSInstant(GVLIKE_TIMESTREAM["expect_datetime"],
                                GVLIKE_TIMESTREAM["expect_subsecond"],
                                GVLIKE_TIMESTREAM["expect_indices"][i])
        assert image.instant == expect_inst
        assert np.array_equal(image.pixels, GVLIKE_TIMESTREAM["expect_pixels"])


def test_zipout(tmpdir):
    def check_output_ok(outpath):
        for i, image in enumerate(TimeStream(outpath)):
            expect_inst = TSInstant(SMALL_TIMESTREAMS["expect_times"][i],
                                    subsecond=0, index=None)
            assert image.instant == expect_inst
            assert np.array_equal(image.pixels, SMALL_TIMESTREAMS["expect_pixels"])

    outputs = {
        "root":  [
            "output.zip",
        ],
        "year":  [
            "output/output_2001.zip",
        ],
        "month": [
            "output/2001/output_2001_02.zip",
        ],
        "day":   [
            "output/2001/2001_02/output_2001_02_01.zip",
            "output/2001/2001_02/output_2001_02_02.zip",
        ],
        "hour":  [
            "output/2001/2001_02/2001_02_02/output_2001_02_02_09.zip",
            "output/2001/2001_02/2001_02_02/output_2001_02_02_13.zip",
            "output/2001/2001_02/2001_02_02/output_2001_02_02_10.zip",
            "output/2001/2001_02/2001_02_02/output_2001_02_02_12.zip",
            "output/2001/2001_02/2001_02_02/output_2001_02_02_11.zip",
            "output/2001/2001_02/2001_02_01/output_2001_02_01_13.zip",
            "output/2001/2001_02/2001_02_01/output_2001_02_01_11.zip",
            "output/2001/2001_02/2001_02_01/output_2001_02_01_12.zip",
            "output/2001/2001_02/2001_02_01/output_2001_02_01_09.zip",
            "output/2001/2001_02/2001_02_01/output_2001_02_01_10.zip",
        ],
        "none":  [
            "output/2001/2001_02/2001_02_02/2001_02_02_09/output_2001_02_02_09_14_15_00.tif",
            "output/2001/2001_02/2001_02_02/2001_02_02_13/output_2001_02_02_13_14_15_00.tif",
            "output/2001/2001_02/2001_02_02/2001_02_02_10/output_2001_02_02_10_14_15_00.tif",
            "output/2001/2001_02/2001_02_02/2001_02_02_12/output_2001_02_02_12_14_15_00.tif",
            "output/2001/2001_02/2001_02_02/2001_02_02_11/output_2001_02_02_11_14_15_00.tif",
            "output/2001/2001_02/2001_02_01/2001_02_01_13/output_2001_02_01_13_14_15_00.tif",
            "output/2001/2001_02/2001_02_01/2001_02_01_11/output_2001_02_01_11_14_15_00.tif",
            "output/2001/2001_02/2001_02_01/2001_02_01_12/output_2001_02_01_12_14_15_00.tif",
            "output/2001/2001_02/2001_02_01/2001_02_01_09/output_2001_02_01_09_14_15_00.tif",
            "output/2001/2001_02/2001_02_01/2001_02_01_10/output_2001_02_01_10_14_15_00.tif",
        ],
    }

    for level in outputs.keys():
        outpath = tmpdir.join(level, "output")
        if level == "root":
            outpath += ".zip"
        out = TimeStream(path=outpath, mode="w", format="tif", bundle_level=level,
                         name="output")
        for image in TimeStream("testdata/timestreams/nested"):
            out.write(image)
        out.close()
        check_output_ok(outpath)

        expect = {str(tmpdir.join(level, x)) for x in outputs[level]}
        assert set(find_files(outpath)) == expect
