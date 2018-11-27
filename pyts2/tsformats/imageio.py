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


class ImageIOError(Exception):
    pass



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

    def __init__(self, path=None, image=None, datetime=None, raw_process_params=None, subsec_index=0):
        self._pixels = None
        self._filelike = None
        self.subsec_index = subsec_index
        if path is None and image is None:
            raise ValueError("One of path or image must be given")

        self.rawparams = raw_process_params
        if isinstance(image, bytes):
            # you can give raw bytes to imageio.imread, so do so
            return self.read_from(image, datetime)

        if path is not None:
            return self.read_from(path, datetime)
        elif datetime is None:
            raise ValueError("Datetime must be given if image is given")

        if not isinstance(image, np.ndarray):
            raise TypeError("image should be an NxMx3 numpy array, uint8 or uint16, or image bytes")

        if isinstance(datetime, str):
            datetime = parse_date(datetime)
        if not isinstance(datetime, dt.datetime):
            raise TypeError("datetime should be datetime.datetime")
        self.datetime = datetime
        self._pixels = image


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

    def read_from(self, filelike, datetime=None):
        """Reads image from a file-like object

        :param filelike: Either a path-like object to a file on disk, or bytes.
            If bytes, datetime must be given.
        :param datetime: A datetime object or timestamp.
        """
        # handle image lazily, just store the filelike for now
        self._filelike = filelike

        # handle datetime
        if datetime is None:
            dtidx = ts_image_path_get_date_index(filelike)
            self.datetime = dtidx["datetime"]
            self.subsec_index = dtidx["index"]
        else:
            self.datetime = parse_date(datetime)
        if not isinstance(self.datetime, dt.datetime):
            raise TypeError("Don't know what to do with your datetime")

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
