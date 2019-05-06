# Copyright (c) 2018 Kevin Murray <kdmfoss@gmail.com>
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from pyts2.timestream import *
import datetime as dt
import os

import imageio
import msgpack


class TSv2Stream(object):
    DATE_FORMAT = "%Y-%m-%dT%H:%M:%S" # FIXME: time zones

    def __init__(self, path=None, mode="r"):
        self.sorted = False  # FIXME: support sorted iteration
        self.fh = None
        if path is not None:
            self.open(path, mode)

    def open(self, path, mode="r"):
        if mode not in ("r", "w"):
            raise ValueError("Invalid mode " + mode)
        if isinstance(path, str) or isinstance(path, os.PathLike):
            file = open(path, mode + "b")
        self.fh = file
        if 'r' in mode:
            self.unpacker = msgpack.Unpacker(self.fh)
        if 'w' in mode:
            self.packer = msgpack.Packer()

    def close(self):
        self.packer = None
        self.unpacker = None
        self.fh.close()

    def read(self):
        if self.fh is None or self.fh.closed:
            raise RuntimeError("TSv2Stream not opened")
        msgdict = next(self.unpacker)
        datestr = msgdict[b"datetime"].decode('ascii')
        imgbytes = msgdict[b"image"]
        filename = msgdict[b"filename"].decode("utf8")
        return TimestreamFile(content=imgbytes, instant=TSInstant(datestr), filename=filename)

    def write(self, image):
        if self.fh is None or self.fh.closed:
            raise RuntimeError("TSv2Stream not opened")
        if not isinstance(image, TimestreamFile):
            raise TypeError("image should be a TimestreamFile")
        date_enc = image.instant.datetime.strftime(self.DATE_FORMAT).encode("ascii")
        filename = image.filename.encode("utf8")
        msgdict = {b"datetime": date_enc, b"image": image.content, b'filename': filename}
        self.fh.write(self.packer.pack(msgdict))


    def __iter__(self):
        return self

    def __next__(self):
        res = self.read()
        if res is None:
            raise StopIteraton
        return res
