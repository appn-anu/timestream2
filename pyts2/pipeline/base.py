# Copyright (c) 2018 Kevin Murray <kdmfoss@gmail.com>
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

class PipelineStep(object):

    def process_image(self, image):
        return image


class TSPipeline(object):
    def __init__(self):
        self.steps = []

    def add_step(self, step):
        if not hasattr(step, "process_image"):
            raise ValueError("step doesn't seem to be a pipeline step")
        self.steps.append(step)
        return self # so one can chain calls

    def process_image(self, image):
        # This should mirror PipelineStep, so an entire pipeline can function
        # as a pipeline step
        for step in self.steps:
            image = step.process_image(image)
            if image is None:
                break
        return image

    def process_from(self, input_stream, ncpus=1):
        if ncpus > 1:
            from multiprocessing import Pool
            pool = Pool(ncpus)
            map = pool.imap
        yield from map(self.process_one, input_stream)

    def process_to(self, input_stream, output, ncpus=1):
        for done in self.process_from(input_stream, ncpus=ncpus):
            output.write(done)

    def write(self, image):
        # needed so that pipelines can be used as files
        pass

    def read(self, image):
        # needed so that pipelines can be used as files
        pass

