from pyts2.pipeline import *
from pyts2 import *
from .data import *
from .utils import *

import pytest
import numpy as np
from PIL import Image
from io import BytesIO
from os import path as op

class PretendTimestream(object):
    def __init__(self):
        self.files = []

    def write(self, file):
        self.files.append(file)


def test_pipeline():
    fakeout = PretendTimestream()
    pipe = TSPipeline()
    pipe.add_step(TeeStep(fakeout))

    files = []
    for file in pipe(TimeStream("testdata/timestreams/flat")):
        files.append(file)

    for wegot, pretendgot in zip(files, fakeout.files):
        assert wegot is pretendgot


def test_encodedecodestep():
    def encode_decode_roundtrip(format):
        pixels = np.array([[[255,255,255], [0, 0, 0]]], dtype="u1")
        instant = TSInstant.now()
        orig_image = TimestreamImage(instant=instant, pixels=pixels,
                                     filename="pretend.file")

        encoded_image = EncodeImageFileStep(format=format).process_file(orig_image)
        assert isinstance(encoded_image, TimestreamFile)
        assert encoded_image.filename == f"pretend.{format}"
        assert encoded_image.instant == instant

        # More involved checks: parse out the encoded bytes using pil, check format etc.
        pil = Image.open(BytesIO(encoded_image.content))
        expect_fmt = {"tif": "TIFF", "jpg": "JPEG", "png": "PNG"}
        assert pil.format.upper() == expect_fmt[format]
        assert pil.mode == "RGB"

        decoded_image = DecodeImageFileStep().process_file(encoded_image)
        assert isinstance(decoded_image, TimestreamImage)
        assert decoded_image.filename == f"pretend.{format}"
        assert decoded_image.instant == instant
        assert np.array_equal(decoded_image.pixels, pixels)

    for format in ("tif", "jpg", "png"):
        encode_decode_roundtrip(format)


@pytest.mark.remote_data
def test_decoderaw(largedata):
    rawfile = largedata["GC37L_2019_04_11_04_00_00.cr2"]
    tsfile = TimestreamFile.from_path(rawfile)
    decoded_image = DecodeImageFileStep().process_file(tsfile)
    assert isinstance(decoded_image, TimestreamImage)
    assert decoded_image.filename == op.basename(rawfile)
    assert decoded_image.instant == TSInstant("2019_04_11_04_00_00")



def test_imagepixels():
    pixels = np.array([[[255,255,255], [0, 0, 0]]], dtype="u1")
    instant = TSInstant.now()
    image = TimestreamImage(instant=instant, pixels=pixels,
                           filename="pretend.file")

    assert np.array_equal(image.pixels, pixels)
    assert np.array_equal(image.rgb, pixels)
    Lab = np.array([[[100, 0, 0], [0, 0, 0]]])
    assert np.allclose(image.Lab, Lab, atol=0.01)  # the LAB above is rounded
    assert np.array_equal(image.pixels01, pixels/255.0)


