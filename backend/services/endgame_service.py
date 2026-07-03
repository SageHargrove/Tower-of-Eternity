"""Endgame facilities (floors 30-75): Bestiary, Reliquary, Chronosphere,
Transcendence Core.

The core facilities all unlock by floor 25 (the "early game rush") — these
four exist so the base keeps gaining CONTENT, not just levels, through the
long climb. Tables/columns self-migrate here (same pattern as
ship_service) so nothing breaks on older saves.
"""
import json
import random
import time
from datetime import datetime


def _ensure_schema(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS bestiary_beasts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            species TEXT NOT NULL,
            floor_caught INTEGER NOT NULL,
            power INTEGER NOT NULL,
            is_guarding INTEGER DEFAULT 1,
            captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS reliquary_trophies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            boss_name TEXT NOT NULL,
            floor INTEGER NOT NULL UNIQUE,
            buff_key TEXT NOT NULL,
            buff_value INTEGER NOT NULL,
            is_mounted INTEGER DEFAULT 0,
            earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    for col, ddl in [
        ("last_chrono_time", "ALTER TABLE base ADD COLUMN last_chrono_time REAL DEFAULT 0"),
        ("transcendence_infusions", "ALTER TABLE base ADD COLUMN transcendence_infusions INTEGER DEFAULT 0"),
    ]:
        try:
            conn.execute(ddl)
        except Exception:
            pass


def _facility_level(conn, fac_type: str) -> int:
    row = conn.execute("SELECT level FROM facilities WHERE type = ? AND base_id = 1", (fac_type,)).fetchone()
    return row["level"] if row else 0


# ── Bestiary ─────────────────────────────────────────────────────────

BEAST_EPITHETS = ["Grim", "Old", "One-Eye", "Ashen", "Razor", "Dusk", "Iron", "Sly", "Broken-Fang", "Moss"]

# Bosses aren't capturable (they drop Reliquary trophies instead), and
# neither are humanoid "people" enemies — the pen holds BEASTS.
UNCAPTURABLE = {"Bandit", "Cultist", "Dark Knight", "Fallen Paladin", "Necromancer", "Rogue Mage"}


def bestiary_capacity(level: int) -> int:
    return 3 + level // 5


def maybe_capture_beast(conn, floor_number: int, enemy_names: list[str], is_boss: bool) -> dict | None:
    """One capture roll per winning fight — called from tower.py's
    _resolve_real_combat after loot is granted. Returns the captured beast
    dict (for the result payload) or None."""
    if is_boss or not enemy_names:
        return None
    level = _facility_level(conn, "Bestiary")
    if level <= 0:
        return None
    _ensure_schema(conn)

    held = conn.execute("SELECT COUNT(*) AS c FROM bestiary_beasts").fetchone()["c"]
    if held >= bestiary_capacity(level):
        return None

    chance = 0.06 + 0.01 * (level // 5)
    if random.random() > chance:
        return None

    candidates = [n for n in enemy_names if n not in UNCAPTURABLE]
    if not candidates:
        return None
    species = random.choice(candidates)
    name = f"{random.choice(BEAST_EPITHETS)} {species}"
    power = 10 + floor_number * 2
    cur = conn.execute(
        "INSERT INTO bestiary_beasts (name, species, floor_caught, power) VALUES (?,?,?,?)",
        (name, species, floor_number, power)
    )
    return {"id": cur.lastrowid, "name": name, "species": species, "power": power, "floor_caught": floor_number}


def get_bestiary(conn) -> dict:
    _ensure_schema(conn)
    level = _facility_level(conn, "Bestiary")
    beasts = [dict(r) for r in conn.execute("SELECT * FROM bestiary_beasts ORDER BY power DESC").fetchall()]
    return {
        "built": level > 0,
        "level": level,
        "capacity": bestiary_capacity(level),
        "beasts": beasts,
        "defense_bonus": sum(b["power"] for b in beasts if b["is_guarding"]),
        "capture_chance_pct": round((0.06 + 0.01 * (level // 5)) * 100, 1) if level else 0,
    }


def release_beast(conn, beast_id: int) -> dict:
    _ensure_schema(conn)
    row = conn.execute("SELECT name FROM bestiary_beasts WHERE id = ?", (beast_id,)).fetchone()
    if not row:
        raise ValueError("No such beast.")
    conn.execute("DELETE FROM bestiary_beasts WHERE id = ?", (beast_id,))
    return {"ok": True, "released": row["name"]}


def bestiary_defense(conn) -> int:
    try:
        _ensure_schema(conn)
        row = conn.execute("SELECT COALESCE(SUM(power), 0) AS p FROM bestiary_beasts WHERE is_guarding = 1").fetchone()
        return row["p"] if _facility_level(conn, "Bestiary") > 0 else 0
    except Exception:
        return 0


# ── Reliquary ────────────────────────────────────────────────────────

# Buff cycle by boss floor — floor 10's trophy is index 0, floor 20's is
# index 1, etc., wrapping. Values are PERCENT.
TROPHY_BUFF_CYCLE = [
    ("hp_pct", 3, "+3% Max Health (all heroes)"),
    ("atk_pct", 3, "+3% Strength (all heroes)"),
    ("gold_pct", 5, "+5% Gold from fights"),
    ("def_pct", 3, "+3% Endurance (all heroes)"),
    ("int_pct", 3, "+3% Intelligence (all heroes)"),
    ("gold_pct", 5, "+5% Gold from fights"),
    ("agi_pct", 3, "+3% Agility (all heroes)"),
    ("luck_pct", 3, "+3% Luck (all heroes)"),
]


def reliquary_mount_slots(level: int) -> int:
    return 2 + level // 5


def maybe_award_trophy(conn, floor_number: int, enemy_names: list[str]) -> dict | None:
    """Called on a winning BOSS fight (every 10th floor). The trophy exists
    whether or not the Reliquary is built yet — you earned it; the building
    is just where you display it."""
    if floor_number % 10 != 0:
        return None
    _ensure_schema(conn)
    existing = conn.execute("SELECT id FROM reliquary_trophies WHERE floor = ?", (floor_number,)).fetchone()
    if existing:
        return None
    boss_name = enemy_names[0] if enemy_names else f"Floor {floor_number} Guardian"
    key, value, label = TROPHY_BUFF_CYCLE[(floor_number // 10 - 1) % len(TROPHY_BUFF_CYCLE)]
    cur = conn.execute(
        "INSERT INTO reliquary_trophies (boss_name, floor, buff_key, buff_value) VALUES (?,?,?,?)",
        (boss_name, floor_number, key, value)
    )
    return {"id": cur.lastrowid, "boss_name": boss_name, "floor": floor_number, "buff_label": label}


def get_reliquary(conn) -> dict:
    _ensure_schema(conn)
    level = _facility_level(conn, "Reliquary")
    trophies = [dict(r) for r in conn.execute("SELECT * FROM reliquary_trophies ORDER BY floor").fetchall()]
    labels = {(k): lbl for k, v, lbl in TROPHY_BUFF_CYCLE}
    for t in trophies:
        t["buff_label"] = next((lbl for k, v, lbl in TROPHY_BUFF_CYCLE if k == t["buff_key"] and v == t["buff_value"]), t["buff_key"])
    return {
        "built": level > 0,
        "level": level,
        "mount_slots": reliquary_mount_slots(level),
        "mounted_count": sum(1 for t in trophies if t["is_mounted"]),
        "trophies": trophies,
    }


def set_trophy_mounted(conn, trophy_id: int, mounted: bool) -> dict:
    _ensure_schema(conn)
    level = _facility_level(conn, "Reliquary")
    if level <= 0:
        raise ValueError("Build the Reliquary first.")
    row = conn.execute("SELECT * FROM reliquary_trophies WHERE id = ?", (trophy_id,)).fetchone()
    if not row:
        raise ValueError("No such trophy.")
    if mounted:
        mounted_now = conn.execute("SELECT COUNT(*) AS c FROM reliquary_trophies WHERE is_mounted = 1").fetchone()["c"]
        if mounted_now >= reliquary_mount_slots(level):
            raise ValueError(f"All {reliquary_mount_slots(level)} display pedestals are full — upgrade the Reliquary or unmount something.")
    conn.execute("UPDATE reliquary_trophies SET is_mounted = ? WHERE id = ?", (1 if mounted else 0, trophy_id))
    return {"ok": True}


# ── Global empowerment (Reliquary trophies + Transcendence infusions) ──

def get_global_empowerment(conn) -> dict:
    """Aggregated roster-wide percentage buffs. stat keys are per-stat
    percents; 'all_stats_pct' (from Transcendence infusions) applies to
    every combat stat on top."""
    _ensure_schema(conn)
    out = {"hp_pct": 0, "atk_pct": 0, "def_pct": 0, "int_pct": 0, "agi_pct": 0, "luck_pct": 0, "gold_pct": 0, "all_stats_pct": 0}
    try:
        if _facility_level(conn, "Reliquary") > 0:
            for r in conn.execute("SELECT buff_key, buff_value FROM reliquary_trophies WHERE is_mounted = 1").fetchall():
                out[r["buff_key"]] = out.get(r["buff_key"], 0) + r["buff_value"]
        row = conn.execute("SELECT transcendence_infusions FROM base WHERE id = 1").fetchone()
        if row and _facility_level(conn, "Transcendence Core") > 0:
            out["all_stats_pct"] = row["transcendence_infusions"] or 0
    except Exception:
        pass
    return out


# ── Chronosphere ─────────────────────────────────────────────────────

CHRONO_COOLDOWN_SECONDS = 24 * 3600
# Every column that drives an offline/passive tick — winding these back N
# hours makes the very next /base/ load process N hours of generation
# (gold, ingredients, aether, XP, fatigue recovery, potions, morale...).
CHRONO_TICK_COLUMNS = [
    "last_fatigue_tick", "last_research_tick", "last_mage_tick",
    "last_alchemist_tick", "last_restaurant_tick", "last_infirmary_tick",
    "last_tavern_tick", "last_shrine_tick",
]


def chrono_skip_hours(level: int) -> int:
    return 4 + level // 5


def get_chronosphere(conn) -> dict:
    _ensure_schema(conn)
    level = _facility_level(conn, "Chronosphere")
    row = conn.execute("SELECT last_chrono_time FROM base WHERE id = 1").fetchone()
    last = (row["last_chrono_time"] or 0) if row else 0
    remaining = max(0, int(CHRONO_COOLDOWN_SECONDS - (time.time() - last)))
    return {
        "built": level > 0,
        "level": level,
        "skip_hours": chrono_skip_hours(level),
        "cooldown_remaining": remaining,
        "ready": level > 0 and remaining == 0,
    }


def activate_chronosphere(conn) -> dict:
    _ensure_schema(conn)
    level = _facility_level(conn, "Chronosphere")
    if level <= 0:
        raise ValueError("Build the Chronosphere first.")
    row = conn.execute("SELECT last_chrono_time FROM base WHERE id = 1").fetchone()
    last = (row["last_chrono_time"] or 0) if row else 0
    remaining = CHRONO_COOLDOWN_SECONDS - (time.time() - last)
    if remaining > 0:
        hours = int(remaining // 3600)
        mins = int((remaining % 3600) // 60)
        raise ValueError(f"The sands are still settling — ready in {hours}h {mins}m.")

    hours = chrono_skip_hours(level)
    base_cols = {r[1] for r in conn.execute("PRAGMA table_info(base)").fetchall()}
    for col in CHRONO_TICK_COLUMNS:
        if col in base_cols:
            conn.execute(
                f"UPDATE base SET {col} = datetime({col}, '-{hours} hours') WHERE id = 1 AND {col} IS NOT NULL"
            )
    conn.execute("UPDATE base SET last_chrono_time = ? WHERE id = 1", (time.time(),))
    return {"ok": True, "hours_skipped": hours,
            "message": f"The clock faces shatter and reform — {hours} hours of the base's work happen in a heartbeat."}


# ── Transcendence Core ───────────────────────────────────────────────

TRANSCENDENCE_BASE_COST = 100_000
TRANSCENDENCE_COST_GROWTH = 1.6


def transcendence_cost(infusions_done: int) -> int:
    return int(TRANSCENDENCE_BASE_COST * (TRANSCENDENCE_COST_GROWTH ** infusions_done))


def get_transcendence(conn) -> dict:
    _ensure_schema(conn)
    level = _facility_level(conn, "Transcendence Core")
    row = conn.execute("SELECT transcendence_infusions, gold FROM base WHERE id = 1").fetchone()
    done = (row["transcendence_infusions"] or 0) if row else 0
    return {
        "built": level > 0,
        "level": level,
        "infusions": done,
        # The facility's level is the infusion cap — the Core must be
        # physically grown (gold, wall-gated) to channel more power.
        "max_infusions": level,
        "next_cost": transcendence_cost(done),
        "bonus_pct": done,
    }


def infuse_transcendence(conn) -> dict:
    _ensure_schema(conn)
    level = _facility_level(conn, "Transcendence Core")
    if level <= 0:
        raise ValueError("Build the Transcendence Core first.")
    row = conn.execute("SELECT transcendence_infusions, gold FROM base WHERE id = 1").fetchone()
    done = row["transcendence_infusions"] or 0
    if done >= level:
        raise ValueError(f"The Core can't channel more at Lv.{level} — upgrade the facility to unlock infusion {done + 1}.")
    cost = transcendence_cost(done)
    if row["gold"] < cost:
        raise ValueError(f"Not enough gold. Need {cost:,}.")
    conn.execute(
        "UPDATE base SET gold = gold - ?, transcendence_infusions = ? WHERE id = 1",
        (cost, done + 1)
    )
    return {"ok": True, "infusions": done + 1, "bonus_pct": done + 1, "gold_spent": cost,
            "message": f"The Core drinks {cost:,} gold and hums a note only your heroes can hear. +1% to everything, forever."}
