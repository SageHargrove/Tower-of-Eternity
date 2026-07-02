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
    total = min(10, gain_per_pulse * pulses)  # cap a long-offline catchup
    if total > 0:
        conn.execute("UPDATE heroes SET affinity = MIN(100, COALESCE(affinity, 0) + ?) WHERE is_alive = 1", (total,))
    conn.execute("UPDATE base SET last_shrine_tick = CURRENT_TIMESTAMP WHERE id = 1")
