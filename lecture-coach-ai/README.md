# Lecture Coach

Upload a lecture slide deck (`.pptx`), get a study guide back — an overview, key concepts grouped by topic with short definitions, and a handful of self-test questions.

**Also in this repo:** [../README.md](../README.md) — [Cloud Coach](../README.md) (AWS/Terraform/Kubernetes) and [course-coach-ai/](../course-coach-ai/) (multi-class study app). This app is unrelated to both: no hardcoded subject matter, no course setup — just upload a deck and read the guide it produces.

---

## How it works

1. **Upload** a `.pptx` file. The app reads every slide's title, bullet text, and speaker notes.
2. Click **Generate study guide**. A local LLM (Ollama) turns the slide content into a structured Markdown study guide grounded in what the deck actually says.
3. **View** it in the browser or **download** it as a `.md` file.

Without Ollama running, uploading and browsing still work, but "Generate" produces a raw outline of the slide text instead of a synthesized guide — start Ollama for the real thing.

---

## Requirements

- macOS (primary target)
- Python 3.10+
- [Ollama](https://ollama.com) — optional, but needed for an actual synthesized study guide rather than a raw outline

---

## Install

### Fast path — double-click

1. Clone this repo.
2. Double-click **`Start Lecture Coach.command`** inside this folder.
3. First run installs everything automatically — then opens http://127.0.0.1:8768 in your browser.
4. To stop it, close that Terminal window.

### Manual

```bash
cd lecture-coach-ai
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
chmod +x run.sh
./run.sh
```

Open http://127.0.0.1:8768

### Local LLM (optional, recommended)

```bash
brew install ollama
brew services start ollama
ollama pull llama3.1
```

---

## Layout

```
lecture-coach-ai/
  app/
    knowledge/SYSTEM.md   the study-guide writer's behavioral contract
    pptx_extract.py        pulls title/bullets/notes off every slide of an uploaded .pptx
    store.py                persistence -- lectures.json, per-lecture slide JSON, per-lecture guide .md
    llm.py                  Ollama call + offline fallback (raw outline)
    main.py                 FastAPI
  web/                      upload form, lecture list, study guide viewer
  data/                     created at runtime (gitignored)
  run.sh                    macOS/Linux launcher (CLI)
  Start Lecture Coach.command   macOS launcher (double-click)
```

## Disclaimer

Study guides are grounded in your own uploaded slides. The model may add a brief clarifying definition for a term your slides name but don't define, but it isn't given, and shouldn't be trusted for, any information beyond what's in the deck.
