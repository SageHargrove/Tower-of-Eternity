import random
import math

# Pull weights — strict percentages (out of 10000 total)
RARITY_WEIGHTS = {
    1: 6000, # 60.00%
    2: 2000, # 20.00%
    3: 1200, # 12.00%
    4: 600,  # 6.00%
    5: 175,  # 1.75%
    6: 20,   # 0.20%
    7: 5,    # 0.05%
}

TOTAL_WEIGHT = sum(RARITY_WEIGHTS.values())

def pull_rarity() -> int:
    """Roll a birth star rarity using weighted RNG."""
    roll = random.uniform(0, TOTAL_WEIGHT)
    cumulative = 0
    for star, weight in RARITY_WEIGHTS.items():
        cumulative += weight
        if roll <= cumulative:
            return star
    return 1

def generate_base_stats(birth_star: int) -> dict:
    """
    Base stats scale with birth star, but not linearly.
    High birth star = strong start, less room for surprise growth.
    """
    base = {
        1: {"hp": 80,  "attack": 8,  "defense": 4,  "speed": 9},
        2: {"hp": 95,  "attack": 10, "defense": 5,  "speed": 10},
        3: {"hp": 115, "attack": 13, "defense": 7,  "speed": 11},
        4: {"hp": 140, "attack": 17, "defense": 9,  "speed": 12},
        5: {"hp": 175, "attack": 22, "defense": 12, "speed": 14},
        6: {"hp": 220, "attack": 30, "defense": 16, "speed": 16},
        7: {"hp": 300, "attack": 42, "defense": 22, "speed": 20},
    }
    stats = base[birth_star].copy()
    # Add some variance per hero (+/- 10%)
    for key in stats:
        variance = random.uniform(0.9, 1.1)
        stats[key] = max(1, int(stats[key] * variance))
    stats["max_hp"] = stats["hp"]
    return stats

def generate_aptitudes(birth_star: int) -> dict:
    """
    Hidden aptitudes. Low rarity can roll prodigies.
    High rarity tends toward average-high with less variance.
    """
    if birth_star <= 2:
        # Wild variance — rags-to-riches potential
        lo, hi = 10, 100
    elif birth_star <= 4:
        lo, hi = 30, 90
    else:
        # High rarity: safer floor but less ceiling surprise
        lo, hi = 50, 85

    aptitudes = {}
    for apt in ["combat", "tactical", "survival", "mental", "leadership"]:
        # Chance of a prodigy spike on any single aptitude
        if random.random() < 0.08:  # 8% chance per stat
            aptitudes[f"apt_{apt}"] = random.randint(90, 100)
        else:
            aptitudes[f"apt_{apt}"] = random.randint(lo, hi)

    return aptitudes

def get_pull_cost() -> int:
    return 100  # gold per pull, can expand to pity system later
