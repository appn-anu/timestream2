# Copyright (c) 2018 Kevin Murray <kdmfoss@gmail.com>
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import datetime as dt
import io
import os
import os.path as op
import re

import imageio
import iso8601
import numpy as np


TS_IMAGE_DATEFMT = "%Y_%m_%d_%H_%M_%S"
TS_IMAGE_DATETIME_RE = re.compile(r"^\d{4}_[0-1]\d_[0-3]\d_[0-2]\d_[0-5]\d_[0-5]\d")


class ImageIOError(Exception):
    pass


def jgmtf_date(datestr):
    # first, try iso8601 of some form
    try:
        return iso8601.parse_date(datestr)
    except:
        pass
    # Then the usual
    try:
        return dt.datetime.strptime(datestr, TS_IMAGE_DATEFMT)
    except:
        pass

    # Add more things here in try-excepts if we want to accept other date
    # formats

    # Uh-oh, nothing's worked
    raise ValueError("date string '" + datestr + "' doesn't match valid date formats")


def ts_image_path_get_date(path):
    fn = op.basename(path)
    m = TS_IMAGE_DATETIME_RE.match(fn)
    if m is None:
        raise ValueError("path '" + path + "' doesn't contain a timestream date")
    return jgmtf_date(m[0])


class TSImage(object):
    """Image class for all timestreams

    Essentially only two fields: datetime and image. Image will always be a
    numpy array. datetime will always be datetime.datetime.
    """

    def __init__(self, path=None, image=None, datetime=None):
        if path is None and image is None:
            raise ValueError("One of path or image must be given")

        if isinstance(image, bytes):
            # you can give raw bytes to imageio.imread, so do so
            return self.read_from(image, datetime)

        if path is not None:
            return self.read_from(path, datetime)
        elif datetime is None:
            raise ValueError("Datetime must be given if image is given")

        if not isinstance(image, np.ndarray):
            raise TypeError("image should be an NxMx3 numpy array, uint8 or uint16")

        if not isinstance(datetime, dt.datetime):
            raise TypeError("datetime should be datetime.datetime")
        self.datetime = datetime
        self.image = image


    def read_from(self, filelike, datetime=None):
        # handle image
        try:
            image = imageio.imread(filelike)
        except Exception as e:
            raise ImageIOError("Failed to read image: " + str(e))

        # handle datetime
        if isinstance(datetime, str):
            datetime = jgmtf_date(datetime)
        if datetime is None:
            datetime = ts_image_path_get_date(filelike)
        if not isinstance(datetime, dt.datetime):
            raise ValueError("Don't know what to do with your datetime")

        self.image = image
        self.datetime = datetime

    def as_tiff(self):
        return imageio.imwrite('<bytes>', self.image, format="TIFF")

    def isodate(self):
        """convenience helper to get iso8601 string"""
        return self.datetime.strftime("%Y-%m-%dT%H:%M:%S")
