#!/bin/bash

set -e  # Exit on error

# Check if input and output paths are provided
if [ "$#" -lt 2 ]; then
    echo "Usage: $0 <input_path> <output_path> [cpu]"
    exit 1
fi

# Get absolute paths in a cross-platform way
get_absolute_path() {
    local path="$1"
    if [ -e "$path" ]; then
        if command -v realpath >/dev/null 2>&1; then
            realpath "$path"
        else
            echo "$(cd "$(dirname "$path")" && pwd)/$(basename "$path")"
        fi
    else
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
touch "$OUTPUT_PATH" 2>/dev/null

# Get script directory and config directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CONFIG_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"

# Create a temporary build context
BUILD_DIR=$(mktemp -d)
trap 'rm -rf "$BUILD_DIR"' EXIT

# Copy all files from config directory to build directory
cp -r "$CONFIG_DIR"/* "$BUILD_DIR"/ 2>/dev/null || true
cp "$CONFIG_DIR/.dockerignore" "$BUILD_DIR"/ 2>/dev/null || true
cp "$CONFIG_DIR/.env" "$BUILD_DIR"/ 2>/dev/null || true

# Verify required files quietly
required_files=("Dockerfile" "docker-compose.yml" ".dockerignore" ".env" "inference.py" "model.py" "utils.py" "download.py")
missing_files=()

for file in "${required_files[@]}"; do
    if [ ! -f "$BUILD_DIR/$file" ]; then
        missing_files+=("$file")
    fi
done

if [ ${#missing_files[@]} -ne 0 ]; then
    echo "Error: Missing required files: ${missing_files[*]}"
    exit 1
fi

# Export paths for docker-compose
export INPUT_PATH
export OUTPUT_PATH

# Run docker-compose with the specified profile
echo "Starting segmentation..."
if ! docker compose --profile "$PROFILE" up --build --remove-orphans --quiet-pull 2>/dev/null; then
    echo "Error: Segmentation failed"
    exit 1
fi

# Check if output file exists
if [ ! -f "$OUTPUT_PATH" ]; then
    echo "Error: Output file was not created"
    exit 1
fi 