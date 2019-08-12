from pyts2.timestream import TimestreamFile
from pyts2.time import *

from .utils import *
from .data import *


def test_file(data):
    f = TimestreamFile.from_path(data("images/GC37L~320_2019_04_01_00_00_00.jpg"))

    assert f.instant == TSInstant("2019_04_01_00_00_00")  # FIXME: hand-code the components
    assert f.format == "jpg"
    assert f.md5sum == "f082ca6435195428ea50058edec9c189"

