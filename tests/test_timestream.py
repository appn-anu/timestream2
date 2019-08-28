from pyts2.timestream import TimeStream
from pyts2.time import *
from pyts2.utils import find_files

from .utils import *
from .data import *

import datetime as dt

def test_read(data):
    timestreams = [
        data("timestreams/flat"),
        data("timestreams/flat.zip"),
        data("timestreams/flat.tar"),
        data("timestreams/nested/"), # with trailing slash
        data("timestreams/nested"),
        data("timestreams/nested.zip"),
        data("timestreams/nested.tar"),
        data("timestreams/tarball-day"),
        data("timestreams/zipball-day"),
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

        assert list(sorted(stream.instants.keys())) == expect_insts


def test_gvlike(data):
    for i, file in enumerate(TimeStream(data("timestreams/gvlike"))):
        expect_inst = TSInstant(GVLIKE_TIMESTREAM["expect_datetime"],
                                GVLIKE_TIMESTREAM["expect_subsecond"],
                                GVLIKE_TIMESTREAM["expect_indices"][i])
        assert file.instant == expect_inst


def test_zipout(tmpdir, data):
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
        for file in TimeStream(data("timestreams/nested")):
            out.write(file)
        out.close()
        check_output_ok(outpath)

        expect = {str(tmpdir.join(level, x)) for x in outputs[level]}
        assert set(find_files(tmpdir.join(level))) == expect


def test_dict(data):
    timestreams = [
        data("timestreams/nested"),
        data("timestreams/nested.zip"),
        data("timestreams/nested.tar"),
    ]
    filenames = [
        "2001_02_01_09_14_15_00.tif",
        "2001_02_01_10_14_15_00.tif",
        "2001_02_01_11_14_15_00.tif",
        "2001_02_01_12_14_15_00.tif",
        "2001_02_01_13_14_15_00.tif",
        "2001_02_02_09_14_15_00.tif",
        "2001_02_02_10_14_15_00.tif",
        "2001_02_02_11_14_15_00.tif",
        "2001_02_02_12_14_15_00.tif",
        "2001_02_02_13_14_15_00.tif",
    ]
    for timestream in timestreams:
        stream = TimeStream(timestream)
        for fn in filenames:
            gotfile = stream[fn]
            assert gotfile.filename == fn
            assert len(gotfile.content) > 0
            assert isinstance(gotfile.content, bytes)
        with pytest.raises(KeyError):
            stream["Not a file"]


def test_read_with_filter(data):
    timestreams = [
        data("timestreams/nested/"), # with trailing slash
        data("timestreams/nested"),
        data("timestreams/nested.zip"),
        data("timestreams/nested.tar"),
        data("timestreams/zipball-day"),
    ]

    tfilter = TimeFilter(dt.date(2001, 2, 1), dt.date(2001, 2, 1),
                         dt.time(10, 0, 0), dt.time(12, 0, 0))
    expect_insts = [TSInstant.from_path("2001_02_01_10_14_15"),
                    TSInstant.from_path("2001_02_01_11_14_15")]
    for timestream in timestreams:
        stream = TimeStream(timestream, timefilter=tfilter)
        for i, file in enumerate(stream):
            if stream.sorted:
                assert file.instant == expect_insts[i]
            else:
                assert file.instant in expect_insts
        assert list(sorted(stream.instants.keys())) == expect_insts

def test_zip_overwrite(data, tmpdir):
    in_stream = TimeStream(data("timestreams/nested"))
    out_stream = TimeStream(path=tmpdir.join("test_ts.zip"), bundle_level='root', name="output")
    
    file = next(in_stream.iter())

    out_stream.write(file)
    out_stream.write(file)
    file.clear_content()
    file._content = b"this isn't the correct content"
    with pytest.raises(RuntimeError):
        out_stream.write(file)
