# Lesion Segmentor

A containerized deep learning tool for automated lesion segmentation in FLAIR MRI scans using a pre-trained SegResNet model.

## Setup

1. **Prerequisites**:
   - Docker (>= 20.10.0)
   - NVIDIA Container Toolkit (optional, for GPU support)

2. **Installation**:
   ```bash
   # Clone repository
   git clone <repository-url> lesion_segmentor
   cd lesion_segmentor

   # Make script executable
   chmod +x scripts/docker_segment.sh

   # Build Docker image (CPU version)
   docker compose --profile cpu build

   # Or build GPU version (if you have NVIDIA GPU)
   docker compose --profile gpu build
   ```

## Usage

1. **Basic Usage**:
   ```bash
   ./scripts/docker_segment.sh <input_flair.nii.gz> <output_mask.nii.gz> [cpu|gpu]
   ```

2. **Examples**:
   ```bash
   # Using CPU
   ./scripts/docker_segment.sh /path/to/flair.nii.gz /path/to/output.nii.gz cpu

   # Using GPU (requires NVIDIA GPU and drivers)
   ./scripts/docker_segment.sh /path/to/flair.nii.gz /path/to/output.nii.gz gpu
   ```

3. **Environment Variables** (optional):
   ```bash
   # Customize directories
   export INPUT_DIR=/path/to/input/directory   # Default: /tmp
   export OUTPUT_DIR=/path/to/output/directory # Default: /tmp
   export MODEL_DIR=/path/to/model/directory   # Default: ~/.lesion_segmentor
   ```

4. **Important Notes**:
   - Use absolute paths for input and output
   - Ensure output directory exists and is writable
   - Input must be a FLAIR MRI in NIfTI format (.nii.gz)

## Model Information

- Input: FLAIR MRI scan (.nii.gz)
- Output: Binary mask (0: Background, 1: Lesion)

## Troubleshooting

1. **Common Issues**:
   ```bash
   # If output directory doesn't exist
   mkdir -p /path/to/output/directory

   # If script isn't executable
   chmod +x scripts/docker_segment.sh

   # If GPU isn't working, fall back to CPU
   ./scripts/docker_segment.sh input.nii.gz output.nii.gz cpu
   ```