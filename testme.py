# Copyright (c) 2018 Kevin Murray <kdmfoss@gmail.com>
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from pyts2.tsformats import TSImage, TSv1Stream,  TSv2Stream

out = TSv2Stream("test.ts2", "w")
for img in TSv1Stream("testdata/images"):
    print(img.isodate(), img.image.shape)
    out.write(img)
out.close()

out = TSv1Stream("testdata/TMP", "w")
for img in TSv2Stream("test.ts2", "r"):
    print(img.isodate(), img.image.shape)
    out.write(img)
out.close()
