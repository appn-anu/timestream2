from .base import *
from .imageio import *

import cv2
import imageio
import skimage as ski
import numpy as np
import scipy as sp
from scipy import optimize

import warnings
import sys

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
    colours = ski.img_as_float32(np.array([
        [[115,  83,  68], [196, 147, 127], [ 91, 122, 155], [ 94, 108,  66], [129, 128, 176], [ 98, 190, 168]],
        [[223, 124,  47], [ 58,  92, 174], [194,  82,  96], [ 93,  60, 103], [162, 190,  62], [229, 158,  41]],
        [[ 49,  66, 147], [ 77, 153,  71], [173,  57,  60], [241, 201,  25], [190,  85, 150], [  0, 135, 166]],
        [[242, 243, 245], [203, 203, 204], [162, 163, 162], [120, 120, 120], [ 84,  84,  84], [ 50,  50,  52]]],
        dtype=np.uint8
    ))
    rows = colours.shape[0]
    cols = colours.shape[1]


class ColourCorrectImageStep(PipelineStep):
    """Colour corrector step

    params:

        - colourcard: An instance of ColourCard (currently only CameraTrax24ColorCard) that defines
          the "true" colour card values.
        - cc_cellsize: The size of each cell in the colour card in pixels. This should roughly match
          the size of each cell in the colour card captured in each image.
    """

    def __init__(self, colourcard=CameraTrax24ColorCard, cc_cellsize=20, min_cc_match_score=0.5):
        self.CC = colourcard
        self.CCsize = cc_cellsize
        self.min_cc_match_score=min_cc_match_score
        self.CCpx = ski.img_as_ubyte(self.CC.getCC(self.CCsize))
        self.last_cc_roi = None

    def extract_observed_CC(self, file):
        def matchCC(I, C, mscore, mw, msc, o, sc):
            """does the actual template matching at a given scale"""
            if I.shape <= self.CCpx.shape:
                return (0, None, None)

            x = cv2.matchTemplate(I, C, cv2.TM_CCOEFF_NORMED)
            m = x.max()
            wm = np.unravel_index(x.argmax(), x.shape)
            if m > mscore:
                return(m, wm, sc, 0)

            x = cv2.matchTemplate(I, np.rot90(C, 2), cv2.TM_CCOEFF_NORMED)
            m = x.max()
            wm = np.unravel_index(x.argmax(), x.shape)
            if m > mscore:
                return(m, wm, sc, 180)
            return (mscore, mw, msc, morient)


        # Find colour card using multi-scale template matching
        mscore = 0
        mwhich = None
        mscale = None
        morient = 0

        if self.last_cc_roi is not None:
            # last bbox
            lt, lb, ll, lr = self.last_cc_roi
            lh = lb - lt
            lw = lr - ll
            assert lh > 0 and lw > 0

            # new bbox
            nt = max(lt - (lh/2), 0)
            nb = min(lb + (lh/2), file.pixels.shape[1])
            nl = max(ll - (lw/2), 0)
            nr = min(lr + (lw/2), file.pixels.shape[1])

            last_size = np.round((lb - lt)/self.CC.rows).astype(int)
            CC = ski.img_as_ubyte(self.CC.getCC(last_size))
            mscore, mwhich, mscale, morient = matchCC(file.rgb_8[nt:nb, nl:nr, :], mscore, mwhich, mscale, morient, 1)

        if mscore < self.min_cc_match_score:  # either we had no last ROI, or the last ROI's score was too low.
            for scale in np.linspace(0.05, 1, 20):
                CC=self.CCpx
                I = cv2.resize(ski.img_as_ubyte(file.pixels), None, fx=scale, fy=scale)
                mscore, mwhich, mscale, morient = matchCC(I, CC, mscore, mwhich, mscale, morient, scale)

        if mscore < self.min_cc_match_score:
            raise RuntimeError("Best colour card match is too dissimilar to template, can't correct this image")

        # Convert from scaled image coordinates to original image coordinates
        t =  int(mwhich[0]/mscale)
        b = t + int(np.ceil(CC.shape[0]/mscale))
        l = int(mwhich[1]/mscale)
        r = l + int(np.ceil(CC.shape[1]/mscale))
        cell = int(np.ceil(self.CCsize/mscale))
        subcell = cell//5
        celloff = (cell - subcell)//2

        # Get cropped ROI
        CCdet = file.pixels[t:b, l:r, :]
        if morient == 180:
            CCdet = np.rot90(CCdet, 2)
        self.last_cc_roi = (t, b, l, r)
        file.data["correction"]["CC_roi"] = (t, b, l, r)

        # get observed values corresonding to each colour card cell
        obs = np.zeros_like(self.CC.colours, dtype='float32')
        for i in range(self.CC.rows):
            for j in range(self.CC.cols):
                t = int(i*cell + celloff)
                b = int(t + subcell)
                l = int(j*cell + celloff)
                r = int(l + subcell)
                obs[i, j, :] = np.median(CCdet[t:b, l:r, :], axis=(0,1))
        return obs

    def apply_correction(self, image, M, C, G):
        # I is image as a flat vector of pixels
        I = image.reshape((image.shape[0]*image.shape[1],image.shape[2]))
        Icorr = np.clip(np.power(np.dot(I, M) + C, G), 0, 1)
        return Icorr.reshape(image.shape)  # Back to rowsXcolsXdepth

    def optmize_correction_params(self, CCdet):
        """Finds corrections parameters (M, C, G) s.t. apply_correction(CCdet, M, C, G) == CCtrue"""

        def MCG2arg(M, C, G):
            arg = np.zeros(9 + 3 + 3)  # (len(M) + len(C) + len(G))
            arg[:9] = M.flatten()
            arg[9:12] = C.flatten()
            arg[12:15] = G.flatten()
            return arg

        def arg2MCG(arg):
            M = arg[:9].reshape((3, 3))
            C = arg[9:12]
            G = arg[12:15]
            return M, C, G

        def residfunc(arg):
            M, C, G = arg2MCG(arg)
            return (self.CC.colours - self.apply_correction(CCdet, M, C, G)).flatten()

        optim = optimize.least_squares(residfunc, MCG2arg(np.eye(3), np.zeros(3), np.ones(3)))
        return arg2MCG(optim.x)

    def process_file(self, file):
        assert hasattr(file, "pixels")  # TODO proper check
        file.data["correction"] = {}

        obscolours = self.extract_observed_CC(file)
        M, C, G = self.optmize_correction_params(obscolours)
        new = TimestreamImage.from_timestreamfile(file)
        new.pixels = self.apply_correction(file.pixels, M, C, G)
        new.data["correction"].update({"M": M, "C": C, "G": G})
        return new
