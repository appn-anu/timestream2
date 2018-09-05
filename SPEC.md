# timestream2 Specification

## Definitions:

*TIMESTREAM_DATETIME_PATTERN* : "YYYY\_mm\_DD\_HH\_MM\_SS\_00"

*TIMESTREAM_FILE_PATTERN* : "YYYY/YYYY\_mm/YYYY\_mm\_DD/YYYY\_mm\_DD\_HH\_MM\_SS\_00.[ext]"

## General

* SHALL be statically compilable for x86_64 architecture at least
* SHOULD be reasonably performant on x86_64 architecture
* SHOULD be architected to reduce disk io
* SHALL NOT have hardcoded any specific file paths or file path fragments
* SHALL NOT depend on any 3rd party compiled program or require installation of any 3rd party library or toolchain

## Timestream2 format

* SHALL be encoded using a cross-language, cross-platform binary representation of images and their metadata.
* SHALL be archivable as a single-file dump of a timestream
* SHALL allow stream processing (i.e. allow 

## Module system

* SHOULD allow for easy extensibility through a module system
* this module system SHALL pass data from module to module and SHALL NOT use disk io for this task
* this module system SHALL provide the ability to load configuration files or command line configuration parameters

## Standard modules

inputs are defined as recieved from a previous module

outputs are defined as the data sent to the next module

### resize

inputs:

- image

configuration:

- resolution
- (OPTIONAL) resoution edge case (keep aspect, force, favor height, favor width)
- (OPTIONAL) resampling method

outputs:

- resized image with metadata

### write
- SHALL write images to files based on a provided pattern
- SHALL create directories if needed
- SHALL write images in the correct format based on the extension for the pattern
- SHOULD have reasonable defaults for compression for image formats
- SHOULD error if the specified compression type is not compatible with the output format
- SHOULD write a log file including the images metadata if a log file is specified in the configuration

inputs:

- image with metadata

configuration:

- (OPTIONAL) output path pattern, defaults to the *TIMESTREAM FILE PATTERN* with jpg format
- (OPTIONAL) compression for output file if output file path pattern type supports compression
- (OPTIONAL) path to log file

outputs: 

- image with metadata


### load

- SHALL load image data from disk and infer metadata (such as the time) from the filename or the exif data
- SHALL recurse into directories
- SHOULD NOT error if a corrupt image is encountered, and SHALL NOT pass corrupt images to subsequent tools
- SHOULD parse the timestamp from the filename regardless of the timestamps location within the filename

inputs:

- None

configuration:

- source path
- (OPTIONAL) file timestamp format, defaults to the *TIMESTREAM DATETIME PATTERN* 
- (OPTIONAL) flag to use exif to get the timestamp
- (OPTIONAL) interval parameter on how long to truncate the timestamp, defaults to 0s or no truncation
- (OPTIONAL) remove images from disk after encoding (i.e. "mv" to ts2 formatted stream on stdout).

outputs:

- image with metadata
