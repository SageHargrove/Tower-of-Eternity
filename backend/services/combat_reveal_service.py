"""Deferred death reveal for tower combat.

A fight is resolved instantly server-side (see routers/tower.py's
_resolve_real_combat), but the player watches it play out as a timed
animation in CombatArena. Committing a fallen hero's death to the DB
immediately meant they showed up dead on the Heroes/Memorial tabs the
*instant* you entered a floor — long before the animation reached the turn
they actually died on. A hard spoiler, and the reason a "background" fight
felt like it had already ended the moment you looked away.

So a combat death is DEFERRED: instead of killing the hero at resolve time,
we record a `pending_combat` row and only apply the kill (+ its legacy and
portrait cleanup) once the fight's real-time timeline has elapsed:

  • the client calls POST /tower/floor/finalize the moment its animation
    finishes — works at any playback speed the player chose, and fires the
    death right as they'd see it; OR
  • any hero-visible read (the Heroes tab, a hero detail, the Memorial)
    lazily reveals rows whose reveal_at has passed — the safety net for a
    player who closed the app mid-fight and never triggered finalize.

Everything else about a fight (rewards, XP, survivor heal, the survivors'
witness-death trauma) still commits instantly at resolve — only the fallen's
own death is held back, because that's the only lasting, roster-visible
consequence that spoils.
"""
import json
import time

from database import db

# Per-turn animation delay in CombatArena (ms). The fallback reveal_at is
# sized off this at 1x playback — the slowest the fight can visibly run — so
# a lazy reveal never fires *earlier* than the player could have watched the
# death. Watching faster (2x/4x) just means the client's explicit finalize
# lands first, which is exactly what we want.
TURN_ANIM_MS = 800
# A little slack over the raw turn time for the post-fight completion beat
# (CombatArena waits ~1.5s after the last turn before onComplete).
REVEAL_BUFFER_S = 2.5


def turns_in_result(combat_result: dict) -> int:
    """Longest leg of a fight, in turns — multi-team floors play N arenas in
    parallel, so the animation isn't over until the longest one is."""
    if not combat_result:
        return 0
    legs = combat_result.get("team_results") or [combat_result]
    return max((len(leg.get("turns", []) or []) for leg in legs if leg), default=0)


def register_pending_deaths(conn, floor_number: int, dead_ids: list[int], combat_result: dict):
    """Record a fight's fallen for deferred reveal. Returns the new row id
    (the client echoes it back to /floor/finalize), or None when nobody
    died (nothing to defer)."""
    dead_ids = [int(d) for d in dead_ids]
    if not dead_ids:
        return None
    n_turns = turns_in_result(combat_result)
    reveal_at = time.time() + (n_turns * TURN_ANIM_MS / 1000.0) + REVEAL_BUFFER_S
    cur = conn.execute(
        "INSERT INTO pending_combat (floor_number, dead_ids, reveal_at, created_at) VALUES (?, ?, ?, ?)",
        (floor_number, json.dumps(dead_ids), reveal_at, time.time()),
    )
    return cur.lastrowid


def _kill_fallen(conn, dead_id: int, floor_number: int):
    """Apply one fallen hero's death: write their auto 'Memory of' legacy row
    if they qualify, then mark them dead. Returns the pre-death hero dict so
    the caller can run portrait/create_legacy OUTSIDE this connection (both
    open their own — see legacy_service.create_legacy). This is the exact
    logic that used to run inline in _resolve_real_combat's death loop."""
    hr = conn.execute("SELECT * FROM heroes WHERE id = ?", (dead_id,)).fetchone()
    if not hr:
        return None
    hr_dict = dict(hr)
    # Already dead (a race, or applied twice) — don't double-kill / double-legacy.
    if not hr_dict.get("is_alive", 1):
        return None
    if hr_dict.get("unique_floors_cleared", 0) >= 10:
        clears = hr_dict["unique_floors_cleared"]
        buff_pct = min(25, 5 + (clears - 10))
        buffs = json.dumps({"primary_bonus": {"stat": "str_pct", "label": "ATK", "value": buff_pct * 0.01, "desc": f"+{buff_pct}% ATK to all"}})
        conn.execute(
            "INSERT INTO legacies (hero_id, hero_name, hero_star, title, flavor_text, bonus_json, score, is_sacrifice) VALUES (?, ?, ?, ?, ?, ?, 1000, 1)",
            (hr_dict["id"], hr_dict["name"], hr_dict.get("birth_star", 1), f"Memory of {hr_dict['name']}", f"Fell on Floor {floor_number} after {clears} unique clears.", buffs)
        )
    conn.execute("UPDATE heroes SET is_alive = 0, is_on_team = 0 WHERE id = ?", (dead_id,))
    return hr_dict


def _finalize_fallen(fallen: list[dict]):
    """Portrait cleanup + create_legacy for a batch of fallen — MUST run with
    no db() connection held open (both of these open their own)."""
    for hero_dict in fallen:
        try:
            from services.portrait_cache import handle_fallen_portrait
            hero_dict["portrait_path"] = handle_fallen_portrait(hero_dict["id"], hero_dict.get("portrait_path"), False)
        except Exception as e:
            print(f"Portrait cleanup error: {e}")
        try:
            from services.legacy_service import create_legacy
            create_legacy(hero_dict, is_sacrifice=False)
        except Exception as e:
            print(f"Legacy creation error: {e}")


def apply_pending(pending_ids: list[int] | None = None, only_due: bool = False) -> list[dict]:
    """Reveal deferred deaths. Selection:
      • pending_ids given → force-apply exactly those rows (the client's
        finalize, once its animation ends, regardless of reveal_at);
      • only_due=True     → apply every row whose reveal_at has passed (the
        lazy read-side safety net);
      • neither           → apply ALL pending rows (force, e.g. when a new
        fight is about to start — the previous one is conceptually over).
    Idempotent: rows are claimed under a write lock and deleted as applied,
    so concurrent callers can't double-kill. Returns the fallen hero dicts."""
    fallen: list[dict] = []
    with db() as conn:
        # Take the write lock up front so two overlapping callers (e.g. a
        # background poll racing the client's finalize) serialize instead of
        # both processing the same row and inserting duplicate legacies.
        try:
            conn.execute("BEGIN IMMEDIATE")
        except Exception:
            pass

        if pending_ids is not None:
            if not pending_ids:
                return []
            placeholders = ",".join("?" * len(pending_ids))
            rows = conn.execute(
                f"SELECT * FROM pending_combat WHERE id IN ({placeholders})", tuple(pending_ids)
            ).fetchall()
        elif only_due:
            rows = conn.execute(
                "SELECT * FROM pending_combat WHERE reveal_at <= ?", (time.time(),)
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM pending_combat").fetchall()

        for row in rows:
            for dead_id in json.loads(row["dead_ids"]):
                hd = _kill_fallen(conn, dead_id, row["floor_number"])
                if hd:
                    fallen.append(hd)
            conn.execute("DELETE FROM pending_combat WHERE id = ?", (row["id"],))

    # Outside the connection — these open their own.
    _finalize_fallen(fallen)
    return fallen


def reveal_due_combats():
    """Cheap lazy check for the hero-read endpoints: apply any fight whose
    real-time timeline has elapsed. No-op (one SELECT) when nothing is due."""
    return apply_pending(only_due=True)
