#!/usr/bin/env python3
import argparse
import subprocess
import sys
import os
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def check_docker():
    """Check if docker is running and available."""
    try:
        subprocess.run(['docker', 'info'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def check_nvidia_docker():
    """Check if NVIDIA docker is available."""
    try:
        subprocess.run(['nvidia-smi'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def ensure_docker_image():
    """Ensure the docker image is built and up to date."""
    script_dir = Path(__file__).parent.parent
    
    # Check if image exists
    result = subprocess.run(['docker', 'images', '-q', 'lesion_segmentor:latest'], capture_output=True, text=True)
    
    if not result.stdout.strip():
        logger.info("Building Docker image (this may take a few minutes)...")
        subprocess.run(['docker', 'compose', '--profile', 'cpu', 'build'], cwd=script_dir, check=True)
        if check_nvidia_docker():
            subprocess.run(['docker', 'compose', '--profile', 'gpu', 'build'], cwd=script_dir, check=True)

def run_segmentation(input_path: Path, output_path: Path, force_cpu: bool = False):
    """Run the segmentation using docker."""
    script_dir = Path(__file__).parent.parent
    docker_script = script_dir / 'scripts' / 'docker_segment.sh'
    
    # Make script executable
    docker_script.chmod(0o755)
    
    # Prepare command
    cmd = [str(docker_script), str(input_path.absolute()), str(output_path.absolute())]
    if force_cpu:
        cmd.append('cpu')
    elif not check_nvidia_docker():
        logger.info("No GPU detected, falling back to CPU...")
        cmd.append('cpu')
    
    # Run segmentation
    subprocess.run(cmd, check=True)

def main():
    parser = argparse.ArgumentParser(description='Lesion Segmentation Tool')
    parser.add_argument('-i', '--input', type=str, required=True, help='Input FLAIR image path (.nii.gz)')
    parser.add_argument('-o', '--output', type=str, required=True, help='Output mask path (.nii.gz)')
    parser.add_argument('--cpu', action='store_true', help='Force CPU usage')
    parser.add_argument('--update', action='store_true', help='Force update of docker image')
    args = parser.parse_args()

    # Convert to Path objects
    input_path = Path(args.input)
    output_path = Path(args.output)

    # Validate input
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    if not input_path.suffix == '.gz' and not input_path.suffixes == ['.nii', '.gz']:
        logger.error("Input must be a .nii.gz file")
        sys.exit(1)

    # Create output directory if it doesn't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Check docker
    if not check_docker():
        logger.error("Docker is not running or not installed")
        sys.exit(1)

    try:
        # Ensure docker image is ready
        ensure_docker_image()
        
        # Run segmentation
        logger.info("Starting segmentation...")
        run_segmentation(input_path, output_path, args.cpu)
        logger.info(f"Segmentation complete! Output saved to: {output_path}")
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Segmentation failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 