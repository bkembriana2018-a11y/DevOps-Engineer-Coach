import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP_DIR = Path(__file__).resolve().parent
WEB_DIR = ROOT / "web"
DATA_DIR = ROOT / "data"
LECTURES_PATH = DATA_DIR / "lectures.json"
SLIDES_DIR = DATA_DIR / "slides"
STUDY_GUIDES_DIR = DATA_DIR / "study_guides"

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
DEFAULT_MODEL = "llama3.1"

MAX_UPLOAD_BYTES = 25 * 1024 * 1024  # 25 MB
# Slide text budget per generation call, in characters.
CONTEXT_BUDGET = 20000
