#!/bin/bash
set -e  # Exit on error

# Function to check if system has NVIDIA GPU support
check_gpu_support() {
    # Check if running on macOS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        return 1
    fi
    
    # Check for nvidia-smi
    if ! command -v nvidia-smi &> /dev/null; then
        return 1
    fi
    
    # Check for NVIDIA runtime in Docker
    if ! docker info 2>/dev/null | grep -q "NVIDIA"; then
        return 1
    fi
    
    return 0
}

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

# Get absolute paths (Mac-compatible version)
if [[ "$OSTYPE" == "darwin"* ]]; then
    # On Mac, use directory realpath and then append filename
    INPUT_DIR=$(cd "$(dirname "$1")" && pwd)
    INPUT_FILE="${INPUT_DIR}/$(basename "$1")"
    OUTPUT_DIR=$(mkdir -p "$(dirname "$2")" && cd "$(dirname "$2")" && pwd)
    OUTPUT_FILE="${OUTPUT_DIR}/$(basename "$2")"
else
    # On Linux, use realpath directly
    INPUT_FILE=$(realpath "$1")
    OUTPUT_FILE=$(realpath "$2")
    INPUT_DIR=$(dirname "$INPUT_FILE")
    OUTPUT_DIR=$(dirname "$OUTPUT_FILE")
fi

# Create output directory
echo "Creating output directory: $OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"

# Check if we can write to the output directory
if [ ! -w "$OUTPUT_DIR" ]; then
    echo "Error: Cannot write to output directory: $OUTPUT_DIR"
    echo "Try: sudo chown -R $USER:$USER $OUTPUT_DIR"
    exit 1
fi

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

# Determine if GPU is available and requested
DEVICE=${3:-auto}  # Default to auto-detect
if [ "$DEVICE" = "auto" ]; then
    if check_gpu_support; then
        DEVICE="gpu"
    else
        DEVICE="cpu"
        echo "GPU support not detected, using CPU mode"
    fi
fi

# Run docker-compose with appropriate configuration
if [ "$DEVICE" = "gpu" ]; then
    if ! check_gpu_support; then
        echo "Error: GPU mode requested but GPU support not available"
        echo "Falling back to CPU mode"
        DEVICE="cpu"
    fi
fi

# Run the appropriate service
if [ "$DEVICE" = "cpu" ]; then
    docker compose --profile cpu run --rm lesion_segmentor \
        /data/input/$INPUT_FILENAME /data/output/$OUTPUT_FILENAME --device cpu
else
    docker compose --profile gpu run --rm lesion_segmentor_gpu \
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