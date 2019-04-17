# Copyright (c) 2018 Kevin Murray <kdmfoss@gmail.com>
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from ..time import *
from ..utils import *
from ..timestream import *
from .base import *
from .imageio import *

import numpy as np
import zbarlight
from PIL import Image


class ImageMeanColourStep(PipelineStep):
    def __init__(self, recorder):
        self.recorder = recorder

    def process_file(self, file):
        assert hasattr(file, "pixels")  # TODO proper check
        meancol = file.pixels.mean(axis=(0,1)).astype(int)
        if meancol.shape == ():
            self.recorder.record(file.instant, ImageMeanValue=meancol)
        elif len(meancol) == 3:
            self.recorder.record(file.instant,
                                 ImageMeanRed=meancol[0],
                                 ImageMeanGreen=meancol[1],
                                 ImageMeanBlue=meancol[1])
        return file


class ScanQRCodesStep(PipelineStep):
    def __init__(self, recorder):
        self.recorder = recorder

    def process_file(self, file):
        assert hasattr(file, "pixels")  # TODO proper check

        image = file.pil
        codes = zbarlight.scan_codes('qrcode', image)
        if codes is not None:
            codes = ';'.join([x.decode('utf8') for x in codes])
        self.recorder.record(file.instant, QRCodes=codes)
        return file

