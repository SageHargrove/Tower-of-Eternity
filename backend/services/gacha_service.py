import random
import math

# Pull weights — strict percentages (out of 100000 total). Steeply
# exponential by design: the game should start heavily 1★/2★-focused, with
# higher rarities reading as a genuine lottery rather than a routine pull.
# Evolution (see routers/heroes.py promote_hero) is the intended way out of
# low rarity, not re-rolling — this curve is what makes that path matter.
RARITY_WEIGHTS = {
    1: 80000, # 80.000%
    2: 15000, # 15.000%
    3: 3900,  # 3.900%
    4: 1000,  # 1.000%
    5: 80,    # 0.080%
    6: 15,    # 0.015%
    7: 5,     # 0.005%
}

TOTAL_WEIGHT = sum(RARITY_WEIGHTS.values())

def pull_rarity(min_star: int = 1, max_star: int = 7) -> int:
    """Roll a birth star rarity using weighted RNG, optionally restricted to
    a [min_star, max_star] window (gold pulls are capped at 1-4★, gem pulls
    at 2-7★ — see /gacha/pull). Re-normalizes against just that subset of
    RARITY_WEIGHTS rather than clamping the unrestricted roll, so the
    relative odds between the allowed stars stay proportional to their
    original weights instead of getting distorted by clamping."""
    allowed = {s: w for s, w in RARITY_WEIGHTS.items() if min_star <= s <= max_star}
    total = sum(allowed.values())
    roll = random.uniform(0, total)
    cumulative = 0
    for star, weight in allowed.items():
        cumulative += weight
        if roll <= cumulative:
            return star
    return min_star

# Health is no longer its own rolled stat — Endurance (the old Defense slot)
# now drives it directly, so a hero's effective tankiness is one number, not
# two independently-rolled ones. See HP_FLOOR/HP_PER_ENDURANCE below.
HP_FLOOR = 20
HP_PER_ENDURANCE = 12

def health_from_endurance(endurance: int) -> int:
    return HP_FLOOR + int(endurance) * HP_PER_ENDURANCE

# Mana is the same kind of derived stat as Health-from-Endurance — not its
# own rolled value, computed at combat time from Intelligence/Willpower.
MANA_FLOOR = 20
MANA_PER_INT = 4
MANA_PER_WIL = 2

def mana_from_stats(intelligence: int, willpower: int) -> int:
    return MANA_FLOOR + int(intelligence) * MANA_PER_INT + int(willpower) * MANA_PER_WIL

def generate_base_stats(birth_star: int) -> dict:
    """
    Base stats scale with birth star, but not linearly.
    High birth star = strong start, less room for surprise growth.
    """
    base = {
        1: {"strength": 8,  "intelligence": 4,  "endurance": 5,  "agility": 9,  "willpower": 6,  "luck": 5},
        2: {"strength": 10, "intelligence": 5,  "endurance": 6,  "agility": 10, "willpower": 7,  "luck": 6},
        3: {"strength": 13, "intelligence": 7,  "endurance": 8,  "agility": 11, "willpower": 9,  "luck": 7},
        4: {"strength": 17, "intelligence": 9,  "endurance": 10, "agility": 12, "willpower": 12, "luck": 8},
        5: {"strength": 22, "intelligence": 12, "endurance": 14, "agility": 14, "willpower": 16, "luck": 9},
        6: {"strength": 30, "intelligence": 16, "endurance": 18, "agility": 16, "willpower": 21, "luck": 10},
        7: {"strength": 42, "intelligence": 22, "endurance": 26, "agility": 20, "willpower": 28, "luck": 12},
    }
    stats = base[birth_star].copy()
    # Add some variance per hero (+/- 10%)
    for key in stats:
        variance = random.uniform(0.9, 1.1)
        stats[key] = max(1, int(stats[key] * variance))
    # defense is the legacy column name still read by a few old call sites —
    # kept in sync with endurance rather than removed, see database.py migration notes.
    stats["defense"] = stats["endurance"]
    stats["max_health"] = health_from_endurance(stats["endurance"])
    stats["health"] = stats["max_health"]
    return stats

# Generation gives every hero a class-neutral STR/INT split — a Mage would
# otherwise roll with more raw muscle than magic, which makes no sense once
# class is known. Lean shifts points between STR and INT (positive = more
# physical, negative = more magical) without changing their combined total,
# so a class's overall power budget at a given star stays the same — it's
# reshuffled, not boosted.
CLASS_STAT_LEAN = {
    "Warrior": 0.40, "Spearman": 0.35, "Thief": 0.30, "Archer": 0.30,
    "Mage": -0.45, "Spellsword": -0.05, "Acolyte": -0.35, "Priest": -0.40,
    "Tactician": -0.20, "Scout": 0.15, "Blacksmith": 0.20, "Medic": -0.25,
    "Quartermaster": -0.10, "Farmer": 0.10, "Merchant": -0.10,
    "Alchemist": -0.30, "Magic Engineer": -0.30,
}

def apply_class_stat_bias(stats: dict, hero_class: str) -> dict:
    lean = CLASS_STAT_LEAN.get(hero_class, 0.0)
    if lean == 0.0:
        return stats
    total = stats["strength"] + stats["intelligence"]
    shift = int(total * abs(lean) * 0.5)
    if lean > 0:
        stats["strength"] += shift
        stats["intelligence"] = max(1, stats["intelligence"] - shift)
    else:
        stats["intelligence"] += shift
        stats["strength"] = max(1, stats["strength"] - shift)
    return stats

