#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null; then
  echo "python3 is required"
  exit 1
fi

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -q -r requirements.txt

export PYTHONUNBUFFERED=1
echo
echo "Course Coach  →  http://127.0.0.1:8767"
echo "Optional: install Ollama, then  ollama pull llama3.1"
echo
exec python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8767 --reload
