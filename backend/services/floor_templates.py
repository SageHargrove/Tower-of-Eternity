"""
Floor Templates Service
=======================
Defines mechanical templates for all floor types beyond standard combat.
All outcomes are deterministic — the backend decides everything, LLM only narrates.

Floor types:
  combat   — Standard fight (existing, handled by combat_service)
  event    — Choice encounter (existing, handled by event_service)
  survival — Endure X rounds of waves. Stress/HP drain per round.
  defend   — Protect a point. Enemies try to breach.
  explore  — Risk/reward discovery. Find loot, traps, or materials.
  escort   — Protect an NPC to safety.
  boss     — Every 10th floor. Powerful single enemy.
  rest     — Every floor after boss. Free healing, no combat.
"""

import random

# ─── Floor Type Distribution ───────────────────────────────────────

def get_floor_type(floor_number: int) -> str:
    """Determine floor type based on floor number."""
    # Fixed floors
    if floor_number % 10 == 0:
        return "boss"
    if floor_number % 10 == 5:
        return "miniboss"
    if floor_number % 10 == 1 and floor_number > 1:
        return "rest"

    # Weighted random for other floors
    weights = {
        "combat": 100,
    }

    # Higher floors = more dangerous floor types
    if floor_number > 50:
        weights["combat"] = 100

    types = list(weights.keys())
    wts = list(weights.values())
    return random.choices(types, weights=wts, k=1)[0]


# ─── Survival Floor ────────────────────────────────────────────────

