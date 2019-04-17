import re
import os
import os.path as op
import zipfile
from io import BytesIO

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


@pytest.fixture
def largedata(request):
    datadir = "testdata/large/"
    if request.config.cache.get("large_testdata", None) is None:
        with requests.get("https://github.com/appf-anu/large_testdata/archive/master.zip") as r:
            with zipfile.ZipFile(BytesIO(r.content)) as zip:
                zip.extractall(datadir)
                datapaths = {op.basename(filename): op.join(datadir, filename)
                             for filename in zip.namelist()}
                request.config.cache.set("large_testdata", datapaths)
    return request.config.cache.get("large_testdata", {})






