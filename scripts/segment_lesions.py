import os
import argparse
import nibabel as nib
from lesion_segmentor.model import get_network
from lesion_segmentor.download import download_pretrained_weights
from lesion_segmentor.inference import LesionSegmentor

def main():
    parser = argparse.ArgumentParser(description='Segment lesions in FLAIR MRI')
    parser.add_argument('input_path', help='Path to input FLAIR NIfTI file')
    parser.add_argument('output_path', help='Path to save segmentation mask')
    parser.add_argument('--model_dir', default='~/.lesion_segmentor', 
                      help='Directory to store/load model weights')
    parser.add_argument('--device', default=None,
                      help='Device to use (cuda or cpu). Default: auto-detect')
    
    args = parser.parse_args()
    
    # Expand user directory if needed
    model_dir = os.path.expanduser(args.model_dir)
    
    # Download/load weights
    model_path = download_pretrained_weights(model_dir)
    
    # Initialize segmentor
    segmentor = LesionSegmentor(model_path, device=args.device)
    
    # Run inference
    result = segmentor(args.input_path)
    
    # Save result
    nib.save(result, args.output_path)
    print(f"Segmentation saved to {args.output_path}")

if __name__ == '__main__':
    main() 