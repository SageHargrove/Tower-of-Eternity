"""Dining Hall cooking — the early-game consumable loop.

The Farm grows raw INGREDIENTS; before the Alchemist Lab ever exists the
Dining Hall can already cook them into simple food consumables (heals/
morale) heroes carry into the Tower. Food reuses the exact same effect
vocabulary as potions (heal_pct / stress_delta / morale_delta), so the
existing equip-consumable slot, in-combat auto-use, and /inventory/use
endpoints all work on it unchanged.

Balance intent: food is CHEAP and weak-to-mid; potions stay the stronger
mid/late-game option so the Alchemist Lab doesn't get obsoleted by soup.
"""

FOOD_CATALOG = [
    {"id": "baked_potato", "name": "Baked Potato", "desc": "Humble, hot, restores 15% of max Health.",
     "effect": {"heal_pct": 0.15}, "ingredients": 4, "min_level": 1},
    {"id": "travelers_rations", "name": "Traveler's Rations", "desc": "Dense trail food — restores 25% of max Health.",
     "effect": {"heal_pct": 0.25}, "ingredients": 7, "min_level": 1},
    {"id": "mandrake_stew", "name": "Mandrake Stew", "desc": "An alchemist's comfort food. Restores 40% max Health and clears 10 stress.",
     "effect": {"heal_pct": 0.4, "stress_delta": -10}, "ingredients": 14, "min_level": 5},
    {"id": "heros_feast", "name": "Hero's Feast", "desc": "A banquet in a box — restores 60% max Health and lifts morale by 10.",
     "effect": {"heal_pct": 0.6, "morale_delta": 10}, "ingredients": 25, "min_level": 10},
]


def cook_food(conn, recipe_id: str, quantity: int = 1, quality_mult: float = 1.0) -> dict:
    """quality_mult is the SEASON THE POT minigame result: 1.0 = auto-resolve
    baseline; up to x3 multiplies the PORTIONS a batch yields; 0 = CATASTROPHE
    (the pot is scorched — ingredients spent, nothing served). Server-clamped."""
    recipe = next((f for f in FOOD_CATALOG if f["id"] == recipe_id), None)
    if not recipe:
        raise ValueError("Unknown recipe.")
    quantity = max(1, min(50, int(quantity)))
    ruined = (quality_mult or 1.0) <= 0.05
    quality = max(0.3, min(3.0, quality_mult or 1.0))

    hall = conn.execute("SELECT id, level FROM facilities WHERE type = 'Dining Hall' AND base_id = 1").fetchone()
    if not hall:
        raise ValueError("Build the Dining Hall first.")
    if hall["level"] < recipe["min_level"]:
        raise ValueError(f"{recipe['name']} needs Dining Hall Lv.{recipe['min_level']}.")

    # A Chef on staff runs a tighter kitchen — 25% fewer ingredients wasted.
    chef = conn.execute("""
        SELECT 1 FROM facility_assignments fa
        JOIN heroes h ON fa.hero_id = h.id
        WHERE fa.facility_id = ? AND h.is_alive = 1 AND h.hero_class IN ('Chef', 'Cook')
    """, (hall["id"],)).fetchone()
    per_unit = recipe["ingredients"]
    if chef:
        per_unit = max(1, int(per_unit * 0.75))
    total_cost = per_unit * quantity

    base = conn.execute("SELECT ingredients FROM base WHERE id = 1").fetchone()
    if base["ingredients"] < total_cost:
        raise ValueError(f"Not enough ingredients. Need {total_cost}, have {base['ingredients']}.")

    conn.execute("UPDATE base SET ingredients = ingredients - ? WHERE id = 1", (total_cost,))
    if ruined:
        return {"cooked": 0, "ruined": True, "item": recipe["name"], "ingredients_spent": total_cost,
                "message": "The pot scorches black — the kitchen fills with smoke, and nothing is served."}
    # quality multiplies the PORTIONS the same ingredients yield
    quantity = max(1, round(quantity * quality))
    existing = conn.execute(
        "SELECT id FROM inventory WHERE item_name = ? AND item_type = 'food'", (recipe["name"],)
    ).fetchone()
    if existing:
        conn.execute("UPDATE inventory SET quantity = quantity + ? WHERE id = ?", (quantity, existing["id"]))
    else:
        conn.execute(
            "INSERT INTO inventory (item_name, item_type, quantity, description) VALUES (?, 'food', ?, ?)",
            (recipe["name"], quantity, recipe["desc"])
        )
    return {"cooked": quantity, "item": recipe["name"], "ingredients_spent": total_cost, "chef_discount": bool(chef)}


def get_cooking_catalog(conn) -> list[dict]:
    hall = conn.execute("SELECT level FROM facilities WHERE type = 'Dining Hall' AND base_id = 1").fetchone()
    hall_level = hall["level"] if hall else 0
    out = []
    for f in FOOD_CATALOG:
        entry = dict(f)
        entry["unlocked"] = hall_level >= f["min_level"]
        out.append(entry)
    return out


# ── Aether refining (Alchemist Lab) ─────────────────────────────────
# The fast-but-paid path to ship fuel: the Skydock condenses Aether slowly
# for free (time_service passive tick); the Lab converts gold + ingredients
# into it on demand.
AETHER_REFINE_COST = {"gold": 400, "ingredients": 20}
AETHER_REFINE_YIELD = 25


def refine_aether(conn, batches: int = 1, quality_mult: float = 1.0) -> dict:
    """quality_mult is THE STILL minigame result: 1.0 = auto-resolve baseline;
    up to x3 multiplies the aether yield; 0 = CATASTROPHE (the condenser
    ruptures — gold and ingredients spent, no aether). Server-clamped."""
    batches = max(1, min(20, int(batches)))
    ruined = (quality_mult or 1.0) <= 0.05
    quality = max(0.3, min(3.0, quality_mult or 1.0))
    lab = conn.execute("SELECT id, level FROM facilities WHERE type = 'Alchemist Lab' AND base_id = 1").fetchone()
    if not lab:
        raise ValueError("Build the Alchemist Lab first.")

    gold_cost = AETHER_REFINE_COST["gold"] * batches
    ing_cost = AETHER_REFINE_COST["ingredients"] * batches
    base = conn.execute("SELECT gold, ingredients FROM base WHERE id = 1").fetchone()
    if base["gold"] < gold_cost:
        raise ValueError(f"Not enough gold. Need {gold_cost}.")
    if base["ingredients"] < ing_cost:
        raise ValueError(f"Not enough ingredients. Need {ing_cost}.")

    if ruined:
        conn.execute("UPDATE base SET gold = gold - ?, ingredients = ingredients - ? WHERE id = 1",
                     (gold_cost, ing_cost))
        return {"refined": 0, "ruined": True, "gold_spent": gold_cost, "ingredients_spent": ing_cost,
                "message": "The condenser ruptures — raw mana vents into the night, and nothing is kept."}

    # Lab level improves the distillation — +2% yield per level; the STILL
    # minigame's quality multiplies the final yield.
    yield_amt = int(AETHER_REFINE_YIELD * batches * (1 + 0.02 * (lab["level"] - 1)) * quality)
    conn.execute(
        "UPDATE base SET gold = gold - ?, ingredients = ingredients - ?, aether = aether + ? WHERE id = 1",
        (gold_cost, ing_cost, yield_amt)
    )
    return {"refined": yield_amt, "gold_spent": gold_cost, "ingredients_spent": ing_cost, "quality": quality}