# Talent has NO ceiling — a 0-100 scale can't fit the "genuine 1-in-a-
# million prodigy" the brief asked for without either capping it (defeats
# the point) or making the cap meaningless (a "200 out of 100"). Instead,
# every star gets a guaranteed FLOOR, then an unbounded exponential
# "bonus" roll on top, same shape for every star rank. That second part is
# what makes the headline trick work: a 1★'s bonus roll alone has *exactly
# the same odds* of reaching any given height as a 7★'s bonus roll does —
# the only thing star rank buys is a higher starting point. A 1★ landing
# 137+ purely from its own bonus (no floor to help it) is precisely as
# rare as a 7★'s GUARANTEED floor — i.e. a real, math-backed "1 in 900,000
# talent on a 1★" moment, not a flavor-text exaggeration.
#
# Floors below are TALENT_TAIL_SCALE * ln(rarity), so each one IS that
# rarity within the same exponential distribution every bonus roll uses
# (see _roll_talent) — this is also why outliers are unbounded: an
# exponential tail never hits a wall, it just keeps getting rarer.
# Rarity anchors are clean powers of 10 (10, 100, 1k, 10k, 100k, 1M) so
# 7★'s floor lands on exactly 1-in-1,000,000 as requested, and every other
# star's floor falls out of the same formula rather than being hand-picked.
TALENT_TAIL_SCALE = 10.0
TALENT_FLOOR = {
    1: 0,                                    # no guarantee — full open-ended range
    2: round(TALENT_TAIL_SCALE * math.log(10)),         # ~1-in-10
    3: round(TALENT_TAIL_SCALE * math.log(100)),        # ~1-in-100
    4: round(TALENT_TAIL_SCALE * math.log(1_000)),      # ~1-in-1,000
    5: round(TALENT_TAIL_SCALE * math.log(10_000)),     # ~1-in-10,000
    6: round(TALENT_TAIL_SCALE * math.log(100_000)),    # ~1-in-100,000
    7: round(TALENT_TAIL_SCALE * math.log(1_000_000)),  # ~1-in-1,000,000
}

def _roll_talent(birth_star: int) -> float:
    floor = TALENT_FLOOR.get(birth_star, 0)
    bonus = random.expovariate(1.0 / TALENT_TAIL_SCALE)
    return floor + bonus

def generate_aptitudes(birth_star: int) -> dict:
    """
    Hidden aptitudes drive how steeply a hero's stats grow per level — not
    their current power. One overall talent roll (_roll_talent) sets the
    hero's "true" talent; each of the 6 aptitudes wobbles a little around
    that core value rather than rolling fully independently, so
    talent_score (level_service.py, the average of 5 of these) reflects
    the same roll instead of compounding into a far-rarer separate event.
    """
    base = _roll_talent(birth_star)
    return {f"apt_{apt}": max(0, round(base + random.uniform(-8, 8)))
            for apt in ["combat", "tactical", "survival", "mental", "leadership", "diligence"]}

def get_pull_cost() -> int:
    return 100  # gold per pull, can expand to pity system later

EQUIPMENT_PULL_COST = {"gold": 500, "gem": 150}
# Gold pulls: D-B tier (cheap, common gear). Gem pulls: C-S tier (pricier,
# meaningfully better floor). SS/SSS/Z are never available from any gacha
# pull either way — crafting and rare boss/high-floor drops only.
EQUIPMENT_PULL_ODDS = {
    "gold": [("D-", "D", "D+", 0.55), ("C-", "C", "C+", 0.35), ("B-", "B", "B+", 0.10)],
    "gem":  [("C-", "C", "C+", 0.45), ("B-", "B", "B+", 0.40), ("A-", "A", "A+", 0.12), ("S-", "S", "S+", 0.03)],
}

def pull_equipment_gacha(conn, currency: str = "gold") -> dict:
    from services.equipment_service import _roll_equipment_stats, RARITY_MULTS, EQUIPMENT_ADJECTIVES
    import random

    currency = currency if currency in EQUIPMENT_PULL_COST else "gold"
    cost = EQUIPMENT_PULL_COST[currency]
    col = "gems" if currency == "gem" else "gold"
    base = conn.execute(f"SELECT {col} FROM base WHERE id = 1").fetchone()
    if base[col] < cost:
        raise ValueError(f"Not enough {col}.")
    conn.execute(f"UPDATE base SET {col} = {col} - ? WHERE id = 1", (cost,))

    roll = random.random()
    cumulative = 0.0
    tiers = EQUIPMENT_PULL_ODDS[currency]
    rarity = tiers[-1][1]  # fallback to the top tier's middle sub-grade
    for *grades, weight in tiers:
        cumulative += weight
        if roll <= cumulative:
            rarity = random.choice(grades)
            break

    eq_type = random.choice(["Weapon", "Armor", "Accessory"])
    mult = RARITY_MULTS[rarity]
    stats = _roll_equipment_stats(eq_type, mult)
    name = f"{EQUIPMENT_ADJECTIVES.get(rarity, rarity)} {eq_type}"

    return {
        "name": name, "type": eq_type, "rarity": rarity, "level": 1,
        **stats,
    }
