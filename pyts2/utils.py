# Copyright (c) 2018 Kevin Murray <kdmfoss@gmail.com>
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import datetime as dt
import warnings

import os
import iso8601


TS_IMAGE_DATEFMT = "%Y_%m_%d_%H_%M_%S"


def nowarnings(func):
    """Decorator to always ignore warnings generated with `func`."""
    def wrapped(*args, **kwargs):
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return func(*args, **kwargs)
    return wrapped


def parse_date(datestr):
    if isinstance(datestr, dt.datetime):
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
        return dt.datetime.strptime(datestr, TS_IMAGE_DATEFMT)
    except:
        pass

    # Add more things here in try-excepts if we want to accept other date
    # formats

    raise ValueError("date string '" + datestr + "' doesn't match valid date formats")



def find_files(base):
    if os.path.exists(base) and os.path.isfile(base):
        yield base
    for root, dirs, files in os.walk(base):
        for file in files:
            yield os.path.join(root, file)
