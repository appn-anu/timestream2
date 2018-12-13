from pyts2.timestream import TSv1Stream
from pyts2.utils import parse_date, find_files

from .data import SMALL_TIMESTREAMS

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
        stream = TSv1Stream(timestream)
        for image in stream:
            assert stream.sorted == ('tar' not in timestream)
            assert image.subsecond == 0
            assert image.index is None
            assert np.array_equal(image.pixels, SMALL_TIMESTREAMS["expect_pixels"])
            assert image.datetime in SMALL_TIMESTREAMS["expect_times"]
            if stream.sorted and last_time is not None:
                assert image.datetime >= last_time
            last_time = image.datetime

    indices = []
    for image in TSv1Stream("testdata/timestreams/gvlike"):
        indices.append(image.index)
        assert image.subsecond == 0
        assert np.array_equal(image.pixels, SMALL_TIMESTREAMS["expect_pixels"])
        assert image.datetime in SMALL_TIMESTREAMS["expect_times"]
    # images should have been in order
    assert indices == ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10"]

def test_zipout(tmpdir):
    def check_output_ok(outpath):
        for image in TSv1Stream(outpath):
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
        out = TSv1Stream(path=outpath, mode="w", format="tif", bundle_level=level,
                         name="output")
        for image in TSv1Stream("testdata/timestreams/nested"):
            out.write(image)
        out.close()
        check_output_ok(outpath)

        expect = {str(tmpdir.join(level, x)) for x in outputs[level]}
        assert set(find_files(outpath)) == expect
