# Installation Guide

## Prerequisites

### For macOS:
1. Install Docker Desktop for Mac:
```bash
# Using Homebrew
brew install --cask docker

# Or download from: https://www.docker.com/products/docker-desktop
```

2. Start Docker Desktop and wait for it to fully load

### For Linux (Ubuntu/Debian):
1. Install Docker:
```bash
# Add Docker's official GPG key
sudo apt-get update
sudo apt-get install ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Add the repository to Apt sources
echo \
  "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add your user to docker group (optional, to run docker without sudo)
sudo usermod -aG docker $USER
newgrp docker
```

2. For GPU support (Linux only):
```bash
# Install NVIDIA Container Toolkit
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
```

## Installation Steps

1. Clone the repository:
```bash
git clone <repository-url> lesion_segmentor
cd lesion_segmentor
```

2. Make the script executable:
```bash
chmod +x scripts/docker_segment.sh
```

3. Create necessary directories:
```bash
# Create model directory
mkdir -p ~/.lesion_segmentor

# Set proper permissions
sudo chown -R $USER:$USER ~/.lesion_segmentor
```

4. Build the Docker image:
```bash
docker compose build
```

## Testing the Installation

1. Test with CPU mode:
```bash
./scripts/docker_segment.sh \
    path/to/your/input.nii.gz \
    path/to/your/output.nii.gz \
    cpu
```

2. Test with GPU mode (Linux only):
```bash
./scripts/docker_segment.sh \
    path/to/your/input.nii.gz \
    path/to/your/output.nii.gz \
    gpu
```

## Troubleshooting

### Common Issues

1. Docker permission issues:
```bash
# Add user to docker group (Linux)
sudo usermod -aG docker $USER
newgrp docker
```

2. Output directory permission issues:
```bash
# Fix permissions
sudo chown -R $USER:$USER /path/to/output/directory
```

3. Docker disk space issues:
```bash
# Clean up Docker system
docker system prune -a
```

4. For macOS: Docker Desktop settings
- Open Docker Desktop
- Go to Settings -> Resources
- Increase CPU, Memory, and Disk Image size limits as needed

### Verifying Installation

Check if Docker is running:
```bash
docker info
```

Check GPU support (Linux only):
```bash
nvidia-smi
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi
``` 