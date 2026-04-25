# Build Workflow: Image Selector CLI
> Give this entire document to Gemma 4.
> The terminal is already open inside the project folder. Build everything here.

---

## Context

The user already has a project folder open in their terminal and VS Code.
Do NOT tell them to `mkdir` a project folder or `cd` anywhere.
All commands run from the project root as-is.
All file paths in code are relative to `app.py` using `__file__`.

---

## What the App Does

1. User drops photos into the `images\` folder inside the project
2. User runs `python app.py`
3. App picks the best image (highest resolution)
4. Generates a caption + 5 hashtags using BLIP + Ollama
5. Saves `output.txt` to the project root
6. When the app closes — for any reason — `images\` is fully emptied

---

## Final Folder Structure to Build

```
<project-root>\          ← terminal is already here
├── app.py
├── requirements.txt
├── output.txt           ← created on first run
├── images\              ← user drops photos here
│   └── .gitkeep
└── ai\
    ├── __init__.py
    ├── caption.py
    └── scoring.py
```

---

## Pre-Requisites (One-Time Setup)

Tell the user to run these once in their terminal before building.
These assume the terminal is already in the project root.

### Python check
```cmd
python --version
```
Needs 3.10 or higher. If not installed: https://www.python.org/downloads/windows/
✅ Check "Add Python to PATH" during install.

### Virtual environment
```cmd
python -m venv venv
venv\Scripts\activate
```

### Ollama
Download and install from: https://ollama.com/download/windows
Then pull the model:
```cmd
ollama pull mistral
```

---

## Step 1 — `requirements.txt`

Create this file in the project root:

```
torch
torchvision
transformers
Pillow
requests
```

Then run:
```cmd
pip install -r requirements.txt
```

---

## Step 2 — `images\` folder + placeholder

```cmd
mkdir images
type nul > images\.gitkeep
```

The `.gitkeep` keeps the folder trackable in git.
The cleanup logic must never delete `.gitkeep`.

---

## Step 3 — `ai\__init__.py`

```cmd
mkdir ai
type nul > ai\__init__.py
```

Empty file — just makes `ai` a Python package.

---

## Step 4 — `ai\scoring.py`

```python
# ai/scoring.py
from PIL import Image


def score_image(image_path: str) -> int:
    """Score an image by its pixel count. Higher = better quality."""
    try:
        with Image.open(image_path) as img:
            w, h = img.size
            return w * h
    except Exception:
        return 0


def select_best_image(image_paths: list[str]) -> str:
    """Return the path of the highest-resolution image."""
    return max(image_paths, key=score_image)
```

This file is intentionally isolated.
Upgrading to CLIP later only requires changing this file — nothing else.

---

## Step 5 — `ai\caption.py`

```python
# ai/caption.py
import requests
import torch
from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration


MODEL_NAME  = "Salesforce/blip-image-captioning-base"
OLLAMA_URL  = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "mistral"

_processor = None
_model = None


def _load_blip() -> None:
    global _processor, _model
    if _processor is None:
        print("  Loading BLIP model (first run downloads ~900MB)...")
        _processor = BlipProcessor.from_pretrained(MODEL_NAME)
        _model     = BlipForConditionalGeneration.from_pretrained(MODEL_NAME)


def generate_description(image_path: str) -> str:
    """Run BLIP on the image and return a plain English description."""
    _load_blip()
    image  = Image.open(image_path).convert("RGB")
    inputs = _processor(image, return_tensors="pt")
    with torch.no_grad():
        out = _model.generate(**inputs)
    return _processor.decode(out[0], skip_special_tokens=True).strip()


def _call_ollama(prompt: str) -> str:
    """Send a prompt to the local Ollama server and return the response text."""
    try:
        r = requests.post(
            OLLAMA_URL,
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=60,
        )
        r.raise_for_status()
        return r.json()["response"].strip()
    except requests.exceptions.ConnectionError:
        print("\n  ERROR: Ollama is not running.")
        print("  Open a new terminal window and run: ollama serve")
        raise SystemExit(1)


def generate_caption(description: str) -> str:
    """Turn a BLIP description into a short Instagram caption via Ollama."""
    prompt = (
        "Generate a short, natural, human-like Instagram caption (max 15 words). "
        "Make it engaging, emotional, and not robotic. "
        "Include 1-2 relevant emojis. Avoid generic phrases. "
        f"Description: {description}"
    )
    return _call_ollama(prompt)


