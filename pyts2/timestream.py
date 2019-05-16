# Copyright (c) 2018 Kevin Murray <kdmfoss@gmail.com>
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from pyts2.time import *
from pyts2.utils import *


import datetime as dt
import io
import os
import os.path as op
import re
import tarfile
import warnings
import zipfile
from pathlib import Path
import hashlib


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
        m = TS_DATETIME_RE.search(path)
        if m is None:
            return False
        if extensions is not None:
            return any([path.lower().endswith(ext) for ext in extensions])
        return True
    except ValueError:
        return False


class ZipContentFetcher(object):
    def __init__(self, zipfile, pathinzip):
        self.zipfile = zipfile
        self.pathinzip = pathinzip

    def get(self):
        with zipfile.ZipFile(str(self.zipfile)) as zfh:
            return zfh.read(self.pathinzip)

class TarContentFetcher(object):
    def __init__(self, tarfile, pathintar):
        self.tarfile = tarfile
        self.pathintar = pathintar

    def get(self):
        with tarfile.TarFile(self.tarfile) as tfh:
            return tar.extractfile(self.pathintar).read()


class FileContentFetcher(object):
    def __init__(self, path):
        self.path = Path(path)

    def get(self):
        with open(self.path, "rb") as fh:
            return fh.read()



class TimestreamFile(object):
    '''A container class for files in timestreams'''
    def __init__(self, instant=None, filename=None, fetcher=None, content=None, report=None, data=dict()):
        self.instant = instant
        self.filename = filename
        self.fetcher = fetcher
        self.data = data
        self._content = content
        # a report from various pipeline components on this file
        if report is None:
            report = dict()
        self.report = report
        if self.instant is None and self.filename is not None:
            self.instant = TSInstant.from_path(self.filename)
        if self.instant is None:
            raise ValueError("TimestreamFile must have an instant")
        if self.filename is None:
            raise ValueError("TimestreamFile must have a filename")
        if self.__class__ is TimestreamFile and self._content is None and self.fetcher is None:
            raise ValueError("TimestreamFile must have content (directly or via a fetcher)")

    @property
    def content(self):
        if self._content is None and self.fetcher is not None:
            self._content = self.fetcher.get()
        return self._content

    # TODO: work out where this should go. be careful, as setting here should sync to
    # disc perhaps?
    #@content.setter
    #def _set_content(self, content):
    #    self._content = content

    @classmethod
    def from_path(cls, path, instant=None):
        if instant is None:
            instant = TSInstant.from_path(path)
        return cls(fetcher=FileContentFetcher(path),
                   filename=op.basename(path),
                   instant=instant)

    @classmethod
    def from_bytes(cls, filebytes, filename, instant=None):
        if not isinstance(filebytes, bytes):
            raise ValueError("from_bytes must be given file contents as bytes")
        if instant is None:
            instant = TSInstant.from_path(filename)
        return cls(content=filebytes, filename=filename, instant=instant)

    def isodate(self):
        """convenience helper to get iso8601 string"""
        return self.instant.isodate("%Y-%m-%dT%H:%M:%S")

    def __len__(self):
        return len(self.content)

    def checksum(self, algorithm="md5"):
        hasher = hashlib.new(algorithm)
        hasher.update(self.content)
        return hasher.hexdigest()

    def __repr__(self):
        return self.filename


