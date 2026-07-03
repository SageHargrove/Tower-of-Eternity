"""
Training Grounds — solo drills (regimens).

Each hero ASSIGNED to the Training Grounds can be set to a regimen: an
ongoing self-directed drill that ticks over time (process_training, called
from get_base like the other facility ticks). This is the "train by
yourself" pillar, alongside the discrete Sparring/Mentorship sessions in
sparring_service.py.

Regimens:
  focus        — the classic flat XP trickle (the old default behavior).
  conditioning — permanently raises a chosen BASE stat, a point at a time,
                 up to a cap that scales with the Training Grounds level
                 (so the facility is worth leveling). Tracked in
                 heroes.training_gains so the cap is enforceable and gains
                 are distinguishable from a hero's rolled base.
  meditation   — raises apt_mental toward 100 and, tick by tick, has a
                 chance to REVEAL an unrevealed aptitude (a second path to
                 discovery alongside the Mirror of Fate).
  weapon_drill — grinds one specific SKILL the hero already knows, faster
                 and more reliably than a random sparring bump.

Intensity (light / moderate / intense) is the dial: it multiplies every
gain but also piles on fatigue and stress per tick. Intense drilling with
no rest builds fatigue toward the tower-entry lockout (fatigue >= 10) — so
the Tavern/Dining Hall recovery loop matters. Cheap, safe, and it makes
"push the roster hard then rest them" a real rhythm.
"""
import json
import random

STAT_KEYS = ["strength", "intelligence", "agility", "endurance", "willpower", "luck"]

REGIMENS = {
    "focus":        {"label": "Focused Study",   "desc": "A steady trickle of XP — the reliable all-rounder."},
    "conditioning": {"label": "Conditioning",    "desc": "Permanently raises a chosen stat, up to a cap set by the Training Grounds level."},
    "meditation":   {"label": "Meditation",      "desc": "Sharpens Mental aptitude and may reveal a hidden aptitude over time."},
    "weapon_drill": {"label": "Weapon Drills",   "desc": "Relentlessly grinds one specific skill toward its next level."},
}

INTENSITY = {
    # gain multiplier, fatigue per tick, stress per tick
    "light":    {"mult": 0.5, "fatigue": 0, "stress": 0, "label": "Light"},
    "moderate": {"mult": 1.0, "fatigue": 1, "stress": 1, "label": "Moderate"},
    "intense":  {"mult": 2.0, "fatigue": 2, "stress": 3, "label": "Intense"},
}

# Per-stat conditioning cap = TG level * this. A level-10 TG lets a hero
# earn +30 in any single stat from drilling — meaningful but bounded.
CONDITIONING_CAP_PER_LEVEL = 3

# How much apt_mental meditation adds per tick, and the per-tick chance to
# reveal a new aptitude (scaled by intensity).
MEDITATION_APT_PER_TICK = 1
MEDITATION_REVEAL_CHANCE = 0.05


def set_regimen(conn, hero_id: int, regimen: str, focus: str = None, intensity: str = "moderate") -> dict:
    if regimen is not None and regimen not in REGIMENS:
        raise ValueError("Unknown regimen.")
    if intensity not in INTENSITY:
        raise ValueError("Unknown intensity.")

    hero = conn.execute("SELECT id FROM heroes WHERE id = ? AND is_alive = 1", (hero_id,)).fetchone()
    if not hero:
        raise ValueError("Hero not found.")

    assigned = conn.execute("""
        SELECT 1 FROM facility_assignments fa
        JOIN facilities f ON fa.facility_id = f.id
        WHERE fa.hero_id = ? AND f.type = 'Training Grounds' AND f.base_id = 1
    """, (hero_id,)).fetchone()
    if not assigned:
        raise ValueError("Hero must be assigned to the Training Grounds first.")

    if regimen == "conditioning":
        if focus not in STAT_KEYS:
            raise ValueError("Conditioning needs a valid stat to train.")
    elif regimen == "weapon_drill":
        skills = json.loads(conn.execute("SELECT skills FROM heroes WHERE id = ?", (hero_id,)).fetchone()["skills"] or "[]")
        if not any(s.get("id") == focus for s in skills):
            raise ValueError("Weapon Drills needs one of the hero's own skills to focus on.")
    else:
        focus = None

    conn.execute(
        "UPDATE heroes SET training_regimen = ?, training_focus = ?, training_intensity = ? WHERE id = ?",
        (regimen, focus, intensity, hero_id),
    )
    return {"ok": True, "regimen": regimen, "focus": focus, "intensity": intensity}


def _conditioning_cap(tg_level: int) -> int:
    return max(1, tg_level) * CONDITIONING_CAP_PER_LEVEL


