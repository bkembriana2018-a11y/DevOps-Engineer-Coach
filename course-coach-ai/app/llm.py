from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import httpx

from .config import APP_DIR, DEFAULT_MODEL, OLLAMA_URL

SYSTEM_PROMPT = (APP_DIR / "knowledge" / "SYSTEM.md").read_text(encoding="utf-8")


def ollama_available() -> dict[str, Any]:
    try:
        r = httpx.get(f"{OLLAMA_URL}/api/tags", timeout=1.5)
        r.raise_for_status()
        models = [m.get("name") for m in r.json().get("models", [])]
        return {"ok": True, "models": models}
    except Exception as exc:
        return {"ok": False, "error": str(exc), "models": []}


def _pick_model(models: list[str]) -> str:
    if not models:
        return DEFAULT_MODEL
    preferred = ["llama3.1", "llama3.2", "llama3", "mistral", "qwen2.5", "gemma2", "phi3"]
    for p in preferred:
        for m in models:
            if m.split(":")[0] == p or m.startswith(p):
                return m
    return models[0]


def chat(
    messages: list[dict[str, str]],
    course_name: str,
    topic_label: str | None,
    context: str,
    model: str | None = None,
) -> dict[str, Any]:
    status = ollama_available()
    scope = f"Course: {course_name}" + (f" -- Topic: {topic_label}" if topic_label else "")
    sys = SYSTEM_PROMPT + f"\n\n--- {scope} ---\n\n--- LECTURE MATERIAL ---\n{context or '(none posted yet for this topic)'}"
    if not status["ok"]:
        return {"provider": "fallback", "model": None, "content": _fallback(messages, context), "ollama": status}
    chosen = model or _pick_model(status["models"])
    payload = {
        "model": chosen,
        "stream": False,
        "messages": [{"role": "system", "content": sys}] + messages[-12:],
        "options": {"temperature": 0.3},
    }
    try:
        r = httpx.post(f"{OLLAMA_URL}/api/chat", json=payload, timeout=300)
        r.raise_for_status()
        content = r.json().get("message", {}).get("content") or ""
        return {"provider": "ollama", "model": chosen, "content": content, "ollama": status}
    except Exception as exc:
        return {
            "provider": "fallback",
            "model": chosen,
            "content": _fallback(messages, context) + f"\n\n(Ollama call failed: {exc})",
            "ollama": status,
        }


def generate_quiz_items(course_name: str, topic_label: str, context: str, n: int, difficulty: str) -> list[dict[str, Any]] | None:
    status = ollama_available()
    if not status["ok"] or not context.strip():
        return None
    prompt = (
        f"Using ONLY the lecture material below for the course '{course_name}', topic '{topic_label}', "
        f"write {n} ORIGINAL multiple-choice practice questions at {difficulty} difficulty that test what "
        f"was actually covered. Never invent facts not supported by the material. Return ONLY a JSON object "
        f"of the exact form {{\"items\": [...]}} containing {n} objects, each with keys: topic (a short tag "
        "naming the specific concept), stem, choices (array of 4 strings starting with 'A) ', 'B) ', 'C) ', "
        "'D) '), answer (the letter), explanation.\n\n"
        f"--- LECTURE MATERIAL ---\n{context}"
    )
    payload = {
        "model": _pick_model(status["models"]),
        "stream": False,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "options": {"temperature": 0.5},
        "format": "json",
    }
    try:
        r = httpx.post(f"{OLLAMA_URL}/api/chat", json=payload, timeout=180)
        r.raise_for_status()
        raw = r.json().get("message", {}).get("content") or "{}"
        return _coerce_items(_parse_json_loose(raw), ("stem", "choices", "answer"))
    except Exception:
        return None


def generate_flashcards(course_name: str, topic_label: str, context: str, n: int) -> list[dict[str, Any]] | None:
    status = ollama_available()
    if not status["ok"] or not context.strip():
        return None
    prompt = (
        f"Using ONLY the lecture material below for the course '{course_name}', topic '{topic_label}', "
        f"write {n} ORIGINAL flashcards (term/concept on the front, a concise explanation on the back) "
        f"covering the most exam-relevant points. Return ONLY a JSON object of the exact form "
        f'{{"items": [...]}} containing {n} objects, each with keys front, back.\n\n'
        f"--- LECTURE MATERIAL ---\n{context}"
    )
    payload = {
        "model": _pick_model(status["models"]),
        "stream": False,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "options": {"temperature": 0.5},
        "format": "json",
    }
    try:
        r = httpx.post(f"{OLLAMA_URL}/api/chat", json=payload, timeout=180)
        r.raise_for_status()
        raw = r.json().get("message", {}).get("content") or "{}"
        return _coerce_items(_parse_json_loose(raw), ("front", "back"))
    except Exception:
        return None


def _parse_json_loose(raw: str) -> Any:
    """Ollama's format=json mode usually returns bare JSON, but some models still
    wrap it in a markdown code fence -- strip that before parsing if present."""
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text
        if text.endswith("```"):
            text = text[: -3]
        text = text.strip()
    return json.loads(text)


def _coerce_items(data: Any, required_keys: tuple[str, ...]) -> list[dict[str, Any]] | None:
    """Ollama's format=json mode reliably returns a JSON *object*, not a bare array,
    even when asked for one -- normalize whatever shape comes back into a list of items."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        if all(k in data for k in required_keys):
            return [data]
        for v in data.values():
            if isinstance(v, list):
                return v
    return None


def _fallback(messages: list[dict[str, str]], context: str) -> str:
    user_text = ""
    for m in reversed(messages):
        if m.get("role") == "user":
            user_text = m.get("content") or ""
            break
    if not user_text.strip():
        return (
            "Ollama is not running. Start it with `ollama serve` (or `brew services start ollama`) "
            "and make sure a model is pulled (`ollama pull llama3.1`). Practice questions, flashcard "
            "generation, and Coach chat all need it -- posting lectures and tracking readiness still "
            "work without it."
        )
    excerpt = context[:2500].strip()
    if not excerpt:
        return (
            "Ollama is offline, and there's no lecture material posted for this topic yet, so there's "
            "nothing to ground an answer in. Post this topic's lecture notes, and start Ollama for full "
            "coaching."
        )
    return (
        "Ollama is offline, so here's the raw lecture excerpt instead of a generated answer.\n\n"
        f"You asked: {user_text}\n\n{excerpt}\n\n"
        "Start Ollama for a real explanation."
    )
