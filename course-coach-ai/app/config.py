import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP_DIR = Path(__file__).resolve().parent
WEB_DIR = ROOT / "web"
DATA_DIR = ROOT / "data"
COURSES_PATH = DATA_DIR / "courses.json"
LECTURES_DIR = DATA_DIR / "lectures"
FLASHCARDS_DIR = DATA_DIR / "flashcards"
PROGRESS_DIR = DATA_DIR / "progress"

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
DEFAULT_MODEL = "llama3.1"

# Knowledge-pack budget per chat/generation call, in characters.
CONTEXT_BUDGET = 16000
