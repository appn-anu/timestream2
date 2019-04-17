# Copyright (c) 2018 Kevin Murray <kdmfoss@gmail.com>
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


class TSPipeline(object):
    def __init__(self):
        self.steps = []

    def add_step(self, step):
        if not hasattr(step, "process_file"):
            raise ValueError("step doesn't seem to be a pipeline step")
        self.steps.append(step)
        return self # so one can chain calls

    def process_file(self, file):
        # This should mirror PipelineStep, so an entire pipeline can function
        # as a pipeline step
        for step in self.steps:
            file = step.process_file(file)
            if file is None:
                break
        return file

    def process_from(self, input_stream, ncpus=1):
        if ncpus > 1:
            from multiprocessing import Pool
            pool = Pool(ncpus)
            map = pool.imap
        yield from map(self.process_one, input_stream)

    def process_to(self, input_stream, output, ncpus=1):
        for done in self.process_from(input_stream, ncpus=ncpus):
            output.write(done)

    def write(self, file):
        # needed so that pipelines can be used as files
        pass

    def read(self, file):
        # needed so that pipelines can be used as files
        pass

class PipelineStep(object):

    def process_file(self, file):
        return file


class CopyStep(PipelineStep):
    """Does Nothing"""
    pass


class TeeStep(PipelineStep):
    """Write each file to output, without changing the file"""
    def __init__(self, output):
        self.output = output

    def process_file(self, file):
        self.output.write(file)
        return file
