from __future__ import annotations

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


def generate_study_guide(title: str, slide_text: str, model: str | None = None) -> dict[str, Any]:
    status = ollama_available()
    if not status["ok"]:
        return {
            "provider": "fallback",
            "model": None,
            "content": _fallback_outline(title, slide_text),
            "ollama": status,
        }
    chosen = model or _pick_model(status["models"])
    prompt = (
        f"Lecture title: {title}\n\n"
        "Write the study guide now, following the format in your instructions, from this slide content:\n"
        f"--- SLIDES ---\n{slide_text}"
    )
    payload = {
        "model": chosen,
        "stream": False,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "options": {"temperature": 0.3},
    }
    try:
        r = httpx.post(f"{OLLAMA_URL}/api/chat", json=payload, timeout=300)
        r.raise_for_status()
        content = r.json().get("message", {}).get("content") or ""
        if not content.strip():
            raise ValueError("empty response")
        return {"provider": "ollama", "model": chosen, "content": content, "ollama": status}
    except Exception as exc:
        return {
            "provider": "fallback",
            "model": chosen,
            "content": _fallback_outline(title, slide_text)
            + f"\n\n*(Ollama call failed, showing a raw outline instead: {exc})*",
            "ollama": status,
        }


def _fallback_outline(title: str, slide_text: str) -> str:
    if not slide_text.strip():
        return (
            f"# {title}\n\n"
            "This deck had no extractable text (it may be image-only slides), so there's nothing to "
            "build a study guide from yet."
        )
    header = (
        f"# {title}\n\n"
        "*Ollama is offline, so this is the raw slide outline rather than a generated study guide. "
        "Start Ollama (`ollama serve`, with a model pulled) and regenerate for a real synthesized "
        "guide with grouped topics, key terms, and practice questions.*\n"
    )
    return header + "\n" + slide_text
