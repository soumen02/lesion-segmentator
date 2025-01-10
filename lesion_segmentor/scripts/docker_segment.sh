#!/bin/bash

set -e  # Exit on error
set -x  # Print commands as they are executed

# Check if input and output paths are provided
if [ "$#" -lt 2 ]; then
    echo "Usage: $0 <input_path> <output_path> [cpu]"
    exit 1
fi

# Get absolute paths in a cross-platform way
get_absolute_path() {
    local path="$1"
    # If path exists, use realpath/pwd
    if [ -e "$path" ]; then
        if command -v realpath >/dev/null 2>&1; then
            realpath "$path"
        else
            echo "$(cd "$(dirname "$path")" && pwd)/$(basename "$path")"
        fi
    else
        # For non-existent paths (like output file), construct the path
        local dir=$(dirname "$path")
        local base=$(basename "$path")
        if [ -d "$dir" ]; then
            echo "$(cd "$dir" && pwd)/$base"
        else
            mkdir -p "$dir"
            echo "$(cd "$dir" && pwd)/$base"
        fi
    fi
}

INPUT_PATH=$(get_absolute_path "$1")
OUTPUT_PATH=$(get_absolute_path "$2")
PROFILE=${3:-gpu}  # Default to GPU if not specified

# Create empty output file if it doesn't exist
touch "$OUTPUT_PATH"

# Get script directory and config directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CONFIG_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"

echo "Directory structure:"
echo "SCRIPT_DIR: $SCRIPT_DIR"
echo "CONFIG_DIR: $CONFIG_DIR"
ls -la "$CONFIG_DIR"

# Create a temporary build context
BUILD_DIR=$(mktemp -d)
trap 'rm -rf "$BUILD_DIR"' EXIT

echo "Preparing Docker context in $BUILD_DIR..."

# First, copy all files from config directory to build directory
echo "Copying all files from config directory..."
cp -v "$CONFIG_DIR"/* "$BUILD_DIR"/ 2>/dev/null || true
cp -v "$CONFIG_DIR/.dockerignore" "$BUILD_DIR"/ 2>/dev/null || true
cp -v "$CONFIG_DIR/.env" "$BUILD_DIR"/ 2>/dev/null || true

# Verify required files
required_files=("Dockerfile" "docker-compose.yml" ".dockerignore" ".env" "inference.py" "model.py" "utils.py" "download.py")
missing_files=()

echo "Checking required files in build directory:"
for file in "${required_files[@]}"; do
    if [ ! -f "$BUILD_DIR/$file" ]; then
        echo "Missing: $file"
        missing_files+=("$file")
    else
        echo "Found: $file"
    fi
done

if [ ${#missing_files[@]} -ne 0 ]; then
    echo "Error: Missing required files: ${missing_files[*]}"
    echo "Contents of build directory:"
    ls -la "$BUILD_DIR"
    echo "Contents of config directory:"
    ls -la "$CONFIG_DIR"
    exit 1
fi

# Export paths for docker-compose
export INPUT_PATH
export OUTPUT_PATH

echo "Using paths:"
echo "  Input: $INPUT_PATH"
echo "  Output: $OUTPUT_PATH"
echo "  Profile: $PROFILE"
echo "  Build directory: $BUILD_DIR"
echo "  Config directory: $CONFIG_DIR"

# Run docker-compose with the specified profile
echo "Starting Docker container..."
cd "$BUILD_DIR"  # Change to build directory
if ! docker compose --profile "$PROFILE" up --build --remove-orphans; then
    echo "Docker compose failed"
    echo "Contents of build directory:"
    ls -la
    exit 1
fi

# Check if output file exists
if [ ! -f "$OUTPUT_PATH" ]; then
    echo "Error: Output file was not created"
    exit 1
fi

echo "Segmentation completed successfully!"
echo "Output saved to: $OUTPUT_PATH" 