FROM pytorch/pytorch:2.0.1-cuda11.7-cudnn8-runtime

WORKDIR /app

# Show build information
RUN echo "Building lesion segmentor container..."

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy the package files
COPY . /app/

# Show what files were copied
RUN ls -la /app/

# Install the package and dependencies
RUN pip install --no-cache-dir -e .

# Create directories
RUN mkdir -p /root/.lesion_segmentor /data/input /data/output

# Show final structure
RUN echo "Final container structure:" && \
    ls -la / && \
    echo "App directory:" && \
    ls -la /app/

# Set the entrypoint to the segmentation script
ENTRYPOINT ["segment_lesions"] 