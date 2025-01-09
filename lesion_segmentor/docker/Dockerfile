FROM pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Install Python packages
RUN pip install --no-cache-dir \
    monai>=1.2.0 \
    nibabel>=4.0.0 \
    numpy>=1.21.0 \
    scikit-image>=0.19.0

# Copy necessary files
COPY . /app/

# Set environment variables
ENV PYTHONPATH=/app

# Entry point
ENTRYPOINT ["python", "inference.py"] 