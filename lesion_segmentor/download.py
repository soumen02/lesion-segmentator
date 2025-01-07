import os
import gdown

def download_pretrained_weights(model_dir):
    """Downloads pretrained weights if they don't exist."""
    os.makedirs(model_dir, exist_ok=True)
    model_path = os.path.join(model_dir, "segresnet_lesion.pt")
    
    if not os.path.exists(model_path):
        # For Google Drive, we need the file ID from the sharing URL
        file_id = "1sTVF-nmthJSOvhXpsXL24fkp3G_NDqma"  # Extract this from your URL
        url = f"https://drive.google.com/uc?id={file_id}"
        try:
            gdown.download(url, model_path, quiet=False)
            if not os.path.exists(model_path):
                raise RuntimeError("Download failed")
        except Exception as e:
            print(f"Error downloading model: {str(e)}")
            print("Please download the model manually and place it at:", model_path)
            raise
    
    return model_path 