# Copyright (c) 2018 Kevin Murray <kdmfoss@gmail.com>
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import datetime
import re
import os.path as op

import iso8601


TS_DATEFMT = "%Y_%m_%d_%H_%M_%S"
TS_DATETIME_RE = re.compile(r"(\d{4}_[0-1]\d_[0-3]\d_[0-2]\d_[0-5]\d_[0-5]\d)(_\d+)?(_\w+)?")


def extract_datetime(path):
    """Extracts the datetime-only portion of a path, or returns the full path"""
    m = TS_DATETIME_RE.search(path)
    if m is None:
        return path
    else:
        return m[0]


def parse_date(datestr):
    '''Parses dates in iso8601-ish formats to datetime.datetime objects'''
    if isinstance(datestr, datetime.datetime):
        return datestr

    # first, try iso8601 of some form
    try:
        date = iso8601.parse_date(datestr)
        # Remove timezone since all dates are assumed to be local time
        # FIXME this is a terrible hack. we need to find a way around this
        # eventually
        return date.replace(tzinfo=None)
    except:
        pass
    # Then the usual
    try:
        return datetime.datetime.strptime(datestr, TS_DATEFMT)
    except:
        pass

    # Add more things here in try-excepts if we want to accept other date
    # formats

    raise ValueError("date string '" + datestr + "' doesn't match valid date formats")


class TSInstant(object):
    """
    TSInstant: a generalised "moment in time", including both timepoint and
    optional index within a timepoint.

    >>> TSInstant(datetime.datetime(2017, 01, 02, 03, 04, 05))
    2017_01_02_03_04_05_00
    >>> TSInstant(datetime.datetime(2017, 01, 02, 03, 04, 05), 0, "0011")
    2017_01_02_03_04_05_00_0011
    """

    def __init__(self, datetime, subsecond=0, index=None):
        self.datetime = parse_date(datetime)
        if subsecond is None:
            subsecond = 0
        self.subsecond = int(subsecond)
        self.index = index

    def __str__(self):
        idx = "" if self.index is None else f"_{self.index}"
        subsec = f"_{self.subsecond:02d}"
        return f"{self.datetime.strftime('%Y_%m_%d_%H_%M_%S')}{subsec}{idx}"


    def __eq__(self, other):
        return (self.datetime, self.subsecond, self.index) == \
               (other.datetime, other.subsecond, other.index)

    def __lt__(self, other):
        if self.index is not None and other.index is not None:
            return (self.datetime, self.subsecond, self.index) < \
                (other.datetime, other.subsecond, other.index)
        else:
            return (self.datetime, self.subsecond) < \
                (other.datetime, other.subsecond)

    def __le__(self, other):
        if self.index is not None and other.index is not None:
            return (self.datetime, self.subsecond, self.index) <= \
                (other.datetime, other.subsecond, other.index)
        else:
            return (self.datetime, self.subsecond) <= \
                (other.datetime, other.subsecond)

    def __gt__(self, other):
        if self.index is not None and other.index is not None:
            return (self.datetime, self.subsecond, self.index) > \
                (other.datetime, other.subsecond, other.index)
        else:
            return (self.datetime, self.subsecond) > \
                (other.datetime, other.subsecond)

    def __ge__(self, other):
        if self.index is not None and other.index is not None:
            return (self.datetime, self.subsecond, self.index) >= \
                (other.datetime, other.subsecond, other.index)
        else:
            return (self.datetime, self.subsecond) >= \
                (other.datetime, other.subsecond)


    def __repr__(self):
        return str(self)

    def iso8601(self):
        return self.datetime.strftime("%Y-%m-%dT%H:%M:%S")

    @classmethod
    def now(cls):
        return cls(datetime.datetime.now())

    @staticmethod
    def from_path(path):
        """Extract date and index from path to timestream image

        :param path: File path, with or without directory
        """
        fn = op.splitext(op.basename(path))[0]
        m = TS_DATETIME_RE.search(fn)
        if m is None:
            raise ValueError("path '" + path + "' doesn't contain a timestream date")

        dt, subsec, index = m.groups()

        datetime = parse_date(dt)

        if subsec is not None:
            try:
                subsec = int(subsec.lstrip("_"))
            except ValueError:
                subsec = 0

        if index is not None:
            index = index.lstrip("_")
        return TSInstant(datetime, subsec, index)


class TimeFilter(object):
    def __init__(self, startdate=None, enddate=None, starttime=None, endtime=None):
        def convert_date(d):
            if isinstance(d, datetime.date):
                return d
            elif isinstance(d, TSInstant):
                return time.datetime.date()
            elif isinstance(d, datetime.datetime):
                return d.date()
            elif isinstance(d, str):
                return parse_date(d).date()
            elif d is None:
                return None
            else:
                TypeError("Bad date")

        def convert_time(t):
            if isinstance(t, datetime.time):
                return t
            elif isinstance(t, TSInstant):
                return t.datetime.time()
            elif isinstance(t, datetime.datetime):
                return t.time()
            elif isinstance(t, str):
                return parse_date(t).time()
            elif t is None:
                return None
            else:
                TypeError("Bad date")

        self.startdate = convert_date(startdate)
        self.enddate = convert_date(enddate)
        if self.startdate is not None and self.enddate is not None and self.startdate > self.enddate:
            raise ValueError("Can't have startdate > enddate")

        self.starttime = convert_time(starttime)
        self.endtime = convert_time(endtime)
        if self.starttime is not None and self.endtime is not None and self.starttime > self.endtime:
            raise ValueError("Can't have starttime > endtime")

    def __call__(self, datetime):
        d = datetime.date()
        t = datetime.time()
        if self.startdate is not None and d < self.startdate:
            return False
        if self.enddate is not None and d > self.enddate:
            return False
        if self.starttime is not None and t < self.starttime:
            return False
        if self.endtime is not None and t > self.endtime:
            return False
        return True
