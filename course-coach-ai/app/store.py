from __future__ import annotations

import json
import secrets
from datetime import datetime, timezone, date
from typing import Any

from .config import COURSES_PATH, DATA_DIR, FLASHCARDS_DIR, LECTURES_DIR, PROGRESS_DIR


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id(prefix: str) -> str:
    return f"{prefix}_{secrets.token_hex(4)}"


def _load_json(path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _save_json(path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


# ---------- courses ----------

def _load_courses() -> dict[str, Any]:
    return _load_json(COURSES_PATH, {"courses": []})


def _save_courses(data: dict[str, Any]) -> None:
    _save_json(COURSES_PATH, data)


def list_courses() -> list[dict[str, Any]]:
    return _load_courses()["courses"]


def get_course(course_id: str) -> dict[str, Any] | None:
    for c in list_courses():
        if c["id"] == course_id:
            return c
    return None


def create_course(name: str, code: str | None = None) -> dict[str, Any]:
    data = _load_courses()
    course = {
        "id": _new_id("c"),
        "name": name,
        "code": code or "",
        "created_at": _now(),
        "topics": [],
        "exams": [],
    }
    data["courses"].append(course)
    _save_courses(data)
    return course


def delete_course(course_id: str) -> bool:
    data = _load_courses()
    before = len(data["courses"])
    data["courses"] = [c for c in data["courses"] if c["id"] != course_id]
    _save_courses(data)
    lec = LECTURES_DIR / f"{course_id}.json"
    fc = FLASHCARDS_DIR / f"{course_id}.json"
    pr = PROGRESS_DIR / f"{course_id}.json"
    for p in (lec, fc, pr):
        if p.exists():
            p.unlink()
    return len(data["courses"]) < before


def _mutate_course(course_id: str, fn):
    data = _load_courses()
    for c in data["courses"]:
        if c["id"] == course_id:
            fn(c)
            _save_courses(data)
            return c
    raise KeyError(f"No course {course_id}")


def add_topic(course_id: str, label: str) -> dict[str, Any]:
    topic = {"id": _new_id("t"), "label": label, "created_at": _now()}

    def fn(c):
        c["topics"].append(topic)

    _mutate_course(course_id, fn)
    return topic


def delete_topic(course_id: str, topic_id: str) -> None:
    def fn(c):
        c["topics"] = [t for t in c["topics"] if t["id"] != topic_id]

    _mutate_course(course_id, fn)


def add_exam(course_id: str, label: str, exam_date: str | None, topic_ids: list[str]) -> dict[str, Any]:
    exam = {"id": _new_id("e"), "label": label, "date": exam_date, "topic_ids": topic_ids}

    def fn(c):
        c["exams"].append(exam)

    _mutate_course(course_id, fn)
    return exam


def next_exam(course: dict[str, Any]) -> dict[str, Any] | None:
    today = date.today()
    upcoming = []
    for e in course.get("exams", []):
        if not e.get("date"):
            continue
        try:
            d = date.fromisoformat(e["date"])
        except ValueError:
            continue
        if d >= today:
            upcoming.append((d, e))
    if not upcoming:
        return None
    upcoming.sort(key=lambda pair: pair[0])
    d, e = upcoming[0]
    return {**e, "days_away": (d - today).days}


# ---------- lectures ----------

def _lectures_path(course_id: str):
    return LECTURES_DIR / f"{course_id}.json"


def list_lectures(course_id: str, topic_id: str | None = None) -> list[dict[str, Any]]:
    items = _load_json(_lectures_path(course_id), [])
    if topic_id:
        items = [i for i in items if i.get("topic_id") == topic_id]
    return items


def add_lecture(course_id: str, title: str, topic_id: str | None, week: int | None, content: str) -> dict[str, Any]:
    items = _load_json(_lectures_path(course_id), [])
    lecture = {
        "id": _new_id("l"),
        "title": title,
        "topic_id": topic_id,
        "week": week,
        "content": content,
        "added_at": _now(),
    }
    items.append(lecture)
    _save_json(_lectures_path(course_id), items)
    return lecture


def get_lecture(course_id: str, lecture_id: str) -> dict[str, Any] | None:
    for l in list_lectures(course_id):
        if l["id"] == lecture_id:
            return l
    return None


def topic_context(course_id: str, topic_id: str | None, budget: int) -> str:
    """Concatenate this topic's lectures (most recent first) up to a character budget."""
    items = list_lectures(course_id, topic_id)
    items.sort(key=lambda i: i.get("added_at", ""), reverse=True)
    chunks = []
    used = 0
    for l in items:
        piece = f"\n\n--- LECTURE: {l['title']} (week {l.get('week') or '?'}) ---\n{l['content']}"
        if used + len(piece) > budget:
            remain = budget - used
            if remain > 300:
                chunks.append(piece[:remain])
            break
        chunks.append(piece)
        used += len(piece)
    return "".join(chunks)


# ---------- flashcards ----------

def _flashcards_path(course_id: str):
    return FLASHCARDS_DIR / f"{course_id}.json"


def list_flashcards(course_id: str, topic_id: str | None = None) -> list[dict[str, Any]]:
    items = _load_json(_flashcards_path(course_id), [])
    if topic_id:
        items = [i for i in items if i.get("topic_id") == topic_id]
    return items


def add_flashcards(course_id: str, cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items = _load_json(_flashcards_path(course_id), [])
    added = []
    for c in cards:
        card = {
            "id": _new_id("f"),
            "topic_id": c.get("topic_id"),
            "front": c["front"],
            "back": c["back"],
            "source": c.get("source", "manual"),
            "added_at": _now(),
        }
        items.append(card)
        added.append(card)
    _save_json(_flashcards_path(course_id), items)
    return added


def delete_flashcard(course_id: str, card_id: str) -> None:
    items = _load_json(_flashcards_path(course_id), [])
    items = [c for c in items if c["id"] != card_id]
    _save_json(_flashcards_path(course_id), items)


# ---------- progress / readiness ----------

def _progress_path(course_id: str):
    return PROGRESS_DIR / f"{course_id}.json"


def _default_topic_stat() -> dict[str, Any]:
    return {
        "attempts": 0,
        "correct": 0,
        "seen_ids": [],
        "miss_topics": {},
        "last_percent": None,
        "last_at": None,
    }


def load_progress(course_id: str) -> dict[str, Any]:
    return _load_json(_progress_path(course_id), {"events": [], "topics": {}})


def save_progress(course_id: str, data: dict[str, Any]) -> None:
    _save_json(_progress_path(course_id), data)


def _band(percent: float | None, attempts: int) -> str:
    if attempts < 3 or percent is None:
        return "untested"
    if percent >= 85:
        return "ready"
    if percent >= 70:
        return "borderline"
    return "weak"


def record_quiz(course_id: str, graded: dict[str, Any], elapsed_sec: float | None) -> dict[str, Any]:
    data = load_progress(course_id)
    data["events"].append(
        {
            "at": _now(),
            "correct": graded["correct"],
            "total": graded["total"],
            "percent": graded["percent"],
            "elapsed_sec": elapsed_sec,
        }
    )
    data["events"] = data["events"][-300:]
    by_topic: dict[str, list] = {}
    for r in graded["results"]:
        by_topic.setdefault(r.get("topic_id") or "general", []).append(r)
    for tid, rows in by_topic.items():
        slot = data["topics"].setdefault(tid, _default_topic_stat())
        slot["attempts"] += len(rows)
        slot["correct"] += sum(1 for r in rows if r["correct"])
        for r in rows:
            if r["id"] not in slot["seen_ids"]:
                slot["seen_ids"].append(r["id"])
            if not r["correct"]:
                tag = r.get("tag") or "general"
                slot["miss_topics"][tag] = slot["miss_topics"].get(tag, 0) + 1
        slot["last_percent"] = round(100 * sum(1 for r in rows if r["correct"]) / len(rows), 1)
        slot["last_at"] = _now()
        slot["seen_ids"] = slot["seen_ids"][-300:]
    save_progress(course_id, data)
    return readiness(course_id)


def readiness(course_id: str) -> dict[str, Any]:
    course = get_course(course_id)
    if not course:
        raise KeyError(f"No course {course_id}")
    data = load_progress(course_id)
    topics_out = {}
    percents = []
    for t in course["topics"]:
        tid = t["id"]
        slot = data["topics"].get(tid, _default_topic_stat())
        attempts = slot["attempts"]
        pct = round(100 * slot["correct"] / attempts, 1) if attempts else None
        misses = sorted(slot.get("miss_topics", {}).items(), key=lambda kv: -kv[1])[:5]
        band = _band(pct, attempts)
        topics_out[tid] = {
            "id": tid,
            "label": t["label"],
            "attempts": attempts,
            "correct": slot["correct"],
            "percent": pct,
            "band": band,
            "top_miss_topics": [m[0] for m in misses],
            "lecture_count": len(list_lectures(course_id, tid)),
        }
        if pct is not None:
            percents.append(pct)

    overall_pct = round(sum(percents) / len(percents), 1) if percents else None
    overall_band = _band(overall_pct, 3 if percents else 0)

    nxt = next_exam(course)
    actions = []
    priority = sorted(
        topics_out.values(),
        key=lambda t: (0 if t["band"] == "weak" else 1 if t["band"] == "untested" else 2 if t["band"] == "borderline" else 3),
    )
    for t in priority:
        if t["band"] in ("weak", "untested", "borderline"):
            why = {
                "untested": "No practice logged yet.",
                "weak": "Accuracy below 70%.",
                "borderline": "Getting there -- push to 85%+.",
            }[t["band"]]
            miss = t["top_miss_topics"]
            extra = f" Miss tags: {', '.join(miss)}." if miss else ""
            lec_note = "" if t["lecture_count"] else " No lectures posted for this topic yet."
            actions.append(f"{t['label']}: {why}{extra}{lec_note}")
        if len(actions) >= 6:
            break
    if not actions:
        actions.append("Every topic is green. Keep a light weekly review going so nothing decays before the exam.")

    return {
        "course_id": course_id,
        "course_name": course["name"],
        "overall_percent": overall_pct,
        "overall_band": overall_band,
        "topics": topics_out,
        "next_actions": actions,
        "next_exam": nxt,
        "event_count": len(data.get("events", [])),
        "disclaimer": "Practice percent reflects only the questions this app has quizzed you on -- it is not a grade prediction.",
    }
