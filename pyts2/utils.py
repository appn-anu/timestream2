# Copyright (c) 2018 Kevin Murray <kdmfoss@gmail.com>
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import datetime as dt
from signal import *
import sys
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


class CatchSignalThenExit(object):
    """Context manager to catch any signals, then exit.

    ```
    with CatchSignalThenExit(exit=True, returncode=1):
        do_something_critical()
    ```

    In the above, if the program receives some signal (SIG{ABRT,INT,TERM,HUP}) during the
    body of the with statement, then at the close of the with statement, exit with status 1.
    """

    def __init__(self, signals=[SIGABRT, SIGINT, SIGTERM, SIGHUP], exit=True, returncode=1):
        self.signals = signals
        self.exit = exit
        self.returncode = returncode
        self.caught = False

    def handler(self, *args):
        print("Caught signal, will terminate when finished", file=sys.stderr)
        self.caught = True

    def __enter__(self):
        for sig in self.signals:
            try:
                signal(sig, self.handler)
            except ValueError:
                pass

    def __exit__(self, *args):
        if self.exit and self.caught:
            sys.exit(self.returncode)
