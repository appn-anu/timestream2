# Copyright (c) 2018 Kevin Murray <kdmfoss@gmail.com>
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import datetime as dt
from signal import *
import sys
import warnings
import os
import os.path as op
from zipfile import ZipFile, ZIP_STORED
import fasteners


def nowarnings(func):
    """Decorator to always ignore warnings generated with `func`."""
    def wrapped(*args, **kwargs):
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return func(*args, **kwargs)
    return wrapped


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

class LockFile(object):
    def __init__(self, lockpath, attempts=100000):
        self.path = lockpath
        self.attempts = attempts
        self.lock = fasteners.InterProcessLock(self.path)

    def __enter__(self, *args):
        workdir = op.dirname(self.path)
        if not op.exists(workdir):
            os.makedirs(workdir, exist_ok=True)
        self.lock.acquire()
        #while op.exists(self.path) \
        #        and not self.lock.acquire(timeout=0.01) \
        #        and (self.attempts is None or self.attempts > 0):
        #    time.sleep(0.01)
        #if op.exists(self.path) or not self.lock.acquire(timeout=0.1):
        #    raise RuntimeError(f"Can't lock {self.path}")
        #with open(self.path, "a") as f:
        #    pass

    def __exit__(self, *args):
        self.lock.release()
        if op.exists(self.path):
            os.unlink(self.path)
