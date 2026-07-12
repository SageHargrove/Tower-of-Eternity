"""Tavern + Shrine passive ticks — same own-clock pattern as
restaurant_service/infirmary_service (processed on base load).

Tavern: assigned hosts take the edge off the roster's STRESS over time
(Bards and Chefs are natural hosts). Complements the Restaurant (morale)
and Infirmary (trauma) so each recovery stat has a home.

Shrine: assigned clergy slowly deepen the roster's AFFINITY/loyalty —
the same 0-100 track gifts raise, which the raid/loyalty mechanics
consume. Deliberately slow: gifts are the active path, this is the
passive drip.
"""
from datetime import datetime


def _minutes_since(conn, column: str) -> int | None:
    """Shared tick-clock read; returns None when the clock was just
    initialized (nothing to process yet)."""
    try:
        conn.execute(f"ALTER TABLE base ADD COLUMN {column} TIMESTAMP")
    except Exception:
        pass
    base = conn.execute("SELECT * FROM base WHERE id = 1").fetchone()
    if not base:
        return None
    last_str = dict(base).get(column)
    if not last_str:
        conn.execute(f"UPDATE base SET {column} = CURRENT_TIMESTAMP WHERE id = 1")
        return None
    try:
        last = datetime.strptime(last_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        conn.execute(f"UPDATE base SET {column} = CURRENT_TIMESTAMP WHERE id = 1")
        return None
    return int((datetime.utcnow() - last).total_seconds() / 60)


def _assigned_classes(conn, fac_id: int) -> list[str]:
    rows = conn.execute("""
        SELECT h.hero_class FROM facility_assignments fa
        JOIN heroes h ON fa.hero_id = h.id
        WHERE fa.facility_id = ? AND h.is_alive = 1
    """, (fac_id,)).fetchall()
    return [r["hero_class"] for r in rows]


def process_tavern(conn):
    minutes = _minutes_since(conn, "last_tavern_tick")
    if minutes is None or minutes < 5:
        return
    tavern = conn.execute("SELECT id, level FROM facilities WHERE type = 'Tavern' AND base_id = 1").fetchone()
    if not tavern:
        conn.execute("UPDATE base SET last_tavern_tick = CURRENT_TIMESTAMP WHERE id = 1")
        return
    hosts = _assigned_classes(conn, tavern["id"])
    if not hosts:
        conn.execute("UPDATE base SET last_tavern_tick = CURRENT_TIMESTAMP WHERE id = 1")
        return

    ticks = minutes // 5
    level_mult = 1 + (tavern["level"] - 1) * 0.1
    relief_per_tick = sum(2 if c in ("Bard", "Chef", "Maestro", "Troubadour") else 1 for c in hosts) * level_mult
    total = int(relief_per_tick * ticks)
    if total > 0:
        conn.execute("UPDATE heroes SET stress = MAX(0, stress - ?) WHERE is_alive = 1", (total,))
    conn.execute("UPDATE base SET last_tavern_tick = CURRENT_TIMESTAMP WHERE id = 1")


# ─── Tavern interactive layer ───────────────────────────────────────
# Patrons are simply the most stressed living heroes; rounds are a gold
# sink that buys stress relief + a morale bump. One round per hero per
# day and one house round per day (state in base.tavern_json) — the
# warning about growing fond of the stool is enforced, not just flavor.

HOST_CLASSES = ("Bard", "Chef", "Maestro", "Troubadour")
HERO_ROUND_COST = 500
HOUSE_ROUND_COST = 2000

PATRON_DOINGS = [
    "Drowning the last floor", "Dicing with the regulars", "Listening to the bard",
    "Staring into the tankard", "Retelling an old wound", "Carving names in the table",
    "Losing at cards, gladly", "Watching the fire",
]


def _tavern_state(conn) -> dict:
    from datetime import datetime, timezone
    try:
        conn.execute("ALTER TABLE base ADD COLUMN tavern_json TEXT")
    except Exception:
        pass
    import json
    row = conn.execute("SELECT tavern_json FROM base WHERE id = 1").fetchone()
    try:
        state = json.loads(row["tavern_json"]) if row and row["tavern_json"] else {}
    except (json.JSONDecodeError, TypeError):
        state = {}
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if state.get("date") != today:
        state = {"date": today, "house_round": False, "hero_rounds": []}
    return state


def _save_tavern_state(conn, state: dict):
    import json
    conn.execute("UPDATE base SET tavern_json = ? WHERE id = 1", (json.dumps(state),))


def tavern_status(conn) -> dict:
    tavern = conn.execute("SELECT id, level FROM facilities WHERE type = 'Tavern' AND base_id = 1").fetchone()
    if not tavern:
        return {"built": False}
    hosts = conn.execute("""
        SELECT h.id, h.name, h.hero_class FROM facility_assignments fa
        JOIN heroes h ON fa.hero_id = h.id
        WHERE fa.facility_id = ? AND h.is_alive = 1
    """, (tavern["id"],)).fetchall()
    level_mult = 1 + (tavern["level"] - 1) * 0.1
    relief_per_hour = int(sum(2 if h["hero_class"] in HOST_CLASSES else 1 for h in hosts) * level_mult * 12)
    bard = next((h for h in hosts if h["hero_class"] in HOST_CLASSES), None)

    patrons = conn.execute("""
        SELECT id, name, stress, morale FROM heroes
        WHERE is_alive = 1 AND stress > 0
        ORDER BY stress DESC LIMIT 6
    """).fetchall()
    state = _tavern_state(conn)
    return {
        "built": True,
        "level": tavern["level"],
        "relief_per_hour": relief_per_hour,
        "hosts": [{"name": h["name"], "hero_class": h["hero_class"]} for h in hosts],
        "bard": ({"name": bard["name"], "hero_class": bard["hero_class"]} if bard else None),
        "patrons": [
            {
                "id": p["id"], "name": p["name"], "stress": p["stress"], "morale": p["morale"],
                "doing": PATRON_DOINGS[p["id"] % len(PATRON_DOINGS)],
                "round_bought": p["id"] in state.get("hero_rounds", []),
            }
            for p in patrons
        ],
        "hero_round_cost": HERO_ROUND_COST,
        "house_round_cost": HOUSE_ROUND_COST,
        "house_round_bought": state.get("house_round", False),
    }


def buy_round(conn, hero_id: int = None) -> dict:
    from fastapi import HTTPException
    tavern = conn.execute("SELECT id FROM facilities WHERE type = 'Tavern' AND base_id = 1").fetchone()
    if not tavern:
        raise HTTPException(status_code=400, detail="No tavern stands in this base.")
    state = _tavern_state(conn)
    base = conn.execute("SELECT gold FROM base WHERE id = 1").fetchone()

    if hero_id is not None:
        if hero_id in state.get("hero_rounds", []):
            raise HTTPException(status_code=400, detail="They've had their round tonight — the barkeep cuts them off.")
        hero = conn.execute("SELECT id, name FROM heroes WHERE id = ? AND is_alive = 1", (hero_id,)).fetchone()
        if not hero:
            raise HTTPException(status_code=400, detail="No such patron at the tables.")
        if base["gold"] < HERO_ROUND_COST:
            raise HTTPException(status_code=400, detail=f"Not enough gold ({HERO_ROUND_COST}g).")
        conn.execute("UPDATE base SET gold = gold - ? WHERE id = 1", (HERO_ROUND_COST,))
        conn.execute("UPDATE heroes SET stress = MAX(0, stress - 20), morale = MIN(100, COALESCE(morale, 100) + 5) WHERE id = ?", (hero_id,))
        state.setdefault("hero_rounds", []).append(hero_id)
        _save_tavern_state(conn, state)
        return {"ok": True, "message": f"A round for {hero['name']} — the edge comes off. (-20 stress, +5 morale)"}

    if state.get("house_round"):
        raise HTTPException(status_code=400, detail="The house has had its round tonight.")
    if base["gold"] < HOUSE_ROUND_COST:
        raise HTTPException(status_code=400, detail=f"Not enough gold ({HOUSE_ROUND_COST:,}g).")
    conn.execute("UPDATE base SET gold = gold - ? WHERE id = 1", (HOUSE_ROUND_COST,))
    conn.execute("UPDATE heroes SET stress = MAX(0, stress - 12), morale = MIN(100, COALESCE(morale, 100) + 8) WHERE is_alive = 1")
    state["house_round"] = True
    _save_tavern_state(conn, state)
    return {"ok": True, "message": "A round for the house! Every hero sheds stress and gains a night's morale."}


def process_shrine(conn):
    minutes = _minutes_since(conn, "last_shrine_tick")
    # Slow by design: one affinity pulse per 30 minutes. Don't advance the
    # clock until a full pulse has accrued, so partial time isn't lost.
    if minutes is None or minutes < 30:
        return
    shrine = conn.execute("SELECT id, level FROM facilities WHERE type = 'Shrine' AND base_id = 1").fetchone()
    if not shrine:
        conn.execute("UPDATE base SET last_shrine_tick = CURRENT_TIMESTAMP WHERE id = 1")
        return
    clergy = _assigned_classes(conn, shrine["id"])
    if not clergy:
        conn.execute("UPDATE base SET last_shrine_tick = CURRENT_TIMESTAMP WHERE id = 1")
        return

    pulses = minutes // 30
    gain_per_pulse = sum(2 if c in ("Priest", "Acolyte", "Cleric", "High Priest", "Saint", "Oracle") else 1 for c in clergy)
    # Priest · Confessor (Absolution): mastery-scaled extra loyalty per pulse;
    # the High Confessor capstone also calms the whole roster's stress.
    calm = 0
    try:
        from services.support_service import get_support_effects
        sfx = get_support_effects(conn)
        gain_per_pulse += sfx.get("priest_loyalty_bonus", 0)
        calm = sfx.get("priest_calm_stress", 0)
    except Exception:
        pass
    total = min(10 + gain_per_pulse, gain_per_pulse * pulses)  # cap a long-offline catchup
    if total > 0:
        conn.execute("UPDATE heroes SET affinity = MIN(100, COALESCE(affinity, 0) + ?) WHERE is_alive = 1", (total,))
    if calm > 0:
        conn.execute("UPDATE heroes SET stress = MAX(0, COALESCE(stress, 0) - ?) WHERE is_alive = 1", (min(6, calm * pulses),))
    conn.execute("UPDATE base SET last_shrine_tick = CURRENT_TIMESTAMP WHERE id = 1")
