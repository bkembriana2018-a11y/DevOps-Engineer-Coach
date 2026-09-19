from __future__ import annotations

import json
import random
from typing import Any

from .config import QUESTIONS_PATH, SUBTESTS


def load_items() -> list[dict[str, Any]]:
    """Load official bank.json if present, else merge bank_*.json shards."""
    if QUESTIONS_PATH.exists():
        data = json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))
        return data["items"]
    items: list[dict[str, Any]] = []
    for path in sorted(QUESTIONS_PATH.parent.glob("bank_*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            items.extend(payload)
        else:
            items.extend(payload.get("items") or [])
    if not items:
        raise FileNotFoundError(f"No question bank at {QUESTIONS_PATH} or bank_*.json shards")
    return items


ITEMS = load_items()


def by_subtest(subtest: str) -> list[dict[str, Any]]:
    if subtest == "mixed":
        return list(ITEMS)
    return [i for i in ITEMS if i["subtest"] == subtest]


def sample_quiz(
    subtest: str,
    n: int = 8,
    difficulty: str | None = None,
    exclude_ids: set[str] | None = None,
) -> dict[str, Any]:
    pool = by_subtest(subtest)
    if exclude_ids:
        reduced = [i for i in pool if i["id"] not in exclude_ids]
        if reduced:
            pool = reduced
    if not pool:
        pool = by_subtest(subtest) or ITEMS

    n = max(1, n)
    note = None
    if difficulty and difficulty != "any":
        exact = [i for i in pool if i.get("difficulty") == difficulty]
        if len(exact) < n:
            others = [i for i in pool if i.get("difficulty") != difficulty]
            random.shuffle(others)
            fill = others[: n - len(exact)]
            got = len(exact) + len(fill)
            if exact and fill:
                note = (
                    f"Only {len(exact)} '{difficulty}' item(s) in the bank for this topic — "
                    f"filled the remaining {len(fill)} from other difficulties to reach {got}."
                )
            elif fill:
                note = f"No '{difficulty}' items for this topic yet — showing mixed difficulty instead."
            pool = exact + fill
        else:
            pool = exact

    n = max(1, min(n, len(pool)))
    picked = random.sample(pool, n)
    meta = SUBTESTS.get(subtest, {"pace": 60, "minutes": 0, "items": n})
    timed = int(meta["pace"] * n)
    return {
        "quiz_id": f"{subtest}-{random.randint(1000, 9999)}",
        "subtest": subtest,
        "timed_seconds": timed,
        "target_pace_sec_per_item": meta["pace"],
        "note": note,
        "items": [
            {
                "id": i["id"],
                "topic": i.get("topic"),
                "stem": i["stem"],
                "choices": i["choices"],
                "answer": i["answer"],
                "explanation": i["explanation"],
                "difficulty": i.get("difficulty"),
                "visual": i.get("visual"),
            }
            for i in picked
        ],
    }


def grade(responses: list[dict[str, Any]], extra_items: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """responses: [{id, selected, time_sec}]"""
    index = {i["id"]: i for i in ITEMS}
    for item in extra_items or []:
        # Only fills in items the static bank doesn't already have (e.g. LLM-generated
        # extras) -- must never clobber a real bank item with its trimmed client copy,
        # which is missing fields like "subtest" that readiness tracking depends on.
        if item.get("id") and item["id"] not in index:
            index[item["id"]] = item
    results = []
    correct = 0
    for r in responses:
        item = index.get(r["id"])
        if not item:
            continue
        ok = str(r.get("selected", "")).upper()[:1] == str(item["answer"]).upper()[:1]
        if ok:
            correct += 1
        results.append(
            {
                "id": item["id"],
                "subtest": item.get("subtest") or "mixed",
                "topic": item.get("topic"),
                "selected": r.get("selected"),
                "answer": item["answer"],
                "correct": ok,
                "explanation": item["explanation"],
                "time_sec": r.get("time_sec"),
                "stem": item["stem"],
            }
        )
    total = len(results)
    return {
        "correct": correct,
        "total": total,
        "percent": round(100 * correct / total, 1) if total else 0,
        "results": results,
    }
