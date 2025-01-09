import os
import logging
from pathlib import Path
import gdown

logger = logging.getLogger(__name__)

MODEL_URL = "https://drive.google.com/uc?id=1-0t1ZOqz5qHxhXF8y_U4wFJ7tvy75ZSz"
MODEL_FILENAME = "model.pth"

def download_model(model_dir: Path = None) -> Path:
    """Download the pre-trained model if it doesn't exist."""
    if model_dir is None:
        model_dir = Path(__file__).parent

    model_path = model_dir / MODEL_FILENAME
    
    if not model_path.exists():
        logger.info(f"Downloading model to {model_path}...")
        os.makedirs(model_dir, exist_ok=True)
        gdown.download(MODEL_URL, str(model_path), quiet=False)
        logger.info("Model downloaded successfully")
    
    return model_path 