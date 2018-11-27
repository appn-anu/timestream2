# Copyright (c) 2018 Kevin Murray <kdmfoss@gmail.com>
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from pyts2.tsformats.base import *
from pyts2.utils import *

import os
import os.path as op
import tarfile



class TarOrDir(object):

    def __init__(self, input):
        self.input = input

    def walk_paths(self):
        def _walk_tar(tar):
            tf = tarfile.TarFile(tar)
            for entry in tf:
                if entry.isfile():
                    yield op.join(tar, entry.name)


        if not op.isdir(self.input) and self.input.lower().endswith(".tar"):
            yield from _walk_tar(self.input)

        for root, dirs, files in os.walk(self.input):
            for file in files:
                if file.endswith(".tar"):
                    yield from _walk_tar(op.join(root, file))
                else:
                    yield op.join(root, file)

    def walk_contents(self, predictate=lambda f: True):
        for file in self.walk_paths():
            yield (file, self[file])

    def _get_from_tar(self, tar, subitem):
        tf = tarfile.TarFile(op.join(self.input, tar))
        return tf.extractfile(subitem).read()

    def __getitem__(self, item):
        subpaths = item.split("/")
        for i, subpath in enumerate(subpaths):
            fullsubpath = op.join(self.input, subpath[:i])
            remainder = op.join(*subpaths[i:])
            print(fullsubpath)
            if op.isdir(fullsubpath):
                continue
            elif subpath.endswith(".tar") and op.isfile(fullsubpath):
                return self._get_from_tar(fullsubpath, remainder)
            elif op.isfile(fullsubpath + ".tar"):
                return self._get_from_tar(fullsubpath + ".tar", remainder)
            elif op.isfile(fullsubpath):
                with open(fullsubpath, "rb") as fh:
                    return fh.read()
        raise KeyError(item)


