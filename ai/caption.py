# ai/caption.py
import requests
import torch
import os
from typing import List, Optional
from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration

# Configuration
MODEL_NAME = "Salesforce/blip-image-captioning-base"
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "mistral"

# Global cache for the models to avoid reloading
_processor: Optional[BlipProcessor] = None
_model: Optional[BlipForConditionalGeneration] = None

def _load_blip() -> None:
    """Lazy load the BLIP model and processor."""
    global _processor, _model
    if _processor is None or _model is None:
        print("  [AI] Loading BLIP model (first run may download ~900MB)...")
        try:
            _processor = BlipProcessor.from_pretrained(MODEL_NAME)
            _model = BlipForConditionalGeneration.from_pretrained(MODEL_NAME)
            # Move to GPU if available
            device = "cuda" if torch.cuda.is_available() else "cpu"
            _model.to(device)
            print(f"  [AI] BLIP model loaded on {device}.")
        except Exception as e:
            print(f"  [ERROR] Failed to load BLIP model: {e}")
            raise

def generate_description(image_path: str) -> str:
    """
    Analyzes the image at image_path and generates a literal description using BLIP.
    """
    _load_blip()
    
    try:
        image = Image.open(image_path).convert("RGB")
        device = "cuda" if torch.cuda.is_available() else "cpu"
        
        inputs = _processor(image, return_tensors="pt").to(device)
        
        with torch.no_grad():
            out = _model.generate(**inputs)
            
        description = _processor.decode(out[0], skip_special_tokens=True).strip()
        return description
    except Exception as e:
        print(f"  [ERROR] Image description failed: {e}")
        return "A beautiful image."

def _call_ollama(prompt: str) -> str:
    """
    Communication layer for the local Ollama instance.
    """
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False
    }
    
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=60)
        response.raise_for_status()
        return response.json().get("response", "").strip()
    except requests.exceptions.ConnectionError:
        print("\n  [CRITICAL] Ollama service is not reachable.")
        print("  Please ensure Ollama is installed and running (`ollama serve`).")
        raise SystemExit(1)
    except Exception as e:
        print(f"  [ERROR] Ollama request failed: {e}")
        return ""

def generate_caption(description: str) -> str:
    """
    Transforms a literal description into a catchy Instagram caption using LLM.
    """
    prompt = (
        "Context: You are a social media expert.\n"
        f"Description of image: {description}\n"
        "Task: Generate a short, engaging, and natural Instagram caption (max 15 words).\n"
        "Include 1-2 relevant emojis. Avoid being robotic or generic."
    )
    return _call_ollama(prompt)

def generate_hashtags(caption: str) -> List[str]:
    """
    Generates exactly 5 niche hashtags based on the caption.
    """
    prompt = (
        f"Caption: {caption}\n"
        "Task: Generate exactly 5 specific and niche Instagram hashtags for this post.\n"
        "Return ONLY the hashtags separated by spaces. Do not include any other text."
    )
    
    raw_response = _call_ollama(prompt)
    tags = [tag for tag in raw_response.split() if tag.startswith("#")]
    
    # Validation loop for consistency
    attempts = 0
    while len(tags) < 5 and attempts < 2:
        print(f"  [AI] Refining hashtags (Attempt {attempts + 1})...")
        refine_prompt = prompt + "\nImportant: I need exactly 5 hashtags starting with #."
        raw_response = _call_ollama(refine_prompt)
        tags = [tag for tag in raw_response.split() if tag.startswith("#")]
        attempts += 1
        
    return tags[:5]