def generate_hashtags(caption: str) -> list[str]:
    """Generate exactly 5 niche hashtags for the caption via Ollama."""
    prompt = (
        "Generate exactly 5 niche, specific Instagram hashtags for this caption. "
        "Avoid generic tags like #love or #instagood. "
        "Return ONLY the 5 hashtags separated by spaces. No explanation. "
        f"Caption: {caption}"
    )
    raw  = _call_ollama(prompt)
    tags = [w for w in raw.split() if w.startswith("#")]

    if len(tags) < 5:
        raw  = _call_ollama(prompt + " You must return exactly 5 hashtags.")
        tags = [w for w in raw.split() if w.startswith("#")]

    return tags[:5]
```

---

## Step 6 — `app.py`

Build this file exactly as shown, section by section.

```python
# app.py
import atexit
import glob
import os
import signal
import sys

from ai.caption import generate_caption, generate_description, generate_hashtags
from ai.scoring import select_best_image


# ---------------------------------------------------------------------------
# Paths — always relative to this file, no matter where the terminal is
# ---------------------------------------------------------------------------
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR  = os.path.join(BASE_DIR, "images")
OUTPUT_FILE = os.path.join(BASE_DIR, "output.txt")


# ---------------------------------------------------------------------------
# Image scanning
# ---------------------------------------------------------------------------
def find_images() -> list[str]:
    """Return all images inside the images\ folder."""
    extensions = ["*.jpg", "*.jpeg", "*.png", "*.JPG", "*.JPEG", "*.PNG"]
    found = []
    for ext in extensions:
        found.extend(glob.glob(os.path.join(IMAGES_DIR, ext)))

    seen, unique = set(), []
    for p in found:
        key = p.lower()
        if key not in seen:
            seen.add(key)
            unique.append(p)
    return sorted(unique)


# ---------------------------------------------------------------------------
# Cleanup — empties images\ on every exit
# ---------------------------------------------------------------------------
def cleanup_images_folder() -> None:
    """
    Remove every image from images\.
    Always runs on exit — normal finish, error, or Ctrl+C.
    Never deletes the folder itself or .gitkeep.
    """
    print("\n  Cleaning up images\\...")
    extensions = ["*.jpg", "*.jpeg", "*.png", "*.JPG", "*.JPEG", "*.PNG"]
    removed = 0
    for ext in extensions:
        for path in glob.glob(os.path.join(IMAGES_DIR, ext)):
            try:
                os.remove(path)
                print(f"  [REMOVED] {os.path.basename(path)}")
                removed += 1
            except PermissionError:
                print(f"  [SKIP]    {os.path.basename(path)} — close any app using it first")
            except Exception as e:
                print(f"  [SKIP]    {os.path.basename(path)} — {e}")

    if removed == 0:
        print("  images\\ is already empty.")
    else:
        print(f"  Done. {removed} file(s) removed.")


def _on_ctrl_c(sig, frame) -> None:
    """Convert Ctrl+C into a clean sys.exit so atexit still fires."""
    print("\n\n  Interrupted.")
    sys.exit(0)


