"""Daily & Weekly Rites — the DAILIES / WEEKLIES tabs on the Deeds screen
(Achievements spec: "achievements + dailies/weeklies live here as tabs;
this is the single source for daily/weekly quests").

Progress lives in one small table keyed by period (a UTC date for dailies,
an ISO week for weeklies). Game actions call `bump(kind)` — each kind may
advance several rites at once (a summon counts toward both the daily
offering and the weekly rich calling). Hooks are fail-safe: a broken rite
must never break the action that fed it.
"""
import json
from datetime import datetime, timezone, timedelta

from database import db

# kind → the actions the game reports:
#   floor_clear · summon · training_drill · craft · gate_run · muster
DAILIES = {
    "muster": {
        "name": "MORNING MUSTER", "desc": "Log in and survey the base.",
        "kind": "muster", "target": 1, "reward": {"gold": 400},
    },
    "ascent": {
        "name": "DUTIFUL ASCENT", "desc": "Clear any three Tower floors today.",
        "kind": "floor_clear", "target": 3, "reward": {"gold": 600},
    },
    "offering": {
        "name": "THE OFFERING", "desc": "Perform a single summon at either Gate.",
        "kind": "summon", "target": 1, "reward": {"gems": 15},
    },
    "labour": {
        "name": "HONEST LABOUR", "desc": "Complete three training drills.",
        "kind": "training_drill", "target": 3, "reward": {"gold": 400},
    },
}

WEEKLIES = {
    "deep_climb": {
        "name": "THE LONG CLIMB", "desc": "Clear twenty Tower floors this week.",
        "kind": "floor_clear", "target": 20, "reward": {"gems": 60},
    },
    "rich_calling": {
        "name": "A RICH CALLING", "desc": "Perform ten summons this week.",
        "kind": "summon", "target": 10, "reward": {"gems": 40},
    },
    "forgework": {
        "name": "FORGEWORK", "desc": "Craft three pieces at the Forge.",
        "kind": "craft", "target": 3, "reward": {"gold": 2500},
    },
    "gatekeeper": {
        "name": "GATEKEEPER", "desc": "Open five Daily Gates this week.",
        "kind": "gate_run", "target": 5, "reward": {"gold": 2000},
    },
}


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _week() -> str:
    iso = datetime.now(timezone.utc).isocalendar()
    return f"{iso[0]}-W{iso[1]:02d}"


def _seconds_to_utc_midnight() -> int:
    now = datetime.now(timezone.utc)
    return int(86400 - (now.hour * 3600 + now.minute * 60 + now.second))


def _seconds_to_next_monday() -> int:
    now = datetime.now(timezone.utc)
    days = (7 - now.weekday()) % 7 or 7
    nxt = (now + timedelta(days=days)).replace(hour=0, minute=0, second=0, microsecond=0)
    return int((nxt - now).total_seconds())


def _ensure_table(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS quest_progress (
            period_key TEXT NOT NULL,
            quest_id TEXT NOT NULL,
            count INTEGER DEFAULT 0,
            claimed INTEGER DEFAULT 0,
            PRIMARY KEY (period_key, quest_id)
        )
    """)


def bump(kind: str, n: int = 1):
    """Advance every rite fed by this action. Never raises — a rite must
    not break the action that reported it."""
    try:
        with db() as conn:
            _ensure_table(conn)
            for period, defs in ((_today(), DAILIES), (_week(), WEEKLIES)):
                for qid, q in defs.items():
                    if q["kind"] != kind:
                        continue
                    conn.execute("""
                        INSERT INTO quest_progress (period_key, quest_id, count) VALUES (?,?,?)
                        ON CONFLICT(period_key, quest_id) DO UPDATE SET count = count + ?
                    """, (period, qid, n, n))
    except Exception:
        pass


def _rows(conn, period: str, defs: dict) -> list:
    prog = {r["quest_id"]: r for r in conn.execute(
        "SELECT quest_id, count, claimed FROM quest_progress WHERE period_key = ?", (period,)).fetchall()}
    out = []
    for qid, q in defs.items():
        row = prog.get(qid)
        count = min(q["target"], row["count"] if row else 0)
        out.append({
            "id": qid, "name": q["name"], "desc": q["desc"],
            "progress": count, "target": q["target"], "reward": q["reward"],
            "complete": count >= q["target"],
            "claimed": bool(row and row["claimed"]),
        })
    return out


def rites() -> dict:
    with db() as conn:
        _ensure_table(conn)
    # Surveying the rites IS the morning muster.
    bump("muster")
    with db() as conn:
        return {
            "dailies": _rows(conn, _today(), DAILIES),
            "weeklies": _rows(conn, _week(), WEEKLIES),
            "daily_resets_in_seconds": _seconds_to_utc_midnight(),
            "weekly_resets_in_seconds": _seconds_to_next_monday(),
        }


def claim(quest_id: str) -> dict:
    if quest_id in DAILIES:
        period, q = _today(), DAILIES[quest_id]
    elif quest_id in WEEKLIES:
        period, q = _week(), WEEKLIES[quest_id]
    else:
        raise ValueError("No such rite is posted.")
    with db() as conn:
        _ensure_table(conn)
        row = conn.execute(
            "SELECT count, claimed FROM quest_progress WHERE period_key = ? AND quest_id = ?",
            (period, quest_id)).fetchone()
        if not row or row["count"] < q["target"]:
            raise ValueError("The rite is not yet fulfilled.")
        if row["claimed"]:
            raise ValueError("Already claimed — the keepers keep clean ledgers.")
        conn.execute(
            "UPDATE quest_progress SET claimed = 1 WHERE period_key = ? AND quest_id = ?",
            (period, quest_id))
        reward = q["reward"]
        if reward.get("gold"):
            conn.execute("UPDATE base SET gold = gold + ? WHERE id = 1", (reward["gold"],))
        if reward.get("gems"):
            conn.execute("UPDATE base SET gems = gems + ? WHERE id = 1", (reward["gems"],))
    return {"ok": True, "reward": reward, "message": f"{q['name']} — claimed."}
