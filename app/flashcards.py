from __future__ import annotations

import json
from typing import Any

from .config import APP_DIR

FLASHCARDS_DIR = APP_DIR / "questions"

DECK_LABELS = {
    "aws": "AWS Services",
    "terraform": "Terraform & HCL",
    "kubernetes": "Kubernetes",
}


def load_cards() -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for path in sorted(FLASHCARDS_DIR.glob("flashcards_*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            cards.extend(payload)
    return cards


CARDS = load_cards()


def decks() -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for c in CARDS:
        counts[c["deck"]] = counts.get(c["deck"], 0) + 1
    return [
        {"id": deck, "label": DECK_LABELS.get(deck, deck.replace("_", " ").title()), "count": count}
        for deck, count in counts.items()
    ]


def get_cards(deck: str | None = None) -> list[dict[str, Any]]:
    if not deck or deck == "all":
        return list(CARDS)
    return [c for c in CARDS if c["deck"] == deck]
