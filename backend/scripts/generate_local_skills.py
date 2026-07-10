import json
import os
import sys
import random

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.class_service import ALL_CLASSES

# Existing kits we don't need to generate
EXISTING_KITS = {
    "Rookie", "Squire", "Thief", "Acolyte", "Apprentice", "Archer",
    "Knight", "Assassin", "Cleric", "Sorcerer", "Ranger",
    "Paladin", "Nightblade", "High Priest", "Archmage", "Sniper",
    "Berserker", "Druid", "Necromancer", "Bard", "Monk"
}

# Class archetypes for skill generation
CLASS_ARCHETYPES = {
    # Combat/Physical classes
    "Warrior": "melee",
    "Spearman": "melee_ranged",
    "Thief": "assassin",
    "Archer": "ranged",

    # Magic classes
    "Mage": "elemental",
    "Sorcerer": "elemental",
    "Warlock": "dark",
    "Necromancer": "dark",
    "Summoner": "summoner",

    # Hybrid
    "Spellsword": "hybrid",
    "Eldritch Knight": "hybrid",
    "Rune Blade": "hybrid",

    # Support/Healing
    "Acolyte": "support",
    "Cleric": "support",
    "Bard": "support",
    "Druid": "nature",
    "Monk": "martial",

    # Specialized
    "Tactician": "support",
    "Scout": "ranged",
    "Medic": "support",
    "Quartermaster": "support",
    "Farmer": "nature",
    "Blacksmith": "utility",
    "Chef": "utility",
    "Merchant": "utility",
    "Alchemist": "utility",
    "Priest": "support",
}

def get_archetype(class_name):
    """Determine archetype for a class based on keywords and existing archetypes"""
    # Check if we have a direct mapping
    if class_name in CLASS_ARCHETYPES:
        return CLASS_ARCHETYPES[class_name]

    # Infer from class name
    name_lower = class_name.lower()

    if any(x in name_lower for x in ['knight', 'warrior', 'berserker', 'templar', 'paladin', 'crusader']):
        return "melee"
    elif any(x in name_lower for x in ['archer', 'sniper', 'ranger', 'crossbow', 'marksman']):
        return "ranged"
    elif any(x in name_lower for x in ['assassin', 'rogue', 'ninja', 'shadow', 'spy']):
        return "assassin"
    elif any(x in name_lower for x in ['mage', 'sorcerer', 'wizard', 'elementalist', 'archmage']):
        return "elemental"
    elif any(x in name_lower for x in ['warlock', 'demonolog', 'voidwalker', 'lich', 'necromancer']):
        return "dark"
    elif any(x in name_lower for x in ['summoner', 'conjurer']):
        return "summoner"
    elif any(x in name_lower for x in ['spellsword', 'rune', 'eldritch']):
        return "hybrid"
    elif any(x in name_lower for x in ['cleric', 'priest', 'bishop', 'medic', 'surgeon', 'healer']):
        return "support"
    elif any(x in name_lower for x in ['bard', 'troubadour', 'maestro']):
        return "support"
    elif any(x in name_lower for x in ['druid', 'archdruid', 'nature', 'farmer']):
        return "nature"
    elif any(x in name_lower for x in ['monk', 'martial', 'master']):
        return "martial"
    elif any(x in name_lower for x in ['tactician', 'strategist', 'commander', 'general']):
        return "support"
    elif any(x in name_lower for x in ['smith', 'weaponsmith', 'armorer', 'artificer', 'forge']):
        return "utility"
    elif any(x in name_lower for x in ['chef', 'alchemist', 'apothecary', 'merchant', 'trader']):
        return "utility"
    else:
        return "melee"  # default

