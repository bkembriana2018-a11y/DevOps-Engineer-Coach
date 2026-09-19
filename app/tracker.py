from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .config import (
    COMPETITIVE,
    COMPOSITES,
    DATA_DIR,
    DEFAULT_TRACK,
    FLOORS,
    PROGRESS_PATH,
    SUBTESTS,
    TRACK_FOCUS,
    TRACK_SUBTEST_PRIORITY,
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def default_progress() -> dict[str, Any]:
    return {
        "target_track": DEFAULT_TRACK,
        "created": _now(),
        "events": [],
        "subtests": {
            key: {
                "attempts": 0,
                "correct": 0,
                "seen_ids": [],
                "miss_topics": {},
                "last_percent": None,
                "last_at": None,
            }
            for key in SUBTESTS
        },
    }


def load() -> dict[str, Any]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not PROGRESS_PATH.exists():
        data = default_progress()
        save(data)
        return data
    data = json.loads(PROGRESS_PATH.read_text(encoding="utf-8"))
    base = default_progress()
    for k, v in base.items():
        if k not in data:
            data[k] = v
    for key in SUBTESTS:
        if key not in data["subtests"]:
            data["subtests"][key] = base["subtests"][key]
    return data


def save(data: dict[str, Any]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    PROGRESS_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def set_track(track: str) -> dict[str, Any]:
    data = load()
    if track not in TRACK_FOCUS:
        track = DEFAULT_TRACK
    data["target_track"] = track
    save(data)
    return readiness(data)


def record_quiz(graded: dict[str, Any], subtest: str, elapsed_sec: float | None) -> dict[str, Any]:
    data = load()
    data["events"].append(
        {
            "at": _now(),
            "subtest": subtest,
            "correct": graded["correct"],
            "total": graded["total"],
            "percent": graded["percent"],
            "elapsed_sec": elapsed_sec,
        }
    )
    data["events"] = data["events"][-200:]
    by_sub: dict[str, list] = {}
    for r in graded["results"]:
        by_sub.setdefault(r["subtest"], []).append(r)
    for st, rows in by_sub.items():
        if st not in SUBTESTS:
            continue
        slot = data["subtests"].setdefault(
            st,
            {
                "attempts": 0,
                "correct": 0,
                "seen_ids": [],
                "miss_topics": {},
                "last_percent": None,
                "last_at": None,
            },
        )
        slot["attempts"] += len(rows)
        slot["correct"] += sum(1 for r in rows if r["correct"])
        for r in rows:
            if r["id"] not in slot["seen_ids"]:
                slot["seen_ids"].append(r["id"])
            if not r["correct"]:
                topic = r.get("topic") or "general"
                slot["miss_topics"][topic] = slot["miss_topics"].get(topic, 0) + 1
        slot["last_percent"] = round(100 * sum(1 for r in rows if r["correct"]) / len(rows), 1)
        slot["last_at"] = _now()
        slot["seen_ids"] = slot["seen_ids"][-200:]
    save(data)
    return readiness(data)


def _band(percent: float | None, attempts: int) -> str:
    if attempts < 5 or percent is None:
        return "untested"
    if percent >= 85:
        return "ready"
    if percent >= 70:
        return "borderline"
    return "weak"


def readiness(data: dict[str, Any] | None = None) -> dict[str, Any]:
    data = data or load()
    sub = {}
    for key, meta in SUBTESTS.items():
        slot = data["subtests"][key]
        attempts = slot["attempts"]
        pct = round(100 * slot["correct"] / attempts, 1) if attempts else None
        misses = sorted(slot.get("miss_topics", {}).items(), key=lambda kv: -kv[1])[:5]
        sub[key] = {
            **meta,
            "attempts": attempts,
            "correct": slot["correct"],
            "percent": pct,
            "last_percent": slot.get("last_percent"),
            "band": _band(pct, attempts),
            "top_miss_topics": [m[0] for m in misses],
        }

    composites = {}
    for name, parts in COMPOSITES.items():
        parts_data = [sub[p] for p in parts]
        tested = [p for p in parts_data if p["attempts"] >= 5]
        if not tested:
            band = "untested"
            pct = None
        else:
            pct = round(sum(p["percent"] for p in tested) / len(tested), 1)
            if len(tested) < len(parts):
                raw_band = _band(pct, 5)
                band = "borderline" if raw_band == "ready" else raw_band
                if any(p["band"] == "weak" for p in tested):
                    band = "weak"
            else:
                band = _band(pct, 5)
                if any(p["band"] == "weak" for p in parts_data):
                    band = "weak"
        composites[name] = {
            "parts": parts,
            "percent": pct,
            "band": band,
            "floor_percentile": FLOORS.get(name),
            "competitive_percentile": COMPETITIVE.get(name),
            "coverage": f"{len(tested)}/{len(parts)} topics with >=5 items",
        }

    track = data.get("target_track", DEFAULT_TRACK)
    focus = TRACK_FOCUS.get(track, TRACK_FOCUS[DEFAULT_TRACK])
    actions = []
    focus_subs = list(TRACK_SUBTEST_PRIORITY.get(track, []))
    for comp in focus:
        for part in COMPOSITES.get(comp, []):
            if part not in focus_subs:
                focus_subs.append(part)
    seen = set()
    ordered = []
    for k in focus_subs:
        if k not in seen and k in sub:
            seen.add(k)
            ordered.append(k)
    for k in ordered:
        band = sub[k]["band"]
        if band in ("weak", "untested", "borderline"):
            why = {
                "untested": "No baseline yet — pick this up in Practice.",
                "weak": "Accuracy below 70%. Revisit the Learn pack for this topic.",
                "borderline": "Not locked in yet. Push this to 85%+ practice accuracy.",
            }[band]
            miss = sub[k]["top_miss_topics"]
            extra = f" Miss tags: {', '.join(miss)}." if miss else ""
            actions.append(f"{sub[k]['label']}: {why}{extra}")
        if len(actions) >= 5:
            break
    if not actions:
        actions.append(
            "Every topic on your track is green. Keep a weekly mixed drill going and rotate in the topics outside your track so you don't go stale."
        )

    primary = list(dict.fromkeys(focus + ["cloud_native"]))
    return {
        "target_track": track,
        "primary_composites": primary,
        "subtests": sub,
        "composites": composites,
        "next_actions": actions,
        "disclaimer": (
            "Practice percent is not an official certification score. AWS and Terraform "
            "exams use scaled scoring and CKA is graded on hands-on performance tasks, not "
            "multiple choice — this app only drills and checks conceptual knowledge. Verify "
            "current exam blueprints with the certifying body before you register."
        ),
        "event_count": len(data.get("events", [])),
    }
