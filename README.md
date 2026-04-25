# 🧠 Image Selector + AI Caption Generator (CLI)

A lightweight CLI tool that transforms a folder of images into ready-to-post social media content using AI, **completely free, local, and offline**.

---

## 🎬 Demo

https://github.com/34567hg80/_Image-selection_/blob/main/demo.mp4

> Drop your images → Run one command → Get a caption + hashtags instantly.

---

## 🚀 Features

- 📂 Drop images into a folder
- 🏆 Automatically selects the best image (highest resolution)
- 🧠 Generates a natural caption using AI
- 🔖 Adds 5 niche hashtags
- 🧹 Deletes all extra images automatically
- 📄 Outputs everything into a clean `output.txt`

---

## ⚙️ Tech Stack

| Tool | Purpose |
|------|---------|
| Python | Core language |
| BLIP | Image captioning model |
| Ollama + Mistral | Local LLM for caption refinement |
| Pillow | Image processing |
| Transformers | Model inference |

---

## 📁 Project Structure

```
project-root/
├── app.py
├── requirements.txt
├── output.txt
├── images/
│   └── .gitkeep
└── ai/
    ├── caption.py
    └── scoring.py
```

---

## 🛠️ Setup

### 1. Clone the repo

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Ollama

Download from: [https://ollama.com](https://ollama.com)

Then pull the model and start the server:

```bash
ollama pull mistral
ollama serve
```

---

## ▶️ Running the App

### 🪟 Windows Users

Double-click the included `.bat` file — it handles everything for you automatically:

1. It checks that your virtual environment exists
2. Activates it
3. Launches the app
4. Waits so you can read the output before the window closes

> ⚠️ If you see `[ERROR] Virtual environment not found`, make sure you've run `python -m venv venv` first (Step 2 above).

---

### 🐧 Linux / 🍎 macOS Users

If you're not on Windows, skip the `.bat` file — it won't work on your system. Instead, open a terminal in the project folder and run these commands one by one:

**Step 1 — Activate the virtual environment:**

```bash
source venv/bin/activate
```

**Step 2 — Run the app:**

```bash
python app.py
```

**Step 3 — When you're done, deactivate the environment:**

```bash
deactivate
```

That's it! The output will be saved to `output.txt` in the same folder.

---

## 📄 Example Output

```
Caption:
The ocean never runs out of things to say 🌊🌅

Hashtags:
#oceanphotography #sunsetlovers #coastalvibes #goldenhourshots #seascapeart
```

---

## 🧹 Cleanup Behavior

- All images are deleted after execution
- `.gitkeep` is preserved so the `images/` folder stays in the repo
- Cleanup runs even on crash or `Ctrl+C`

---

## 🚧 Future Scope

- 🎥 Video generation from selected images
- 🔗 Auto-posting via Facebook Graph API
- ❌ No dependency on n8n or other automation tools
- 📱 Full system app or web app (based on user feedback)

---

## 💡 Why This Exists

Most social media AI tools are:
- 💸 Paid
- ☁️ Cloud-dependent
- ⚙️ Require third-party automation tools

This project is:
- ✅ **Local-first** — runs entirely on your machine
- ✅ **Fast** — no API calls, no waiting
- ✅ **Free** — forever
- ✅ **Developer-friendly** — simple, readable code

---

## 🤝 Contributing

Open to improvements:

- Better image scoring using CLIP
- Multi-image caption support
- A simple UI layer

Feel free to open a PR or raise an issue!

---

## ⭐ Support

If this project helped you, give it a star ⭐

Feedback and ideas are always welcome, drop them in the Issues tab.
