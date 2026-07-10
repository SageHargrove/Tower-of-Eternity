"""
Server-wide weekly tournaments.

Weekly cadence (UTC weekday):
  Mon-Wed  — Registration Phase: players submit a specific team per bracket.
  Thu-Sat  — Battle Phase: the server runs the bracket autonomously as
             auto-battler rounds (Swiss for the head-to-head formats, an
             elimination free-for-all for Battle Royale). Resolution is
             lazy — the first standings/status request after Wednesday
             runs the whole bracket; every later request just reads it.
  Sunday   — Payouts: the top of the leaderboard receives high-tier Summon
             Tickets and an exclusive Cosmetic via the reward inbox
             (arena_season_rewards — the same inbox the client already
             drains into the in-game Mailbox).

Formats (team sizes in models.TOURNAMENT_FORMATS): 1v1 Duels, 2v2 Pairs,
4v4 Warbands, 5-hero Battle Royale. Fights resolve through the same real
combat sim arena duels use (combat.resolve_arena_fight).
"""
import json
import math
import random
import time
from datetime import datetime, timezone

from fastapi import HTTPException

from combat import resolve_arena_fight
from models import TOURNAMENT_FORMATS

MAX_SWISS_ROUNDS = 7

# Tournament Points by final placement band.
PLACEMENT_POINTS = [(1, 100), (2, 70), (3, 50)]   # exact placements
TOP_HALF_POINTS = 25
PARTICIPATION_POINTS = 10

# Sunday payout bands: top 10% (min 1) are "champions", top 25% run prizes.
CHAMPION_TICKETS = 5
RUNNER_UP_TICKETS = 3
CHAMPION_COSMETICS = {
    "duel": "cosmetic:duelist_crown",
    "pairs": "cosmetic:twin_banners",
    "warband": "cosmetic:warband_standard",
    "royale": "cosmetic:last_one_standing_cape",
}


def week_key(dt: datetime | None = None) -> str:
    iso = (dt or datetime.now(timezone.utc)).isocalendar()
    return f"{iso[0]}-W{iso[1]:02d}"


def current_phase(dt: datetime | None = None) -> str:
    wd = (dt or datetime.now(timezone.utc)).weekday()
    if wd <= 2:
        return "registration"
    if wd <= 5:
        return "battles"
    return "payouts"


def _state(conn, week: str, fmt: str):
    return conn.execute(
        "SELECT * FROM tournament_state WHERE week_key = ? AND format = ?", (week, fmt)
    ).fetchone()


def _entries(conn, week: str, fmt: str):
    return [dict(r) for r in conn.execute(
        "SELECT * FROM tournament_entries WHERE week_key = ? AND format = ? ORDER BY id ASC",
        (week, fmt),
    ).fetchall()]


def register(conn, username: str, fmt: str, team: list[dict]) -> dict:
    week = week_key()
    if current_phase() != "registration":
        raise HTTPException(status_code=400, detail="Registration is Monday-Wednesday — this week's brackets are locked")
    existing = conn.execute(
        "SELECT id FROM tournament_entries WHERE week_key = ? AND format = ? AND username = ?",
        (week, fmt, username),
    ).fetchone()
    if existing:
        conn.execute(
            "UPDATE tournament_entries SET team_json = ?, registered_at = ? WHERE id = ?",
            (json.dumps(team), time.time(), existing["id"]),
        )
        return {"status": "registration updated", "week": week, "format": fmt}
    conn.execute(
        "INSERT INTO tournament_entries (week_key, format, username, team_json, registered_at) VALUES (?, ?, ?, ?, ?)",
        (week, fmt, username, json.dumps(team), time.time()),
    )
    return {"status": "registered", "week": week, "format": fmt}


