#!/bin/bash

PROTO_SRC="./proto"

# Usage: generate_proto <proto_file_name> <destination_directory>
generate_proto() {
    FILE_NAME=$1
    DEST_DIR=$2

    echo "Generating $FILE_NAME for $DEST_DIR..."

    mkdir -p $DEST_DIR

    # A. Generate the Python gRPC code
    # We use -I . to ensure imports are resolved relative to root if needed
    python3 -m grpc_tools.protoc \
        -I$PROTO_SRC \
        --python_out=$DEST_DIR \
        --grpc_python_out=$DEST_DIR \
        $PROTO_SRC/$FILE_NAME.proto

    # B. THE FIX: Convert absolute imports to relative imports
    # This changes "import customer_pb2" -> "from . import customer_pb2"
    # This prevents the "ModuleNotFoundError" when running inside the /proto subfolder.
    
    # Check for Mac (Darwin) vs Linux for sed syntax
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' 's/^import.*_pb2/from . \0/' $DEST_DIR/*_pb2_grpc.py
    else
        sed -i 's/^import.*_pb2/from . \0/' $DEST_DIR/*_pb2_grpc.py
    fi
    
    # C. Create __init__.py so Python treats this dir as a package
    touch $DEST_DIR/__init__.py
}


# --- 3. Execute Generation Targets ---

# Customer Proto -> Buyer Frontend & Customers Database
generate_proto "customers" "./buyer-frontend/proto"
generate_proto "customers" "./customers-database/proto"

# Products Proto -> Seller Frontend & Products Database
generate_proto "products" "./seller-frontend/proto"
generate_proto "products" "./products-database/proto"
generate_proto "products" "./buyer-frontend/proto"

echo "✅ Done! Protos generated and imports fixed."