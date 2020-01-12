all: python go

python: restricter.proto
	python -m grpc_tools.protoc -I . --python_out=api --grpc_python_out=api restricter.proto
	sed -i 's/^\(import.*pb2\)/from . \1/g' api/restricter_pb2_grpc.py

go: restricter.proto
	protoc -I . restricter.proto --go_out=plugins=grpc:api
