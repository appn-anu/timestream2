from pyts2.pipeline import *
from pyts2 import *
from .data import *

import numpy as np
from PIL import Image
from io import BytesIO

class PretendTimestream(object):
    def __init__(self):
        self.files = []

    def write(self, file):
        self.files.append(file)


def test_pipeline():
    pass


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
