# Copyright (c) 2018 Kevin Murray <kdmfoss@gmail.com>
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import imageio
import numpy as np
import rawpy

class ImageIOError(Exception):
    pass



def ts_imread(image, raw_process_params=None):
    try:
        # str means a path
        if isinstance(image, str):
            base, ext = op.splitext(image)
            if ext.lower() in (".cr2", ".nef"):
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
        - CR2 IO: read to NxMx4 (RGBR) TIFF, 16bit
        - image "names", i.e. the stuff before the underscored dates. Should be
          handeled like datetimes, i.e. parsed from image path, or manually set
          for images given from bytes or numpy arrays.
        - Lazy loading: if given file path, and pixels never accessed, on
          write, just copy/mv file. If given bytes, just write bytes. If pixels
          accessed, the load whole file.
    """

    def __init__(self, path=None, image=None, datetime=None, raw_process_params=None):
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
            raise TypeError("image should be an NxMx3 numpy array, uint8 or uint16")

        if isinstance(datetime, str):
            datetime = jgmtf_date(datetime)
        if not isinstance(datetime, dt.datetime):
            raise TypeError("datetime should be datetime.datetime")
        self.datetime = datetime
        self.image = image


    def read_from(self, filelike, datetime=None):
        # handle image
        image = ts_imread(filelike, raw_process_params=self.rawparams)

        # handle datetime
        if isinstance(datetime, str):
            datetime = jgmtf_date(datetime)
        if datetime is None:
            datetime = ts_image_path_get_date(filelike)

        if not isinstance(datetime, dt.datetime):
            raise ValueError("Don't know what to do with your datetime")

        self.image = image
        self.datetime = datetime

    def as_bytes(self, format="TIFF"):
        return imageio.imwrite('<bytes>', self.image, format=format)

    def isodate(self):
        """convenience helper to get iso8601 string"""
        return self.datetime.strftime("%Y-%m-%dT%H:%M:%S")

    def save(self, output):
        imageio.imwrite(output, self.image)

    @classmethod
    def _fakeimg(cls):
        """Generates a fake image for testing etc."""
        return cls(datetime="2018-10-11T01:02:03",
                   image=np.array([[[0, 1, 2], [3, 4, 5]]], dtype='u1'))
