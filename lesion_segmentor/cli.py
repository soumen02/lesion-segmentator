#!/usr/bin/env python3
import argparse
import subprocess
import sys
import os
import shutil
from pathlib import Path
import logging
import pkg_resources
import appdirs

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def get_package_root():
    """Get the root directory where package files are installed."""
    return Path(pkg_resources.resource_filename('lesion_segmentor', ''))

def get_config_dir():
    """Get the standard config directory for the application."""
    config_dir = Path(appdirs.user_config_dir('lesion-segmentor', appauthor="soumen02"))
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir

def files_are_identical(file1, file2):
    """Check if two files are identical."""
    if not (Path(file1).exists() and Path(file2).exists()):
        return False
    return Path(file1).read_bytes() == Path(file2).read_bytes()

def ensure_docker_files():
    """Ensure all necessary Docker files are in the standard config directory."""
    package_root = get_package_root()
    config_dir = get_config_dir()
    
    logger.info(f"Package root: {package_root}")
    logger.info(f"Config directory: {config_dir}")
    
    # Files to copy from docker directory
    docker_files = {
        'Dockerfile': package_root / 'docker' / 'Dockerfile',
        'docker-compose.yml': package_root / 'docker' / 'docker-compose.yml',
        '.dockerignore': package_root / 'docker' / '.dockerignore',
        '.env': package_root / 'docker' / '.env'
    }
    
    # Copy Docker files
    for filename, src in docker_files.items():
        dst = config_dir / filename
        logger.info(f"Checking file {filename}:")
        logger.info(f"  Source: {src} (exists: {src.exists()})")
        logger.info(f"  Destination: {dst} (exists: {dst.exists()})")
        
        if not dst.exists() or not files_are_identical(src, dst):
            if src.exists():
                shutil.copy2(src, dst)
                logger.info(f"  Copied {filename}")
            else:
                logger.error(f"Missing required file: {filename}")
                sys.exit(1)
    
    # Copy Python files
    python_files = ['inference.py', 'model.py', 'utils.py']
    for filename in python_files:
        src = package_root / filename
        dst = config_dir / filename
        logger.info(f"Checking Python file {filename}:")
        logger.info(f"  Source: {src} (exists: {src.exists()})")
        logger.info(f"  Destination: {dst} (exists: {dst.exists()})")
        
        if not dst.exists() or not files_are_identical(src, dst):
            if src.exists():
                shutil.copy2(src, dst)
                logger.info(f"  Copied {filename}")
            else:
                logger.error(f"Missing required Python file: {filename}")
                logger.error(f"Package root contents:")
                for item in package_root.iterdir():
                    logger.error(f"  {item}")
                sys.exit(1)
    
    # Copy script file
    scripts_dir = config_dir / 'scripts'
    scripts_dir.mkdir(exist_ok=True)
    
    src_script = package_root / 'scripts' / 'docker_segment.sh'
    dst_script = scripts_dir / 'docker_segment.sh'
    
    logger.info(f"Checking script docker_segment.sh:")
    logger.info(f"  Source: {src_script} (exists: {src_script.exists()})")
    logger.info(f"  Destination: {dst_script} (exists: {dst_script.exists()})")
    
    if not dst_script.exists() or not files_are_identical(src_script, dst_script):
        if src_script.exists():
            shutil.copy2(src_script, dst_script)
            dst_script.chmod(0o755)  # Make executable
            logger.info("  Copied docker_segment.sh")
        else:
            logger.error("Missing required script: docker_segment.sh")
            sys.exit(1)
    
    return config_dir

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
    config_dir = ensure_docker_files()
    
    # Check if image exists
    result = subprocess.run(['docker', 'images', '-q', 'lesion_segmentor:latest'], 
                          capture_output=True, text=True)
    
    if not result.stdout.strip():
        logger.info("Building Docker image (this may take a few minutes)...")
        subprocess.run(['docker', 'compose', '--profile', 'cpu', 'build'], 
                      cwd=config_dir, check=True)
        if check_nvidia_docker():
            subprocess.run(['docker', 'compose', '--profile', 'gpu', 'build'], 
                         cwd=config_dir, check=True)
    
    return config_dir

def run_segmentation(input_path: Path, output_path: Path, force_cpu: bool = False):
    """Run the segmentation using docker."""
    # Ensure Docker image and get config directory
    config_dir = ensure_docker_image()
    docker_script = config_dir / 'scripts' / 'docker_segment.sh'
    
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
    subprocess.run(cmd, cwd=config_dir, check=True)

def main():
    parser = argparse.ArgumentParser(description='Lesion Segmentation Tool')
    parser.add_argument('-i', '--input', type=str, required=True, help='Input FLAIR image path (.nii.gz)')
    parser.add_argument('-o', '--output', type=str, required=True, help='Output mask path (.nii.gz)')
    parser.add_argument('--cpu', action='store_true', help='Force CPU usage')
    parser.add_argument('--update', action='store_true', help='Force update of docker image')
    parser.add_argument('--clean', action='store_true', help='Clean up all configuration files')
    args = parser.parse_args()

    # Handle cleanup request
    if args.clean:
        config_dir = get_config_dir()
        if config_dir.exists():
            shutil.rmtree(config_dir)
            logger.info("Configuration files cleaned up successfully")
        sys.exit(0)

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