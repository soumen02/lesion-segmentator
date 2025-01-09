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

# Add the current directory to the path so we can import our modules
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from model import get_network
from utils import Restored

# Configure logging
logger = logging.getLogger(__name__)

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
        model_path: Union[str, Path], 
        device: Optional[torch.device] = None,
        roi_size: Tuple[int, int, int] = (120, 120, 120),
        target_spacing: Tuple[float, float, float] = (0.7, 0.7, 0.7)
    ):
        """
        Initialize the LesionSegmentor.
        
        Args:
            model_path: Path to the pre-trained model weights.
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
        
        # Sliding window inferer
        self.inferer = SlidingWindowInferer(
            roi_size=self.roi_size,
            sw_batch_size=2,
            overlap=0.4,
        )

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
            
            # Prepare input
            data = {"image": str(image_path)}
            
            # Pre-processing
            data = self.pre_transforms(data)
            logger.debug(f"Image shape after pre-processing: {data['image'].shape}")
            
            # Store the RAS affine matrix
            if isinstance(data['image'], MetaTensor):
                ras_affine = data['image'].affine
                logger.debug(f"Orientation after pre-processing: {nib.aff2axcodes(ras_affine)}")
            
            # Run inference
            image = data["image"].unsqueeze(0)
            outputs = self.inferer(image, self.model)
            
            # Post-processing
            data["pred"] = outputs[0]
            data = self.post_transforms(data)
            
            # Create output NIFTI using the RAS affine
            pred = data["pred"].cpu().numpy()
            result_img = nib.Nifti1Image(pred.astype(np.uint8), ras_affine.cpu().numpy(), original_img.header)
            
            logger.info("Segmentation completed successfully")
            return result_img
            
        except Exception as e:
            logger.error(f"Segmentation failed: {str(e)}")
            raise