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
def test_correct(largedata, data):

    def dotest(path):
        img = TimestreamImage.from_path(path)

        corr = ColourCorrectImageStep(min_cc_match_score=0.5)

        imgcorr = corr.process_file(img)

        assert not np.allclose(img.rgb_8, imgcorr.rgb_8)
        assert len(imgcorr.data["correction"]) > 0
        t, b, l, r = imgcorr.data["correction"]["CC_roi"]
        #print(imgcorr.data["correction"]["M"])
        #print(imgcorr.data["correction"]["C"])
        #print(imgcorr.data["correction"]["G"])

        #import matplotlib.pyplot as plt
        #plt.imshow(np.hstack((
        #    img.pixels[t:b, l:r, :],
        #    imgcorr.pixels[t:b, l:r, :],
        #)))
        #plt.show()

    # both should work
    dotest(largedata("GC36L_2016_09_30_12_00_00.jpg"))
    dotest(largedata("GC36L_2016_09_30_12_00_00.cr2"))

    # will fail
    #with pytest.raises(RuntimeError):
    #    dotest(largedata("GC37L/GC37L_2019_04_01_12_00_00.cr2"))
    with pytest.raises(Exception):
        dotest(data("images/GC37L~320_2019_04_01_00_00_00.jpg"))


