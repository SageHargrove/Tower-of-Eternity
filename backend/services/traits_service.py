import random

TRAITS_POOL = {
    "positive": [
        {"id": "bloodthirsty", "name": "Bloodthirsty", "desc": "Heals 5% HP on kill"},
        {"id": "fast_learner", "name": "Fast Learner", "desc": "Gains 20% more Skill XP"},
        {"id": "prodigy", "name": "Prodigy", "desc": "Incredible talent capacity, rare"},
        {"id": "iron_constitution", "name": "Iron Constitution", "desc": "+10% Max HP, slower fatigue"},
        {"id": "fearless", "name": "Fearless", "desc": "Immune to fear and morale drops"},
    ],
    "neutral": [
        {"id": "stubborn", "name": "Stubborn", "desc": "+10% DEF, -10% SPD"},
        {"id": "reckless", "name": "Reckless", "desc": "+15% ATK, -15% DEF"},
        {"id": "loner", "name": "Loner", "desc": "Stats increased if no synergy group active"},
    ],
    "negative": [
        {"id": "coward", "name": "Cowardly", "desc": "-10% morale loss, flees easily"},
        {"id": "frail", "name": "Frail", "desc": "-10% Max HP"},
        {"id": "slow_learner", "name": "Slow Learner", "desc": "Gains 20% less Skill XP"},
    ]
}

def generate_traits(birth_star: int) -> list[dict]:
    """
    Generate 1-3 random passive gameplay traits.
    Higher star ratings have a slightly better chance of positive traits.
    """
    count = random.choices([1, 2, 3], weights=[60, 30, 10])[0]
    traits = []
    
    # 1/2 stars can have prodigy, just rarer
    weights = {"positive": 30, "neutral": 40, "negative": 30}
    if birth_star >= 3:
        weights = {"positive": 50, "neutral": 40, "negative": 10}
    if birth_star >= 5:
        weights = {"positive": 70, "neutral": 25, "negative": 5}
        
    categories = list(weights.keys())
    cat_weights = list(weights.values())
    
    for _ in range(count):
        cat = random.choices(categories, weights=cat_weights)[0]
        trait = random.choice(TRAITS_POOL[cat]).copy()
        
        # Ensure prodigy is rare even among positive traits
        if trait["id"] == "prodigy" and random.random() > (0.05 * birth_star):
            # Failed the prodigy check, pick a different positive
            trait = random.choice([t for t in TRAITS_POOL["positive"] if t["id"] != "prodigy"]).copy()
            
        if not any(t["id"] == trait["id"] for t in traits):
            traits.append(trait)
            
    return traits
