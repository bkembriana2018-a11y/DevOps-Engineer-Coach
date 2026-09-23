# Course Coach — Claude Code project notes

Local FastAPI + static UI multi-class study app. Unlike its siblings (afoqt-coach-ai, cloud-coach-ai), this one has NO hardcoded subject matter — every class, topic, exam date, and knowledge base entry is user-created data, not code.

## Run

```bash
chmod +x run.sh
./run.sh
```

App: http://127.0.0.1:8767
Health: http://127.0.0.1:8767/api/health
Ollama (optional, shared with other local apps): http://127.0.0.1:11434

## Content model

- A **course** (`app/store.py`) has topics and exams, created by the user (typically from a syllabus).
- **Lectures** are raw text the user pastes in per topic/week — this is the only source of subject-matter grounding. Nothing about any specific class is hand-authored in this codebase.
- Quiz questions and flashcards are generated on demand by the local Ollama model, grounded ONLY in that topic's posted lecture text (`app/llm.py`). There is no static question bank — without Ollama running, Practice and "Generate cards" won't produce content (posting lectures, tracking readiness, and manually-added flashcards still work).
- All data lives under `data/` (gitignored, created at runtime): `courses.json`, `lectures/<course_id>.json`, `flashcards/<course_id>.json`, `progress/<course_id>.json`.

## Layout

- `app/main.py` — FastAPI, all routes scoped under `/api/courses/{course_id}/...`
- `app/store.py` — all persistence (courses/topics/exams/lectures/flashcards/progress), no domain logic beyond generic band thresholds
- `app/llm.py` — Ollama chat + quiz/flashcard generation, grounded in whatever lecture text is passed in
- `app/knowledge/SYSTEM.md` — the one static file in the app: the tutor's behavioral contract (be honest about what isn't in the lecture material, don't ghostwrite discussion posts, etc.)
- `web/` — dashboard with a course switcher; same visual family as the sibling apps (indigo/violet palette here)

## Guardrails

- Never invent course content not present in what the user posted — if a topic has no lectures yet, say so instead of generating from general knowledge.
- Discussion-forum help should coach the student's own argument, not produce a submittable post for them.
- Port 8767 — 8765 is afoqt-coach-ai, 8766 is cloud-coach-ai.

## Recurring workflow

A local scheduled task (`~/.claude/scheduled-tasks/course-coach-weekly-checkin/SKILL.md`) runs weekly to prompt the user for that week's lecture material (or a new class's syllabus, if no courses exist yet) and add it via this app's API.
