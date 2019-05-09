from .base import *
from .imageio import *

import numpy as np
import zbarlight
import skimage as ski
import cv2
import re

def geom2rowcol(geom):
    m = re.match(r"^(\d*)[Xx](\d*)$", geom)
    if m is None:
        raise ValueError(f"Invalid image geometry: {geom}")
    rows = int(m[1]) if m[1] else None
    cols = int(m[2]) if m[2] else None
    if rows is None and cols is None:
        raise ValueError(f"Invalid image geometry: {geom}")
    return rows, cols


class ResizeImageStep(PipelineStep):
    """Pipeline step which resizes an image to rows * cols"""

    def __init__(self, rows=None, cols=None, scale=None, geom=None):
        """Initialise step with size. Use None for one dimension to keep aspect ratio"""
        if geom is not None:
            rows, cols = geom2rowcol(geom)
        if rows is None and cols is None and scale is None:
            raise ValueError("One of rows, cols, or scale must be given")
        if scale is not None and (rows is not None or cols is not None):
            raise ValueError("Either specify rows/cols or scale, not both")
        self.scale = scale
        self.dims = (rows, cols)

    def process_file(self, file):
        assert hasattr(file, "pixels")  # TODO proper check

        if self.scale is not None:
            newpixels = ski.transform.rescale(file.pixels, self.scale,
                                              order=3, anti_aliasing=True)
        else:
            orows, ocols, _ = file.pixels.shape
            rows, cols = self.dims
            if rows is None:
                rows = orows * (cols / ocols)
            elif cols is None:
                cols = ocols * (rows / orows)
            rows, cols = np.round((rows, cols)).astype(int)
            # slower scikit-image method
            #newpixels = ski.transform.resize(file.pixels, np.round((rows, cols)),
            #                                 order=3, anti_aliasing=True)

            # opencv does rows/cols backwards as (width, height)
            newpixels = cv2.resize(file.bgr_8, dsize=(cols, rows),
                                   interpolation=cv2.INTER_LANCZOS4)[:, :, ::-1] # back to rgb
        return TimestreamImage.from_timestreamfile(file, pixels=newpixels)

