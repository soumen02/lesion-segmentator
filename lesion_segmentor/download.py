import os
import logging
from pathlib import Path
import gdown

logger = logging.getLogger(__name__)

MODEL_URL = "https://drive.google.com/uc?id=1sTVF-nmthJSOvhXpsXL24fkp3G_NDqma"
MODEL_FILENAME = "model.pth"

def download_pretrained_weights(model_dir: Path = None) -> Path:
    """Download the pre-trained model if it doesn't exist."""
    if model_dir is None:
        model_dir = Path(__file__).parent

    model_path = model_dir / MODEL_FILENAME
    
    if not model_path.exists():
        logger.info(f"Downloading model to {model_path}...")
        os.makedirs(model_dir, exist_ok=True)
        
        try:
            # Use gdown with force download and no progress bar
            output = gdown.download(
                url=MODEL_URL,
                output=str(model_path),
                quiet=False,
                fuzzy=True,
                use_cookies=False
            )
            
            if output is None:
                raise RuntimeError("Failed to download the model file")
                
            logger.info("Model downloaded successfully")
            
        except Exception as e:
            if model_path.exists():
                model_path.unlink()  # Remove partially downloaded file
            logger.error(f"Failed to download model: {str(e)}")
            raise
    
    return model_path 