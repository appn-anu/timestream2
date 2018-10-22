# Copyright (c) 2018 Kevin Murray <kdmfoss@gmail.com>
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from .base import PipelineStep


class CopyStep(PipelineStep):
    """Does Nothing"""
    pass


class TeeStep(PipelineStep):
    """Write each image to output, without changing the image"""
    def __init__(self, output):
        self.output = output

    def process_image(self, image):
        self.output.write(image)
        return image
