from __future__ import annotations

import random
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import llm, store
from .config import CONTEXT_BUDGET, WEB_DIR

app = FastAPI(title="Course Coach", version="1.0.0")
app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")
QUIZ_CACHE: dict[str, dict] = {}


class CourseIn(BaseModel):
    name: str
    code: str | None = None


class TopicIn(BaseModel):
    label: str


class ExamIn(BaseModel):
    label: str
    date: str | None = None
    topic_ids: list[str] = []


class LectureIn(BaseModel):
    title: str
    topic_id: str | None = None
    week: int | None = None
    content: str


class GenerateIn(BaseModel):
    n_questions: int = Field(0, ge=0, le=15)
    n_flashcards: int = Field(0, ge=0, le=20)


class QuizIn(BaseModel):
    topic_id: str | None = None
    n: int = Field(6, ge=1, le=15)
    difficulty: str = "any"


class GradeIn(BaseModel):
    quiz_id: str
    elapsed_sec: float | None = None
    responses: list[dict[str, Any]]


class FlashcardIn(BaseModel):
    topic_id: str | None = None
    front: str
    back: str


class FlashcardGenIn(BaseModel):
    topic_id: str
    n: int = Field(8, ge=1, le=20)


class ChatIn(BaseModel):
    messages: list[dict[str, str]]
    topic_id: str | None = None
    model: str | None = None


@app.get("/")
def index():
    return FileResponse(WEB_DIR / "index.html")


@app.get("/api/health")
def health():
    return {"ok": True, "ollama": llm.ollama_available(), "course_count": len(store.list_courses())}


# ---------- courses ----------

@app.get("/api/courses")
def list_courses():
    return {"courses": store.list_courses()}


@app.post("/api/courses")
def create_course(body: CourseIn):
    return store.create_course(body.name, body.code)


@app.get("/api/courses/{course_id}")
def get_course(course_id: str):
    c = store.get_course(course_id)
    if not c:
        raise HTTPException(404, "No such course")
    return c


@app.delete("/api/courses/{course_id}")
def delete_course(course_id: str):
    if not store.delete_course(course_id):
        raise HTTPException(404, "No such course")
    return {"ok": True}


@app.post("/api/courses/{course_id}/topics")
def add_topic(course_id: str, body: TopicIn):
    if not store.get_course(course_id):
        raise HTTPException(404, "No such course")
    return store.add_topic(course_id, body.label)


@app.delete("/api/courses/{course_id}/topics/{topic_id}")
def delete_topic(course_id: str, topic_id: str):
    store.delete_topic(course_id, topic_id)
    return {"ok": True}


@app.post("/api/courses/{course_id}/exams")
def add_exam(course_id: str, body: ExamIn):
    if not store.get_course(course_id):
        raise HTTPException(404, "No such course")
    return store.add_exam(course_id, body.label, body.date, body.topic_ids)


@app.get("/api/courses/{course_id}/readiness")
def readiness(course_id: str):
    try:
        return store.readiness(course_id)
    except KeyError:
        raise HTTPException(404, "No such course")


@app.post("/api/courses/{course_id}/reset")
def reset_progress(course_id: str):
    store.save_progress(course_id, {"events": [], "topics": {}})
    return store.readiness(course_id)


# ---------- lectures ----------

@app.get("/api/courses/{course_id}/lectures")
def list_lectures(course_id: str, topic_id: str | None = None):
    return {"lectures": store.list_lectures(course_id, topic_id)}


@app.post("/api/courses/{course_id}/lectures")
def add_lecture(course_id: str, body: LectureIn):
    if not store.get_course(course_id):
        raise HTTPException(404, "No such course")
    return store.add_lecture(course_id, body.title, body.topic_id, body.week, body.content)


@app.get("/api/courses/{course_id}/context")
def get_context(course_id: str, topic_id: str | None = None):
    return {"content": store.topic_context(course_id, topic_id, CONTEXT_BUDGET)}


@app.post("/api/courses/{course_id}/lectures/{lecture_id}/generate")
def generate_from_lecture(course_id: str, lecture_id: str, body: GenerateIn):
    course = store.get_course(course_id)
    lecture = store.get_lecture(course_id, lecture_id)
    if not course or not lecture:
        raise HTTPException(404, "No such course or lecture")
    topic_label = next((t["label"] for t in course["topics"] if t["id"] == lecture.get("topic_id")), "General")
    result = {"flashcards_added": 0, "questions_previewed": 0}
    if body.n_flashcards:
        cards = llm.generate_flashcards(course["name"], topic_label, lecture["content"], body.n_flashcards)
        if cards:
            saved = store.add_flashcards(
                course_id,
                [{"topic_id": lecture.get("topic_id"), "front": c["front"], "back": c["back"], "source": "ai"} for c in cards if c.get("front") and c.get("back")],
            )
            result["flashcards_added"] = len(saved)
    if body.n_questions:
        items = llm.generate_quiz_items(course["name"], topic_label, lecture["content"], body.n_questions, "any")
        result["questions_previewed"] = len(items) if items else 0
    if not result["flashcards_added"] and not result["questions_previewed"]:
        o = llm.ollama_available()
        if not o["ok"]:
            raise HTTPException(503, "Ollama is offline -- start it to generate from this lecture.")
    return result


# ---------- quiz ----------

