# Course Coach

Local study guide, quiz generator, flashcard deck, and readiness tracker for **any of your college classes** — multi-course, syllabus-first, then grow it week by week with your own lecture notes.

Unlike this repo's other app, [Cloud Coach](../README.md), Course Coach has **no hardcoded subject matter**. Every class, topic, exam date, and piece of knowledge comes from what you post — the app never invents content for a class it hasn't seen material from.

---

## How it works

1. **Add a class** and set up its topics + exam dates (from your syllabus).
2. **Post lecture notes** as you go, organized by topic/week — paste slides, transcripts, or your own notes.
3. The app's local AI (Ollama) generates **flashcards** and **practice questions** grounded *only* in what you've posted for that topic — never from outside knowledge, so nothing you're quizzed on can be off-syllabus.
4. **Coach chat** answers questions and helps you prep for graded discussion posts, grounded in your actual lecture material — it'll tell you plainly if a topic has no material posted yet rather than guessing.
5. **My Progress** tracks accuracy per topic and counts down to your next exam.

---

## Requirements

- macOS (primary target)
- Python 3.10+
- [Ollama](https://ollama.com) — **required** for practice questions, flashcard generation, and Coach chat (there's no static question bank in this app, since content is different for every class). Posting lectures and tracking readiness work without it.

---

## Install

### Fast path — double-click

1. Clone this repo.
2. Double-click **`Start Course Coach.command`** inside this folder.
3. First run installs everything automatically — then opens http://127.0.0.1:8767 in your browser.
4. To stop it, close that Terminal window.

### Manual

```bash
cd course-coach-ai
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
chmod +x run.sh
./run.sh
```

Open http://127.0.0.1:8767

### Local LLM (required for AI features)

```bash
brew install ollama
brew services start ollama
ollama pull llama3.1
```

---

## Layout

```
course-coach-ai/
  app/
    knowledge/SYSTEM.md      the one static file: the tutor's behavioral contract
    store.py                 all persistence -- courses, topics, exams, lectures, flashcards, progress
    llm.py                   Ollama chat + generation, grounded only in posted lecture text
    main.py                  FastAPI, routes scoped under /api/courses/{id}/...
  web/                       dashboard with a course switcher
  data/                      created at runtime -- courses.json, lectures/, flashcards/, progress/ (all gitignored, all yours)
```

## Disclaimer

Practice percent reflects only what this app has quizzed you on from your own posted material — it is not a grade prediction. Coach chat will not ghostwrite discussion posts for you to submit verbatim; it helps you develop your own argument instead.
