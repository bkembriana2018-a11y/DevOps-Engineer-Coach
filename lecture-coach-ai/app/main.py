from __future__ import annotations

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from . import llm, store
from .config import CONTEXT_BUDGET, MAX_UPLOAD_BYTES, WEB_DIR
from .pptx_extract import extract_slides, slides_to_text

app = FastAPI(title="Lecture Coach", version="1.0.0")
app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")


@app.get("/")
def index():
    return FileResponse(WEB_DIR / "index.html")


@app.get("/api/health")
def health():
    return {"ok": True, "ollama": llm.ollama_available(), "lecture_count": len(store.list_lectures())}


@app.get("/api/lectures")
def list_lectures():
    return {"lectures": store.list_lectures()}


@app.post("/api/lectures")
async def upload_lecture(file: UploadFile = File(...), title: str | None = Form(None)):
    if not file.filename.lower().endswith(".pptx"):
        raise HTTPException(400, "Only .pptx files are supported")
    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(400, "File is too large (25 MB limit)")
    try:
        slides = extract_slides(data)
    except Exception as exc:
        raise HTTPException(400, f"Couldn't read this .pptx file: {exc}")
    guessed_title = title or file.filename.rsplit(".", 1)[0]
    lecture = store.add_lecture(guessed_title, file.filename, slides)
    return lecture


@app.get("/api/lectures/{lecture_id}")
def get_lecture(lecture_id: str):
    lecture = store.get_lecture(lecture_id)
    if not lecture:
        raise HTTPException(404, "No such lecture")
    return {**lecture, "slides": store.get_slides(lecture_id)}


@app.delete("/api/lectures/{lecture_id}")
def delete_lecture(lecture_id: str):
    if not store.delete_lecture(lecture_id):
        raise HTTPException(404, "No such lecture")
    return {"ok": True}


@app.post("/api/lectures/{lecture_id}/study-guide")
def generate_study_guide(lecture_id: str):
    lecture = store.get_lecture(lecture_id)
    if not lecture:
        raise HTTPException(404, "No such lecture")
    slides = store.get_slides(lecture_id)
    text = slides_to_text(slides)[:CONTEXT_BUDGET]
    result = llm.generate_study_guide(lecture["title"], text)
    updated = store.save_study_guide(lecture_id, result["content"], result["provider"], result["model"])
    return {**updated, "content": result["content"], "ollama": result["ollama"]}


@app.get("/api/lectures/{lecture_id}/study-guide")
def get_study_guide(lecture_id: str):
    lecture = store.get_lecture(lecture_id)
    if not lecture:
        raise HTTPException(404, "No such lecture")
    content = store.get_study_guide(lecture_id)
    if content is None:
        raise HTTPException(404, "No study guide generated yet for this lecture")
    return {"content": content}


@app.get("/api/lectures/{lecture_id}/study-guide/download")
def download_study_guide(lecture_id: str):
    lecture = store.get_lecture(lecture_id)
    if not lecture:
        raise HTTPException(404, "No such lecture")
    content = store.get_study_guide(lecture_id)
    if content is None:
        raise HTTPException(404, "No study guide generated yet for this lecture")
    safe_name = "".join(c for c in lecture["title"] if c.isalnum() or c in " -_").strip() or "study-guide"
    return PlainTextResponse(
        content,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{safe_name}.md"'},
    )
