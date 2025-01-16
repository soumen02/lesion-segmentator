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
    INPUT_FILE="$(basename "$1")"
    OUTPUT_DIR=$(mkdir -p "$(dirname "$2")" && cd "$(dirname "$2")" && pwd)
    OUTPUT_FILE="$(basename "$2")"
else
    # On Linux, use realpath directly
    INPUT_FILE=$(basename "$1")
    OUTPUT_FILE=$(basename "$2")
    INPUT_DIR=$(dirname "$(realpath "$1")")
    OUTPUT_DIR=$(dirname "$(realpath "$2")")
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

# Print paths for debugging
echo "Input path: $INPUT_DIR/$INPUT_FILE"
echo "Output path: $OUTPUT_DIR/$OUTPUT_FILE"

# Export for docker-compose
export INPUT_DIR=$INPUT_DIR
export OUTPUT_DIR=$OUTPUT_DIR
export INPUT_FILE=$INPUT_FILE
export OUTPUT_FILE=$OUTPUT_FILE

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
    docker compose --profile cpu run -it lesion_segmentor
else
    docker compose --profile gpu run -it lesion_segmentor_gpu
fi

# Clean up after running
docker compose down --remove-orphans > /dev/null 2>&1 || true

# Check if output file was created
if [ ! -f "$OUTPUT_DIR/$OUTPUT_FILE" ]; then
    echo "Error: Output file was not created"
    echo "Please check:"
    echo "1. Docker container has write permissions to: $OUTPUT_DIR"
    echo "2. Enough disk space is available"
    echo "3. The path exists inside the container at: /data/output/"
    exit 1
else
    echo "Successfully created: $OUTPUT_DIR/$OUTPUT_FILE"
fi 