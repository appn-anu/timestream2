from pyts2.timestream import TimeStream
from pyts2.time import *
from pyts2.utils import find_files

from .data import *

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
        for i, file in enumerate(stream):
            assert stream.sorted == ('tar' not in timestream)
            # Instant
            expect_inst = TSInstant(SMALL_TIMESTREAMS["expect_times"][i],
                                    subsecond=0, index=None)
            assert isinstance(file.instant, TSInstant)
            if stream.sorted:
                assert file.instant == expect_inst
            else:
                assert file.instant.datetime in SMALL_TIMESTREAMS["expect_times"]


def test_gvlike():
    for i, file in enumerate(TimeStream("testdata/timestreams/gvlike")):
        expect_inst = TSInstant(GVLIKE_TIMESTREAM["expect_datetime"],
                                GVLIKE_TIMESTREAM["expect_subsecond"],
                                GVLIKE_TIMESTREAM["expect_indices"][i])
        assert file.instant == expect_inst


def test_zipout(tmpdir):
    def check_output_ok(outpath):
        for i, file in enumerate(TimeStream(outpath)):
            expect_inst = TSInstant(SMALL_TIMESTREAMS["expect_times"][i],
                                    subsecond=0, index=None)
            assert file.instant == expect_inst

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
        out = TimeStream(path=outpath, format="tif", bundle_level=level, name="output")
        for file in TimeStream("testdata/timestreams/nested"):
            out.write(file)
        out.close()
        check_output_ok(outpath)

        expect = {str(tmpdir.join(level, x)) for x in outputs[level]}
        assert set(find_files(outpath)) == expect
