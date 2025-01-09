#!/usr/bin/env python3
import argparse
import subprocess
import sys
import os
import shutil
from pathlib import Path
import logging
import pkg_resources

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def get_package_root():
    """Get the root directory where package files are installed."""
    return Path(pkg_resources.resource_filename('lesion_segmentor', ''))

def ensure_docker_files():
    """Ensure all necessary Docker files are in the current directory."""
    package_root = get_package_root()
    current_dir = Path.cwd()
    
    # Files to copy
    docker_files = ['Dockerfile', 'docker-compose.yml', '.dockerignore', '.env']
    
    # Create temporary working directory if needed
    work_dir = current_dir / '.lesion_segmentor'
    work_dir.mkdir(exist_ok=True)
    
    # Copy files
    for file in docker_files:
        src = package_root.parent / file
        if src.exists():
            shutil.copy2(src, work_dir / file)
        else:
            logger.error(f"Missing required file: {file}")
            sys.exit(1)
    
    # Copy scripts directory
    scripts_dir = work_dir / 'scripts'
    scripts_dir.mkdir(exist_ok=True)
    shutil.copy2(package_root.parent / 'scripts' / 'docker_segment.sh', 
                scripts_dir / 'docker_segment.sh')
    
    return work_dir

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
    # Get working directory with Docker files
    work_dir = ensure_docker_files()
    
    # Check if image exists
    result = subprocess.run(['docker', 'images', '-q', 'lesion_segmentor:latest'], 
                          capture_output=True, text=True)
    
    if not result.stdout.strip():
        logger.info("Building Docker image (this may take a few minutes)...")
        subprocess.run(['docker', 'compose', '--profile', 'cpu', 'build'], 
                      cwd=work_dir, check=True)
        if check_nvidia_docker():
            subprocess.run(['docker', 'compose', '--profile', 'gpu', 'build'], 
                         cwd=work_dir, check=True)
    
    return work_dir

def run_segmentation(input_path: Path, output_path: Path, force_cpu: bool = False):
    """Run the segmentation using docker."""
    # Ensure Docker image and get working directory
    work_dir = ensure_docker_image()
    docker_script = work_dir / 'scripts' / 'docker_segment.sh'
    
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
    subprocess.run(cmd, cwd=work_dir, check=True)

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