#!/bin/bash

# Check if input and output paths are provided
if [ "$#" -lt 2 ]; then
    echo "Usage: $0 <input_path> <output_path> [cpu]"
    exit 1
fi

INPUT_PATH="$1"
OUTPUT_PATH="$2"
PROFILE=${3:-gpu}  # Default to GPU if not specified

# Export paths for docker-compose
export INPUT_PATH
export OUTPUT_PATH

# Run docker-compose with the specified profile
docker compose --profile "$PROFILE" up --build

# Check if the segmentation was successful
if [ $? -eq 0 ]; then
    echo "Segmentation completed successfully!"
else
    echo "Segmentation failed!"
    exit 1
fi 