import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Union, Optional, Tuple

import nibabel as nib
import numpy as np
import torch
from monai.data import MetaTensor
from monai.inferers import sliding_window_inference, SlidingWindowInferer
from monai.transforms import (
    Compose,
    LoadImaged,
    EnsureChannelFirstd,
    Orientationd,
    Spacingd,
    ScaleIntensityRanged,
    NormalizeIntensityd,
    GaussianSmoothd,
    EnsureTyped,
    Activationsd,
    AsDiscreted,
)
import monai.config
import gc
import psutil

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Add the current directory to the path so we can import our modules
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from model import get_network
from utils import Restored
from download import download_pretrained_weights, MODEL_FILENAME

class LesionSegmentor:
    """
    A class for segmenting lesions in FLAIR MRI scans using a pre-trained SegResNet model.
    
    Attributes:
        device (torch.device): The device to run inference on (CPU/CUDA).
        model (nn.Module): The loaded SegResNet model.
        roi_size (tuple): Region of interest size for sliding window inference.
        target_spacing (tuple): Target voxel spacing for image resampling.
    """
    
    def __init__(
        self, 
        model_path: Optional[Union[str, Path]] = None,
        device: Optional[torch.device] = None,
        roi_size: Tuple[int, int, int] = (120, 120, 120),
        target_spacing: Tuple[float, float, float] = (0.7, 0.7, 0.7)
    ):
        """
        Initialize the LesionSegmentor.
        
        Args:
            model_path: Path to the pre-trained model weights. If None, will download or use default.
            device: Device to run inference on. If None, will use CUDA if available.
            roi_size: Region of interest size for sliding window inference.
            target_spacing: Target voxel spacing for image resampling.
        """
        # Set up device
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = device
        logger.info(f"Using device: {self.device}")
        
        # Get model path
        if model_path is None:
            model_path = download_pretrained_weights()
        else:
            model_path = Path(model_path)
            if not model_path.exists():
                logger.warning(f"Model not found at {model_path}, downloading default model...")
                model_path = download_pretrained_weights()
            
        # Load model
        try:
            self.model = get_network().to(self.device)
            self.model.load_state_dict(torch.load(model_path, map_location=self.device))
            self.model.eval()
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}")
            raise
        
        # Settings
        self.roi_size = roi_size
        self.target_spacing = target_spacing
        
        # Pre-processing transforms
        self.pre_transforms = Compose([
            LoadImaged(keys="image"),
            EnsureTyped(keys="image", device=self.device),
            EnsureChannelFirstd(keys="image"),
            Orientationd(keys="image", axcodes="RAS"),
            Spacingd(keys="image", pixdim=self.target_spacing),
            NormalizeIntensityd(keys="image", nonzero=True),
            GaussianSmoothd(keys="image", sigma=0.4),
            ScaleIntensityRanged(keys="image", a_min=0, a_max=255, b_min=-1.0, b_max=1.0),
        ])
        
        # Post-processing transforms
        self.post_transforms = Compose([
            EnsureTyped(keys=["image", "pred"], device=self.device),
            Activationsd(keys="pred", softmax=True),
            AsDiscreted(keys="pred", argmax=True),
            Restored(
                keys="pred",
                ref_image="image",
                has_channel=True,
                invert_orient=False,
                mode="nearest",
            ),
        ])
        
        # Detect system type and adjust parameters
        is_macos = sys.platform == "darwin"
        num_threads = os.cpu_count()
        if num_threads:
            # Use 80% of available cores
            num_threads = max(1, int(num_threads * 0.8))
            logger.info(f"Using {num_threads} CPU threads")
            
        # Adjust batch size and ROI size based on system
        if is_macos:
            sw_batch_size = 1  # Smaller batch size for MacOS
            overlap = 0.5  # Increased overlap for better results
            logger.info("Running on MacOS with adjusted parameters")
        else:
            sw_batch_size = 4  # Larger batch size for Linux/Windows
            overlap = 0.4
        
        # Configure sliding window inferer
        self.inferer = SlidingWindowInferer(
            roi_size=self.roi_size,
            sw_batch_size=sw_batch_size,
            overlap=overlap,
            mode="gaussian",
            padding_mode="replicate",
            device=self.device,
            cpu_threads=num_threads,
            progress=True  # Add progress bar
        )

        # Enable memory efficient inference for MacOS
        if is_macos:
            torch.set_grad_enabled(False)
            if hasattr(torch, 'set_float32_matmul_precision'):
                torch.set_float32_matmul_precision('medium')

        # Enable MONAI's cache for transforms
        monai.config.set_compute_device(self.device)
        monai.config.set_cache_dir("/tmp/monai_cache")

    @torch.no_grad()
    def __call__(self, image_path: Union[str, Path]) -> nib.Nifti1Image:
        """
        Perform lesion segmentation on a FLAIR MRI scan.
        
        Args:
            image_path: Path to the input NIFTI image.
            
        Returns:
            nib.Nifti1Image: Segmentation mask in NIFTI format.
            
        Raises:
            FileNotFoundError: If input image doesn't exist.
            RuntimeError: If processing fails.
        """
        try:
            # Validate input
            image_path = Path(image_path)
            if not image_path.exists():
                raise FileNotFoundError(f"Input image not found: {image_path}")
            
            # Load and check original image
            original_img = nib.load(str(image_path))
            original_orientation = nib.aff2axcodes(original_img.affine)
            logger.debug(f"Original image orientation: {original_orientation}")
            
            # Pre-processing with progress info
            logger.info("Pre-processing image...")
            data = self.pre_transforms({"image": str(image_path)})
            
            # Get image shape for verification
            image_shape = data["image"].shape
            logger.info(f"Processed image shape: {image_shape}")
            
            # Run inference with progress info
            logger.info("Running inference...")
            image = data["image"].unsqueeze(0)
            
            # Memory optimization for MacOS
            if sys.platform == "darwin":
                torch.cuda.empty_cache()
                gc.collect()
            
            outputs = self.inferer(image, self.model)
            
            # Verify output shape
            logger.info(f"Output shape: {outputs.shape}")
            
            # Post-processing
            logger.info("Post-processing...")
            data["pred"] = outputs[0]
            data = self.post_transforms(data)
            
            # Verify final prediction
            pred = data["pred"].cpu().numpy()
            logger.info(f"Final prediction shape: {pred.shape}")
            logger.info(f"Prediction range: [{pred.min()}, {pred.max()}]")
            logger.info(f"Non-zero voxels: {np.count_nonzero(pred)}")
            
            # Create output with verification
            result_img = nib.Nifti1Image(
                pred.astype(np.uint8), 
                data["image"].affine.cpu().numpy(), 
                original_img.header
            )
            
            return result_img
            
        except Exception as e:
            logger.error(f"Segmentation failed: {str(e)}")
            logger.error(f"System: {sys.platform}")
            logger.error(f"Available memory: {psutil.virtual_memory().available / (1024**3):.2f} GB")
            raise

def main():
    parser = argparse.ArgumentParser(description='Lesion Segmentation Tool')
    parser.add_argument('--input', '-i', type=str, required=True, help='Input FLAIR image path (.nii.gz)')
    parser.add_argument('--output', '-o', type=str, required=True, help='Output mask path (.nii.gz)')
    parser.add_argument('--model', type=str, default='/app/model.pth', help='Path to model weights')
    parser.add_argument('--device', type=str, choices=['cuda', 'cpu'], default=None, help='Device to use')
    args = parser.parse_args()

    try:
        # Initialize segmentor
        device = torch.device(args.device) if args.device else None
        segmentor = LesionSegmentor(args.model, device=device)
        
        # Run segmentation
        logger.info(f"Processing {args.input}...")
        result = segmentor(args.input)
        
        # Save output
        logger.info(f"Saving output to {args.output}...")
        nib.save(result, args.output)
        logger.info("Done!")
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()