@app.post("/api/courses/{course_id}/quiz")
def make_quiz(course_id: str, body: QuizIn):
    course = store.get_course(course_id)
    if not course:
        raise HTTPException(404, "No such course")
    topic_label = "Mixed"
    if body.topic_id:
        topic_label = next((t["label"] for t in course["topics"] if t["id"] == body.topic_id), "Topic")
    context = store.topic_context(course_id, body.topic_id, CONTEXT_BUDGET)
    note = None
    items: list[dict[str, Any]] = []
    if not context.strip():
        note = "No lectures posted for this topic yet -- post some notes first so questions can be grounded in what was actually taught."
    else:
        raw = llm.generate_quiz_items(course["name"], topic_label, context, body.n, body.difficulty)
        if raw:
            for i, item in enumerate(raw):
                choices = item.get("choices")
                answer_raw = str(item.get("answer") or "").strip()
                if not item.get("stem") or not choices or not answer_raw:
                    continue
                # Models sometimes answer with the full choice text instead of
                # just its letter -- normalize to a single letter either way.
                answer_letter = answer_raw[:1].upper()
                items.append(
                    {
                        "id": f"Q-{random.randint(100000, 999999)}-{i}",
                        "topic_id": body.topic_id,
                        "tag": item.get("topic") or topic_label,
                        "stem": item["stem"],
                        "choices": choices,
                        "answer": answer_letter,
                        "explanation": item.get("explanation") or "",
                    }
                )
        if not items:
            o = llm.ollama_available()
            note = "Ollama is offline -- start it to generate practice questions." if not o["ok"] else "Couldn't generate valid questions from this material -- try again or post more detailed notes."
    quiz_id = f"quiz-{random.randint(100000, 999999)}"
    quiz = {"quiz_id": quiz_id, "topic_id": body.topic_id, "topic_label": topic_label, "note": note, "items": items}
    QUIZ_CACHE[quiz_id] = quiz
    if len(QUIZ_CACHE) > 100:
        QUIZ_CACHE.pop(next(iter(QUIZ_CACHE)), None)
    return quiz


@app.post("/api/courses/{course_id}/grade")
def grade(course_id: str, body: GradeIn):
    quiz = QUIZ_CACHE.get(body.quiz_id)
    if not quiz:
        raise HTTPException(400, "Quiz expired or not found -- start a new one")
    index = {i["id"]: i for i in quiz["items"]}
    results = []
    correct = 0
    for r in body.responses:
        item = index.get(r["id"])
        if not item:
            continue
        ok = str(r.get("selected", "")).upper()[:1] == str(item["answer"]).upper()[:1]
        if ok:
            correct += 1
        results.append(
            {
                "id": item["id"],
                "topic_id": item.get("topic_id"),
                "tag": item.get("tag"),
                "selected": r.get("selected"),
                "answer": item["answer"],
                "correct": ok,
                "explanation": item["explanation"],
                "stem": item["stem"],
            }
        )
    total = len(results)
    graded = {"correct": correct, "total": total, "percent": round(100 * correct / total, 1) if total else 0, "results": results}
    ready = store.record_quiz(course_id, graded, body.elapsed_sec)
    return {"graded": graded, "readiness": ready}


# ---------- flashcards ----------

@app.get("/api/courses/{course_id}/flashcards")
def list_flashcards(course_id: str, topic_id: str | None = None):
    return {"cards": store.list_flashcards(course_id, topic_id)}


@app.post("/api/courses/{course_id}/flashcards")
def add_flashcard(course_id: str, body: FlashcardIn):
    saved = store.add_flashcards(course_id, [{"topic_id": body.topic_id, "front": body.front, "back": body.back, "source": "manual"}])
    return saved[0]


@app.post("/api/courses/{course_id}/flashcards/generate")
def generate_flashcards(course_id: str, body: FlashcardGenIn):
    course = store.get_course(course_id)
    if not course:
        raise HTTPException(404, "No such course")
    topic_label = next((t["label"] for t in course["topics"] if t["id"] == body.topic_id), "Topic")
    context = store.topic_context(course_id, body.topic_id, CONTEXT_BUDGET)
    if not context.strip():
        raise HTTPException(400, "No lectures posted for this topic yet")
    cards = llm.generate_flashcards(course["name"], topic_label, context, body.n)
    if not cards:
        o = llm.ollama_available()
        raise HTTPException(503 if not o["ok"] else 500, "Ollama is offline" if not o["ok"] else "Generation failed, try again")
    saved = store.add_flashcards(course_id, [{"topic_id": body.topic_id, "front": c["front"], "back": c["back"], "source": "ai"} for c in cards if c.get("front") and c.get("back")])
    return {"cards": saved}


@app.delete("/api/courses/{course_id}/flashcards/{card_id}")
def delete_flashcard(course_id: str, card_id: str):
    store.delete_flashcard(course_id, card_id)
    return {"ok": True}


# ---------- chat ----------

@app.post("/api/courses/{course_id}/chat")
def chat(course_id: str, body: ChatIn):
    course = store.get_course(course_id)
    if not course:
        raise HTTPException(404, "No such course")
    if not body.messages:
        raise HTTPException(400, "No messages")
    topic_label = None
    if body.topic_id:
        topic_label = next((t["label"] for t in course["topics"] if t["id"] == body.topic_id), None)
    context = store.topic_context(course_id, body.topic_id, CONTEXT_BUDGET)
    return llm.chat(body.messages, course["name"], topic_label, context, model=body.model)
