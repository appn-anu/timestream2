class ImageIOError(Exception):
    pass



class TimestreamImage(TimestreamFile):
    """Image class for all timestreams

    Essentially a TimestreamFile with some extra fields for image-only stuff.
    """

    def __init__(self, instant=None, filename=None, fetcher=None, content=None):
        super().__init__(instant=instant, filename=filename, fetcher=fetcher, content=content)
        self._pixels = None

    def mkpixels():
        doc = "The image pixels"
        def fget(self):
            if self._pixels is None:
                self._pixels = ts_imread(self._filelike, raw_process_params=self.rawparams)
            return self._pixels
        def fset(self, value):
            self._pixels = value
        def fdel(self):
            del self._pixels
        return locals()
    pixels = property(**mkpixels())

    def as_bytes(self, format="verbatim"):
        """Returns the bytes representing the image saved in `format`.

        :param format: Image file format as string. See docs for imageio.imwrite(). If
                       `format` is "verbatim", return the source file's bytes
        """
        if format is None or format=="verbatim":
            return self.content
            # catch-all if neither of the above is true
            format = "TIFF"
        return imageio.imwrite('<bytes>', self.pixels, format=format)

    def save(self, outpath):
        """Writes file to `outpath`, in whatever format the extension of `outpath` suggests.

        :param outpath: Path of output file
        """
        imageio.imwrite(outpath, self.pixels)

