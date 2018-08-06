#include <iostream>
#include <string>
#include <fstream>

#include "image.hh"
#include "protobufstream.hh"

#include "pb/ts_image.pb.h"

using namespace std;
namespace ts=timestream2;
using namespace protobufstream;


int main(int argc, char *argv[])
{
    if (argc == 1) {
        // ENCODE images from stdin to stdout
        string line;
        opbstream pbo(&cout);
        while (getline(cin, line)) {
            ts::Image img (line);

            timestream2::ImageMsg imgm;
            imgm.set_datetime(img.datetime());
            imgm.set_imgbytes(img.bytes());
            imgm.set_crc32(0);

            pbo << imgm;
        }
    } else {
        // decode from file
        ifstream infile(argv[1], ios_base::in | ios_base::binary);
        ipbstream ipb(&infile);
        timestream2::ImageMsg imgm;
        while (ipb.read(imgm)) {
            cout << imgm.datetime() << '\t' <<  imgm.imgbytes().size() << '\n';
        }
    }
    return 0;
}
