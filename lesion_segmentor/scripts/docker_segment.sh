#!/bin/bash

set -e  # Exit on error

# Check if input and output paths are provided
if [ "$#" -lt 2 ]; then
    echo "Usage: $0 <input_path> <output_path> [cpu]"
    exit 1
fi

# Get absolute paths
if command -v realpath >/dev/null 2>&1; then
    INPUT_PATH=$(realpath "$1")
    OUTPUT_PATH=$(realpath -m "$2")  # -m flag to not require output file to exist
else
    # Fallback for systems without realpath
    INPUT_PATH="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
    OUTPUT_PATH="$(cd "$(dirname "$2")" && pwd)/$(basename "$2")"
fi

PROFILE=${3:-gpu}  # Default to GPU if not specified

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PACKAGE_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Copy necessary files to Docker context
echo "Preparing Docker context..."
cp "$PACKAGE_ROOT/inference.py" .
cp "$PACKAGE_ROOT/model.py" .
cp "$PACKAGE_ROOT/utils.py" .

# Export paths for docker-compose
export INPUT_PATH
export OUTPUT_PATH

echo "Using paths:"
echo "  Input: $INPUT_PATH"
echo "  Output: $OUTPUT_PATH"
echo "  Profile: $PROFILE"
echo "  Package root: $PACKAGE_ROOT"

# Run docker-compose with the specified profile
echo "Starting Docker container..."
if ! docker compose --profile "$PROFILE" up --build --remove-orphans; then
    echo "Docker compose failed"
    exit 1
fi

# Check if output file exists
if [ ! -f "$OUTPUT_PATH" ]; then
    echo "Error: Output file was not created"
    exit 1
fi

echo "Segmentation completed successfully!"
echo "Output saved to: $OUTPUT_PATH" 