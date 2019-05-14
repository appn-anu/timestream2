from .base import *
from .imageio import *

import cv2
import imageio
import skimage as ski
import numpy as np
import matplotlib.pyplot as plt
import scipy as sp
import scipy.ndimage as ndi
from scipy import optimize
import warnings

__all__ = [
    "ColourCorrectImageStep",
]



class ColourCard(object):
    """Base class of all colour cards. Should holds all the methods"""
    @classmethod
    def getCC(CC, cellsize=1):
        ccbig = CC.colours.repeat(cellsize, axis=0).repeat(cellsize, axis=1)
        return ski.img_as_float32(ccbig)

class CameraTrax24ColorCard(ColourCard):
    """APPF-standard CameraTrax 24 Color Card"""
    colours = np.array([
        [[115,  83,  68], [196, 147, 127], [ 91, 122, 155], [ 94, 108,  66], [129, 128, 176], [ 98, 190, 168]],
        [[223, 124,  47], [ 58,  92, 174], [194,  82,  96], [ 93,  60, 103], [162, 190,  62], [229, 158,  41]],
        [[ 49,  66, 147], [ 77, 153,  71], [173,  57,  60], [241, 201,  25], [190,  85, 150], [  0, 135, 166]],
        [[242, 243, 245], [203, 203, 204], [162, 163, 162], [120, 120, 120], [ 84,  84,  84], [ 50,  50,  52]]],
        dtype=np.uint8
    )
    rows = colours.shape[0]
    cols = colours.shape[1]


class ColourCorrector(object):

    def __init__(self, M=None, C=None, G=None):
        self.M = M
        self.C = C
        self.G = G


    def calc_params(self, true_colours, observed_colours):
        pass

    @property
    def as_arg(self):
        arg = np.zeros(9 + 3 + 3)  # (len(M) + len(C) + len(G))
        arg[:9] = self.M.flatten()
        arg[9:12] = self.C.flatten()
        arg[12:15] = self.G.flatten()
        return arg

    @as_arg.setter
    def as_arg(self, arg):
        self.M = arg[:9].reshape((3, 3))
        self.C = arg[9:12]
        self.G = arg[12:15]

    def reset(self):
        self.M = np.eye(3)
        self.C = np.zeros(3)
        self.G = np.ones(3)

    def apply_correction(self, image):
        assert self.M is not None and self.C is not None and self.G is not None
        # I is image as a flat vector of pixels
        I = image.reshape((image.shape[0]*image.shape[1],image.shape[2]), copy=False)
        Icorr = np.clip(np.power(np.dot(I, self.M) + self.C, self.G), 0, 1)
        return Icorr.reshape(image.shape)  # Back to rowsXcolsXdepth

    def optimize(self, CCtrue, CCdet):
        """Finds corrections parameters (M, C, G) s.t. applyCorrection(CCdet, M, C, G) == CCtrue"""
        def residfunc(arg):
            self.as_arg = arg
            return (CCtrue - self.apply_correction(CCdet)).flatten()

        self.reset()
        optim = optimize.least_squares(residfunc, )
        self.as_arg = optim.x


class ColourCorrectImageStep(PipelineStep):
    """Colour corrector step

    params:

        - colourcard: An instance of ColourCard (currently only CameraTrax24ColorCard) that defines
          the "true" colour card values.
        - cc_cellsize: The size of each cell in the colour card in pixels. This should roughly match
          the size of each cell in the colour card captured in each image.
    """

    def __init__(self, colourcard=CameraTrax24ColorCard, cc_cellsize=20):
        self.CC = colourcard
        self.CCsize = cc_cellsize

    def find_CC(self, image):
        def matchCC(I, C):
            if I.shape <= C.shape:
                return (0, None, None)
            x = cv2.matchTemplate(I, C, cv2.TM_CCOEFF_NORMED)
            m = x.max()
            wm = np.unravel_index(x.argmax(), x.shape)
            return(m, wm, x)

        # Find colour card using multi-scale template matching
        CC = ski.img_as_ubyte(self.CC.getCC(self.CCsize))
        CC180 = np.rot90(CC, 2)
        mscore = 0
        mwhich = None
        mscale = None
        morient = 0
        for scale in np.linspace(0.5, 1, 10):
            I = cv2.resize(ski.img_as_ubyte(image), None, fx=scale, fy=scale).astype('u1')
            m, wm, X = matchCC(I, CC)
            if m > mscore:
                mscore = m
                mwhich = wm
                mscale = scale
                morient = 0
            m, wm, X = matchCC(I, CC180)
            if m > mscore:
                mscore = m
                mwhich = wm
                mscale = scale
                morient = 180

        r, c = mwhich

        # Convert from scaled image coordinates to original image coordinates
        r =  int(r/mscale)
        c = int(c/mscale)
        h = int(np.ceil(CC.shape[0]/mscale))
        w = int(np.ceil(CC.shape[1]/mscale))
        cell = int(np.ceil(self.CCsize/mscale))
        subcell = cell//5
        celloff = (cell - subcell)//2

        # Get cropped ROI
        CCdet = image[r:r+h, c:c+w, :]
        if morient == 180:
            CCdet = np.rot90(CCdet, 2)


        # get observed values corresonding to each colour card cell
        obs = np.zeros_like(self.CC.colours)
        for i in range(self.CC.rows):
            for j in range(self.CC.cols):
                t = int(i*cell + celloff)
                b = int(t + subcell)
                l = int(j*cell + celloff)
                r = int(l + subcell)
                obs[i, j, :] = np.median(CCdet[t:b, l:r, :], axis=(0,1))

        return obs

        def process_file(self, file):
            assert hasattr(file, "pixels")  # TODO proper check

            CCdet = self.findCC(file.pixels)
            corrector = ColourCorrector()
            corrector.optimize(self.CC.colours, CCdet)
            file.pixels = corrector.apply_correction(file.pixels)

            return file
