import torch
import nibabel as nib
import numpy as np
from monai.transforms import (
    Compose,
    LoadImaged,
    EnsureTyped,
    EnsureChannelFirstd,
    Orientationd,
    Spacingd,
    NormalizeIntensityd,
    GaussianSmoothd,
    ScaleIntensityd,
    Activationsd,
    AsDiscreted,
    KeepLargestConnectedComponentd,
)
from monai.inferers import SlidingWindowInferer
from monailabel.transform.post import Restored
from .model import get_network

class LesionSegmentor:
    def __init__(self, model_path, device=None):
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = device
            
        self.model = get_network().to(self.device)
        self.model.load_state_dict(torch.load(model_path, map_location=self.device))
        self.model.eval()

        # Match transforms exactly from segmentation_original.py
        self.pre_transforms = Compose([
            LoadImaged(keys="image"),
            EnsureTyped(keys="image", device=self.device),
            EnsureChannelFirstd(keys="image"),
            Orientationd(keys="image", axcodes="RAS"),
            Spacingd(
                keys="image", 
                pixdim=(0.7, 0.7, 0.7),
                allow_missing_keys=True
            ),
            NormalizeIntensityd(keys="image", nonzero=True),
            GaussianSmoothd(keys="image", sigma=0.4),
            ScaleIntensityd(keys="image", minv=-1.0, maxv=1.0),
        ])

        # Add post transforms from segmentation_original.py
        self.post_transforms = Compose([
            EnsureTyped(keys="pred", device=self.device),
            Activationsd(keys="pred", softmax=True),
            AsDiscreted(keys="pred", argmax=True),
            KeepLargestConnectedComponentd(keys="pred"),
            Restored(keys="pred", ref_image="image"),
        ])

        # Create inferer matching your implementation
        self.inferer = SlidingWindowInferer(
            roi_size=(120, 120, 120),
            sw_batch_size=2,
            overlap=0.4,
            padding_mode="replicate",
            mode="gaussian",
        )

    @torch.no_grad()
    def __call__(self, image_path):
        # Prepare input
        data = self.pre_transforms({"image": image_path})
        image = data["image"].unsqueeze(0)
        
        # Run inference using sliding window inferer
        output = self.inferer(image, self.model)
        
        # Post-process
        data["pred"] = output
        data = self.post_transforms(data)
        pred = data["pred"].squeeze().cpu().numpy()
        
        # Save with same metadata as input
        original_img = nib.load(image_path)
        result_img = nib.Nifti1Image(pred.astype(np.uint8), original_img.affine)
        
        return result_img 