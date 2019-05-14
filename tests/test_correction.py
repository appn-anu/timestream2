from pyts2.pipeline import *
from pyts2.pipeline.correction import ColourCorrectImageStep
from pyts2 import *

from .data import *
from .utils import *

import pytest
import numpy as np
from io import BytesIO
from os import path as op


@pytest.mark.remote_data
def test_correct(largedata):
    img = TimestreamImage.from_path(largedata("GC37L/GC37L_2019_04_01_12_00_00.jpg"))

    corr = ColourCorrectImageStep()

    imgcorr = corr.process_file(img)

    import matplotlib.pyplot as plt
    plt.imshow(imgcorr.rgb_8)
    plt.show()
