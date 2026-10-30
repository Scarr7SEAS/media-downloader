import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DOWNLOADS_DIR = BASE_DIR / "downloads"
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)

# Server Config
HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", 8000))

# FFmpeg & Node configs
NODE_PATH = r"C:\Program Files\nodejs\node.exe"
if not os.path.exists(NODE_PATH):
    NODE_PATH = None
