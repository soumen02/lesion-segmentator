# Lesion Segmentor

A containerized deep learning tool for automated lesion segmentation in FLAIR MRI scans using a pre-trained SegResNet model.

## Installation

1. **Prerequisites**:
   - Python >= 3.8
   - Docker >= 20.10.0
   - NVIDIA Container Toolkit (optional, for GPU support)

2. **Quick Install**:

```bash
   # Create a new conda environment (recommended)
   conda create -n lesion_segmentor python=3.9
   conda activate lesion_segmentor

   # Install the package (will now install all dependencies)
   pip install git+https://github.com/soumen02/lesion-segmentator.git

   # Run the tool
   lesion-segmentor -i /path/to/flair.nii.gz -o /path/to/output.nii.gz

   # The tool will handle Docker setup automatically on first run
```

## Usage

1. **Command Line Interface (Recommended)**:
   ```bash
   # Basic usage
   lesion-segmentor -i /path/to/flair.nii.gz -o /path/to/output.nii.gz

   # Force CPU usage
   lesion-segmentor -i input.nii.gz -o output.nii.gz --cpu

   # Force docker image update
   lesion-segmentor -i input.nii.gz -o output.nii.gz --update
   ```

2. **Docker Direct Usage** (alternative):
   ```bash
   # Clone repository
   git clone https://github.com/soumen02/lesion-segmentator.git
   cd lesion-segmentator

   # Build Docker image (CPU version)
   docker compose --profile cpu build

   # Run segmentation
   ./scripts/docker_segment.sh /path/to/flair.nii.gz /path/to/output.nii.gz
   ```

3. **Environment Variables** (optional):
   ```bash
   # Customize directories for docker
   export INPUT_DIR=/path/to/input/directory   # Default: /tmp
   export OUTPUT_DIR=/path/to/output/directory # Default: /tmp
   export MODEL_DIR=/path/to/model/directory   # Default: ~/.lesion_segmentor
   ```

## Important Notes

- Input must be a FLAIR MRI in NIfTI format (.nii.gz)
- Output will be a binary mask (0: Background, 1: Lesion)
- The tool will automatically:
  - Build/update Docker images as needed
  - Use GPU if available, fallback to CPU if not
  - Create output directories if they don't exist

## Troubleshooting

1. **Common Issues**:
   ```bash
   # If Docker is not running
   sudo systemctl start docker

   # If you don't have Docker permissions
   sudo usermod -aG docker $USER  # Then log out and back in

   # If GPU isn't working
   lesion-segmentor -i input.nii.gz -o output.nii.gz --cpu
   ```

2. **For Help**:
   ```bash
   lesion-segmentor --help
   ```

## Cleanup

If you need to clean up the installation or start fresh:

1. Clean up configuration files:
```bash
lesion-segmentor --clean
```

2. Remove Docker images and containers:
```bash
# Remove the Docker containers
docker rm -f $(docker ps -a -q --filter "name=lesion-segmentor")

# Remove the Docker images
docker rmi -f $(docker images -q lesion-segmentor*)
```

3. Uninstall the package:
```bash
pip uninstall lesion-segmentor
```

4. Clean up cache directory (optional):
```bash
rm -rf "/Users/$USER/Library/Application Support/lesion-segmentor"  # macOS
rm -rf "$HOME/.local/share/lesion-segmentor"  # Linux
```


## Uninstallation
```
# 1. Clean up configuration files
lesion-segmentor --clean

# 2. Remove Docker containers and images
docker rm -f $(docker ps -a -q --filter "name=lesion-segmentor")
docker rmi -f $(docker images -q lesion-segmentor*)

# 3. Uninstall the Python package
pip uninstall lesion-segmentor

# 4. Clean up cache directories (for macOS)
rm -rf "/Users/$USER/Library/Application Support/lesion-segmentor"
rm -rf "$HOME/.local/share/lesion-segmentor"
```


