from .base import *
from .imageio import *

import numpy as np
import zbarlight
import skimage as ski


class ResizeImageStep(PipelineStep):
    """Pipeline step which resizes an image to rows * cols"""

    def __init__(self, rows=None, cols=None, scale=None):
        """Initialise step with size. Use None for one dimension to keep aspect ratio"""
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
            newpixels = ski.transform.resize(file.pixels, np.round((rows, cols)),
                                             order=3, anti_aliasing=True)
        return TimestreamImage.from_timestreamfile(file, pixels=newpixels)

