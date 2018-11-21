# Copyright (c) 2018 Kevin Murray <kdmfoss@gmail.com>
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from pyts2.tsformats.base import *
from pyts2.utils import *

import datetime as dt
import io
import os
import os.path as op
import re
import tarfile
import warnings



TS_IMAGE_DATETIME_RE = re.compile(r"(\d{4}_[0-1]\d_[0-3]\d_[0-2]\d_[0-5]\d_[0-5]\d)(_\d+)?")
TS_IMAGE_FILE_RE = re.compile(r"\d{4}_[0-1]\d_[0-3]\d_[0-2]\d_[0-5]\d_[0-5]\d(_\d+)?.(\S+)$", re.I)


def ts_image_path_get_date_index(path):
    """Extract date and index from path to timestream image

    :param path: File path, with or without directory
    """

    fn = op.splitext(op.basename(path))[0]
    m = TS_IMAGE_DATETIME_RE.search(fn)
    if m is None:
        raise ValueError("path '" + path + "' doesn't contain a timestream date")
    try:
        index = int(m[2].lstrip("_"))
    except:
        index = 0
    return {"date": parse_date(m[1]), "index": index}



def path_is_timestream_file(path):
    """Test if pathname pattern matches the expected

    :param path: File path, with or without directory
    """
    try:
        ts_image_path_get_date_index(path)
        return True
    except ValueError:
        return False


def find_timestream_files(rootdir, format=None):
    """Finds and yields all valid timestream image paths below rootdir"""
    for root, dirs, files in os.walk(rootdir):
        for file in files:
            if format is not None and not file.endswith(format):
                continue
            if path_is_timestream_image(file):
                yield op.join(root, file)


class TSv1Stream(object):

    def __init__(self, path=None, mode="r", format=None, onerror="warn",
                 raw_process_params=None):
        """path is the base directory of a timestream"""
        self.files = None
        self.name = None
        self.format = None
        self.rawparams = raw_process_params
        if onerror == "raise" or onerror == "skip" or onerror == "warn":
            self.onerror = onerror
        else:
            raise ValueError("onerror should be one of raise, skip, or warn")
        if path is not None:
            self.open(path, mode, format=format)

    def open(self, path, mode="r", format=None, files=None):
        self.name = op.basename(path)
        if format is not None:
            format = format.lstrip(".")
        self.format = format
        self.path = path
        if mode == "r":
            if files is None:
                files = find_timestream_files(path, format=format)
            self.files = files
        else:
            self.files = []

    def read(self):
        if self.files is None:
            raise RuntimeError("TSv1Stream not opened")
        for path in self.files:
            try:
                return TSImage(path=path, raw_process_params=self.rawparams)
            except ImageIOError as exc:
                if self.onerror == "raise":
                    raise exc
                elif self.onerror == "warn":
                    warnings.warn(str(exc))


    def _timestream_path(self, image):
        """Gets path for timestream image.
        """
        path = "{base}/%Y/%Y_%m/%Y_%m_%d/%Y_%m_%d_%H/{name}_%Y_%m_%d_%H_%M_%S_00.{ext}"
        path = image.datetime.strftime(path)
        path = path.format(base=self.path, name=self.name, ext=self.format)
        return path


    def write(self, image):
        if self.name is None or self.format is None:
            raise RuntimeError("TSv2Stream not opened")
        if not isinstance(image, TSImage):
            raise TypeError("image should be a TSImage")
        out = self._timestream_path(image)
        os.makedirs(op.dirname(out), exist_ok=True)
        image.save(out)

    def __iter__(self):
        return self

    def __next__(self):
        res = self.read()
        if res is None:
            raise StopIteration
        return res

    def close(self):
        pass
