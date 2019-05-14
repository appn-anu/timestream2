from pyts2 import TSInstant

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
