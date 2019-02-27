from pyts2.timestream import TimeStream
from pyts2.utils import parse_date, find_files

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
        last_time = None
        stream = TimeStream(timestream)
        for image in stream:
            assert stream.sorted == ('tar' not in timestream)
            assert image.subsecond == 0
            assert image.index is None
            assert np.array_equal(image.pixels, SMALL_TIMESTREAMS["expect_pixels"])
            assert image.datetime in SMALL_TIMESTREAMS["expect_times"]
            if stream.sorted and last_time is not None:
                assert image.datetime >= last_time
            last_time = image.datetime

        last_time = None
        stream = TimeStream(timestream)
        for i, (dt, subsec, idx) in enumerate(stream.iter_datetimes()):
            if stream.sorted and last_time is not None:
                assert dt >= last_time
            assert dt in SMALL_TIMESTREAMS["expect_times"]
            assert subsec == 0
            assert idx is None


def test_gvlike():
    for i, image in enumerate(TimeStream("testdata/timestreams/gvlike")):
        assert image.subsecond == GVLIKE_TIMESTREAM["expect_subsecond"]
        assert np.array_equal(image.pixels, GVLIKE_TIMESTREAM["expect_pixels"])
        assert image.datetime == GVLIKE_TIMESTREAM["expect_datetime"]
        assert image.index == GVLIKE_TIMESTREAM["expect_indices"][i]


def test_zipout(tmpdir):
    def check_output_ok(outpath):
        for image in TimeStream(outpath):
            print(image)
            assert image.subsecond == 0
            assert image.index is None
            assert np.array_equal(image.pixels, SMALL_TIMESTREAMS["expect_pixels"])
            assert image.datetime in SMALL_TIMESTREAMS["expect_times"]

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
