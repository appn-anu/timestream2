# Copyright (c) 2018 Kevin Murray <kdmfoss@gmail.com>
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from pyts2.utils import *
from pyts2.tsformats.base import *

import imageio
import numpy as np
import rawpy
import datetime as dt
import os.path as op
import re


TS_IMAGE_DATETIME_RE = re.compile(r"(\d{4}_[0-1]\d_[0-3]\d_[0-2]\d_[0-5]\d_[0-5]\d)(_\d+)?(_\w+)?")
TS_IMAGE_FILE_RE = re.compile(r"\d{4}_[0-1]\d_[0-3]\d_[0-2]\d_[0-5]\d_[0-5]\d(_\d+)?.(\S+)$", re.I)


class ImageIOError(Exception):
    pass


@nowarnings
def ts_imread(image, raw_process_params=None):
    """Read image from file, bytes, or path

    :param image: An image, in any format recognised by either imageio or
        rawpy. NB: if image is a raw image (cr2, nef, rw2), it must be supplied
        as a string containing a path to file (unless imageio can read it)
    :params raw_process_params: Parameters passed to rawpy during raw image
        prostprocessing.
    :return: Numpy array of pixel values
    """
    try:
        # str means a path
        if isinstance(image, str):
            base, ext = op.splitext(image)
            if ext.lower() in (".cr2", ".nef", ".rw2"):
                with rawpy.imread(image) as img:
                    if raw_process_params is None:
                        return img.raw_image.copy()
                    else:
                        return img.postprocess(params=raw_process_params).copy()
            else:
                return imageio.imread(image)
        # bytes is assumed to be either jpeg/tiff/png as bytes.
        elif isinstance(image, bytes):
            return imageio.imread(image)
        # either it's a file object, or some other funky thing. In either case,
        # throw it at imageio and hope for the best
        else:
            return imageio.imread(image)
    except Exception as err:
        raise ImageIOError("Failed to read image:\n" + str(err)) from err



class TSImage(object):
    """Image class for all timestreams

    Essentially only two fields: datetime and image. Image will always be a
    numpy array. datetime will always be datetime.datetime.


    TODO:
        - subsecond image index
        - image "names", i.e. the stuff before the underscored dates. Should be
          handeled like datetimes, i.e. parsed from image path, or manually set
          for images given from bytes or numpy arrays.
        - Lazy loading: if given file path, and pixels never accessed, on
          write, just copy/mv file. If given bytes, just write bytes. If pixels
          accessed, the load whole file.
    """

    def __init__(self, path=None, image=None, datetime=None,
                 raw_process_params=None, subsecond=0, index=None,
                 filename=None):
        self._pixels = None
        self._filelike = None
        self.subsecond = subsecond
        self.index = index
        self.datetime = None
        if path is None and image is None or path is not None and image is not None:
            raise ValueError("One of path or image must be given")

        self.rawparams = raw_process_params

        # Read pixels
        if path is not None:
            self._filelike = path
        elif isinstance(image, bytes):
            # you can give raw bytes to imageio.imread, so do so
            self._filelike = image
        elif not isinstance(image, np.ndarray):
            raise TypeError("image should be an NxMx3 numpy array, uint8 or uint16, or image bytes")
        else:
            self._pixels = image

        # datetime and other info
        if datetime is not None:
            self.datetime = parse_date(datetime)
        if filename is None and path is not None:
            self._set_time_from_filename(path)
        if filename is not None:
            self._set_time_from_filename(filename)

        if self.datetime is None:
            raise ValueError("Datetime must be provided somehow")

    def pixels():
        doc = "The image pixels"
        def fget(self):
            if self._pixels is None:
                self._pixels = ts_imread(self._filelike,
                                         raw_process_params=self.rawparams)
            return self._pixels
        def fset(self, value):
            self._pixels = value
        def fdel(self):
            del self._pixels
        return locals()
    pixels = property(**pixels())

    def as_bytes(self, format=None):
        if format is None:
            if isinstance(self._filelike, bytes):
                return self._filelike
            elif op.isfile(self._filelike):
                with open(self._filelike, "rb") as fh:
                    return fh.read()
            # catch-all if neither of the above is true
            format = "TIFF"
        return imageio.imwrite('<bytes>', self.pixels, format=format)

    def isodate(self):
        """convenience helper to get iso8601 string"""
        return self.datetime.strftime("%Y-%m-%dT%H:%M:%S")

    def save(self, outpath):
        """Writes file to `outpath`, in whatever format the extension of `outpath` suggests.

        :param outpath: Path of output file
        """
        imageio.imwrite(outpath, self.pixels)

    @classmethod
    def _fakeimg(cls):
        """Generates a fake image for testing etc."""
        return cls(datetime="2018-10-11T01:02:03",
                   image=np.array([[[0, 1, 2], [3, 4, 5]]], dtype='u1'))

    def __repr__(self):
        return f"TSImage at {self.isodate()}"

    def _set_time_from_filename(self, path):
        """Extract date and index from path to timestream image

        :param path: File path, with or without directory
        """
        fn = op.splitext(op.basename(path))[0]
        m = TS_IMAGE_DATETIME_RE.search(fn)
        if m is None:
            raise ValueError("path '" + path + "' doesn't contain a timestream date")

        dt, subsec, index = m.groups()

        self.datetime = parse_date(dt)

        if subsec is not None:
            try:
                self.subsecond = int(subsec.lstrip("_"))
            except ValueError:
                self.subsecond = 0

        if index is not None:
            self.index = index.lstrip("_")
