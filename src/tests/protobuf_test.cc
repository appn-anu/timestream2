#include <iostream>
#include <string>
#include <fstream>
#include "pb/ts_image.pb.h"

#include "google/protobuf/stubs/common.h"
#include "google/protobuf/io/zero_copy_stream.h"
#include "google/protobuf/io/zero_copy_stream_impl.h"
#include "google/protobuf/io/gzip_stream.h"
#include "google/protobuf/io/coded_stream.h"

using namespace std;
using namespace timestream2;

class Image
{
public:
    Image ();

    Image (const string &bytes, const string &datetime)
        : _bytes(bytes)
        , _datetime(datetime)
    {
    }

    virtual ~Image ();

private:
    string _bytes;
    string _datetime;
};


int main(int argc, char *argv[])
{
    if (argc == 1) {
        ::google::protobuf::io::ZeroCopyOutputStream *raw_out =
                      new ::google::protobuf::io::OstreamOutputStream(&cout);
        ::google::protobuf::io::GzipOutputStream *gzip_out =
                      new ::google::protobuf::io::GzipOutputStream(raw_out);
        ::google::protobuf::io::CodedOutputStream *coded_out =
            new ::google::protobuf::io::CodedOutputStream(gzip_out);
        timestream2::ImageMsg imgm;
        string s;
        for (size_t i = 0; i < 10000; i++) {
            imgm.set_datetime("2013_12_11_10_09_08");
            imgm.set_imgbytes("jibberish");
            imgm.SerializeToString(&s);
            coded_out->WriteVarint64(s.size());
            coded_out->WriteRaw(s.data(), s.size());
        }
        delete coded_out;
        delete gzip_out;
        delete raw_out;
    } else {
        ::google::protobuf::io::ZeroCopyInputStream *raw_in =
                      new ::google::protobuf::io::IstreamInputStream(&cin);
        ::google::protobuf::io::GzipInputStream *gzip_in =
                      new ::google::protobuf::io::GzipInputStream(raw_in);
        ::google::protobuf::io::CodedInputStream *coded_in =
                      new ::google::protobuf::io::CodedInputStream(gzip_in);
        timestream2::ImageMsg imgm;
        while (true) {
            uint64_t size = 0;
            coded_in->ReadVarint64((::google::protobuf::uint64*) &size);
            std::string s;
            if (size < 0) break;
            if (!coded_in->ReadString(&s, size)) break;
            imgm.ParseFromString(s);
            cout << imgm.datetime() << '\t' <<  imgm.imgbytes().size() << '\n';
        }
        delete coded_in;
        delete gzip_in;
        delete raw_in;
    }
    return 0;
}
