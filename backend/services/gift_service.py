"""Hero gifting — buy a gift with gold/gems, give it to a hero, and get a
reaction based on their hidden preferences.

Preferences are DERIVED, not stored: a deterministic hash of the hero id
picks 2 loved gifts and 1 disliked gift from the catalog. That keeps them
stable per hero, hidden from the player until discovered, and requires no
schema beyond the affinity column.

Affinity is a 0-100 loyalty track (heroes.affinity). It feeds the upcoming
loyalty/raid mechanics (a captured low-affinity hero may turn on you); for
now it also grants immediate value: loved gifts permanently raise a stat.
"""

import json
import random
from database import db

# Every icon here already exists in frontend/public/icons/ — the "flavor"
# icons finally earn their keep. war_horse_figurine is the manhwa nod.
GIFT_CATALOG = [
    {"id": "war_horse_figurine", "name": "War Horse Figurine", "cost_gold": 400, "cost_gems": 0, "icon": "creature_horse",
     "desc": "A hand-carved cavalry figurine. Some warriors never outgrow their first toy."},
    {"id": "honeyed_rations", "name": "Honeyed Rations", "cost_gold": 150, "cost_gems": 0, "icon": "rations",
     "desc": "Field rations, but someone actually tried. Sweet, dense, and warm."},
    {"id": "lucky_clover", "name": "Lucky Clover Charm", "cost_gold": 250, "cost_gems": 0, "icon": "luck_clover",
     "desc": "Pressed under glass. Probably doesn't work. Probably."},
    {"id": "whetstone", "name": "Mastercraft Whetstone", "cost_gold": 300, "cost_gems": 0, "icon": "anvil",
     "desc": "The kind of edge maintenance that says someone wants you to come back alive."},
    {"id": "wolf_pelt", "name": "Wolf Pelt Cloak", "cost_gold": 350, "cost_gems": 0, "icon": "creature_wolf",
     "desc": "Heavy, warm, and smells faintly of the hunt."},
    {"id": "strength_tonic", "name": "Strength Tonic", "cost_gold": 200, "cost_gems": 0, "icon": "buff_strength",
     "desc": "Tastes like iron and bad decisions. Works, though."},
    {"id": "battle_horn", "name": "Battle Horn", "cost_gold": 500, "cost_gems": 0, "icon": "buff_horn",
     "desc": "Carved from a behemoth's horn. Loud enough to wake the dead — or rally them."},
    {"id": "heart_locket", "name": "Heart Locket", "cost_gold": 0, "cost_gems": 50, "icon": "health_heart",
     "desc": "A small silver locket, empty. What they put inside is up to them."},
    {"id": "storm_in_a_bottle", "name": "Storm in a Bottle", "cost_gold": 0, "cost_gems": 80, "icon": "storm",
     "desc": "A sealed vial of captured skyfire. Shakes angrily when ignored."},
    {"id": "dragon_scale", "name": "Dragon Scale", "cost_gold": 0, "cost_gems": 120, "icon": "arcane_dragon",
     "desc": "Still warm. A trophy from far above any floor you've reached."},
]

AFFINITY_LOVED = 15
AFFINITY_NEUTRAL = 5
AFFINITY_DISLIKED = -5

# Reaction lines by reaction type — picked by hero-id + gift hash so the
# same hero gives the same line for the same gift (feels like personality,
# not a slot machine).
LOVED_LINES = [
    "…How did you know? I— thank you. Truly.",
    "You remembered. Nobody remembers. I'll carry this up every floor.",
    "This is the best thing anyone's given me since I got dragged into this Tower.",
    "Ha! Now THIS is a reason to survive the next climb.",
    "I don't have words. Don't tell the others I teared up.",
]
NEUTRAL_LINES = [
    "Oh — thanks. That's thoughtful of you.",
    "Appreciated. It'll find a use.",
    "Huh. Not what I'd have picked, but the gesture counts for something.",
    "Thanks, boss. Back to work then?",
]
DISLIKED_LINES = [
    "…You really don't know me at all, do you.",
    "I'll… find somewhere to put this. Somewhere far away.",
    "Is this a joke? Please tell me this is a joke.",
    "Right. Thanks. I guess.",
]

STAT_COLUMNS = ["strength", "intelligence", "agility", "endurance", "willpower", "luck"]


def hero_preferences(hero_id: int) -> dict:
    """Deterministic hidden preferences: 2 loved + 1 disliked gift ids."""
    rng = random.Random(hero_id * 7919 + 13)
    ids = [g["id"] for g in GIFT_CATALOG]
    picks = rng.sample(ids, 3)
    return {"loved": picks[:2], "disliked": picks[2]}


def get_catalog() -> list[dict]:
    return GIFT_CATALOG


def give_gift(hero_id: int, gift_id: str) -> dict:
    gift = next((g for g in GIFT_CATALOG if g["id"] == gift_id), None)
    if not gift:
        raise ValueError("Unknown gift.")

    with db() as conn:
        hero = conn.execute("SELECT * FROM heroes WHERE id = ? AND is_alive = 1", (hero_id,)).fetchone()
        if not hero:
            raise ValueError("Hero not found or dead.")
        hero = dict(hero)

        base = conn.execute("SELECT gold, gems FROM base WHERE id = 1").fetchone()
        if gift["cost_gold"] and base["gold"] < gift["cost_gold"]:
            raise ValueError("Not enough gold.")
        if gift["cost_gems"] and base["gems"] < gift["cost_gems"]:
            raise ValueError("Not enough gems.")
        conn.execute("UPDATE base SET gold = gold - ?, gems = gems - ? WHERE id = 1",
                     (gift["cost_gold"], gift["cost_gems"]))

        prefs = hero_preferences(hero_id)
        if gift_id in prefs["loved"]:
            reaction = "loved"
            affinity_delta = AFFINITY_LOVED
            lines = LOVED_LINES
        elif gift_id == prefs["disliked"]:
            reaction = "disliked"
            affinity_delta = AFFINITY_DISLIKED
            lines = DISLIKED_LINES
        else:
            reaction = "neutral"
            affinity_delta = AFFINITY_NEUTRAL
            lines = NEUTRAL_LINES

        line_rng = random.Random(hero_id * 104729 + hash(gift_id) % 9973)
        line = line_rng.choice(lines)

        new_affinity = max(0, min(100, (hero.get("affinity") or 0) + affinity_delta))
        conn.execute("UPDATE heroes SET affinity = ? WHERE id = ?", (new_affinity, hero_id))

        # A loved gift permanently raises one stat — which stat is also
        # deterministic per hero+gift, so re-gifting the same loved gift
        # keeps building the same strength (a discoverable min-max hook).
        stat_gain = None
        if reaction == "loved":
            stat = line_rng.choice(STAT_COLUMNS)
            conn.execute(f"UPDATE heroes SET {stat} = {stat} + 1 WHERE id = ?", (hero_id,))
            stat_gain = {"stat": stat, "amount": 1}
            # A loved gift also lifts spirits on the spot.
            conn.execute("UPDATE heroes SET morale = MIN(100, morale + 10), stress = MAX(0, stress - 5) WHERE id = ?", (hero_id,))

    return {
        "ok": True,
        "reaction": reaction,
        "line": line,
        "affinity": new_affinity,
        "affinity_delta": affinity_delta,
        "stat_gain": stat_gain,
        "gift": gift,
        "hero_name": hero["name"],
    }
