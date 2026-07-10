"""THE HERALD — in-world news feed.

Editorial content (featured edition + notices) lives in data/herald_news.json
so it can be edited without touching code. On top of that the endpoint
aggregates "tidings" from live game state: the latest legacy, the tower
record, the newest high-star recruit, and the daily-gate reseal timer.
"""
from fastapi import APIRouter
from database import db
from datetime import datetime, timezone
import json
import os

router = APIRouter()

NEWS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "herald_news.json")

FALLBACK_NEWS = {
    "featured": {
        "title": "THE GATES OPEN",
        "edition": "VOL. I — THE FIRST ASCENT",
        "body": "The Tower stands open at last. Climb well.",
        "signoff": "— The Keepers",
    },
    "notices": [],
}


def _editorial():
    try:
        with open(NEWS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return FALLBACK_NEWS


def _seconds_to_utc_midnight():
    now = datetime.now(timezone.utc)
    return int(86400 - (now.hour * 3600 + now.minute * 60 + now.second))


def _tidings(conn):
    tidings = []

    row = conn.execute(
        "SELECT hero_name, hero_star, title FROM legacies ORDER BY id DESC LIMIT 1"
    ).fetchone()
    if row:
        tidings.append({
            "kind": "legacy",
            "title": "THE CLIMB REMEMBERS",
            "desc": f"{row['hero_name']}, {row['title'] or 'a soul of the Tower'}, has passed into legacy.",
        })

    row = conn.execute("SELECT MAX(highest_floor) AS record FROM runs").fetchone()
    if row and (row["record"] or 0) > 0:
        tidings.append({
            "kind": "record",
            "title": "RECORD ASCENT",
            "desc": f"Climbers have reached floor {row['record']}. The Tower waits above.",
        })

    row = conn.execute(
        "SELECT name, title, birth_star FROM heroes WHERE birth_star >= 5 AND is_alive = 1 "
        "ORDER BY id DESC LIMIT 1"
    ).fetchone()
    if row:
        star = "★" * row["birth_star"]
        tidings.append({
            "kind": "recruit",
            "title": "A GREAT SOUL ANSWERS",
            "desc": f"{row['name']}{', ' + row['title'] if row['title'] else ''} ({star}) has joined the roster.",
        })

    fallen = conn.execute(
        "SELECT COUNT(*) AS n FROM heroes WHERE is_alive = 0"
    ).fetchone()
    if fallen and fallen["n"] > 0:
        tidings.append({
            "kind": "fallen",
            "title": "NAMES CARVED IN STONE",
            "desc": f"{fallen['n']} hero{'es' if fallen['n'] != 1 else ''} now rest in the Memorial.",
        })

    tidings.append({
        "kind": "gates",
        "title": "THE DAILY GATES",
        "desc": "The gates at the Tower's foot reseal at dawn.",
        "resets_in_seconds": _seconds_to_utc_midnight(),
    })
    return tidings


@router.get("/")
def herald_feed():
    news = _editorial()
    with db() as conn:
        tidings = _tidings(conn)
    return {
        "featured": news.get("featured", FALLBACK_NEWS["featured"]),
        "notices": news.get("notices", []),
        "tidings": tidings,
    }