# Register cleanup and Ctrl+C handler at import time
atexit.register(cleanup_images_folder)
signal.signal(signal.SIGINT, _on_ctrl_c)


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------
def save_output(caption: str, hashtags: list[str]) -> str:
    """Write output.txt to the project root."""
    content = f"Caption:\n{caption}\n\nHashtags: {' '.join(hashtags)}\n"
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(content)
    return OUTPUT_FILE


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    print("=" * 50)
    print("  Image Selector + Caption Generator")
    print("=" * 50)

    # 1. Confirm images\ exists
    if not os.path.isdir(IMAGES_DIR):
        print(f"\n  ERROR: images\\ folder not found.")
        print(f"  Expected at: {IMAGES_DIR}")
        print("  Run: mkdir images")
        sys.exit(1)

    # 2. Scan
    images = find_images()
    if not images:
        print("\n  No images found in images\\")
        print("  Drop .jpg / .jpeg / .png files into the images\\ folder and try again.")
        sys.exit(1)

    print(f"\n  Found {len(images)} image(s):")
    for img in images:
        print(f"    {os.path.basename(img)}")

    # 3. Pick best
    best = select_best_image(images)
    print(f"\n  Best image: {os.path.basename(best)}")

    # 4. Delete the rest (with confirmation)
    others = [p for p in images if os.path.abspath(p) != os.path.abspath(best)]
    if others:
        print(f"\n  These {len(others)} image(s) will be deleted:")
        for p in others:
            print(f"    {os.path.basename(p)}")
        answer = input("\n  Delete them and continue? (y/n): ").strip().lower()
        if answer != "y":
            print("\n  Cancelled. images\\ will still be cleared when the app closes.")
            sys.exit(0)
        for path in others:
            try:
                os.remove(path)
                print(f"  [DELETED] {os.path.basename(path)}")
            except PermissionError:
                print(f"  [WARNING] {os.path.basename(path)} is open in another app — skipped.")
    else:
        print("  Only 1 image — nothing to delete.")

    # 5. BLIP
    print("\n  Describing image with BLIP...")
    description = generate_description(best)
    print(f"  → {description}")

    # 6. Caption
    print("\n  Generating caption with Ollama...")
    caption = generate_caption(description)
    print(f"  → {caption}")

    # 7. Hashtags
    print("\n  Generating hashtags with Ollama...")
    hashtags = generate_hashtags(caption)
    print(f"  → {' '.join(hashtags)}")

    # 8. Save
    out = save_output(caption, hashtags)
    print(f"\n  Saved: {out}")
    print("\n  All done. Closing app — images\\ will be cleared now.")
    # atexit fires here → cleanup_images_folder() runs automatically


if __name__ == "__main__":
    main()
```

---

## How to Run

Terminal is already in the project root. Just:

```cmd
venv\Scripts\activate
python app.py
```

---

## Example Output

```
==================================================
  Image Selector + Caption Generator
==================================================

  Found 3 image(s):
    beach1.jpg
    beach2.png
    sunset_4k.jpg

  Best image: sunset_4k.jpg

  These 2 image(s) will be deleted:
    beach1.jpg
    beach2.png

  Delete them and continue? (y/n): y
  [DELETED] beach1.jpg
  [DELETED] beach2.png

  Describing image with BLIP...
  → a beautiful sunset over the ocean with orange clouds

  Generating caption with Ollama...
  → The ocean never runs out of things to say 🌊🌅

  Generating hashtags with Ollama...
  → #oceanphotography #sunsetlovers #coastalvibes #goldenhourshots #seascapeart

  Saved: C:\Users\YourName\project\output.txt

  All done. Closing app — images\ will be cleared now.

  Cleaning up images\...
  [REMOVED] sunset_4k.jpg
  Done. 1 file(s) removed.
```

---

## output.txt

```
Caption:
The ocean never runs out of things to say 🌊🌅

Hashtags: #oceanphotography #sunsetlovers #coastalvibes #goldenhourshots #seascapeart
```

---

## Error Reference

| Error | Cause | Fix |
|---|---|---|
| `images\` folder not found | Folder missing | Run `mkdir images` |
| No images found | Folder empty | Drop photos into `images\` |
| Ollama connection error | Service not running | Run `ollama serve` in a new terminal |
| `PermissionError` on delete | File open in another app | Close Photos / Paint |
| Emoji shows as `?` | Wrong encoding | Already handled — file uses `utf-8` |
| BLIP download fails | Firewall blocking Python | Allow Python in Windows Firewall |

---

## Checklist

- [ ] `venv` created and activated
- [ ] `pip install -r requirements.txt` done
- [ ] `images\` folder exists with `.gitkeep` inside
- [ ] `ai\__init__.py` exists (empty)
- [ ] `ai\scoring.py` written
- [ ] `ai\caption.py` written
- [ ] `app.py` written with `BASE_DIR = os.path.dirname(os.path.abspath(__file__))`
- [ ] `atexit.register(cleanup_images_folder)` is called before `main()`
- [ ] `signal.signal(signal.SIGINT, _on_ctrl_c)` is registered
- [ ] `output.txt` uses `encoding="utf-8"`
- [ ] Cleanup skips `.gitkeep` and never deletes the `images\` folder itself
- [ ] Tested: drop 3 photos → run → output.txt exists → images\ is empty
