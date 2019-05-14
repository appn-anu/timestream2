import re
import os
import os.path as op
import zipfile
from io import BytesIO
import json

import pytest
import requests


def wget(url, directory):
    with requests.get(url) as r:
        if "Content-Disposition" in r.headers:
            fname = re.findall("filename=(.+)", r.headers["Content-Disposition"])[0]
        else:
            fname = op.basename(url)
        fname = fname.strip("\"'")
        path = op.join(directory, fname)

        with open(path, 'wb') as fh:
            fh.write(r.content)
        return path


def getdatapath(path):
    return f"tests/data/{path}"

@pytest.fixture
def data():
    return getdatapath


@pytest.fixture
def largedata(request):
    from dulwich import porcelain
    datadir = getdatapath("largedata")
    if not op.exists(datadir):
        porcelain.clone("https://github.com/appf-anu/large_testdata.git", datadir, checkout=True)
    else:
        porcelain.pull(datadir, "https://github.com/appf-anu/large_testdata.git")
    return lambda path: f"{datadir}/{path}"
