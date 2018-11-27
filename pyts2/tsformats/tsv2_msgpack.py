# Copyright (c) 2018 Kevin Murray <kdmfoss@gmail.com>
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from .base import *
from .imageio import *
import datetime as dt

import imageio
import msgpack


class TSv2Stream(object):
    DATE_FORMAT = "%Y-%m-%dT%H:%M:%S" # FIXME: time zones

    def __init__(self, path=None, mode="r"):
        self.fh = None
        if path is not None:
            self.open(path, mode)

    def open(self, path, mode="r"):
        if mode not in ("r", "w"):
            raise ValueError("Invalid mode " + mode)
        if isinstance(path, str):
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
        #print(msgdict)
        datestr = msgdict[b"datetime"].decode('ascii')
        imgbytes = msgdict[b"image"]
        return TSImage(image=imgbytes, datetime=datestr)

    def write(self, image):
        if self.fh is None or self.fh.closed:
            raise RuntimeError("TSv2Stream not opened")
        if not isinstance(image, TSImage):
            raise TypeError("image should be a TSImage")
        date_enc = image.datetime.strftime(self.DATE_FORMAT).encode("ascii")
        image_enc = image.as_bytes()
        msgdict = {b"datetime": date_enc,
                   b"image": image_enc}
        #print(msgdict)
        self.fh.write(self.packer.pack(msgdict))

    def write_verbaitm(self, bytesorpath, datetime):
        if self.fh is None or self.fh.closed:
            raise RuntimeError("TSv2Stream not opened")
        if isinstance(datetime, str):
            datetime = parse_date(datetime)
        if not isinstance(bytesorpath, bytes):
            with open(bytesorpath, "rb") as fh:
                bytesorpath = fh.read()
        date_enc = datetime.strftime(self.DATE_FORMAT).encode("ascii")
        msgdict = {b"datetime": date_enc,
                   b"image": bytesorpath}
        self.fh.write(self.packer.pack(msgdict))

    def __iter__(self):
        return self

    def __next__(self):
        res = self.read()
        if res is None:
            raise StopIteraton
        return res
