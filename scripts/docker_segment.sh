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

# Create full output directory path
OUTPUT_DIR=$(dirname "$2")
echo "Creating output directory: $OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"

# Check if we can write to the output directory
if [ ! -w "$OUTPUT_DIR" ]; then
    echo "Error: Cannot write to output directory: $OUTPUT_DIR"
    echo "Try: sudo chown -R $USER:$USER $OUTPUT_DIR"
    exit 1
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

# Print paths for debugging
echo "Input path: $INPUT_FILE"
echo "Output path: $OUTPUT_FILE"
echo "Input directory: $INPUT_DIR"
echo "Output directory: $OUTPUT_DIR"

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
    echo "Please check:"
    echo "1. Docker container has write permissions to: $OUTPUT_DIR"
    echo "2. Enough disk space is available"
    echo "3. The path exists inside the container at: /data/output/"
    exit 1
else
    echo "Successfully created: $OUTPUT_FILE"
fi 