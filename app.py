# app.py
import os
import sys
import glob
import signal
import atexit
import logging
import shutil
from typing import List

from ai.scoring import select_best_image
from ai.caption import generate_description, generate_caption, generate_hashtags

# --- Configuration & Setup ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(BASE_DIR, "images")
SELECTED_DIR = os.path.join(BASE_DIR, "selected_image")
OUTPUT_FILE = os.path.join(BASE_DIR, "output.txt")

# Configure basic logging for a professional feel
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)

def setup_environment():
    """Ensure the necessary directory structure exists."""
    if not os.path.isdir(IMAGES_DIR):
        logger.error(f"Directory not found: {IMAGES_DIR}")
        logger.info("Please create the 'images' folder and add your photos.")
        sys.exit(1)

def find_images() -> List[str]:
    """Scans the images directory for supported formats."""
    extensions = ["*.jpg", "*.jpeg", "*.png", "*.JPG", "*.JPEG", "*.PNG"]
    image_paths = []
    for ext in extensions:
        image_paths.extend(glob.glob(os.path.join(IMAGES_DIR, ext)))
    
    # Remove duplicates and sort
    return sorted(list(set(image_paths)))

def cleanup_images(preserve_best: str = None):
    """
    Cleans up the images directory.
    If preserve_best is provided, it deletes all OTHER images.
    If not, it clears all images (called on exit).
    """
    logger.info("\n  [System] Cleaning up images directory...")
    all_images = find_images()
    removed_count = 0
    
    for img_path in all_images:
        # Never delete .gitkeep
        if os.path.basename(img_path) == ".gitkeep":
            continue
            
        # If we are preserving the best image during the run
        if preserve_best and os.path.abspath(img_path) == os.path.abspath(preserve_best):
            continue
            
        try:
            os.remove(img_path)
            logger.info(f"  [Removed] {os.path.basename(img_path)}")
            removed_count += 1
        except Exception as e:
            logger.warning(f"  [Skip] Could not remove {os.path.basename(img_path)}: {e}")
            
    if removed_count == 0:
        logger.info("  Directory is clean.")
    else:
        logger.info(f"  Cleanup complete. {removed_count} file(s) removed.")

def handle_interrupt(sig, frame):
    """Graceful shutdown on Ctrl+C."""
    logger.info("\n\n  [System] Process interrupted by user.")
    sys.exit(0)

# Register cleanup hooks
atexit.register(cleanup_images)
signal.signal(signal.SIGINT, handle_interrupt)

def save_result(caption: str, hashtags: List[str]):
    """Saves the final caption and hashtags to a text file."""
    try:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("--- Generated Content ---\n\n")
            f.write(f"Caption:\n{caption}\n\n")
            f.write(f"Hashtags:\n{' '.join(hashtags)}\n")
        logger.info(f"\n  [Success] Results saved to: {OUTPUT_FILE}")
    except Exception as e:
        logger.error(f"  [Error] Failed to save output: {e}")

def main():
    print("=" * 60)
    print("      IMAGE SELECTOR & SOCIAL MEDIA CAPTION GENERATOR")
    print("=" * 60)

    setup_environment()
    
    # 1. Discovery
    images = find_images()
    if not images:
        logger.info("\n  [!] No images found in the 'images/' folder.")
        logger.info("  Drop your photos (.jpg, .png) there and restart.")
        return

    logger.info(f"\n  [Scan] Found {len(images)} images.")
    for img in images:
        logger.info(f"    - {os.path.basename(img)}")

    # 2. Selection
    best_image = select_best_image(images)
    logger.info(f"\n  [Selection] Highest quality image: {os.path.basename(best_image)}")

    # 3. Save a copy of the best image
    try:
        if not os.path.exists(SELECTED_DIR):
            os.makedirs(SELECTED_DIR)
        
        dest_path = os.path.join(SELECTED_DIR, os.path.basename(best_image))
        shutil.copy2(best_image, dest_path)
        logger.info(f"  [Archive] Best image copied to: {SELECTED_DIR}")
    except Exception as e:
        logger.error(f"  [Error] Could not archive best image: {e}")

    # 4. Decision
    if len(images) > 1:
        print(f"\n  Ready to process the best image and discard the remaining {len(images)-1} files.")
        confirm = input("  Proceed? (y/n): ").strip().lower()
        if confirm != 'y':
            logger.info("  Operation cancelled by user.")
            return
        
        # Immediate cleanup of non-best images
        cleanup_images(preserve_best=best_image)

    # 4. AI Processing
    logger.info("\n  [AI] Step 1: Generating visual description...")
    description = generate_description(best_image)
    logger.info(f"  > Description: {description}")

    logger.info("\n  [AI] Step 2: Crafting Instagram caption...")
    caption = generate_caption(description)
    logger.info(f"  > Caption: {caption}")

    logger.info("\n  [AI] Step 3: Generating hashtags...")
    hashtags = generate_hashtags(caption)
    logger.info(f"  > Hashtags: {' '.join(hashtags)}")

    # 5. Export
    save_result(caption, hashtags)
    
    print("\n" + "=" * 60)
    print("  Process finished. The final image will be cleared on exit.")
    print("=" * 60)

if __name__ == "__main__":
    main()