def _record_match(conn, week: str, fmt: str, rnd: int, p1: str, p2: str | None, winner: str | None, log: list):
    conn.execute(
        """INSERT INTO tournament_matches (week_key, format, round, player1, player2, winner, log_json, timestamp)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (week, fmt, rnd, p1, p2, winner, json.dumps(log[-40:]), time.time()),
    )


def _fight(a: dict, b: dict) -> str:
    """Returns the winning username. a/b are entry dicts with parsed teams."""
    result = resolve_arena_fight(a["_team"], b["_team"])
    return a["username"] if result["winner"] == "heroes" else b["username"]


def _resolve_swiss(conn, week: str, fmt: str, entries: list[dict]):
    """Swiss-system: everyone plays every round, paired against the closest
    record; final ranking by match wins."""
    n = len(entries)
    rounds = min(MAX_SWISS_ROUNDS, max(3, math.ceil(math.log2(max(2, n)))))
    played = {e["username"]: set() for e in entries}
    for rnd in range(1, rounds + 1):
        pool = sorted(entries, key=lambda e: (-e["wins"], random.random()))
        paired = set()
        for e in pool:
            if e["username"] in paired:
                continue
            opp = next((o for o in pool
                        if o["username"] not in paired and o["username"] != e["username"]
                        and o["username"] not in played[e["username"]]), None)
            if opp is None:  # rematch unavoidable (tiny bracket) or bye
                opp = next((o for o in pool if o["username"] not in paired and o["username"] != e["username"]), None)
            if opp is None:
                # Odd player out gets a bye — a free win, no match record.
                e["wins"] += 1
                paired.add(e["username"])
                continue
            paired.add(e["username"])
            paired.add(opp["username"])
            played[e["username"]].add(opp["username"])
            played[opp["username"]].add(e["username"])
            result = resolve_arena_fight(e["_team"], opp["_team"])
            winner = e if result["winner"] == "heroes" else opp
            loser = opp if winner is e else e
            winner["wins"] += 1
            loser["losses"] += 1
            _record_match(conn, week, fmt, rnd, e["username"], opp["username"],
                          winner["username"], result.get("log", []))
    entries.sort(key=lambda e: (-e["wins"], e["losses"], random.random()))


def _resolve_royale(conn, week: str, fmt: str, entries: list[dict]):
    """Battle Royale: multi-team free-for-all resolved as elimination melee
    rounds — survivors are randomly thrown at each other, losers are out,
    last team standing wins. Placement = elimination order, reversed."""
    remaining = entries[:]
    random.shuffle(remaining)
    eliminated: list[dict] = []
    rnd = 0
    while len(remaining) > 1:
        rnd += 1
        random.shuffle(remaining)
        next_round = []
        while remaining:
            a = remaining.pop()
            if not remaining:
                next_round.append(a)  # odd one out survives the round
                break
            b = remaining.pop()
            result = resolve_arena_fight(a["_team"], b["_team"])
            winner, loser = (a, b) if result["winner"] == "heroes" else (b, a)
            winner["wins"] += 1
            loser["losses"] += 1
            _record_match(conn, week, fmt, rnd, a["username"], b["username"],
                          winner["username"], result.get("log", []))
            next_round.append(winner)
            eliminated.append(loser)
        remaining = next_round
    # Final order: champion first, then latest-eliminated to earliest.
    entries[:] = remaining + eliminated[::-1]


def resolve_bracket(conn, week: str, fmt: str) -> None:
    """Runs the whole bracket once (idempotent via tournament_state)."""
    state = _state(conn, week, fmt)
    if state and state["resolved"]:
        return
    entries = _entries(conn, week, fmt)
    for e in entries:
        e["_team"] = json.loads(e["team_json"])
        e["wins"] = 0
        e["losses"] = 0

    if len(entries) >= 2:
        if fmt == "royale":
            _resolve_royale(conn, week, fmt, entries)
        else:
            _resolve_swiss(conn, week, fmt, entries)

    n = len(entries)
    exact = dict(PLACEMENT_POINTS)
    for i, e in enumerate(entries):
        placement = i + 1
        points = exact.get(placement)
        if points is None:
            points = TOP_HALF_POINTS if placement <= max(3, n // 2) else PARTICIPATION_POINTS
        conn.execute(
            "UPDATE tournament_entries SET points = ?, wins = ?, losses = ?, placement = ? WHERE id = ?",
            (points, e["wins"], e["losses"], placement, e["id"]),
        )
    conn.execute(
        """INSERT INTO tournament_state (week_key, format, resolved, resolved_at) VALUES (?, ?, 1, ?)
           ON CONFLICT(week_key, format) DO UPDATE SET resolved = 1, resolved_at = excluded.resolved_at""",
        (week, fmt, time.time()),
    )


def pay_out(conn, week: str, fmt: str) -> None:
    """Sunday payouts (idempotent): the top of the leaderboard gets high-tier
    Summon Tickets + an exclusive Cosmetic via the reward inbox, which the
    client drains into the in-game Mailbox."""
    state = _state(conn, week, fmt)
    if not state or not state["resolved"] or state["paid_out"]:
        return
    entries = [e for e in _entries(conn, week, fmt) if e["placement"]]
    entries.sort(key=lambda e: e["placement"])
    n = len(entries)
    if n:
        champions = max(1, n // 10)      # top 10%
        runners = max(champions, n // 4)  # through top 25%
        now = time.time()
        for e in entries[:runners]:
            is_champion = e["placement"] <= champions
            tickets = CHAMPION_TICKETS if is_champion else RUNNER_UP_TICKETS
            conn.execute(
                "INSERT INTO arena_season_rewards (username, season_end_date, reward_type, amount) VALUES (?, ?, ?, ?)",
                (e["username"], now, "summon_ticket", tickets),
            )
            if is_champion:
                conn.execute(
                    "INSERT INTO arena_season_rewards (username, season_end_date, reward_type, amount) VALUES (?, ?, ?, ?)",
                    (e["username"], now, CHAMPION_COSMETICS.get(fmt, "cosmetic:champion_emblem"), 1),
                )
    conn.execute(
        "UPDATE tournament_state SET paid_out = 1 WHERE week_key = ? AND format = ?",
        (week, fmt),
    )


def _maybe_advance(conn, week: str, fmt: str) -> None:
    """Lazy scheduler: any read after the Registration Phase resolves the
    bracket; any read in the payout window (or of a past week) also pays."""
    current = week_key()
    phase = current_phase()
    past_week = week < current
    if past_week or phase != "registration":
        resolve_bracket(conn, week, fmt)
    if past_week or phase == "payouts":
        pay_out(conn, week, fmt)


def get_standings(conn, fmt: str, week: str | None = None) -> dict:
    week = week or week_key()
    _maybe_advance(conn, week, fmt)
    state = _state(conn, week, fmt)
    entries = _entries(conn, week, fmt)
    resolved = bool(state and state["resolved"])
    if resolved:
        entries.sort(key=lambda e: (e["placement"] is None, e["placement"] or 0))
    matches = conn.execute(
        "SELECT round, player1, player2, winner FROM tournament_matches WHERE week_key = ? AND format = ? ORDER BY id ASC",
        (week, fmt),
    ).fetchall()
    return {
        "week": week,
        "format": fmt,
        "phase": current_phase() if week == week_key() else "complete",
        "resolved": resolved,
        "paid_out": bool(state and state["paid_out"]),
        "standings": [
            {"username": e["username"], "placement": e["placement"], "points": e["points"],
             "wins": e["wins"], "losses": e["losses"]}
            for e in entries
        ],
        "matches": [dict(m) for m in matches],
    }


def get_status(conn, username: str) -> dict:
    week = week_key()
    phase = current_phase()
    formats = {}
    for fmt, size in TOURNAMENT_FORMATS.items():
        _maybe_advance(conn, week, fmt)
        state = _state(conn, week, fmt)
        entries = _entries(conn, week, fmt)
        mine = next((e for e in entries if e["username"] == username), None)
        formats[fmt] = {
            "team_size": size,
            "entrants": len(entries),
            "registered": mine is not None,
            "my_placement": mine["placement"] if mine else None,
            "my_points": mine["points"] if mine else None,
            "resolved": bool(state and state["resolved"]),
        }
    return {"week": week, "phase": phase, "formats": formats}
