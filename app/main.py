from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import bank, flashcards, llm, tracker
from .config import COMPOSITES, SUBTESTS, WEB_DIR
from .knowledge_loader import retrieve, system_prompt

app = FastAPI(title="Cloud Coach", version="1.0.0")
app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")
QUIZ_CACHE: dict[str, dict] = {}


class ChatIn(BaseModel):
    messages: list[dict[str, str]]
    subtest: str | None = None
    model: str | None = None


class QuizIn(BaseModel):
    subtest: str = "mixed"
    n: int = Field(8, ge=1, le=25)
    difficulty: str = "any"
    use_llm: bool = False


class GradeIn(BaseModel):
    subtest: str = "mixed"
    quiz_id: str | None = None
    elapsed_sec: float | None = None
    responses: list[dict[str, Any]]


class TrackIn(BaseModel):
    target_track: str


@app.get("/")
def index():
    return FileResponse(WEB_DIR / "index.html")


@app.get("/api/health")
def health():
    o = llm.ollama_available()
    return {"ok": True, "ollama": o, "subtests": list(SUBTESTS), "bank_size": len(bank.ITEMS)}


@app.get("/api/meta")
def meta():
    return {"subtests": SUBTESTS, "composites": COMPOSITES}


@app.get("/api/knowledge")
def knowledge(topic: str = "overview"):
    text = retrieve(topic.replace("_", " "), subtest=topic if topic else None)
    return {"topic": topic, "content": text or system_prompt()}


@app.get("/api/flashcards")
def get_flashcards(deck: str | None = None):
    return {"decks": flashcards.decks(), "cards": flashcards.get_cards(deck)}


@app.get("/api/readiness")
def readiness():
    return tracker.readiness()


@app.post("/api/track")
def set_track(body: TrackIn):
    return tracker.set_track(body.target_track)


@app.post("/api/quiz")
def make_quiz(body: QuizIn):
    quiz = bank.sample_quiz(body.subtest, body.n, body.difficulty)
    extra = []
    if body.use_llm:
        extra = llm.generate_quiz_items(body.subtest, min(body.n, 5), body.difficulty) or []
        for i, item in enumerate(extra):
            item.setdefault("id", f"LLM-{body.subtest}-{i}")
            item.setdefault("subtest", body.subtest)
            quiz["items"].append(item)
    QUIZ_CACHE[quiz["quiz_id"]] = quiz
    if len(QUIZ_CACHE) > 50:
        oldest = next(iter(QUIZ_CACHE))
        QUIZ_CACHE.pop(oldest, None)
    return quiz


@app.post("/api/grade")
def grade(body: GradeIn):
    if not body.responses:
        raise HTTPException(400, "No responses")
    extra = []
    if body.quiz_id and body.quiz_id in QUIZ_CACHE:
        extra = QUIZ_CACHE[body.quiz_id].get("items") or []
    graded = bank.grade(body.responses, extra_items=extra)
    ready = tracker.record_quiz(graded, body.subtest, body.elapsed_sec)
    return {"graded": graded, "readiness": ready}


@app.post("/api/chat")
def chat(body: ChatIn):
    if not body.messages:
        raise HTTPException(400, "No messages")
    return llm.chat(body.messages, subtest=body.subtest, model=body.model)


@app.post("/api/reset")
def reset():
    data = tracker.default_progress()
    tracker.save(data)
    return tracker.readiness(data)