def generate_survival_floor(floor_number: int) -> dict:
    """Generate a survival floor challenge."""
    rounds = min(8, 3 + floor_number // 15)
    enemy_power = 1 + (floor_number * 0.06)

    return {
        "floor_type": "survival",
        "theme": "Waves of enemies pour from every corridor. There is no retreat — only endurance.",
        "rounds": rounds,
        "enemy_power_scale": enemy_power,
        "stress_per_round": random.randint(3, 8),
        "hp_drain_per_round_pct": round(random.uniform(0.02, 0.06), 3),
        "reward": {
            "gold": (random.randint(40, 80) + floor_number * 5) * 3,
            "materials": random.randint(1, 3),
        },
    }


def resolve_survival_floor(template: dict, heroes: list[dict]) -> dict:
    """Resolve a survival floor deterministically."""
    rounds = template["rounds"]
    stress_per = template["stress_per_round"]
    hp_drain = template["hp_drain_per_round_pct"]
    log = []
    hero_results = []

    for hero in heroes:
        h = hero.copy()
        for r in range(rounds):
            hp_loss = int(h["max_hp"] * hp_drain)
            h["hp"] = max(1, h["hp"] - hp_loss)
            h["stress"] = min(100, h.get("stress", 0) + stress_per)

            if h["hp"] <= 1:
                log.append(f"  {h['name']} barely holds on, gasping...")
                break

        hero_results.append({
            "id": h["id"],
            "hp": h["hp"],
            "stress_gained": stress_per * rounds,
            "survived": h["hp"] > 0,
        })
        log.append(f"  {h['name']} endured {rounds} waves. HP: {h['hp']}/{h['max_hp']}")

    all_survived = all(r["survived"] for r in hero_results)

    return {
        "success": all_survived,
        "hero_results": hero_results,
        "reward": template["reward"] if all_survived else {"gold": template["reward"]["gold"] // 2},
        "log": [f"Survival — {rounds} waves of relentless assault."] + log,
        "summary": f"{'All heroes endured.' if all_survived else 'The team was overwhelmed.'}",
    }


# ─── Defend Floor ──────────────────────────────────────────────────

def generate_defend_floor(floor_number: int) -> dict:
    """Generate a defend floor challenge."""
    waves = min(5, 2 + floor_number // 20)
    enemy_power = 1 + (floor_number * 0.07)

    return {
        "floor_type": "defend",
        "theme": "A narrow passage. Behind you, something worth protecting. They're coming.",
        "waves": waves,
        "enemy_power_scale": enemy_power,
        "breach_penalty": {
            "hp_pct": -0.20,
            "morale": -15,
        },
        "reward": {
            "gold": (random.randint(50, 100) + floor_number * 4) * 3,
            "materials": random.randint(1, 2),
        },
    }


def resolve_defend_floor(template: dict, heroes: list[dict]) -> dict:
    """Resolve a defend floor. Team DEF determines breach chance."""
    waves = template["waves"]
    log = []
    breaches = 0

    total_def = sum(h.get("defense", 5) for h in heroes)
    avg_def = total_def / max(1, len(heroes))

    for wave in range(waves):
        # Breach chance decreases with higher team DEF
        breach_threshold = max(0.05, 0.40 - (avg_def * 0.01))
        breached = random.random() < breach_threshold

        if breached:
            breaches += 1
            log.append(f"  Wave {wave+1}: BREACH! Enemies broke through the line!")
        else:
            log.append(f"  Wave {wave+1}: Held the line. The barrier stands.")

    hero_results = []
    for hero in heroes:
        hp_loss = int(hero["max_hp"] * abs(template["breach_penalty"]["hp_pct"]) * breaches)
        morale_loss = template["breach_penalty"]["morale"] * breaches
        hero_results.append({
            "id": hero["id"],
            "hp": max(1, hero["hp"] - hp_loss),
            "morale_delta": morale_loss,
        })

    success = breaches == 0
    partial = breaches < waves

    return {
        "success": success,
        "partial": partial,
        "breaches": breaches,
        "hero_results": hero_results,
        "reward": template["reward"] if success else {
            "gold": template["reward"]["gold"] // (1 + breaches),
        },
        "log": [f"Defend — {waves} waves incoming."] + log,
        "summary": f"{'Perfect defense!' if success else f'{breaches} breach(es). The line wavered.'}",
    }


# ─── Explore Floor ─────────────────────────────────────────────────

def generate_explore_floor(floor_number: int) -> dict:
    """Generate an explore floor with risk/reward choices."""
    return {
        "floor_type": "explore",
        "theme": "The corridor opens into an unexplored chamber. Dust and silence.",
        "discovery_chance": min(0.80, 0.50 + floor_number * 0.005),
        "trap_chance": min(0.35, 0.10 + floor_number * 0.004),
        "choices": [
            {
                "id": "thorough",
                "label": "Search thoroughly",
                "hint": "Better loot, higher risk",
                "discovery_bonus": 0.20,
                "trap_bonus": 0.15,
                "time_cost": 2,
            },
            {
                "id": "quick",
                "label": "Quick sweep",
                "hint": "Safe but less reward",
                "discovery_bonus": -0.10,
                "trap_bonus": -0.10,
                "time_cost": 1,
            },
            {
                "id": "leave",
                "label": "Leave immediately",
                "hint": "Nothing ventured",
                "discovery_bonus": -1.0,
                "trap_bonus": -1.0,
                "time_cost": 0,
            },
        ],
        "loot_table": _exploration_loot_table(floor_number),
    }


def resolve_explore_floor(template: dict, choice_id: str, heroes: list[dict]) -> dict:
    """Resolve an explore floor based on the player's choice."""
    choice = next((c for c in template["choices"] if c["id"] == choice_id), template["choices"][1])
    log = []

    discovery = template["discovery_chance"] + choice["discovery_bonus"]
    trap = template["trap_chance"] + choice["trap_bonus"]

    found_something = random.random() < discovery
    hit_trap = random.random() < trap

    loot = {}
    hero_results = []

    if found_something:
        loot = random.choice(template["loot_table"])
        log.append(f"  Discovery! Found: {loot.get('desc', 'something useful')}")
    else:
        log.append("  The chamber held nothing of value.")

    if hit_trap:
        trap_damage_pct = random.uniform(0.05, 0.15)
        log.append("  A trap springs! The team takes damage.")
        for hero in heroes:
            dmg = int(hero["max_hp"] * trap_damage_pct)
            hero_results.append({
                "id": hero["id"],
                "hp": max(1, hero["hp"] - dmg),
                "stress_gained": random.randint(5, 12),
            })
    else:
        for hero in heroes:
            hero_results.append({
                "id": hero["id"],
                "hp": hero["hp"],
                "stress_gained": choice["time_cost"],
            })

    return {
        "success": found_something,
        "trapped": hit_trap,
        "loot": loot,
        "hero_results": hero_results,
        "log": ["Explore — searching the unknown."] + log,
        "summary": f"{'Found treasure!' if found_something else 'Nothing found.'}{' Trap sprung!' if hit_trap else ''}",
    }


def _exploration_loot_table(floor_number: int) -> list[dict]:
    """Generate possible loot for this floor level."""
    base_gold = (30 + floor_number * 3) * 3
    return [
        {"type": "gold", "amount": random.randint(base_gold, base_gold * 2), "desc": f"{base_gold}-{base_gold*2} gold"},
        {"type": "elemental_stone", "amount": 1, "desc": "Elemental Stone ×1"},
        {"type": "materials", "amount": random.randint(2, 5), "desc": "Tower materials"},
        {"type": "gold", "amount": random.randint(base_gold * 2, base_gold * 3), "desc": f"Large gold cache"},
    ]
    # Higher floors add rarer loot
    # (equipment drops would go here once equipment system exists)


# ─── Escort Floor ──────────────────────────────────────────────────

def generate_escort_floor(floor_number: int) -> dict:
    """Generate an escort floor challenge."""
    npc_names = ["a wounded traveler", "a lost child", "a captured merchant", "a dying scholar"]

    return {
        "floor_type": "escort",
        "theme": f"You find {random.choice(npc_names)} who needs safe passage to the next floor.",
        "npc_hp": 80 + floor_number * 2,
        "ambush_count": min(5, 2 + floor_number // 15),
        "ambush_power": 1 + (floor_number * 0.05),
        "reward": {
            "gold": (random.randint(100, 200) + floor_number * 6) * 3,
            "morale": random.randint(5, 15),
            "materials": random.randint(1, 3),
        },
    }


def resolve_escort_floor(template: dict, heroes: list[dict]) -> dict:
    """Resolve an escort floor. Team ATK/DEF determines if NPC survives."""
    ambushes = template["ambush_count"]
    npc_hp = template["npc_hp"]
    log = []

    total_atk = sum(h.get("attack", 5) for h in heroes)
    total_def = sum(h.get("defense", 5) for h in heroes)

    for i in range(ambushes):
        # Heroes intercept damage based on their total ATK
        intercept_pct = min(0.90, total_atk / (total_atk + 50 * template["ambush_power"]))
        npc_damage = int(30 * template["ambush_power"] * (1 - intercept_pct))
        npc_hp -= npc_damage

        hero_damage_pct = random.uniform(0.03, 0.08)

        if npc_hp > 0:
            log.append(f"  Ambush {i+1}: Intercepted! NPC takes {npc_damage} damage. NPC HP: {npc_hp}")
        else:
            log.append(f"  Ambush {i+1}: The NPC fell. You failed to protect them.")
            break

    npc_survived = npc_hp > 0
    hero_results = []
    for hero in heroes:
        dmg = int(hero["max_hp"] * random.uniform(0.03, 0.08) * ambushes)
        hero_results.append({
            "id": hero["id"],
            "hp": max(1, hero["hp"] - dmg),
            "morale_delta": template["reward"]["morale"] if npc_survived else -10,
        })

    return {
        "success": npc_survived,
        "npc_survived": npc_survived,
        "npc_hp": max(0, npc_hp),
        "hero_results": hero_results,
        "reward": template["reward"] if npc_survived else {"gold": template["reward"]["gold"] // 3},
        "log": [f"Escort — {ambushes} ambushes ahead."] + log,
        "summary": f"{'NPC delivered safely!' if npc_survived else 'The NPC was lost.'}",
    }


# ─── Rest Floor ────────────────────────────────────────────────────

def generate_rest_floor(floor_number: int) -> dict:
    """Generate a rest floor — free healing, no combat."""
    return {
        "floor_type": "rest",
        "theme": "A safe chamber. Water flows from cracks in the stone. Your team can rest.",
        "heal_pct": 0.50,  # 50% HP restored
        "stress_reduction": 20,
        "morale_boost": 15,
    }


def resolve_rest_floor(template: dict, heroes: list[dict]) -> dict:
    """Apply rest floor healing to all heroes."""
    hero_results = []
    for hero in heroes:
        heal = int(hero["max_hp"] * template["heal_pct"])
        new_hp = min(hero["max_hp"], hero["hp"] + heal)
        hero_results.append({
            "id": hero["id"],
            "hp": new_hp,
            "stress_gained": -template["stress_reduction"],
            "morale_delta": template["morale_boost"],
        })

    return {
        "success": True,
        "hero_results": hero_results,
        "reward": {"gold": 0},
        "log": [
            "Rest — the team finds a moment of peace.",
            "  Water is found. Wounds are tended. The silence is a gift.",
            f"  All heroes recover {int(template['heal_pct']*100)}% HP, -{template['stress_reduction']} stress, +{template['morale_boost']} morale.",
        ],
        "summary": "The team rests and recovers.",
    }
