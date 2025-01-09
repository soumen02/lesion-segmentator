#!/bin/bash

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

# Export paths for docker-compose
export INPUT_PATH
export OUTPUT_PATH

echo "Using paths:"
echo "  Input: $INPUT_PATH"
echo "  Output: $OUTPUT_PATH"
echo "  Profile: $PROFILE"

# Run docker-compose with the specified profile
docker compose --profile "$PROFILE" up --build --remove-orphans

# Check if the segmentation was successful
if [ $? -eq 0 ]; then
    echo "Segmentation completed successfully!"
else
    echo "Segmentation failed!"
    exit 1
fi 