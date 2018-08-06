
bin/protobuf_test: protobuf_test.cc pb/ts_image.pb.cc
	mkdir -p bin
	$(CXX) -o $@ $^ -lprotobuf -lz

pb/%.pb.cc pb/%.pb.h: %.proto
	protoc --cpp_out=pb $<
