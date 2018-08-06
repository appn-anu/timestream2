
bin/protobuf_test: protobuf_test.cc pb/ts_image.pb.cc
	mkdir -p bin
	$(CXX) -std=c++14 -o $@ $^ -O3 -static -static-libstdc++ -static-libgcc -lprotobuf -lz -lboost_system -lboost_filesystem -lpthread

pb/%.pb.cc pb/%.pb.h: %.proto
	protoc --cpp_out=pb $<
