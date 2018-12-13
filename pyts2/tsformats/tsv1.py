# Copyright (c) 2018 Kevin Murray <kdmfoss@gmail.com>
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from pyts2.tsformats.imageio import *
from pyts2.utils import *

import datetime as dt
import io
import os
import os.path as op
import re
import tarfile
import warnings
import zipfile



def path_is_timestream_file(path, extensions=None):
    """Test if pathname pattern matches the expected

    :param path: File path, with or without directory
    :param path: Optionally, one or more extensions to accept

    >>> path_is_timestream_file("test_2018_12_31_23_59_59_00.jpg")
    True
    >>> path_is_timestream_file("test_2018_12_31_23_59_59_00_1.jpg")
    True
    >>> path_is_timestream_file("2018_12_31_23_59_59_00.jpg")
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
        m = TS_IMAGE_DATETIME_RE.search(path)
        if m is None:
            return False
        if extensions is not None:
            return any([path.lower().endswith(ext) for ext in extensions])
        return True
    except ValueError:
        return False


class TSv1Stream(object):
    bundle_levels = ("root", "year", "month", "day", "hour", "none")

    def __init__(self, path=None, mode="r", format=None, onerror="warn",
                 raw_process_params=None, bundle_level="none", name=None):
        """path is the base directory of a timestream"""
        self.name = name
        self.path = None
        self.format = None
        self.rawparams = raw_process_params
        self.sorted = True
        if bundle_level not in self.bundle_levels:
            raise ValueError("invalid bundle level %s",  bundle_level)
        self.bundle = bundle_level
        if onerror == "raise" or onerror == "skip" or onerror == "warn":
            self.onerror = onerror
        else:
            raise ValueError("onerror should be one of raise, skip, or warn")
        if path is not None:
            self.open(path, mode, format=format)

    def open(self, path, mode="r", format=None):
        if self.name is None:
            self.name = op.splitext(op.basename(path))[0]
        if format is not None:
            format = format.lstrip(".")
        self.format = format
        self.path = path

    def iter(self):
        def walk_archive(path):
            if zipfile.is_zipfile(str(path)):
                with zipfile.ZipFile(str(path)) as zip:
                    # ensure sorted iteration
                    entries = zip.infolist()
                    entries.sort(key=lambda entry: entry.filename)
                    for entry in entries:
                        if entry.is_dir():
                            continue
                        if path_is_timestream_file(entry.filename, extensions=self.format):
                            yield TSImage(image=zip.read(entry),
                                          filename=entry.filename)
            elif tarfile.is_tarfile(path):
                self.sorted = False
                warnings.warn("Extracting images from a tar file. Sorted iteration is not guaranteed")
                with tarfile.TarFile(path) as tar:
                    for entry in tar:
                        if not entry.isfile():
                            continue
                        if path_is_timestream_file(entry.name, extensions=self.format):
                            yield TSImage(image=tar.extractfile(entry).read(),
                                          filename=entry.name)
            else:
                raise ValueError(f"'{path}' appears not to be an archive")

        def is_archive(path):
            return op.exists(path) and op.isfile(path) and \
                (zipfile.is_zipfile(str(path)) or tarfile.is_tarfile(path))

        if is_archive(self.path):
            yield from walk_archive(self.path)

        for root, dirs, files in os.walk(self.path):
            # ensure sorted iteration
            dirs.sort()
            files.sort()
            for file in files:
                path = op.join(root, file)
                if is_archive(path):
                    yield from walk_archive(path)
                if path_is_timestream_file(path, extensions=self.format):
                    yield TSImage(path=path)


    def _timestream_path(self, image):
        """Gets path for timestream image.
        """
        idxstr = ""
        if image.index is not None:
            idxstr = "_" + str(image.index)
        path = "%Y/%Y_%m/%Y_%m_%d/%Y_%m_%d_%H/{name}_%Y_%m_%d_%H_%M_%S_{subsec:02d}{idx}.{ext}"
        path = image.datetime.strftime(path)
        path = path.format(name=self.name, subsec=image.subsecond,
                           idx=idxstr, ext=self.format)
        return path

    def _bundle_archive_path(self, image):
        if self.bundle == "none":
            return None

        if self.bundle == "root":
            return self.path
        elif self.bundle == "year":
            bpath = f"{self.path}/{self.name}_%Y.zip"
        elif self.bundle == "month":
            bpath = f"{self.path}/%Y/{self.name}_%Y_%m.zip"
        elif self.bundle == "day":
            bpath = f"{self.path}/%Y/%Y_%m/{self.name}_%Y_%m_%d.zip"
        elif self.bundle == "hour":
            bpath = f"{self.path}/%Y/%Y_%m/%Y_%m_%d/{self.name}_%Y_%m_%d_%H.zip"
        elif self.bundle == "minute":
            bpath = f"{self.path}/%Y/%Y_%m/%Y_%m_%d/%Y_%m_%d_%H/{self.name}_%Y_%m_%d_%H_%M.zip"
        elif self.bundle == "second":
            bpath = f"{self.path}/%Y/%Y_%m/%Y_%m_%d/%Y_%m_%d_%H/{self.name}_%Y_%m_%d_%H_%M_%S.zip"
        return image.datetime.strftime(bpath)

    def write(self, image):
        if self.name is None or self.format is None:
            raise RuntimeError("TSv2Stream not opened")
        if not isinstance(image, TSImage):
            raise TypeError("image should be a TSImage")
        subpath = self._timestream_path(image)
        if self.bundle == "none":
            outpath = op.join(self.path, subpath)
            os.makedirs(op.dirname(outpath), exist_ok=True)
            image.save(outpath)
        else:
            bundle = self._bundle_archive_path(image)
            os.makedirs(op.dirname(bundle), exist_ok=True)
            with zipfile.ZipFile(bundle, mode="a", compression=zipfile.ZIP_STORED,
                                 allowZip64=True) as zip:
                zip.writestr(op.join(self.name, subpath),
                             image.as_bytes(format=self.format))

    def __iter__(self):
        return self.iter()

    def close(self):
        pass
