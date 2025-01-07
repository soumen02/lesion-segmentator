#!/bin/bash
set -e  # Exit on error

# Check if correct number of arguments provided
if [ "$#" -lt 2 ]; then
    echo "Usage: $0 input_file output_file [gpu|cpu]"
    exit 1
fi

# Clean up any orphaned containers before starting
docker compose down --remove-orphans > /dev/null 2>&1 || true

# Check if input file exists
if [ ! -f "$1" ]; then
    echo "Error: Input file '$1' does not exist"
    exit 1
fi

# Check if output directory exists
OUTPUT_DIR=$(dirname "$2")
if [ ! -d "$OUTPUT_DIR" ]; then
    echo "Creating output directory: $OUTPUT_DIR"
    mkdir -p "$OUTPUT_DIR"
fi

# Get absolute paths
INPUT_FILE=$(realpath "$1")
OUTPUT_FILE=$(realpath "$2")
DEVICE=${3:-gpu}  # Default to GPU if not specified

# Get directories
INPUT_DIR=$(dirname "$INPUT_FILE")
OUTPUT_DIR=$(dirname "$OUTPUT_FILE")
INPUT_FILENAME=$(basename "$INPUT_FILE")
OUTPUT_FILENAME=$(basename "$OUTPUT_FILE")

# Export for docker-compose
export INPUT_DIR=$INPUT_DIR
export OUTPUT_DIR=$OUTPUT_DIR

# Check Docker and nvidia-docker installation if GPU is requested
if [ "$DEVICE" = "gpu" ]; then
    if ! command -v nvidia-smi &> /dev/null; then
        echo "Warning: NVIDIA drivers not found. Falling back to CPU."
        DEVICE="cpu"
    fi
fi

# Run docker-compose with appropriate device setting
if [ "$DEVICE" = "cpu" ]; then
    CUDA_VISIBLE_DEVICES=-1 docker compose run --rm lesion_segmentor \
        /data/input/$INPUT_FILENAME /data/output/$OUTPUT_FILENAME --device cpu
else
    docker compose run --rm lesion_segmentor \
        /data/input/$INPUT_FILENAME /data/output/$OUTPUT_FILENAME
fi

# Clean up after running
docker compose down --remove-orphans > /dev/null 2>&1 || true

# Check if output file was created
if [ ! -f "$OUTPUT_FILE" ]; then
    echo "Error: Output file was not created"
    exit 1
else
    echo "Successfully created: $OUTPUT_FILE"
fi 