import random
from database import db

RARITY_TIERS = [
    "F-", "F", "F+",
    "E-", "E", "E+",
    "D-", "D", "D+",
    "C-", "C", "C+",
    "B-", "B", "B+",
    "A-", "A", "A+",
    "S-", "S", "S+",
    "SS", "SSS", "Z"
]

RARITY_MULTS = {
    "F-": 0.5, "F": 0.7, "F+": 0.9,
    "E-": 1.1, "E": 1.3, "E+": 1.5,
    "D-": 1.8, "D": 2.2, "D+": 2.6,
    "C-": 3.0, "C": 3.5, "C+": 4.0,
    "B-": 4.6, "B": 5.3, "B+": 6.0,
    "A-": 7.0, "A": 8.5, "A+": 10.0,
    "S-": 12.0, "S": 15.0, "S+": 18.0,
    "SS": 25.0,
    "SSS": 40.0,
    "Z": 100.0,
}

TYPES = ["Weapon", "Armor", "Accessory"]

def get_all_equipment():
    with db() as conn:
        rows = conn.execute("SELECT * FROM equipment ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]

def get_hero_equipment(hero_id: int):
    with db() as conn:
        rows = conn.execute("SELECT * FROM equipment WHERE is_equipped_to = ?", (hero_id,)).fetchall()
        return [dict(r) for r in rows]

def get_unequipped():
    with db() as conn:
        rows = conn.execute("SELECT * FROM equipment WHERE is_equipped_to IS NULL ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]

def equip_item(hero_id: int, equipment_id: int):
    with db() as conn:
        item = conn.execute("SELECT * FROM equipment WHERE id = ?", (equipment_id,)).fetchone()
        if not item:
            raise ValueError("Equipment not found")
        
        # Un-equip whatever is in that slot for the hero
        conn.execute("UPDATE equipment SET is_equipped_to = NULL WHERE is_equipped_to = ? AND type = ?", (hero_id, item["type"]))
        
        # Equip the new item
        conn.execute("UPDATE equipment SET is_equipped_to = ? WHERE id = ?", (hero_id, equipment_id))
        return {"success": True}

def unequip_item(equipment_id: int):
    with db() as conn:
        conn.execute("UPDATE equipment SET is_equipped_to = NULL WHERE id = ?", (equipment_id,))
        return {"success": True}

def apply_equipment_stats(hero: dict) -> dict:
    hero_eq = get_hero_equipment(hero["id"])
    for eq in hero_eq:
        hero["attack"] += eq["base_atk"]
        hero["defense"] += eq["base_def"]
        hero["max_hp"] += eq["base_hp"]
        hero["hp"] += eq["base_hp"]
        hero["speed"] += eq["base_spd"]
        
        if "crit_chance" in hero:
            hero["crit_chance"] += eq.get("crit_chance", 0)
        if "dodge_chance" in hero:
            hero["dodge_chance"] += eq.get("dodge_chance", 0)
        if "armor_pen" in hero:
            hero["armor_pen"] += eq.get("armor_pen", 0)
            
    hero["equipment"] = hero_eq
    return hero

def craft_equipment(crafter_id: int):
    with db() as conn:
        crafter = conn.execute("SELECT level, apt_tactical, hero_class FROM heroes WHERE id = ?", (crafter_id,)).fetchone()
        if not crafter:
            raise ValueError("Crafter not found")
            
        base = conn.execute("SELECT gold FROM base WHERE id = 1").fetchone()
        cost = 500
        if base["gold"] < cost:
            raise ValueError("Not enough gold to craft.")
            
        conn.execute("UPDATE base SET gold = gold - ? WHERE id = 1", (cost,))

        level = crafter["level"]
        apt = crafter["apt_tactical"]
        hero_class = crafter["hero_class"]
        
        score = (level) + (apt)
        
        if hero_class in ("Forge Lord", "Runesmith"):
            score *= 2.5
        elif hero_class == "Master Smith":
            score *= 1.8
        elif hero_class == "Blacksmith":
            score *= 1.3
            
        score += random.randint(-20, 100)
        
        if score < 30: rarity = "F-"
        elif score < 50: rarity = "F"
        elif score < 70: rarity = "F+"
        elif score < 90: rarity = "E-"
        elif score < 110: rarity = "E"
        elif score < 130: rarity = "E+"
        elif score < 150: rarity = "D-"
        elif score < 170: rarity = "D"
        elif score < 190: rarity = "D+"
        elif score < 210: rarity = "C-"
        elif score < 230: rarity = "C"
        elif score < 250: rarity = "C+"
        elif score < 270: rarity = "B-"
        elif score < 290: rarity = "B"
        elif score < 310: rarity = "B+"
        elif score < 330: rarity = "A-"
        elif score < 350: rarity = "A"
        elif score < 370: rarity = "A+"
        elif score < 390: rarity = "S-"
        elif score < 420: rarity = "S"
        elif score < 450: rarity = "S+"
        elif score < 500: rarity = "SS"
        else: rarity = "SSS"

        eq_type = random.choice(TYPES)
        mult = RARITY_MULTS[rarity]
        
        base_atk = base_def = base_hp = base_spd = 0
        crit = dodge = armor_pen = 0.0
        scale = int(10 * mult)
        
        if eq_type == "Weapon":
            base_atk = scale * random.randint(1, 3)
            base_spd = int(scale * random.uniform(0, 0.5))
            if random.random() < 0.3: crit = random.uniform(0.01, 0.05) * mult
            if random.random() < 0.2: armor_pen = random.uniform(0.01, 0.05) * mult
        elif eq_type == "Armor":
            base_def = scale * random.randint(1, 3)
            base_hp = scale * random.randint(3, 8)
        else:
            base_atk = int(scale * random.uniform(0.5, 1.5))
            base_def = int(scale * random.uniform(0.5, 1.5))
            base_spd = int(scale * random.uniform(0.5, 1.5))
            if random.random() < 0.4: dodge = random.uniform(0.01, 0.05) * mult
            
        adjectives = {"F-": "Broken", "F": "Rusted", "F+": "Chipped", "E-": "Poor", "E": "Basic", "E+": "Sturdy", "D-": "Standard", "D": "Polished", "D+": "Heavy", "C-": "Fine", "C": "Refined", "C+": "Balanced", "B-": "Masterwork", "B": "Exceptional", "B+": "Flawless", "A-": "Epic", "A": "Legendary", "A+": "Mythic", "S-": "Divine", "S": "Godly", "S+": "Transcendent", "SS": "Omnipotent", "SSS": "Absolute"}
        adj = adjectives.get(rarity, rarity)
        name = f"{adj} {eq_type}"

        cursor = conn.execute(
            "INSERT INTO equipment (name, type, rarity, level, base_atk, base_def, base_hp, base_spd, crit_chance, dodge_chance, armor_pen) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (name, eq_type, rarity, level, base_atk, base_def, base_hp, base_spd, crit, dodge, armor_pen)
        )
        return {"id": cursor.lastrowid, "name": name, "type": eq_type, "rarity": rarity}

def generate_equipment_drop(floor_number: int, is_boss: bool = False, drop_bonus: float = 0.0) -> dict | None:
    # Base chance: 10% on normal floors, 100% on bosses
    base_chance = 1.0 if is_boss else 0.10
    total_chance = min(1.0, base_chance + drop_bonus)
    
    if random.random() > total_chance:
        return None
        
    score = floor_number * 3 + random.randint(0, 50)
    if is_boss:
        score += 100
        
    if score < 30: rarity = "F-"
    elif score < 50: rarity = "F"
    elif score < 70: rarity = "F+"
    elif score < 90: rarity = "E-"
    elif score < 110: rarity = "E"
    elif score < 130: rarity = "E+"
    elif score < 150: rarity = "D-"
    elif score < 170: rarity = "D"
    elif score < 190: rarity = "D+"
    elif score < 210: rarity = "C-"
    elif score < 230: rarity = "C"
    elif score < 250: rarity = "C+"
    elif score < 270: rarity = "B-"
    elif score < 290: rarity = "B"
    elif score < 310: rarity = "B+"
    elif score < 330: rarity = "A-"
    elif score < 350: rarity = "A"
    elif score < 370: rarity = "A+"
    elif score < 390: rarity = "S-"
    elif score < 420: rarity = "S"
    elif score < 450: rarity = "S+"
    elif score < 500: rarity = "SS"
    elif score < 600: rarity = "SSS"
    else: rarity = "Z" # Z can only drop on extreme floors from bosses
    
    eq_type = random.choice(TYPES)
    mult = RARITY_MULTS[rarity]
    
    base_atk = base_def = base_hp = base_spd = 0
    crit = dodge = armor_pen = 0.0
    scale = int(10 * mult)
    
    if eq_type == "Weapon":
        base_atk = scale * random.randint(1, 3)
        base_spd = int(scale * random.uniform(0, 0.5))
        if random.random() < 0.3: crit = random.uniform(0.01, 0.05) * mult
        if random.random() < 0.2: armor_pen = random.uniform(0.01, 0.05) * mult
    elif eq_type == "Armor":
        base_def = scale * random.randint(1, 3)
        base_hp = scale * random.randint(3, 8)
    else:
        base_atk = int(scale * random.uniform(0.5, 1.5))
        base_def = int(scale * random.uniform(0.5, 1.5))
        base_spd = int(scale * random.uniform(0.5, 1.5))
        if random.random() < 0.4: dodge = random.uniform(0.01, 0.05) * mult
        
    adjectives = {"F-": "Broken", "F": "Rusted", "F+": "Chipped", "E-": "Poor", "E": "Basic", "E+": "Sturdy", "D-": "Standard", "D": "Polished", "D+": "Heavy", "C-": "Fine", "C": "Refined", "C+": "Balanced", "B-": "Masterwork", "B": "Exceptional", "B+": "Flawless", "A-": "Epic", "A": "Legendary", "A+": "Mythic", "S-": "Divine", "S": "Godly", "S+": "Transcendent", "SS": "Omnipotent", "SSS": "Absolute", "Z": "Eldritch"}
    adj = adjectives.get(rarity, rarity)
    name = f"{adj} {eq_type}"

    with db() as conn:
        cursor = conn.execute(
            "INSERT INTO equipment (name, type, rarity, level, base_atk, base_def, base_hp, base_spd, crit_chance, dodge_chance, armor_pen) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (name, eq_type, rarity, max(1, floor_number // 5), base_atk, base_def, base_hp, base_spd, crit, dodge, armor_pen)
        )
        return {"id": cursor.lastrowid, "name": name, "type": eq_type, "rarity": rarity}
