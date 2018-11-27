from pyts2.test.utils import *
from pyts2.tsformats.tarballio import TarOrDir

import itertools
import os
import os.path as op


def nested_files(levels, fileseach):
    for p in itertools.product([str(i) for i in range(fileseach)], repeat=levels):
        print(op.join(*p))


def test_walk():
    olddir = os.getcwd()
    os.chdir("./testdata/test_tarordir")
    t = TarOrDir(".")
    x = list(sorted(t.walk_paths()))
    print(x)
    contents = [
        "./1/1.tar/1/1", "./1/1.tar/1/2",
        "./1/2.tar/2/1", "./1/2.tar/2/2",
        "./2/1.tar/1/1", "./2/1.tar/1/2",
        "./2/2.tar/2/1", "./2/2.tar/2/2",
    ]
    assert(x == contents)
    x = list(sorted(t.walk_contents()))
    assert(x == [(c, b"") for c in contents])
    os.chdir(olddir)


