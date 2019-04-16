# Copyright (c) 2018 Kevin Murray <kdmfoss@gmail.com>
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from pyts2.time import *
from pyts2.utils import *

import imageio
import numpy as np
import rawpy
import datetime as dt
import os.path as op
import re


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
    """

    def __init__(self, path=None, image=None, raw_process_params=None,
                 datetime=None, subsecond=0, index=None, instant=None,
                 filename=None):
        self._pixels = None
        self._filelike = None
        self.instant = instant
        if datetime is not None:
            self.instant = TSInstant(parse_date(datetime), subsecond, index)
        self.path = None  # Should only ever be filled if the image was obtained from disk
        if path is None and image is None or path is not None and image is not None:
            raise ValueError("One of path or image must be given")

        self.rawparams = raw_process_params

        # Read pixels
        if path is not None:
            self.path = path
            self._filelike = path
        elif isinstance(image, bytes):
            # you can give raw bytes to imageio.imread, so do so
            self._filelike = image
        elif not isinstance(image, np.ndarray):
            raise TypeError("image should be an NxMx3 numpy array, uint8 or uint16, or image bytes")
        else:
            self._pixels = image

        # datetime and other info
        if filename is None and path is not None and self.instant is None:
            self.instant = TSInstant.from_path(path)
        elif filename is not None and self.instant is None:
            self.instant = TSInstant.from_path(filename)

        if self.instant is None:
            raise ValueError("Image instant must be provided somehow")

    def pixels():
        doc = "The image pixels"
        def fget(self):
            if self._pixels is None:
                self._pixels = ts_imread(self._filelike, raw_process_params=self.rawparams)
            return self._pixels
        def fset(self, value):
            self._pixels = value
        def fdel(self):
            del self._pixels
        return locals()
    pixels = property(**pixels())

    def as_bytes(self, format="verbatim"):
        """Returns the bytes representing the image saved in `format`.

        :param format: Image file format as string. See docs for imageio.imwrite(). If
                       `format` is "verbatim", return the source file's bytes
        """
        if format is None or format=="verbatim":
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
        return self.instant.isodate("%Y-%m-%dT%H:%M:%S")

    def save(self, outpath):
        """Writes file to `outpath`, in whatever format the extension of `outpath` suggests.

        :param outpath: Path of output file
        """
        imageio.imwrite(outpath, self.pixels)

    @classmethod
    def _fakeimg(cls):
        """Generates a fake image for testing etc."""
        return cls(datetime="2018-10-14T01:02:03",
                   image=np.array([[[0, 1, 2], [3, 4, 5]]], dtype='u1'))

    def __repr__(self):
        if self.path is not None:
            return f"Image at {op.basename(self.path)}"
        else:
            return f"Image at {repr(self.instant)}"
