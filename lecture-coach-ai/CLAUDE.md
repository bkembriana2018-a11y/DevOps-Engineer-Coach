# Lecture Coach — Claude Code project notes

Local FastAPI + static UI app: upload a `.pptx`, get a Markdown study guide back. Sibling to `cloud-coach-ai` (repo root) and `course-coach-ai`, same architecture, unrelated domain — no courses, no question bank, just one deck in and one guide out.

## Run

```bash
chmod +x run.sh
./run.sh
```

App: http://127.0.0.1:8768
Health: http://127.0.0.1:8768/api/health
Ollama (optional, shared with any other local app): http://127.0.0.1:11434

## Layout

- `app/main.py` — FastAPI: upload, list, get, delete lectures; generate/fetch/download study guide
- `app/pptx_extract.py` — `python-pptx`-based slide text extraction (title, bullets, speaker notes)
- `app/store.py` — persistence: `data/lectures.json` (index), `data/slides/<id>.json` (extracted text), `data/study_guides/<id>.md` (output)
- `app/llm.py` — Ollama chat call using `app/knowledge/SYSTEM.md` as the system prompt; falls back to a raw slide-text outline if Ollama is unreachable or errors
- `web/` — single-page UI (upload form, lecture list with per-card actions, Markdown viewer). `app.js` includes a small hand-rolled Markdown renderer (headers/bold/italic/code/lists/paragraphs) since the app has no other need for a JS dependency.

## Guardrails

- Study guides should stay grounded in the uploaded slide content (see `SYSTEM.md`) — brief clarifying definitions are fine, invented specifics are not.
- Never claim a generated practice question appeared on a real exam.
- Port 8768 — 8765 is afoqt-coach-ai, 8766 is cloud-coach-ai (this repo's root), 8767 is course-coach-ai.
