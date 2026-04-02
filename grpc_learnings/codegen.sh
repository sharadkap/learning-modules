#!/bin/bash

# Ensure we're in the right directory
cd "$(dirname "$0")"

# Generate gRPC Python code from .proto
python3 -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. protos/messenger.proto

echo "✅ Generated gRPC code in protos/ folder."
