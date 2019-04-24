# Copyright (c) 2018 Kevin Murray <kdmfoss@gmail.com>
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from ..time import *
from ..utils import *
from ..timestream import *
from .base import PipelineStep

import datetime as dt
import os.path as op
import re
import io
import sys

import imageio
import numpy as np
import rawpy
import skimage as ski
from PIL import Image


class ImageIOError(Exception):
    pass


def raiseimageio(func):
    """Decorator to raise an ImageIOError if anything goes wrong with `func`."""
    def wrapped(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as err:
            raise ImageIOError("Failed to read image: " + str(err)) from err
    return wrapped


class DecodeImageFileStep(PipelineStep):
    """Pipeline step to decode image pixels from file or bytes.

    Read image from file, bytes, or path

    :param image: An image, in any format recognised by either imageio or
        rawpy. NB: if image is a raw image (cr2, nef, rw2), it must be supplied as a
        string containing a path to file (unless imageio can read it)
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
            with rawpy.imread(io.BytesIO(file.content)) as img:
                if self.process_raws:
                    pixels = img.postprocess(**self.decode_options[format].copy())
                else:
                    pixels = img.raw_image.copy()
        else:
            pixels = imageio.imread(file.content)
        return TimestreamImage.from_timestreamfile(file, pixels=pixels)


class EncodeImageFileStep(PipelineStep):
    """Pipeline step to encode pixels to a file('s bytes)."""
    default_options = {
        "jpg": {
            "format": "JPEG-PIL", # engine
            "quality": 95,
            "progressive": True,
            "optimize": True,
            "subsampling": "4:4:4",
        },
        "tif": {
            # These are arugments to PIL's image.save. See note below in process_file
            "format": "TIFF",
            "compression": "tiff_lzw"
        },
        "png": {
            "format": "PNG", # engine
            "optimize": True,
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
            raise ValueError("Unsupported image format '{}'".format(format))
        self.format = format

        self.options = self.default_options[self.format].copy()
        if encode_options:
            self.options.update(encode_options)

    @raiseimageio
    def process_file(self, file):
        if not isinstance(file, TimestreamImage):
            raise TypeError("EncodeImageFile operates on TimestreamImage (not TimestreamFile)")

        base, ext = op.splitext(file.filename)
        filename = f"{base}.{self.format}"

        # TODO: encode exif data for tiff & jpeg
        if self.format == "tif":
            # So tiffs are a bit broken in imageio at the moment. Therefore we need some
            # manual hackery with PIL
            with io.BytesIO() as buf:
                file.pil.save(buf, **self.options)
                content = buf.getvalue()
        else:
            content = imageio.imwrite('<bytes>', file.pixels, **self.options)
        # reinstatiate and demote to a TimestreamFile
        return TimestreamFile(content=content, filename=filename,
                              instant=file.instant, report=file.report)


class TimestreamImage(TimestreamFile):
    """Image class for all timestreams"""

    def __init__(self, instant=None, filename=None, fetcher=None, content=None,
                 report=None, pixels=None, exifdata=None):
        super().__init__(instant, filename, fetcher, content, report)
        self.pixels = pixels
        self.exifdata = exifdata

    def save(self, outpath):
        """Writes file to `outpath`, in whatever format the extension of `outpath` suggests.

        :param outpath: Path of output file
        """
        imageio.imwrite(outpath, self.pixels)

    @property
    def rgb(self):
        return self.pixels

    @property
    def Lab(self):
        return ski.color.rgb2lab(self.pixels)

    @property
    def pixels01(self):
        return self.pixels.astype(np.float64) / np.iinfo(self.pixels.dtype).max

    @property
    def pil(self):
        if self.pixels.dtype == np.uint8:
            return Image.fromarray(self.pixels)
        elif self.pixels.dtype == np.uint16:
            pix = (self.pixels / 256.0).astype(np.uint8)
            return Image.fromarray(pix)

    @staticmethod
    def from_path(path):
        file = TimestreamFile.from_path(path)
        return DecodeImageFileStep().process_file(file)

    @classmethod
    def from_timestreamfile(cls, file, **kwargs):
        """Convenience creator for TSFile -> TSImage conversion"""
        params = {
            "instant": file.instant,
            "filename": file.filename,
            "fetcher": file.fetcher,
            "report": file.report,
        }
        params.update(kwargs)
        return cls(**params)
