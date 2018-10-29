#!/usr/bin/env python3
from pyts2.tsformats import TSImage, TSv1Stream,  TSv2Stream, find_timestream_images
import argparse as ap
import rawpy

def main():
    p= ap.ArgumentParser(description="Convert timestream to new format")
    p.add_argument("--verbatim", action="store_true",
                   help="Should we record CR2/NEF RAW image verbatum?")
    p.add_argument("--postprocess-raws", action="store_true",
                   help="Should we decode RAW images to RGB? [default: stay as bayer matrix]")
    p.add_argument("-e", "--on-error", default="warn",
                   choices=["skip", "raise", "warn"],
                   help="What to do if image doesn't load: skip, raise, warn.")
    p.add_argument("-f", "--format", default="jpg",
                   help="Image format (jpg, cr2, png, etc.)")
    p.add_argument("input",
                   help="Input timestream v1 directory")
    p.add_argument("output",
                   help="Output timestream2 file")
    args = p.parse_args()

    rawparam=None
    if args.postprocess_raws:
        rawparam=rawpy.Params(
            output_bps=16,
            use_camera_wb=True,
            demosaic_algorithm=10, # AMAZE
        )
    out = TSv2Stream(args.output, "w")
    if args.verbatim:
        input = find_timestream_images(args.input, args.format)
    else:
        input = TSv1Stream(args.input, format=args.format, onerror="warn",
                            raw_process_params=rawparam)
    for img in input:
        if args.verbatim:
            print(img)
            out.write_verbaitm(img)
        else:
            print(img.isodate(), img.image.shape)
            out.write(img)
    out.close()


if __name__ == "__main__":
    main()
