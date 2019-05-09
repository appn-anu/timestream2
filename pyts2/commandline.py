# Copyright (c) 2018 Kevin Murray <kdmfoss@gmail.com>
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from pyts2 import TimeStream
from pyts2.pipeline import *
from pyts2.utils import CatchSignalThenExit
import argparse as ap
import os
import sys

import click
from click import Choice
from tqdm import tqdm


@click.group()
def tstk_main():
    pass


@tstk_main.command()
@click.option("--force", default=False,
              help="Force writing to an existing stream")
@click.option("--informat", "-F", default=None,
              help="Input image format (use extension as lower case for raw formats)")
@click.option("--bundle", "-b", type=Choice(TimeStream.bundle_levels), default="none",
              help="Level at which to bundle files")
@click.argument("input")
                #help="Input files in timestream format of any form but msgpack")
@click.argument("output")
                #help="Output file or directory")
def bundle(force, informat, format, bundle, input, output):
    input = TimeStream(input, format=informat)
    if os.path.exists(output) and not force:
        click.echo(f"ERROR: output exists: {output}", err=True)
        sys.exit(1)
    output =  TimeStream(output, format=format, bundle_level=bundle)
    for image in input:
        with CatchSignalThenExit():
            output.write(image)
        click.echo(f"Processing {image}")


@tstk_main.command()
@click.option("--output", "-o", required=True,
              help="Output TSV file name")
@click.option("--threads", "-t", default=1,
              help="Number of parallel workers")
@click.option("--informat", "-F", default=None,
              help="Input image format (use extension as lower case for raw formats)")
@click.argument("input")
def audit(output, input, threads=1, informat=None):
    pipe = TSPipeline(
        FileStatsStep(),
        DecodeImageFileStep(),
        ImageMeanColourStep(),
        ScanQRCodesStep(),
    )

    ints = TimeStream(input, format=informat)
    try:
        for image in pipe.process(ints, ncpus=threads):
            if pipe.n % 1000 == 0:
                pipe.report.save(output)
    finally:
        pipe.report.save(output)
        click.echo(f"Audited {input}:{informat}, found {pipe.n} files")


####################################################################################################
#                                              RESIZE                                              #
####################################################################################################
@tstk_main.command()
@click.option("--output", "-o", required=True,
              help="Output TimeStream")
@click.option("--threads", "-t", default=1,
              help="Number of parallel workers")
@click.option("--informat", "-F", default=None,
              help="Input image format (use extension as lower case for raw formats)")
@click.option("--outformat", "-f", default="jpg", type=Choice(("jpg", "png", "tif")),
              help="Output image format")
@click.option("--bundle", "-b", type=Choice(TimeStream.bundle_levels), default="none",
              help="Level at which to bundle files.")
@click.option("--mode", "-m", default='resize', type=Choice(('resize', 'centrecrop')),
              help="Either resize whole image to --size, or crop out central " +
                   "--size pixels at original resolution.")
@click.option("--size", "-s", default='720x',
              help="Output size. Use ROWSxCOLS. One of ROWS or COLS can be omitted to keep aspect ratio.")
@click.argument("input")
def downsize(input, output, threads, informat, outformat, size, bundle, mode):
    if mode == "resize":
        downsizer = ResizeImageStep(geom=size),
    elif mode == "centrecrop" or mode == "crop":
        downsizer = CropCentreStep(geom=size),
    pipe = TSPipeline(
        DecodeImageFileStep(),
        downsizer,
        EncodeImageFileStep(format=outformat),
    )
    ints = TimeStream(input, format=informat)
    outts = TimeStream(output, format=outformat, bundle_level=bundle)
    try:
        pipe.process_to(ints, outts, ncpus=threads)
    finally:
        click.echo(f"{mode} {input}:{informat} to {output}:{outformat}, found {pipe.n} files")


if __name__ == "__main__":
    tstk_main()
