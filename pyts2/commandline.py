from pyts2.tsformats import TSImage, TSv1Stream,  TSv2Stream
import argparse as ap
import os
import sys

import click
from click import Choice


@click.group()
def tstk_main():
    pass


@tstk_main.command()
@click.option("--force", default=False,
              help="Force writing to an existing stream")
@click.option("--informat", "-F", default=None,
              help="Input image format (use extension as lower case for raw formats)")
@click.option("--format", "-f", default="tif",
              help="Output image format (use extension as lower case for raw formats)")
@click.option("--bundle", "-b", type=Choice(TSv1Stream.bundle_levels), default="none",
              help="Level at which to bundle files")
@click.argument("input")
                #help="Input files in timestream format of any form but msgpack")
@click.argument("output")
                #help="Output file or directory")
def convert(force, informat, format, bundle, input, output):
    input = TSv1Stream(input, format=informat)
    if os.path.exists(output) and not force:
        click.echo(f"ERROR: output exists: {output}", err=True)
        sys.exit(1)
    output =  TSv1Stream(output, format=format, bundle_level=bundle)
    for image in input:
        click.echo(f"processing {image}")
        output.write(image)


def make_ts2():
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
    tstk_main()
