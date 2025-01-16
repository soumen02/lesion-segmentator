FROM pytorch/pytorch:2.0.1-cuda11.7-cudnn8-runtime

WORKDIR /app

# Show build information
RUN echo "Building lesion segmentor container..."

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables for better performance
# Use shell substitution to get CPU count
RUN echo "export OMP_NUM_THREADS=\$(nproc)" >> /etc/profile.d/threading.sh && \
    echo "export MKL_NUM_THREADS=\$(nproc)" >> /etc/profile.d/threading.sh && \
    echo "export NUMEXPR_NUM_THREADS=\$(nproc)" >> /etc/profile.d/threading.sh && \
    echo "export OPENBLAS_NUM_THREADS=\$(nproc)" >> /etc/profile.d/threading.sh

# Source the threading configuration
RUN echo "source /etc/profile.d/threading.sh" >> ~/.bashrc

# Copy the package files
COPY . /app/

# Show what files were copied
RUN ls -la /app/

# Install the package and dependencies
RUN pip install --no-cache-dir -e .

# Create directories
RUN mkdir -p /root/.lesion_segmentor /data/input /data/output /tmp/monai_cache

# Show final structure
RUN echo "Final container structure:" && \
    ls -la / && \
    echo "App directory:" && \
    ls -la /app/

# Set the entrypoint to use the installed CLI
ENTRYPOINT ["lesion-segmentor"] 