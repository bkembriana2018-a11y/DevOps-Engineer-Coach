# Cloud Coach

Local study guide, quiz generator, and readiness tracker for **AWS**, **Terraform**, and **Kubernetes** — the stack behind most Cloud Engineer / DevOps Engineer / Platform Engineer roles.

This is **not** official AWS, HashiCorp, or CNCF exam content. All practice questions are original.

**Sibling project:** [afoqt-coach-ai](https://github.com/WGLewis0721/afoqt-coach-ai) — same architecture, different domain.

**Also in this repo:** [course-coach-ai/](course-coach-ai/) — a separate, unrelated app for keeping up with your own college classes (multi-course, syllabus + your own lecture notes, no hardcoded subject matter). Runs on its own port (8767) and has its own README.

---

## What you get

- **Study pack** a local LLM can use as grounding (`app/knowledge/`) covering AWS core/architecture, Terraform fundamentals/advanced, and Kubernetes core/operations
- **Quiz engine** from an original item bank (60 items across `app/questions/bank_*.json`), optional Ollama-generated extras
- **Flashcards** (61 cards across AWS, Terraform, and Kubernetes decks)
- **Readiness tracker** in `data/progress.json` (practice percent is not an official certification score)

Your "goal" on the dashboard just changes what's prioritized in "What to do next" — every topic is always available:

- **Full-stack DevOps** (default) — balanced across all three
- **Platform Engineer** — weights Kubernetes + Terraform higher
- **Cloud Architect** — weights AWS higher

---

## Requirements

- macOS (primary target)
- Python 3.10+ (the app uses modern type-hint syntax)
- Optional: [Ollama](https://ollama.com) for Coach chat and generated items

---

## Install

### Fast path — double-click

1. Clone this repo.
2. Double-click **`Start Cloud Coach.command`**.
3. First run installs everything automatically (a Terminal window will show progress) — after that it opens http://127.0.0.1:8766 in your browser by itself.
4. To stop it, close that Terminal window.

If macOS blocks it the first time ("cannot be opened because it is from an unidentified developer"): right-click the file → **Open** → **Open** again to confirm once.

### Manual

```bash
git clone https://github.com/bkembriana2018-a11y/DevOps-Engineer-Coach.git
cd DevOps-Engineer-Coach
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
chmod +x run.sh
./run.sh
```

Open http://127.0.0.1:8766

### Local LLM (optional, recommended for Coach)

Practice and flashcards work without this. Coach chat and "Add a few AI questions" need Ollama.

```bash
brew install ollama
brew services start ollama
ollama pull llama3.1
```

The app calls `http://127.0.0.1:11434`. Confirm:

```bash
curl -s http://127.0.0.1:11434/api/tags
curl -s http://127.0.0.1:8766/api/health
```

`health.ollama.ok` should be `true` once the daemon and a model are present.

---

## Layout

```
DevOps-Engineer-Coach/
  app/
    knowledge/                        LLM grounding (SYSTEM.md, OVERVIEW.md, DEVOPS_TRACKS.md, ...)
    questions/bank_aws.json           AWS Core + Architecture items
    questions/bank_terraform.json     Terraform Fundamentals + Advanced items
    questions/bank_k8s.json           Kubernetes Core + Operations items
    questions/flashcards_*.json       flashcard decks (aws, terraform, kubernetes)
    main.py                           FastAPI
  web/
    fonts/                            self-hosted webfonts (works offline)
    index.html, styles.css, app.js
  data/                               created at runtime
  run.sh                              macOS/Linux launcher (CLI)
  Start Cloud Coach.command           macOS launcher (double-click)
```

---

## Certifications this app loosely tracks

None are required to use this app, and none of its practice percentages are official predictors of a real score:

| Certification | Format | Commonly published passing bar |
|---|---|---|
| AWS Certified Solutions Architect – Associate | 65 scored MCQ, scaled 100–1000 | Scaled 720 (not literally 72% of raw questions) |
| HashiCorp Certified: Terraform Associate | ~57 MCQ/true-false | Scaled, commonly cited ~70% |
| Certified Kubernetes Administrator (CKA) | Hands-on tasks, live cluster, no MCQ | 66/100 |

Confirm current format and passing bars with the certifying body before you register.

## Disclaimer

Original practice items only. Not affiliated with Amazon Web Services, HashiCorp, or the Cloud Native Computing Foundation. Do not treat practice percent as an official exam score.
