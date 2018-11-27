import numpy as np
import datetime as dt

SMALL_TIMESTREAMS = dict(
    expect_times = set([
        dt.datetime(2001, 2, 1,  9, 14, 15),
        dt.datetime(2001, 2, 1, 10, 14, 15),
        dt.datetime(2001, 2, 1, 11, 14, 15),
        dt.datetime(2001, 2, 1, 12, 14, 15),
        dt.datetime(2001, 2, 1, 13, 14, 15),
        dt.datetime(2001, 2, 2,  9, 14, 15),
        dt.datetime(2001, 2, 2, 10, 14, 15),
        dt.datetime(2001, 2, 2, 11, 14, 15),
        dt.datetime(2001, 2, 2, 12, 14, 15),
        dt.datetime(2001, 2, 2, 13, 14, 15),
    ]),
    expect_pixels = np.array([[255,255]], dtype="u1"),
)

