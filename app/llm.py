from __future__ import annotations

import json
from typing import Any

import httpx

from .config import DEFAULT_MODEL, OLLAMA_URL
from .knowledge_loader import retrieve, system_prompt


def ollama_available() -> dict[str, Any]:
    try:
        r = httpx.get(f"{OLLAMA_URL}/api/tags", timeout=1.5)
        r.raise_for_status()
        models = [m.get("name") for m in r.json().get("models", [])]
        return {"ok": True, "models": models}
    except Exception as exc:
        return {"ok": False, "error": str(exc), "models": []}


def chat(
    messages: list[dict[str, str]],
    subtest: str | None = None,
    model: str | None = None,
) -> dict[str, Any]:
    status = ollama_available()
    user_text = ""
    for m in reversed(messages):
        if m.get("role") == "user":
            user_text = m.get("content") or ""
            break
    context = retrieve(user_text, subtest=subtest)
    sys = system_prompt() + "\n\n--- KNOWLEDGE PACK ---\n" + context
    if not status["ok"]:
        return {
            "provider": "fallback",
            "model": None,
            "content": _fallback(user_text, context),
            "ollama": status,
        }
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
            "content": _fallback(user_text, context) + f"\n\n(Ollama call failed: {exc})",
            "ollama": status,
        }


def generate_quiz_items(subtest: str, n: int, difficulty: str) -> list[dict[str, Any]] | None:
    status = ollama_available()
    if not status["ok"]:
        return None
    context = retrieve(subtest.replace("_", " "), subtest=subtest)
    prompt = (
        f"Generate {n} ORIGINAL multiple-choice study questions on the topic '{subtest}' "
        f"at {difficulty} difficulty, in the style of AWS/Terraform/Kubernetes certification "
        "prep (never quote or paraphrase real exam questions). Return ONLY a JSON array of "
        "item objects with keys id, topic, stem, choices, answer, explanation. Four choices A-D."
    )
    sys = system_prompt() + "\n\n" + context
    payload = {
        "model": _pick_model(status["models"]),
        "stream": False,
        "messages": [
            {"role": "system", "content": sys},
            {"role": "user", "content": prompt},
        ],
        "options": {"temperature": 0.7},
        "format": "json",
    }
    try:
        r = httpx.post(f"{OLLAMA_URL}/api/chat", json=payload, timeout=120)
        r.raise_for_status()
        raw = r.json().get("message", {}).get("content") or "[]"
        data = json.loads(raw)
        if isinstance(data, dict) and "items" in data:
            data = data["items"]
        if isinstance(data, list):
            return data
    except Exception:
        return None
    return None


def _pick_model(models: list[str]) -> str:
    if not models:
        return DEFAULT_MODEL
    preferred = ["llama3.1", "llama3.2", "llama3", "mistral", "qwen2.5", "gemma2", "phi3"]
    for p in preferred:
        for m in models:
            if m.split(":")[0] == p or m.startswith(p):
                return m
    return models[0]


def _fallback(user_text: str, context: str) -> str:
    q = (user_text or "").strip()
    if not q:
        return (
            "Ollama is not running. Start it with `ollama serve` and pull a model "
            "(llama3.1 recommended). Meanwhile use Practice mode — the local item bank "
            "and readiness tracker work offline."
        )
    excerpt = context[:2500].strip()
    return (
        "Local LLM is offline, so this is a knowledge-pack excerpt rather than a generated answer.\n\n"
        f"You asked: {q}\n\n{excerpt}\n\n"
        "Start Ollama for full coaching. Practice and readiness still work."
    )
