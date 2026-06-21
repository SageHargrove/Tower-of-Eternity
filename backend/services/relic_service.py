import random
from database import db

def generate_relic_drop(floor_number: int) -> dict:
    """Generate a powerful relic from a boss kill."""
    relic_types = [
        ("The Hollow Crown", "Increases Max HP by 5% for all heroes.", "stat_hp_pct", 0.05),
        ("Blood-Soaked Banner", "Increases Attack by 5% for all heroes.", "stat_atk_pct", 0.05),
        ("Aegis of the Fallen", "Increases Defense by 5% for all heroes.", "stat_def_pct", 0.05),
        ("Winged Boots of the Abyss", "Increases Speed by 5% for all heroes.", "stat_spd_pct", 0.05),
        ("Idol of the Forgotten", "Heroes gain 10% more XP.", "stat_xp_pct", 0.10),
    ]
    
    name, desc, effect, value = random.choice(relic_types)
    
    # Scale slightly based on floor
    scale = 1 + (floor_number // 50)
    value *= scale
    desc = desc.replace("5%", f"{int(value*100)}%").replace("10%", f"{int(value*100)}%")
    
    return {
        "name": name,
        "description": desc,
        "effect_type": effect,
        "effect_value": value
    }

def save_relic(relic_data: dict) -> int:
    with db() as conn:
        cursor = conn.execute(
            "INSERT INTO relics (name, description, effect_type, effect_value) VALUES (?,?,?,?)",
            (relic_data["name"], relic_data["description"], relic_data["effect_type"], relic_data["effect_value"])
        )
        return cursor.lastrowid

def get_all_relics() -> list[dict]:
    with db() as conn:
        rows = conn.execute("SELECT * FROM relics").fetchall()
        return [dict(r) for r in rows]

def apply_relic_stats(hero_stats: dict, relics: list[dict]) -> dict:
    for r in relics:
        eff = r["effect_type"]
        val = r["effect_value"]
        if eff == "stat_hp_pct":
            hero_stats["max_hp"] = int(hero_stats["max_hp"] * (1 + val))
            hero_stats["hp"] = min(hero_stats["max_hp"], hero_stats["hp"])
        elif eff == "stat_atk_pct":
            hero_stats["attack"] = int(hero_stats["attack"] * (1 + val))
        elif eff == "stat_def_pct":
            hero_stats["defense"] = int(hero_stats["defense"] * (1 + val))
        elif eff == "stat_spd_pct":
            hero_stats["speed"] = int(hero_stats["speed"] * (1 + val))
    return hero_stats
