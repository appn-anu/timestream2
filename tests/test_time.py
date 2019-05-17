from pyts2.time import TSInstant, TimeFilter, parse_partial_date
import datetime as dt

from .utils import *


def test_tsinstant_cmp():
    testcases = [
        # a list of (smaller, bigger) instants
        (TSInstant("2019_12_31_23_59_59", 0, None),
         TSInstant("2019_12_31_23_59_59", 1, None)),
        (TSInstant("2019_12_31_23_59_59", 1, "abc"),
         TSInstant("2019_12_31_23_59_59", 1, "def")),
    ]

    for (smaller, bigger) in testcases:
        assert bigger > smaller
        assert not bigger < smaller
        assert not bigger < bigger
        assert bigger >= smaller
        assert bigger >= bigger
        assert not bigger <= smaller
        assert bigger <= bigger


def test_timefilter():
    dtnow = dt.datetime.now()
    dnow = dtnow.date()
    tnow = dtnow.time()

    assert TimeFilter()(dtnow)
    assert TimeFilter(dt.date(2001, 1, 1), dt.date(2100, 1, 1))(dtnow)
    assert TimeFilter(dt.date(2001, 1, 1))(dtnow)
    assert TimeFilter(enddate=dt.date(2100, 1, 1))(dtnow)
    assert not TimeFilter(dt.date(2100, 1, 1), dt.date(2200, 1, 1))(dtnow)

    tminus1 = (dtnow - dt.timedelta(hours=1)).time()
    tplus1 = (dtnow + dt.timedelta(hours=1)).time()
    assert TimeFilter(starttime=tminus1)(dtnow)
    assert TimeFilter(starttime=tminus1, endtime=tplus1)(dtnow)
    assert not TimeFilter(endtime=tminus1)(dtnow)

    with pytest.raises(ValueError):
        assert TimeFilter(dt.date(2100, 1, 1), dt.date(2000, 1, 1))
    with pytest.raises(ValueError):
        assert TimeFilter(endtime=tminus1, starttime=tplus1)
    with pytest.raises(ValueError):
        assert TimeFilter("bad", "nonsense")

    filt = TimeFilter(dt.date(2019, 2, 2), dt.date(2019, 11, 29),
                      dt.time(8, 2, 4, 0), dt.time(17, 0, 0, 0))

    assert filt.partial_within("2019")
    assert not filt.partial_within("2020")
    assert not filt.partial_within("2018")

    assert filt.partial_within("2019_11")
    assert not filt.partial_within("2019_01")
    assert not filt.partial_within("2019_12")

    assert filt.partial_within("2019_11_29")
    assert not filt.partial_within("2019_11_30")
    assert not filt.partial_within("2019_02_01")

    assert filt.partial_within("2019_11_29_08")
    assert not filt.partial_within("2019_11_29_07")
    assert not filt.partial_within("2019_11_29_18")

    assert filt.partial_within("2019_11_29_08_02")
    assert not filt.partial_within("2019_11_29_08_01")
    assert not filt.partial_within("2019_11_29_17_01")

    assert filt.partial_within("2019_11_29_08_02_04")
    assert not filt.partial_within("2019_11_29_08_02_03")
    assert not filt.partial_within("2019_11_29_17_00_01")


def test_parsepartial():
    dmin = dt.date.min
    dmax = dt.date.max
    tmin = dt.time.min
    tmax = dt.time.max

    #assert parse_partial_date("", max=False) == dmin
    #assert parse_partial_date("", max=True) == dmax

    assert parse_partial_date("2019", max=False) == \
           (dmin.replace(2019), None)
    assert parse_partial_date("2019", max=True) == \
           (dmax.replace(2019), None)
    assert parse_partial_date("blahname_2019_blahsubsec.blah", max=True) == \
           (dmax.replace(2019), None)

    assert parse_partial_date("2019_12", max=False) == \
           (dmin.replace(2019, 12), None)
    assert parse_partial_date("2019_12", max=True) == \
           (dmax.replace(2019, 12), None)
    assert parse_partial_date("blahname_2019_12_blahsubsec.blah", max=True) == \
           (dmax.replace(2019, 12), None)

    assert parse_partial_date("2019_12_31", max=False) == \
           (dmin.replace(2019, 12, 31), None)
    assert parse_partial_date("2019_12_31", max=True) == \
           (dmax.replace(2019, 12, 31), None)
    assert parse_partial_date("blahname_2019_12_31_blahsubsec.blah", max=True) == \
           (dmax.replace(2019, 12, 31), None)

    assert parse_partial_date("2019_12_31_23", max=False) == \
           (dmin.replace(2019, 12, 31), tmin.replace(23))
    assert parse_partial_date("2019_12_31_23", max=True) == \
           (dmax.replace(2019, 12, 31), tmax.replace(23))
    assert parse_partial_date("blahname_2019_12_31_23_blahsubsec.blah", max=True) == \
           (dmax.replace(2019, 12, 31), tmax.replace(23))

    assert parse_partial_date("2019_12_31_23_59", max=False) == \
           (dmin.replace(2019, 12, 31), tmin.replace(23, 59))
    assert parse_partial_date("2019_12_31_23_59", max=True) == \
           (dmax.replace(2019, 12, 31), tmax.replace(23, 59))
    assert parse_partial_date("blahname_2019_12_31_23_59_blahsubsec.blah", max=True) == \
           (dmax.replace(2019, 12, 31), tmax.replace(23, 59))

    assert parse_partial_date("2019_12_31_23_59_00", max=False) == \
           (dmin.replace(2019, 12, 31), tmin.replace(23, 59, 00))
    assert parse_partial_date("2019_12_31_23_59_00", max=True) == \
           (dmax.replace(2019, 12, 31), tmax.replace(23, 59, 00))
    assert parse_partial_date("blahname_2019_12_31_23_59_00_blahsubsec.blah", max=True) == \
           (dmax.replace(2019, 12, 31), tmax.replace(23, 59, 00))
