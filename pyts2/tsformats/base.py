# Copyright (c) 2018 Kevin Murray <kdmfoss@gmail.com>
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from pyts2.utils import *

import os.path as op
import re

TS_IMAGE_DATETIME_RE = re.compile(r"(\d{4}_[0-1]\d_[0-3]\d_[0-2]\d_[0-5]\d_[0-5]\d)(_\d+)?")
TS_IMAGE_FILE_RE = re.compile(r"\d{4}_[0-1]\d_[0-3]\d_[0-2]\d_[0-5]\d_[0-5]\d(_\d+)?.(\S+)$", re.I)


def ts_image_path_get_date_index(path):
    """Extract date and index from path to timestream image

    :param path: File path, with or without directory
    """
    fn = op.splitext(op.basename(path))[0]
    m = TS_IMAGE_DATETIME_RE.search(fn)
    if m is None:
        raise ValueError("path '" + path + "' doesn't contain a timestream date")

    try:
        index = int(m[2].lstrip("_"))
    except:
        index = 0
    return {"datetime": parse_date(m[1]), "index": index}