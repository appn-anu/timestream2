# Copyright (c) 2018 Kevin Murray <kdmfoss@gmail.com>
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from pyts2.tsformats.base import *
from pyts2.utils import *

import re
import os
import os.path as op
import warnings
import tarfile


TS_IMAGE_FILE_RE = re.compile(r"\d{4}_[0-1]\d_[0-3]\d_[0-2]\d_[0-5]\d_[0-5]\d(_\d\d)?.(\S+)$", re.I)


def path_is_timestream_image(path):
    """Test if pathname pattern matches the expected

    :param path: File path, with or without directory

    >>> path_is_timestream_image("2001_02_03_13_14_15_00.png")
    True
    >>> path_is_timestream_image("with/a/path/2001_02_03_13_14_15_00.png")
    True
    >>> path_is_timestream_image("with/a/path/2001_02_03_13_14_15_00.JPG")
    True
    >>> path_is_timestream_image("with/a/path/2001_02_03_13_14_15_00.CR2")
    True
    >>> path_is_timestream_image("with/a/path/cameraname_2001_02_03_13_14_15_00.png")
    True
    >>> path_is_timestream_image("with/a/path/cameraname_2001_02_03_13_14_15.jpg")
    True
    >>> path_is_timestream_image("this_aint_a_tsimage.png")
    False
    """
    filename = op.basename(path)
    m = TS_IMAGE_FILE_RE.search(filename)
    return m is not None


class TarOrDir(object):

    def __init__(self, input):
        self.input = input

    def walk_paths(self):
        def _walk_tar(tar):
            tf = tarfile.TarFile(tar)
            for entry in tf:
                if entry.isfile():
                    yield op.join(tar, entry.name)


        if not op.isdir(self.input) and self.input.lower().endswith(".tar"):
            yield from _walk_tar(self.input)

        for root, dirs, files in os.walk(self.input):
            for file in files:
                if file.endswith(".tar"):
                    yield from _walk_tar(op.join(root, file))
                else:
                    yield op.join(root, file)

    def walk_contents(self, predictate=lambda f: True):
        for file in self.walk_paths():
            yield (file, self[file])

    def _get_from_tar(self, tar, subitem):
        tf = tarfile.TarFile(op.join(self.input, tar))
        return tf.extractfile(subitem).read()

    def __getitem__(self, item):
        subpaths = item.split("/")
        for i, subpath in enumerate(subpaths):
            fullsubpath = op.join(self.input, subpath[:i])
            remainder = op.join(*subpaths[i:])
            print(fullsubpath)
            if op.isdir(fullsubpath):
                continue
            elif subpath.endswith(".tar") and op.isfile(fullsubpath):
                return self._get_from_tar(fullsubpath, remainder)
            elif op.isfile(fullsubpath + ".tar"):
                return self._get_from_tar(fullsubpath + ".tar", remainder)
            elif op.isfile(fullsubpath):
                with open(fullsubpath, "rb") as fh:
                    return fh.read()
        raise KeyError(item)



def find_timestream_images(rootdir, format=None):
    """Finds and yields all valid timestream image paths below rootdir"""
    for root, dirs, files in os.walk(rootdir):
        for file in files:
            if format is not None and not file.endswith(format):
                continue
            if path_is_timestream_image(file):
                yield op.join(root, file)

@nowarnings
def gather_images(tarordir, format="jpg"):
    if op.isdir(tarordir):
        files = glob.glob("{base}/*.{ext}".format(base=tarordir, ext=format))
        for file in files:
            try:
                c, d, i, e = filename2dateidx(file)
                if e == format:
                    pix = imageio.imread(file)
                    yield Image(file, c, d, i, e, pix)
            except Exception as e:
                print("Skipping", entry.name, ":", str(e), file=stderr)
    else:
        tf = tarfile.TarFile(tarordir)
        for entry in tf:
            try:
                c, d, i, e = filename2dateidx(entry.name)
                if e == format:
                    pix = imageio.imread(tf.extractfile(entry).read())
                    yield Image(entry.name, c, d, i, e, pix)
            except Exception as e:
                print("Skipping", entry.name, ":", str(e), file=stderr)


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
                files = find_timestream_images(path, format=format)
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
