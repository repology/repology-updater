all: distri_pb2.py distri_pb2.pyi

fetch::
	@echo "Fetching distri.proto..."
	wget -qO- https://raw.githubusercontent.com/distr1/distri/master/LICENSE | sed -e 's|^|// |' > distri.proto
	wget -qO- https://raw.githubusercontent.com/distr1/distri/master/pb/build.proto >> distri.proto

distri_pb2.py: distri.proto
	protoc --python_out=. distri.proto

distri_pb2.pyi: distri.proto
	protoc --pyi_out=. distri.proto
