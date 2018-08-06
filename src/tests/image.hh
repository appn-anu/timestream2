//#include <filesystem>
#include <boost/filesystem.hpp>
#include <boost/filesystem/fstream.hpp>
#include <regex>
#include <string>
#include <iostream>

namespace timestream2
{
using namespace std;
//namespace fs = std::filesystem;
namespace fs = boost::filesystem;

class Image
{
public:
    Image ();

    Image (const fs::path &filename)
    {
        // parse datetime
        string datetime (filename.filename().string());
        // this is just for now. fill in date parsing later. Either exif or from filename
        _datetime = datetime;

        // read file
        std::ifstream t(filename.string(), ios_base::in | ios_base::binary);
        std::stringstream buffer;
        buffer << t.rdbuf();
        _bytes = buffer.str();
    }

    Image (const string &bytes, const string &datetime)
        : _bytes(bytes)
        , _datetime(datetime)
    {
    }

    /*
    Image (const ImageMsg &msg)
    {
        _bytes = msg.bytes();
        _datetime = msg.datetime();
    }

    ImageMsg as_message() const
    {
        return ImageMsg()

    }
    */

    string &bytes()
    {
        return _bytes;
    }
    string &datetime()
    {
        return _datetime;
    }


private:
    string _bytes;
    string _datetime;
};

}; /* timestream2 */ 
