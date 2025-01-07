FROM pytorch/pytorch:2.0.1-cuda11.7-cudnn8-runtime

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy the package files
COPY . /app/

# Install the package and dependencies
RUN pip install --no-cache-dir -e .

# Create directory for model weights
RUN mkdir -p /root/.lesion_segmentor

# Create data directories
RUN mkdir -p /data/input /data/output

# Set the entrypoint to the segmentation script
ENTRYPOINT ["segment_lesions"] 