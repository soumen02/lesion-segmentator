# Lesion Segmentor

A containerized tool for segmenting lesions in FLAIR MRI scans using a pre-trained SegResNet model. The tool supports both GPU and CPU inference.

## Prerequisites

- Docker (>= 20.10.0)
- NVIDIA Container Toolkit (optional, for GPU support on Linux)
  ```bash
  # For Ubuntu
  curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
  curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
  sudo apt-get update
  sudo apt-get install -y nvidia-container-toolkit
  ```

  ### System Compatibility
  - Linux: Supports both GPU (with NVIDIA drivers) and CPU modes
  - macOS: Supports CPU mode only (GPU mode will automatically fall back to CPU)
  - Windows: Supports CPU mode only (GPU mode will automatically fall back to CPU)

## Installation

1. Clone the repository:
```bash
git clone <repository-url> lesion_segmentor
cd lesion_segmentor
```

2. Make the segmentation script executable:
```bash
chmod +x scripts/docker_segment.sh
```

3. Build the Docker image:
```bash
docker compose build
```

## Usage

### Basic Usage

```bash
# Auto-detect mode (recommended)
./scripts/docker_segment.sh input.nii.gz output.nii.gz

# Force CPU mode
./scripts/docker_segment.sh input.nii.gz output.nii.gz cpu

# Force GPU mode (will fall back to CPU if GPU not available)
./scripts/docker_segment.sh input.nii.gz output.nii.gz gpu
```

Example:
```bash
# GPU inference (default)
./scripts/docker_segment.sh \
    /path/to/input/flair.nii.gz \
    /path/to/output/mask.nii.gz

# Force CPU inference
./scripts/docker_segment.sh \
    /path/to/input/flair.nii.gz \
    /path/to/output/mask.nii.gz \
    cpu
```

### Input Requirements

- Input should be a FLAIR MRI scan in NIfTI format (.nii.gz)
- Image should be in standard radiological orientation
- The model expects 3D volumes

### Output

- Binary segmentation mask in NIfTI format (.nii.gz)
- Labels:
  - 0: Background
  - 1: Lesion

## Model Details

The segmentation model uses:
- Architecture: SegResNet
- Input spacing: 0.7 x 0.7 x 0.7 mm
- Sliding window inference with:
  - ROI size: 120 x 120 x 120
  - Batch size: 2
  - Overlap: 0.4

## Troubleshooting

### GPU Issues
If you encounter GPU-related errors:
```bash
# Check NVIDIA drivers
nvidia-smi

# Check NVIDIA Docker
nvidia-docker version

# Force CPU usage if GPU is unavailable
./scripts/docker_segment.sh input.nii.gz output.nii.gz cpu
```

### Permission Issues
If you encounter permission issues:
```bash
# Fix script permissions
chmod +x scripts/docker_segment.sh

# Fix model directory permissions
sudo chown -R $USER:$USER ~/.lesion_segmentor
```

### Docker Issues
If Docker fails to build or run:
```bash
# Clean and rebuild
docker compose down --remove-orphans
docker system prune -f
docker compose build --no-cache
```

### Common Error Messages

1. "NVIDIA drivers not found. Falling back to CPU":
   - GPU is not available or properly configured
   - The script will automatically fall back to CPU mode

2. "Error: Input file does not exist":
   - Check the path to your input file
   - Make sure to use absolute paths or correct relative paths

3. "Error: Output file was not created":
   - Check write permissions in the output directory
   - Ensure enough disk space is available

4. "No such file or directory" for output path:
   ```bash
   # Create the output directory with proper permissions
   sudo mkdir -p /path/to/output/directory
   sudo chown -R $USER:$USER /path/to/output/directory
   
   # Or run the script with sudo if needed
   sudo ./scripts/docker_segment.sh input.nii.gz output.nii.gz
   ```

## License

[Your License Information]

## Citation

If you use this tool in your research, please cite:
[Citation Information] 

### Mac-Specific Issues
```bash
# If you get "realpath: no such file or directory" error:
# Make sure the parent directory of your output file exists:
mkdir -p "$(dirname /path/to/output/mask.nii.gz)"

# Then run the script:
./scripts/docker_segment.sh input.nii.gz output.nii.gz
``` 