def _minutes_since(conn, column: str) -> int:
    from datetime import datetime
    try:
        conn.execute(f"ALTER TABLE base ADD COLUMN {column} TIMESTAMP")
    except Exception:
        pass
    row = conn.execute(f"SELECT {column} FROM base WHERE id = 1").fetchone()
    val = dict(row).get(column) if row else None
    if not val:
        conn.execute(f"UPDATE base SET {column} = CURRENT_TIMESTAMP WHERE id = 1")
        return 0
    try:
        last = datetime.strptime(val, "%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        conn.execute(f"UPDATE base SET {column} = CURRENT_TIMESTAMP WHERE id = 1")
        return 0
    return int((datetime.utcnow() - last).total_seconds() / 60)


def process_training(conn):
    """Tick every Training-Grounds-assigned hero's regimen. One tick per 5
    real minutes elapsed (capped so a long absence doesn't dump absurd
    gains in one go — the Chronosphere is the intended big time-skip)."""
    minutes = _minutes_since(conn, "last_train_tick")
    ticks = min(minutes // 5, 24)  # cap ~2 hours of catch-up
    if ticks <= 0:
        return

    tg = conn.execute("SELECT id, level FROM facilities WHERE type = 'Training Grounds' AND base_id = 1").fetchone()
    if not tg:
        conn.execute("UPDATE base SET last_train_tick = CURRENT_TIMESTAMP WHERE id = 1")
        return
    tg_level = tg["level"]
    cap = _conditioning_cap(tg_level)

    assigned = conn.execute("""
        SELECT h.* FROM facility_assignments fa
        JOIN heroes h ON fa.hero_id = h.id
        WHERE fa.facility_id = ? AND h.is_alive = 1
    """, (tg["id"],)).fetchall()

    from services.level_service import recalculate_hero_level

    for row in assigned:
        h = dict(row)
        regimen = h.get("training_regimen") or "focus"
        intensity = INTENSITY.get(h.get("training_intensity") or "moderate", INTENSITY["moderate"])
        mult = intensity["mult"]

        if regimen == "focus":
            xp = int(50 * tg_level * mult) * ticks
            conn.execute("UPDATE heroes SET xp = COALESCE(xp, 0) + ? WHERE id = ?", (xp, h["id"]))

        elif regimen == "conditioning":
            stat = h.get("training_focus")
            if stat in STAT_KEYS:
                gains = json.loads(h.get("training_gains") or "{}")
                already = gains.get(stat, 0)
                room = max(0, cap - already)
                # ~1 stat point per 3 ticks at moderate; intensity scales it.
                earned = min(room, int(ticks * mult / 3))
                if earned > 0:
                    gains[stat] = already + earned
                    conn.execute(
                        f"UPDATE heroes SET {stat} = {stat} + ?, training_gains = ? WHERE id = ?",
                        (earned, json.dumps(gains), h["id"]),
                    )

        elif regimen == "meditation":
            apt = min(100, (h.get("apt_mental") or 50) + int(MEDITATION_APT_PER_TICK * mult) * ticks)
            revealed = h.get("aptitudes_revealed") or 0
            for _ in range(ticks):
                if revealed < 6 and random.random() < MEDITATION_REVEAL_CHANCE * mult:
                    revealed += 1
            conn.execute(
                "UPDATE heroes SET apt_mental = ?, aptitudes_revealed = ? WHERE id = ?",
                (apt, min(6, revealed), h["id"]),
            )

        elif regimen == "weapon_drill":
            skills = json.loads(h.get("skills") or "[]")
            target = next((s for s in skills if s.get("id") == h.get("training_focus")), None)
            if target:
                target["xp"] = target.get("xp", 0) + int(40 * tg_level * mult) * ticks
                # Roll the skill up as many times as accumulated XP allows.
                while target["xp"] >= target.get("max_xp", 100):
                    target["xp"] -= target.get("max_xp", 100)
                    target["level"] = target.get("level", 1) + 1
                    target["max_xp"] = int(target.get("max_xp", 100) * 1.5)
                conn.execute("UPDATE heroes SET skills = ? WHERE id = ?", (json.dumps(skills), h["id"]))

        # Intensity toll — fatigue and stress accrue with hard training.
        fatigue_add = intensity["fatigue"] * ticks
        stress_add = intensity["stress"] * ticks
        if fatigue_add or stress_add:
            conn.execute(
                "UPDATE heroes SET fatigue = MIN(10, fatigue + ?), stress = MIN(100, stress + ?) WHERE id = ?",
                (fatigue_add, stress_add, h["id"]),
            )

        # Recompute level in case conditioning/focus/drills pushed a threshold.
        fresh = conn.execute("SELECT * FROM heroes WHERE id = ?", (h["id"],)).fetchone()
        if fresh:
            new_level = recalculate_hero_level(dict(fresh))
            if new_level != fresh["level"]:
                conn.execute("UPDATE heroes SET level = ? WHERE id = ?", (new_level, h["id"]))

    conn.execute("UPDATE base SET last_train_tick = CURRENT_TIMESTAMP WHERE id = 1")


def get_training_status(conn) -> dict:
    """Everything the Training Grounds UI needs: assigned heroes with their
    regimen state, the conditioning cap, and each hero's skills for the
    weapon-drill picker."""
    tg = conn.execute("SELECT id, level FROM facilities WHERE type = 'Training Grounds' AND base_id = 1").fetchone()
    if not tg:
        return {"built": False, "heroes": []}
    assigned = conn.execute("""
        SELECT h.id, h.name, h.level, h.hero_class, h.skills, h.fatigue, h.stress,
               h.training_regimen, h.training_focus, h.training_intensity, h.training_gains,
               h.apt_mental, h.aptitudes_revealed
        FROM facility_assignments fa
        JOIN heroes h ON fa.hero_id = h.id
        WHERE fa.facility_id = ? AND h.is_alive = 1
    """, (tg["id"],)).fetchall()
    heroes = []
    for row in assigned:
        h = dict(row)
        h["skills"] = json.loads(h.get("skills") or "[]")
        h["training_gains"] = json.loads(h.get("training_gains") or "{}")
        heroes.append(h)
    return {
        "built": True,
        "level": tg["level"],
        "conditioning_cap": _conditioning_cap(tg["level"]),
        "stat_keys": STAT_KEYS,
        "regimens": REGIMENS,
        "intensity": {k: {"label": v["label"]} for k, v in INTENSITY.items()},
        "heroes": heroes,
    }
