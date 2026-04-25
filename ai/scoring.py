# ai/scoring.py
import os
from typing import List
from PIL import Image

def score_image(image_path: str) -> int:
    """
    Score an image based on its total pixel count (width * height).
    Higher resolution images receive a higher score.
    
    Returns 0 if the image cannot be opened or is invalid.
    """
    if not os.path.exists(image_path):
        return 0
    try:
        with Image.open(image_path) as img:
            w, h = img.size
            return w * h
    except (IOError, SyntaxError, Image.DecompressionBombError):
        # Specific image loading errors
        return 0
    except Exception:
        return 0

def select_best_image(image_paths: List[str]) -> str:
    """
    Evaluate a list of image paths and return the one with the highest resolution.
    
    Args:
        image_paths: A list of absolute or relative file paths to images.
        
    Returns:
        The path to the best image.
    """
    if not image_paths:
        raise ValueError("No images provided for selection.")
    
    # Using max with a key is efficient and idiomatic
    return max(image_paths, key=score_image)