def generate_skill(class_name, skill_index, rarity, skill_type, archetype):
    """Generate a single skill with realistic values"""
    random.seed(hash((class_name, skill_index)) % (2**32))  # Deterministic randomness

    # Common stat modifiers for passives
    stat_modifiers = {
        'str': 0.10, 'int': 0.10, 'agi': 0.10, 'hlt': 0.10,
        'crit': 0.08, 'dodge': 0.08, 'armor_pen': 0.15,
        'regen': 0.05, 'dmg_reduction': 0.12
    }

    # Active skill templates by archetype and rarity
    active_templates = {
        "melee": {
            "common": [
                {"name": "Slash", "mana": 15, "cooldown": 2, "target": "one_enemy", "power": 1.5, "stat": "strength"},
                {"name": "Cleave", "mana": 20, "cooldown": 3, "target": "random_enemies", "power": 1.2, "stat": "strength", "target_count": 2},
                {"name": "Charge", "mana": 18, "cooldown": 2, "target": "one_enemy", "power": 1.8, "stat": "strength"},
            ],
            "uncommon": [
                {"name": "Whirlwind", "mana": 30, "cooldown": 4, "target": "all_enemies", "power": 1.0, "stat": "strength"},
                {"name": "Rending Strike", "mana": 25, "cooldown": 3, "target": "one_enemy", "power": 2.0, "stat": "strength", "debuff": "bleed"},
            ],
            "rare": [
                {"name": "Execute", "mana": 40, "cooldown": 4, "target": "one_enemy", "power": 2.5, "stat": "strength", "execute": True},
                {"name": "Titan's Blow", "mana": 35, "cooldown": 3, "target": "all_enemies", "power": 1.8, "stat": "strength"},
            ],
        },
        "ranged": {
            "common": [
                {"name": "Arrow Shot", "mana": 12, "cooldown": 1, "target": "one_enemy", "power": 1.2, "stat": "agility"},
                {"name": "Multi-Shot", "mana": 18, "cooldown": 3, "target": "random_enemies", "power": 1.0, "stat": "agility", "target_count": 3},
                {"name": "Piercing Shot", "mana": 15, "cooldown": 2, "target": "one_enemy", "power": 1.5, "stat": "agility", "armor_pen": True},
            ],
            "uncommon": [
                {"name": "Barrage", "mana": 28, "cooldown": 4, "target": "all_enemies", "power": 0.9, "stat": "agility"},
                {"name": "Snipe", "mana": 20, "cooldown": 2, "target": "highest_hp_enemy", "power": 2.2, "stat": "agility"},
            ],
        },
        "assassin": {
            "common": [
                {"name": "Stab", "mana": 12, "cooldown": 2, "target": "one_enemy", "power": 1.3, "stat": "agility", "crit": True},
                {"name": "Poison Strike", "mana": 15, "cooldown": 3, "target": "one_enemy", "power": 1.0, "stat": "agility", "status": "poison"},
                {"name": "Ambush", "mana": 18, "cooldown": 2, "target": "one_enemy", "power": 2.0, "stat": "agility"},
            ],
            "uncommon": [
                {"name": "Death Mark", "mana": 25, "cooldown": 4, "target": "one_enemy", "power": 1.5, "stat": "agility", "execute": True},
            ],
        },
        "elemental": {
            "common": [
                {"name": "Fireball", "mana": 20, "cooldown": 2, "target": "all_enemies", "power": 1.2, "stat": "intelligence"},
                {"name": "Frost Bolt", "mana": 15, "cooldown": 2, "target": "one_enemy", "power": 1.5, "stat": "intelligence", "status": "freeze"},
                {"name": "Lightning Strike", "mana": 18, "cooldown": 3, "target": "random_enemies", "power": 1.4, "stat": "intelligence", "target_count": 2},
            ],
            "uncommon": [
                {"name": "Meteor", "mana": 35, "cooldown": 5, "target": "all_enemies", "power": 1.8, "stat": "intelligence"},
                {"name": "Blizzard", "mana": 30, "cooldown": 4, "target": "all_enemies", "power": 1.3, "stat": "intelligence", "status": "freeze"},
            ],
        },
        "dark": {
            "common": [
                {"name": "Shadow Bolt", "mana": 18, "cooldown": 2, "target": "one_enemy", "power": 1.4, "stat": "intelligence"},
                {"name": "Drain Life", "mana": 20, "cooldown": 3, "target": "one_enemy", "power": 1.2, "stat": "intelligence", "lifesteal": True},
                {"name": "Curse", "mana": 15, "cooldown": 2, "target": "one_enemy", "power": 0.8, "stat": "intelligence", "status": "curse"},
            ],
        },
        "support": {
            "common": [
                {"name": "Heal", "mana": 20, "cooldown": 1, "target": "all_allies", "heal": 1.2, "stat": "intelligence"},
                {"name": "Cleanse", "mana": 25, "cooldown": 2, "target": "all_allies", "cleanse": True},
                {"name": "Blessing", "mana": 18, "cooldown": 3, "target": "all_allies", "buff": "all"},
            ],
            "uncommon": [
                {"name": "Revival", "mana": 40, "cooldown": 5, "target": "dead_ally", "revive": True},
            ],
        },
    }

    # Skill ID and base name
    skill_id = f"{class_name.lower().replace(' ', '_')}_{skill_type}_{skill_index}"

    # Generate passive skills
    if skill_type == "passive":
        modifiers = []

        if rarity == "common":
            # Common passives: simple stat boosts
            mod_key = random.choice(list(stat_modifiers.keys()))
            modifiers.append({mod_key: stat_modifiers[mod_key]})
        elif rarity == "uncommon":
            # Uncommon: multiple small boosts or one conditional
            if random.random() < 0.5:
                mod_key = random.choice(list(stat_modifiers.keys()))
                modifiers.append({mod_key: stat_modifiers[mod_key] * 1.5})
            else:
                modifiers.append({"triggers": [{"event": "on_kill", "chance": 0.5, "name": "Trigger"}]})
        elif rarity == "rare":
            # Rare: strong passive or conditional
            if random.random() < 0.6:
                modifiers.append({"triggers": [{"event": "on_hit_taken", "chance": 0.4, "name": "Counter"}]})
            else:
                modifiers.append({"all_pct": 0.15})
        elif rarity == "epic":
            # Epic: very strong conditional or defensive
            modifiers.append({"triggers": [{"event": "on_low_hp", "chance": 0.8, "name": "Guardian"}]})
        else:  # legendary
            # Legendary: game-changing passive
            modifiers.append({"death_save": 1})

        return {
            "id": skill_id,
            "name": f"{archetype.title()} Mastery {skill_index}",
            "type": "passive",
            "rarity": rarity,
            "desc": f"Passive enhancement for {class_name}",
            "effect": modifiers[0] if modifiers else {"str_pct": 0.05}
        }

    # Generate active skills
    else:
        # Use templates or create a generic one
        archetype_lower = archetype.lower()
        if archetype_lower in active_templates and rarity in active_templates[archetype_lower]:
            template = random.choice(active_templates[archetype_lower][rarity])

            actions = [{"kind": "damage", "power": template.get("power", 1.5), "stat": template.get("stat", "strength")}]

            if template.get("debuff"):
                actions.append({"kind": "status", "status": template["debuff"], "duration": 2, "magnitude": 0.3})
            elif template.get("status"):
                actions.append({"kind": "status", "status": template["status"], "duration": 2, "magnitude": 0.3})
            elif template.get("buff"):
                actions.append({"kind": "buff", "stat": template["buff"], "pct": 0.3, "duration": 2})
            elif template.get("cleanse"):
                actions = [{"kind": "cleanse", "count": 3}]
            elif template.get("revive"):
                actions = [{"kind": "revive", "pct": 0.5}]
            elif template.get("heal"):
                actions = [{"kind": "heal", "heal_power": template.get("heal", 1.2), "stat": "intelligence"}]
            elif template.get("lifesteal"):
                actions[0]["lifesteal"] = 0.3
            elif template.get("armor_pen"):
                actions[0]["ignore_def"] = 0.5
            elif template.get("crit"):
                actions[0]["guaranteed_crit"] = True
            elif template.get("execute"):
                actions[0]["execute_threshold"] = 0.3
                actions[0]["execute_bonus"] = 0.5

            return {
                "id": skill_id,
                "name": template.get("name", f"Skill {skill_index}"),
                "type": "active",
                "rarity": rarity,
                "desc": f"Active skill for {class_name}",
                "effect": {
                    "mana_cost": template.get("mana", 20),
                    "cooldown": template.get("cooldown", 2),
                    "target": template.get("target", "one_enemy"),
                    "actions": actions
                }
            }

        # Default active skill
        return {
            "id": skill_id,
            "name": f"{class_name} Attack",
            "type": "active",
            "rarity": rarity,
            "desc": f"Active attack for {class_name}",
            "effect": {
                "mana_cost": 20,
                "cooldown": 2,
                "target": "one_enemy",
                "actions": [{"kind": "damage", "power": 1.5, "stat": "strength"}]
            }
        }

