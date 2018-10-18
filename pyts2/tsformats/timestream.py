# Copyright (c) 2018 Kevin Murray <kdmfoss@gmail.com>
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import re
import os
import os.path as op


TS_IMAGE_FILE_RE = re.compile(r"\d{4}_[0-1]\d_[0-3]\d_[0-2]\d_[0-5]\d_[0-5]\d(_\d\d)")


def file_is_timestream_image(path):
    """Test if filename pattern matches the expected

    :param filename: File path, with or without directory

    >>> file_is_timestream_image("2001_02_03_13_14_15_00.png")
    True
    >>> file_is_timestream_image("with/a/path/2001_02_03_13_14_15_00.png")
    True
    >>> file_is_timestream_image("with/a/path/2001_02_03_13_14_15_00.JPG")
    True
    >>> file_is_timestream_image("with/a/path/2001_02_03_13_14_15_00.CR2")
    True
    >>> file_is_timestream_image("this_aint_a_tsimage.png")
    False
    """
    filename = op.basename(path)
    m = TS_IMAGE_FILE_RE.match(filename)
    return m is not None


def find_timestream_images(rootdir):
    """Finds and yields all valid timestream image paths below rootdir"""
    for root, dirs, files in os.walk(rootdir):
        for file in files:
            if file_is_timestream_image(file):
                yield op.join(root, file)


class TSv1Stream(object):
    pass


