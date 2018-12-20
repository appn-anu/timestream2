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
              help="Output image format (use extension as lower case for raw formats. "
                   "Use 'verbatim' to output the source file as is)")
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
        output.write(image)
        click.echo(f"Processing {image}")

if __name__ == "__main__":
    tstk_main()
