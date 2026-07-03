"""
Legacy Service
==============
When a hero dies, their sacrifice echoes through the roster forever.

Legacy bonuses are permanent passive buffs based on the fallen hero's
accomplishments: floors survived, kills, star rank, trauma endured.

The LLM generates a legacy title and flavor text based on the hero's story.
"""

import random
import json
from database import db


# A hero only earns a place in the Hall of Legacies if they actually left a
# mark. Sacrifices are always enshrined (a deliberate, memorialized death —
# handled by the is_sacrifice bypass in create_legacy), but an ordinary
# combat death has to clear ONE of these bars, or they're simply gone. This
# stops the Hall filling with level-1 fodder that died on floor 2.
LEGACY_MIN_UNIQUE_FLOORS = 10
LEGACY_MIN_LEVEL = 30


def qualifies_for_legacy(hero: dict, is_sacrifice: bool = False) -> bool:
    """Whether a fallen hero is worth enshrining. Sacrifices always are.
    Ordinary deaths must have cleared 10+ unique tower floors, reached
    level 30, or served as a mentor (mentored_count > 0 — the Training
    Grounds mentorship track, so a support hero who never fought still earns
    remembrance for the students they raised)."""
    if is_sacrifice:
        return True
    if hero.get("level", 1) >= LEGACY_MIN_LEVEL:
        return True
    unique_floors = hero.get("unique_floor_clears", 0) or hero.get("unique_floors_cleared", 0) or 0
    if unique_floors >= LEGACY_MIN_UNIQUE_FLOORS:
        return True
    if (hero.get("mentored_count", 0) or 0) > 0:
        return True
    return False


