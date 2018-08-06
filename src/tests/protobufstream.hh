#ifndef PROTOBUFSTREAM_HH_RPZWD32W
#define PROTOBUFSTREAM_HH_RPZWD32W

#include <iostream>
#include <string>

#include "google/protobuf/stubs/common.h"
#include "google/protobuf/io/zero_copy_stream.h"
#include "google/protobuf/io/zero_copy_stream_impl.h"
#include "google/protobuf/io/gzip_stream.h"
#include "google/protobuf/io/coded_stream.h"


namespace protobufstream
{
    
using namespace std;
namespace pbio = ::google::protobuf::io;

/************
*  OUTPUT  *
************/

class opbstream
{
public:
    opbstream (ostream *stream)
    {
        _raw_out = new pbio::OstreamOutputStream(stream);
        _gzip_out = new pbio::GzipOutputStream(_raw_out);
        _coded_out = new pbio::CodedOutputStream(_gzip_out);
    }
    virtual ~opbstream ()
    {
        delete _coded_out;
        delete _gzip_out;
        delete _raw_out;
    }

    template <typename MessageT>
    void write(MessageT &message)
    {
        message.SerializeToString(&_buffer);
        _coded_out->WriteVarint64(_buffer.size());
        _coded_out->WriteRaw(_buffer.data(), _buffer.size());
    }

private:
    pbio::ZeroCopyOutputStream *_raw_out;
    pbio::GzipOutputStream *_gzip_out;
    pbio::CodedOutputStream *_coded_out;
    string _buffer;
    /* data */
};

template <typename MessageT>
opbstream& operator<< (opbstream& stream, MessageT& message)
{
    stream.write(message);
    return stream;
}

/***********
*  INPUT  *
***********/

class ipbstream
{
public:
    ipbstream (istream *stream)
    {
        _real_stream = stream;
        _raw_in = new pbio::IstreamInputStream(stream);
        _gzip_in = new pbio::GzipInputStream(_raw_in);
        _coded_in = new pbio::CodedInputStream(_gzip_in);
    }
    virtual ~ipbstream ()
    {
        delete _coded_in;
        delete _gzip_in;
        delete _raw_in;
    }

    template <typename MessageT>
    bool read(MessageT &message)
    {
        uint64_t size = 0;
        if (!_coded_in->ReadVarint64((::google::protobuf::uint64*) &size)) {
            if (_real_stream->eof()) return false;
            throw std::runtime_error("Got size < 0 in protobuf message decoding");
        }
        if (!_coded_in->ReadString(&_buffer, size)) {
            if (_real_stream->eof()) return false;
            throw std::runtime_error("Failed to read messsage string in protobuf message decoding");
        }
        message.ParseFromString(_buffer);
        return true;
    }

private:
    pbio::ZeroCopyInputStream *_raw_in;
    pbio::GzipInputStream *_gzip_in;
    pbio::CodedInputStream *_coded_in;
    string _buffer;
    istream *_real_stream;
    /* data */
};

template <typename MessageT>
ipbstream& operator>> (ipbstream& stream, MessageT& message)
{
    stream.read(message);
    return stream;
}

} /* namespace protobufstream */ 

#endif /* end of include guard: PROTOBUFSTREAM_HH_RPZWD32W */
