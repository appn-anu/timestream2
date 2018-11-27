# Copyright (c) 2018 Kevin Murray <kdmfoss@gmail.com>
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from pyts2.tsformats.base import *
from pyts2.tsformats.imageio import *
from pyts2.utils import *

import datetime as dt
import io
import os
import os.path as op
import re
import tarfile
import warnings



def path_is_timestream_file(path, extensions=None):
    """Test if pathname pattern matches the expected

    :param path: File path, with or without directory
    :param path: Optionally, one or more extensions to accept

    >>> path_is_timestream_file("test_2018_12_31_23_59_59_00.jpg")
    True
    >>> path_is_timestream_file("test_2018_12_31_23_59_59_00.jpg", extensions="jpg")
    True
    >>> path_is_timestream_file("test_2018_12_31_23_59_59_00.jpg", extensions="tif")
    False
    >>> path_is_timestream_file("not-a-timestream.jpg")
    False
    """
    if isinstance(extensions, str):
        extensions = [extensions, ]
    try:
        ts_image_path_get_date_index(path)
        if extensions is not None:
            return any([path.lower().endswith(ext) for ext in extensions])
        return True
    except ValueError:
        return False


class TSv1Stream(object):

    def __init__(self, path=None, mode="r", format=None, onerror="warn",
                 raw_process_params=None, bundle_level="none"):
        """path is the base directory of a timestream"""
        self.path = None
        self.name = None
        self.format = None
        self.rawparams = raw_process_params
        self.bundle = bundle_level
        if onerror == "raise" or onerror == "skip" or onerror == "warn":
            self.onerror = onerror
        else:
            raise ValueError("onerror should be one of raise, skip, or warn")
        if path is not None:
            self.open(path, mode, format=format)

    def open(self, path, mode="r", format=None):
        self.name = op.basename(path)
        if format is not None:
            format = format.lstrip(".")
        self.format = format
        self.path = path

    def iter(self):
        def walk_tar(tar):
            tf = tarfile.TarFile(tar)
            for entry in tf:
                if entry.isfile():
                    if path_is_timestream_file(entry.name, extensions=self.format):
                        dtidx = ts_image_path_get_date_index(entry.name)
                        yield TSImage(image=tf.extractfile(entry).read(),
                                      datetime=dtidx["datetime"],
                                      subsec_index=dtidx["index"])

        if op.isfile(self.path) and self.path.lower().endswith(".tar"):
            yield from walk_tar(self.path)
        for root, dirs, files in os.walk(self.path):
            for file in files:
                path = op.join(root, file)
                if path.lower().endswith(".tar"):
                    yield from walk_tar(path)
                if path_is_timestream_file(path, extensions=self.format):
                    yield TSImage(path=path)


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
        return self.iter()

    def close(self):
        pass