class TimeStream(object):
    bundle_levels = ("root", "year", "month", "day", "hour", "none")

    def __init__(self, path=None, format=None, onerror="warn",
                 bundle_level="none", name=None):
        """path is the base directory of a timestream"""
        self._files = set() # TODO: add each new entry encountered
        self.name = name
        self.path = None
        self.format = None
        self.sorted = True
        if bundle_level not in self.bundle_levels:
            raise ValueError("invalid bundle level %s",  bundle_level)
        self.bundle = bundle_level
        if onerror == "raise" or onerror == "skip" or onerror == "warn":
            self.onerror = onerror
        else:
            raise ValueError("onerror should be one of raise, skip, or warn")
        if path is not None:
            self.open(path, format=format)

    def open(self, path, format=None):
        if self.name is None:
            self.name = op.basename(path)
            for ext in [".tar", ".zip", f".{format}"]:
                if self.name.lower().endswith(ext):
                    self.name = self.name[:-len(ext)]
        if format is not None:
            format = format.lstrip(".")
        self.format = format
        self.path = path

    @property
    def instants(self):
        return list(sorted(f.instant for f in self.iter(tar_contents=False)))

    def iter(self, tar_contents=True):
        def walk_archive(path):
            if zipfile.is_zipfile(str(path)):
                with zipfile.ZipFile(str(path)) as zip:
                    # ensure sorted iteration
                    entries = zip.infolist()
                    entries.sort(key=lambda entry: extract_datetime(entry.filename))
                    for entry in entries:
                        if entry.is_dir():
                            continue
                        if path_is_timestream_file(entry.filename, extensions=self.format):
                            yield TimestreamFile(filename=entry.filename,
                                                 fetcher=ZipContentFetcher(path, entry.filename))
            elif tarfile.is_tarfile(path):
                self.sorted = False
                warnings.warn("Extracting files from a tar file. Sorted iteration is not guaranteed")
                with tarfile.TarFile(path) as tar:
                    for entry in tar:
                        if not entry.isfile():
                            continue
                        if path_is_timestream_file(entry.name, extensions=self.format):
                            filebytes = tar.extractfile(entry).read()
                            if tar_contents:
                                yield TimestreamFile.from_bytes(filebytes, filename=entry.name)
                            else:
                                yield TimestreamFile(filename=entry.name,
                                                     fetcher=TarContentFetcher(path, entry.name))
            else: raise ValueError(f"'{path}' appears not to be an archive")

        def is_archive(path):
            return op.exists(path) and op.isfile(path) and \
                (zipfile.is_zipfile(str(path)) or tarfile.is_tarfile(path))

        if is_archive(self.path):
            yield from walk_archive(self.path)

        for root, dirs, files in os.walk(self.path):
            # ensure sorted iteration
            dirs.sort()
            files.sort(key=lambda f: extract_datetime(f))
            for file in files:
                path = op.join(root, file)
                if is_archive(path):
                    yield from walk_archive(path)
                if path_is_timestream_file(path, extensions=self.format):
                    yield TimestreamFile.from_path(path)


    def _timestream_path(self, instant):
        """Gets path for timestream file.
        """
        idxstr = ""
        if instant.index is not None:
            idxstr = "_" + str(instant.index)
        path = "%Y/%Y_%m/%Y_%m_%d/%Y_%m_%d_%H/{name}_%Y_%m_%d_%H_%M_%S_{subsec:02d}{idx}.{ext}"
        path = instant.datetime.strftime(path)
        path = path.format(name=self.name, subsec=instant.subsecond,
                           idx=idxstr, ext=self.format)
        return path

    def _bundle_archive_path(self, instant):
        if self.bundle == "none":
            return None
        if self.bundle == "root":
            return f"{self.path}.{self.format}.zip"
        elif self.bundle == "year":
            bpath = f"{self.path}/{self.name}_%Y.{self.format}.zip"
        elif self.bundle == "month":
            bpath = f"{self.path}/%Y/{self.name}_%Y_%m.{self.format}.zip"
        elif self.bundle == "day":
            bpath = f"{self.path}/%Y/%Y_%m/{self.name}_%Y_%m_%d.{self.format}.zip"
        elif self.bundle == "hour":
            bpath = f"{self.path}/%Y/%Y_%m/%Y_%m_%d/{self.name}_%Y_%m_%d_%H.{self.format}.zip"
        elif self.bundle == "minute":
            bpath = f"{self.path}/%Y/%Y_%m/%Y_%m_%d/%Y_%m_%d_%H/{self.name}_%Y_%m_%d_%H_%M.{self.format}.zip"
        elif self.bundle == "second":
            bpath = f"{self.path}/%Y/%Y_%m/%Y_%m_%d/%Y_%m_%d_%H/{self.name}_%Y_%m_%d_%H_%M_%S.{self.format}.zip"
        return instant.datetime.strftime(bpath)

    def write(self, file):
        if self.name is None or self.format is None:
            raise RuntimeError("TSv2Stream not opened")
        if not isinstance(file, TimestreamFile):
            raise TypeError("file should be a TimestreamFile")
        subpath = self._timestream_path(file.instant)
        if self.bundle == "none":
            outpath = op.join(self.path, subpath)
            os.makedirs(op.dirname(outpath), exist_ok=True)
            # TODO this logic should probably live in TSfile
            with open(outpath, 'wb') as fh:
                fh.write(file.content)
        else:
            if self.bundle == "root":
                self.path = str(self.path)
                for ext in [".tar", ".zip", f".{self.format}"]:
                    if self.path.lower().endswith(ext):
                        self.path = self.path[:-len(ext)]
                self.path = Path(self.path)
            bundle = self._bundle_archive_path(file.instant)
            bdir = op.dirname(bundle)
            if bdir:  # i.e. if not $PWD
                os.makedirs(bdir, exist_ok=True)
            # TODO this logic should probably live in TSfile
            with zipfile.ZipFile(bundle, mode="a", compression=zipfile.ZIP_STORED,
                                 allowZip64=True) as zip:
                zip.writestr(op.join(self.name, subpath), file.content)

    def __iter__(self):
        return self.iter()

    def close(self):
        pass
