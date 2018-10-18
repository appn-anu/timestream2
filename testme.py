from pyts2.tsformats import TSImage, TSv2Stream, find_timestream_images


out = TSv2Stream("test.ts2", "w")

for fp in find_timestream_images("testdata/images"):
    img = TSImage(path=fp)
    print(img.isodate(), img.image.shape)
    out.write(img)

out.close()

for img in TSv2Stream("test.ts2", "r"):
    print(img.isodate(), img.image.shape)