def calculate_legacy_bonus(hero: dict) -> dict:
    """
    Calculate the legacy bonus a dead hero leaves behind.
    Higher accomplishments = stronger legacy.
    """
    floors = hero.get("floors_survived", 0)
    kills = hero.get("kills", 0)
    star = hero.get("birth_star", 1)
    trauma = hero.get("trauma", 0)
    level = hero.get("level", 1)

    # Score determines legacy power
    score = (floors * 2) + (kills * 3) + (star * 10) + (trauma // 5) + (level * 2)

    # Determine bonus type based on hero's strongest trait
    bonus_types = [
        ("str_pct", "ATK", hero.get("strength", 0)),
        ("int_pct", "DEF", hero.get("intelligence", 0)),
        ("hlt_pct", "Health", hero.get("max_health", 0) // 10),
        ("agi_pct", "SPD", hero.get("agility", 0)),
    ]

    # Pick the stat the hero was best at
    best_stat = max(bonus_types, key=lambda x: x[2])
    bonus_key = best_stat[0]
    bonus_label = best_stat[1]

    # Calculate bonus magnitude (1-5% based on score)
    magnitude = min(5, max(1, score // 30))

    # Special bonuses for exceptional heroes
    special = None
    if kills >= 20:
        special = {"id": "killer_instinct", "desc": f"+{magnitude}% crit chance to all heroes",
                   "effect": {"team_crit_pct": magnitude * 0.01}}
    elif floors >= 30:
        special = {"id": "veteran_wisdom", "desc": f"-{magnitude * 2}% stress gain for all heroes",
                   "effect": {"team_stress_reduce": magnitude * 0.02}}
    elif trauma >= 70:
        special = {"id": "iron_spirit", "desc": f"+{magnitude}% fear resistance to all heroes",
                   "effect": {"team_fear_resist": magnitude * 0.01}}

    return {
        "hero_id": hero["id"],
        "hero_name": hero.get("name", "Unknown"),
        "hero_star": star,
        "score": score,
        "primary_bonus": {
            "stat": bonus_key,
            "label": bonus_label,
            "value": magnitude * 0.01,  # percentage
            "desc": f"+{magnitude}% {bonus_label} to all heroes",
        },
        "special_bonus": special,
        "floors_survived": floors,
        "kills": kills,
        "level": level,
    }


def create_legacy(hero: dict, title: str = None, flavor: str = None, is_sacrifice: bool = False) -> dict | None:
    """Create and save a legacy record for a fallen hero, IF they qualify
    (see qualifies_for_legacy). Returns None for a hero who didn't earn one
    — an unremarkable death that leaves no echo.

    Portraits are only preserved for sacrificed heroes — sacrifice is a
    deliberate, memorialized death, so the team chooses to immortalize their
    face. An ordinary combat death is just gone; the legacy keeps their name
    and story, not their portrait.
    """
    if not qualifies_for_legacy(hero, is_sacrifice):
        return None

    bonus = calculate_legacy_bonus(hero)

    # Try LLM-generated title and flavor
    if not title or not flavor:
        try:
            from services.llm_service import generate_legacy_text
            llm_title, llm_flavor = generate_legacy_text(
                hero.get("name", "Unknown"),
                hero.get("birth_star", 1),
                hero.get("floors_survived", 0),
                hero.get("kills", 0),
                hero.get("backstory", ""),
            )
            title = title or llm_title
            flavor = flavor or llm_flavor
        except Exception:
            pass

    if not title:
        title = _generate_fallback_title(hero)
    if not flavor:
        flavor = f"They survived {bonus['floors_survived']} floors and slew {bonus['kills']} foes."

    portrait_path = hero.get("portrait_path") if is_sacrifice else None

    with db() as conn:
        conn.execute("""
            INSERT INTO legacies (hero_id, hero_name, hero_star, title, flavor_text,
                                  bonus_json, score, is_sacrifice, portrait_path, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            hero["id"], hero.get("name", "Unknown"), hero.get("birth_star", 1),
            title, flavor, json.dumps(bonus), bonus["score"],
            1 if is_sacrifice else 0, portrait_path,
        ))

    return {"title": title, "flavor": flavor, "is_sacrifice": is_sacrifice, "portrait_path": portrait_path, **bonus}


def get_all_legacies() -> list[dict]:
    """Return all legacy records."""
    with db() as conn:
        rows = conn.execute("""
            SELECT * FROM legacies ORDER BY score DESC
        """).fetchall()
    return [dict(r) for r in rows]


def get_active_legacy_bonuses() -> dict:
    """Calculate total legacy bonuses — only sacrificed/memorialized heroes
    contribute a stat bonus. An ordinary combat death is remembered (title,
    flavor, the legacy entry itself) but doesn't buff the team; that's
    reserved for the deliberate, rare act of sacrifice."""
    legacies = [l for l in get_all_legacies() if l.get("is_sacrifice")]
    total = {
        "str_pct": 0, "int_pct": 0, "hlt_pct": 0, "agi_pct": 0,
        "team_crit_pct": 0, "team_stress_reduce": 0, "team_fear_resist": 0,
    }

    for legacy in legacies:
        try:
            bonus = json.loads(legacy.get("bonus_json", "{}"))
        except (json.JSONDecodeError, TypeError):
            continue

        primary = bonus.get("primary_bonus", {})
        stat = primary.get("stat", "")
        if stat in total:
            total[stat] += primary.get("value", 0)

        special = bonus.get("special_bonus")
        if special and isinstance(special, dict):
            for key, val in special.get("effect", {}).items():
                if key in total:
                    total[key] += val

    return total


def apply_legacy_bonuses(hero: dict) -> dict:
    """Apply legacy bonuses to hero stats before combat."""
    bonuses = get_active_legacy_bonuses()
    h = hero.copy()

    if bonuses["str_pct"] > 0:
        h["strength"] = int(h["strength"] * (1 + bonuses["str_pct"]))
    if bonuses["int_pct"] > 0:
        h["intelligence"] = int(h["intelligence"] * (1 + bonuses["int_pct"]))
    if bonuses["hlt_pct"] > 0:
        h["max_health"] = int(h["max_health"] * (1 + bonuses["hlt_pct"]))
        h["health"] = int(h["health"] * (1 + bonuses["hlt_pct"]))
    if bonuses["agi_pct"] > 0:
        h["agility"] = int(h["agility"] * (1 + bonuses["agi_pct"]))
    if bonuses["team_crit_pct"] > 0:
        h["crit_chance"] = h.get("crit_chance", 0.05) + bonuses["team_crit_pct"]
    if bonuses["team_fear_resist"] > 0:
        h["fear_resist"] = h.get("fear_resist", 0) + bonuses["team_fear_resist"]

    return h


def _generate_fallback_title(hero: dict) -> str:
    """Fallback title if LLM is unavailable."""
    templates = [
        f"The Memory of {hero.get('name', 'the Fallen')}",
        f"{hero.get('name', 'Unknown')}'s Final Echo",
        f"Shadow of {hero.get('name', 'the Lost')}",
        f"The Weight {hero.get('name', 'They')} Carried",
    ]
    return random.choice(templates)