def generate_class_skills(class_name):
    """Generate exactly 30 skills for a class with proper distribution"""
    archetype = get_archetype(class_name)
    skills = []

    # Skill distribution: 10 Common, 8 Uncommon, 6 Rare, 4 Epic, 2 Legendary
    distribution = [
        ("common", 10),
        ("uncommon", 8),
        ("rare", 6),
        ("epic", 4),
        ("legendary", 2),
    ]

    skill_index = 0
    for rarity, count in distribution:
        # Ensure each rarity has both active and passive
        # Most skills should be passive
        active_count = 1 if count >= 2 else 0
        passive_count = count - active_count

        # Generate actives for this rarity
        for i in range(active_count):
            skill = generate_skill(class_name, skill_index, rarity, "active", archetype)
            skills.append(skill)
            skill_index += 1

        # Generate passives for this rarity
        for i in range(passive_count):
            skill = generate_skill(class_name, skill_index, rarity, "passive", archetype)
            skills.append(skill)
            skill_index += 1

    # Shuffle to randomize order (but keep deterministic)
    random.seed(hash(class_name) % (2**32))
    random.shuffle(skills)

    return {
        "class_name": class_name,
        "skills": skills
    }

def get_missing_classes():
    """Find classes that still need generation"""
    generated_classes = set()

    # Load already generated
    out_file = os.path.join(os.path.dirname(__file__), "generated_skills.json")
    if os.path.exists(out_file):
        try:
            with open(out_file, "r") as f:
                data = json.load(f)
                for c in data:
                    generated_classes.add(c["class_name"])
        except:
            pass

    missing = []
    for cls in ALL_CLASSES:
        if cls not in EXISTING_KITS and cls not in generated_classes:
            missing.append(cls)

    return sorted(missing)

def main():
    missing = get_missing_classes()
    print(f"Generating skills for {len(missing)} missing classes...")

    all_results = []

    # Generate skills for each missing class
    for i, class_name in enumerate(missing, 1):
        class_skills = generate_class_skills(class_name)
        all_results.append(class_skills)

        if i % 10 == 0:
            print(f"  Generated {i}/{len(missing)} classes...")

    out_file = os.path.join(os.path.dirname(__file__), "generated_skills.json")

    # Load existing and combine
    if os.path.exists(out_file):
        with open(out_file, "r") as f:
            existing_data = json.load(f)
            all_results = existing_data + all_results

    # Save combined results
    with open(out_file, "w") as f:
        json.dump(all_results, f, indent=2)

    print(f"Successfully generated {len(all_results)} class kits total!")
    print(f"Saved to {out_file}")

if __name__ == "__main__":
    main()
