from __future__ import annotations

import json
import secrets
from datetime import datetime, timezone
from typing import Any

from .config import LECTURES_PATH, SLIDES_DIR, STUDY_GUIDES_DIR


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id() -> str:
    return f"lec_{secrets.token_hex(4)}"


def _load_json(path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _save_json(path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _load_lectures() -> list[dict[str, Any]]:
    return _load_json(LECTURES_PATH, [])


def _save_lectures(items: list[dict[str, Any]]) -> None:
    _save_json(LECTURES_PATH, items)


def list_lectures() -> list[dict[str, Any]]:
    items = _load_lectures()
    return sorted(items, key=lambda l: l.get("uploaded_at", ""), reverse=True)


def get_lecture(lecture_id: str) -> dict[str, Any] | None:
    for l in _load_lectures():
        if l["id"] == lecture_id:
            return l
    return None


def add_lecture(title: str, filename: str, slides: list[dict[str, Any]]) -> dict[str, Any]:
    items = _load_lectures()
    lecture = {
        "id": _new_id(),
        "title": title,
        "filename": filename,
        "slide_count": len(slides),
        "uploaded_at": _now(),
        "study_guide_ready": False,
        "generated_by": None,
        "model": None,
        "generated_at": None,
    }
    items.append(lecture)
    _save_lectures(items)
    _save_json(SLIDES_DIR / f"{lecture['id']}.json", slides)
    return lecture


def get_slides(lecture_id: str) -> list[dict[str, Any]]:
    return _load_json(SLIDES_DIR / f"{lecture_id}.json", [])


def _study_guide_path(lecture_id: str):
    return STUDY_GUIDES_DIR / f"{lecture_id}.md"


def get_study_guide(lecture_id: str) -> str | None:
    path = _study_guide_path(lecture_id)
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def save_study_guide(lecture_id: str, content: str, generated_by: str, model: str | None) -> dict[str, Any] | None:
    path = _study_guide_path(lecture_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

    items = _load_lectures()
    updated = None
    for l in items:
        if l["id"] == lecture_id:
            l["study_guide_ready"] = True
            l["generated_by"] = generated_by
            l["model"] = model
            l["generated_at"] = _now()
            updated = l
            break
    if updated is not None:
        _save_lectures(items)
    return updated


def delete_lecture(lecture_id: str) -> bool:
    items = _load_lectures()
    before = len(items)
    items = [l for l in items if l["id"] != lecture_id]
    _save_lectures(items)
    for path in (SLIDES_DIR / f"{lecture_id}.json", _study_guide_path(lecture_id)):
        if path.exists():
            path.unlink()
    return len(items) < before
