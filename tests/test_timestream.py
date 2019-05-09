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

    expect_insts = [TSInstant(t, subsecond=0, index=None)
                    for t in SMALL_TIMESTREAMS["expect_times"]]
    for timestream in timestreams:
        stream = TimeStream(timestream)
        for i, file in enumerate(stream):
            assert stream.sorted == ('tar' not in timestream)
            assert isinstance(file.instant, TSInstant)
            if stream.sorted:
                assert file.instant == expect_insts[i]

        assert stream.instants == expect_insts


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
            "output.tif.zip",
        ],
        "year":  [
            "output/output_2001.tif.zip",
        ],
        "month": [
            "output/2001/output_2001_02.tif.zip",
        ],
        "day":   [
            "output/2001/2001_02/output_2001_02_01.tif.zip",
            "output/2001/2001_02/output_2001_02_02.tif.zip",
        ],
        "hour":  [
            "output/2001/2001_02/2001_02_02/output_2001_02_02_09.tif.zip",
            "output/2001/2001_02/2001_02_02/output_2001_02_02_13.tif.zip",
            "output/2001/2001_02/2001_02_02/output_2001_02_02_10.tif.zip",
            "output/2001/2001_02/2001_02_02/output_2001_02_02_12.tif.zip",
            "output/2001/2001_02/2001_02_02/output_2001_02_02_11.tif.zip",
            "output/2001/2001_02/2001_02_01/output_2001_02_01_13.tif.zip",
            "output/2001/2001_02/2001_02_01/output_2001_02_01_11.tif.zip",
            "output/2001/2001_02/2001_02_01/output_2001_02_01_12.tif.zip",
            "output/2001/2001_02/2001_02_01/output_2001_02_01_09.tif.zip",
            "output/2001/2001_02/2001_02_01/output_2001_02_01_10.tif.zip",
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
        out = TimeStream(path=outpath, format="tif", bundle_level=level, name="output")
        for file in TimeStream("testdata/timestreams/nested"):
            out.write(file)
        out.close()
        check_output_ok(outpath)

        expect = {str(tmpdir.join(level, x)) for x in outputs[level]}
        assert set(find_files(tmpdir.join(level))) == expect
