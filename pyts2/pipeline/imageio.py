# Copyright (c) 2018 Kevin Murray <kdmfoss@gmail.com>
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from pyts2.time import *
from pyts2.utils import *

from .base import PipelineStep

import imageio
import numpy as np
import rawpy
import datetime as dt
import os.path as op
import re
from PIL import Image

class ImageIOError(Exception):
    pass

def raiseimageio(func):
    """Decorator to raise an ImageIOError if anything goes wrong with `func`."""
    def wrapped(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as err:
            raise ImageIOError("Failed to read image:\n" + str(err)) from err
    return wrapped


class DecodeImageFile(PipelineStep):
    """Pipeline step to decode image pixels from file or bytes.

    Read image from file, bytes, or path

    :param image: An image, in any format recognised by either imageio or
        rawpy. NB: if image is a raw image (cr2, nef, rw2), it must be supplied as a string containing a path to file (unless imageio can read it)
    :params raw_process_params: Parameters passed to rawpy during raw image
        prostprocessing.
    :return: Numpy array of pixel values
    """
    default_options = {
        "jpg": {},
        "tif": {},
        "png": {},
        "cr2": {
            "use_camera_wb": True,
            "median_filter_passes": 0, # no median filtering after demosaicing
            "output_bps": 16,
            "auto_bright_thr": 0.001, # Use auto brightness, but only allow clipping 0.1%
        },
    }
    def __init__(self, decode_options=None, process_raws=True):
        self.decode_options = self.default_options
        if decode_options:
            self.decode_options.update(self.decode_options)
        self.process_raws = process_raws

    @raiseimageio
    def process_file(self, file):
        base, ext = op.splitext(file.filename)
        format = ext.lower().strip(".")
        if format in ("cr2", "nef", "rw2"):
            with rawpy.imread(image) as img:
                if self.process_raws:
                    pixels = img.postprocess(params=self.decode_options[ext.lower()]).copy()
                else:
                    pixels = img.raw_image.copy()
        else:
            pixels = imageio.imread(image)
        return TimestreamImage.from_timestreamfile(file, pixels=pixels)

class EncodeImageFile(PipelineStep):
    """Pipeline step to encode pixels to file."""
    default_options = {
        "jpg": {
            "format": "JPEG-PIL", # engine
            "pilmode": "RGB",
            "quality": 95,
            "progressive": True,
            "optimise": True,
            "subsampling": "4:4:4",
        },
        "tif": {
            "format": "TIFF-PIL", # engine
            "compression": "tiff_lzw"
        },
        "png": {
            "format": "TIFF-PIL", # engine
        },
    }
    def __init__(self, format="tiff", encode_options=None):
        # Normalise format
        format = format.lower()
        if format == "jpeg":
            format = "jpg"
        if format == "tiff":
            format = "tif"

        if format not in self.default_options:
            raise ValueError("invalid image format '{}'".format(format))

        self.options = self.default_options[self.format]
        if encode_options:
            self.options.update(encode_options)

    @raiseimageio
    def process_file(self, file):
        """Returns the bytes representing the image saved in `format`.

        :param format: Image file format as string. See docs for imageio.imwrite(). If
                       `format` is "verbatim", return the source file's bytes
        """
        if not isinstance(file, TimestreamImage):
            raise TypeError("EncodeImageFile operates on TimestreamImage (not TimestreamFile)")

        base, ext = op.splitext(self.filename)
        filename = f"{base}.{self.format}"

        # TODO: encode exif data for tiff & jpeg
        content = imageio.imwrite('<bytes>', self.pixels, **self.options)
        return TimestreamFile(content=content, filename=filename, instant=file.instant)




class TimestreamImage(TimestreamFile):
    """Image class for all timestreams"""

    def __init__(self, instant=None, filename=None, fetcher=None, content=None, pixels=None, exifdata=None):
        super().__init__(instant, filename, fetcher, content)
        self.pixels = pixels
        self.exifdata = exifdata

    def save(self, outpath):
        """Writes file to `outpath`, in whatever format the extension of `outpath` suggests.

        :param outpath: Path of output file
        """
        imageio.imwrite(outpath, self.pixels)

    @classmethod
    def from_timestreamfile(cls, file, **kwargs):
        """Convenience creator for TSFile -> TSImage conversion"""
        params = {
            "instant": file.instant,
            "filename": file.filename,
            "fetcher": file.fetcher,
        }.update(kwargs)
        cls(**params)

