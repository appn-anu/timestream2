from pyts2 import TSInstant, TimeFilter
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
