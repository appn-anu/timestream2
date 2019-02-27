import numpy as np
import datetime as dt

SMALL_TIMESTREAMS = dict(
    expect_times = [
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
    ],
    expect_pixels = np.array([[255,255]], dtype="u1"),
)

GVLIKE_TIMESTREAM = dict(
    expect_datetime = dt.datetime(2001, 2, 1,  9, 14, 15),
    expect_subsecond = 0,
    expect_indices = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10"],
    expect_pixels = np.array([[255,255]], dtype="u1"),
)
