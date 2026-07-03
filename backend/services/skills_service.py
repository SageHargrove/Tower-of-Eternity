"""
Skills Service
==============
Hero skills system with rarity tiers (Common → Legendary).
Heroes gain skills at creation and through progression.

Skills can be:
  - PASSIVE: Always active, modify stats or behavior
  - ACTIVE: Used in combat with cooldowns (AI-controlled)
  - BOSS_DROP: Extremely rare skills only from boss kills

Rarity tiers:
  Common (60%) → Uncommon (25%) → Rare (10%) → Epic (4%) → Legendary (1%)

Class coverage: every one of the 8 combat base classes (Warrior, Spearman,
Thief, Archer, Mage, Magic Engineer, Acolyte, Spellsword), every
support-combat base class that fights even unevolved (Medic, Scout,
Tactician — see class_service.SUPPORT_COMBAT_CLASSES), AND every pure
profession base class (Blacksmith, Alchemist, Chef, Priest, Quartermaster,
Merchant, Farmer) has its own full kit below — the last group never
fights at their literal base name, but every one of their evolutions
does, so the kit matters the moment they evolve. On top of that, every
class's FIRST evolution tier (e.g. Warrior -> Knight/Berserker/Paladin)
gets its own bespoke signature kit, since those are the evolutions
players see constantly.
Second-tier "pinnacle" evolutions (e.g. Knight -> Aegis/Templar) are
numerous (~80 names) and inherit their base lineage's kit via
_LINEAGE_MAP rather than each getting hand-tuned content — a real kit,
just shared with their tier-30 siblings under the same lineage, not the
bland classless GENERIC_SKILLS fallback every one of these used to get.
"""

import random

SKILL_RARITY_WEIGHTS = {
    "common": 60,
    "uncommon": 25,
    "rare": 10,
    "epic": 4,
    "legendary": 1,
}

SKILL_RARITY_COLORS = {
    "common": "#888",
    "uncommon": "#4a9a6a",
    "rare": "#4a7aaa",
    "epic": "#8030c8",
    "legendary": "#c9a84c",
}

# ─── Skill Definitions ─────────────────────────────────────────────
# type: "passive" | "active" | "boss_drop"
# For active skills: cooldown = rounds between uses

SKILL_POOL = {
    # ═══════════════════════════════════════════════════════════════
    # BASE LINEAGE: WARRIOR (frontline tank/bruiser)
    # ═══════════════════════════════════════════════════════════════
    "Warrior": {
        "common": [
            {"id": "iron_skin", "name": "Iron Skin", "type": "passive",
             "desc": "+10% DEF", "effect": {"int_pct": 0.10}},
            {"id": "heavy_strikes", "name": "Heavy Strikes", "type": "passive",
             "desc": "+8% ATK", "effect": {"str_pct": 0.08}},
            {"id": "thick_hide", "name": "Thick Hide", "type": "passive",
             "desc": "+6% Health", "effect": {"hlt_pct": 0.06}},
        ],
        "uncommon": [
            {"id": "shield_wall", "name": "Shield Wall", "type": "active",
             "desc": "Absorb 30% team damage for 2 rounds", "cooldown": 5,
             "effect": {"team_dmg_reduce": 0.30, "duration": 2, "mana_cost": 30}},
            {"id": "battle_cry", "name": "Battle Cry", "type": "passive",
             "desc": "+5% ATK to all frontline allies", "effect": {"team_atk_pct": 0.05}},
            {"id": "scarred_veteran", "name": "Scarred Veteran", "type": "passive",
             "desc": "+8% damage reduction", "effect": {"dmg_reduction_pct": 0.08}},
        ],
        "rare": [
            {"id": "last_stand", "name": "Last Stand", "type": "passive",
             "desc": "When below 20% Health, ATK doubles", "effect": {"low_hp_atk_mult": 2.0, "threshold": 0.20}},
            {"id": "taunt", "name": "Taunt", "type": "active",
             "desc": "Force all enemies to target you for 2 rounds", "cooldown": 4,
             "effect": {"taunt_duration": 2, "mana_cost": 25}},
            {"id": "reckless_swing", "name": "Reckless Swing", "type": "active",
             "desc": "220% ATK single target", "cooldown": 4,
             "effect": {"dmg_pct": 2.2, "single_target": True, "mana_cost": 30}},
            {"id": "adrenaline_rush", "name": "Adrenaline Rush", "type": "active",
             "desc": "Recover 20% of your own max Health", "cooldown": 5,
             "effect": {"self_heal_pct": 0.20, "mana_cost": 25}},
        ],
        "epic": [
            {"id": "undying_will", "name": "Undying Will", "type": "passive",
             "desc": "Survive one killing blow with 1 Health (once per fight)",
             "effect": {"death_save": 1}},
        ],
        "legendary": [
            {"id": "berserker_rage", "name": "Berserker Rage", "type": "passive",
             "desc": "Each kill grants +15% ATK for the rest of combat",
             "effect": {"kill_atk_stack": 0.15}},
        ],
    },
    # KNIGHT — disciplined defender, tier-30 Warrior signature
    "Knight": {
        "common": [
            {"id": "knight_drill", "name": "Drilled Stance", "type": "passive",
             "desc": "+10% DEF, +5% Health", "effect": {"int_pct": 0.10, "hlt_pct": 0.05}},
            {"id": "knight_polish", "name": "Polished Plate", "type": "passive",
             "desc": "+7% damage reduction", "effect": {"dmg_reduction_pct": 0.07}},
        ],
        "uncommon": [
            {"id": "shield_bash", "name": "Shield Bash", "type": "active",
             "desc": "150% ATK, stun the target 1 round", "cooldown": 4,
             "effect": {"dmg_pct": 1.5, "single_target": True, "mana_cost": 30}},
        ],
        "rare": [
            {"id": "guardians_oath", "name": "Guardian's Oath", "type": "active",
             "desc": "Taunt all enemies and reduce team damage taken 25% for 2 rounds", "cooldown": 6,
             "effect": {"taunt_duration": 2, "team_dmg_reduce": 0.25, "mana_cost": 35}},
        ],
        "epic": [
            {"id": "bulwark", "name": "Bulwark", "type": "passive",
             "desc": "+12% damage reduction, +10% physical resist",
             "effect": {"dmg_reduction_pct": 0.12, "physical_resist_pct": 0.10}},
        ],
        "legendary": [
            {"id": "knights_vow", "name": "Knight's Vow", "type": "passive",
             "desc": "Survive one killing blow with 1 Health, then +20% ATK for the rest of the fight",
             "effect": {"death_save": 1, "kill_atk_stack": 0.0}},
        ],
    },
    # BERSERKER — all-in glass cannon, tier-30 Warrior signature
    "Berserker": {
        "common": [
            {"id": "bloodlust", "name": "Bloodlust", "type": "passive",
             "desc": "+12% ATK, -4% Health", "effect": {"str_pct": 0.12, "hlt_pct": -0.04}},
            {"id": "fury", "name": "Fury", "type": "passive",
             "desc": "+6% crit chance", "effect": {"crit_pct": 0.06}},
        ],
        "uncommon": [
            {"id": "rampage", "name": "Rampage", "type": "active",
             "desc": "200% ATK to a single target, heal 15% of damage dealt", "cooldown": 4,
             "effect": {"dmg_pct": 2.0, "single_target": True, "lifesteal_pct": 0.15, "mana_cost": 30}},
        ],
        "rare": [
            {"id": "blood_frenzy", "name": "Blood Frenzy", "type": "passive",
             "desc": "Below 50% Health, +20% ATK", "effect": {"low_hp_atk_mult": 1.2, "threshold": 0.50}},
        ],
        "epic": [
            {"id": "execute", "name": "Execute", "type": "active",
             "desc": "180% ATK, +100% damage if target is below 30% Health", "cooldown": 5,
             "effect": {"dmg_pct": 1.8, "single_target": True, "execute_bonus_pct": 1.0, "execute_threshold": 0.30, "mana_cost": 35}},
        ],
        "legendary": [
            {"id": "unstoppable_rage", "name": "Unstoppable Rage", "type": "passive",
             "desc": "Each kill grants +20% ATK for the rest of combat",
             "effect": {"kill_atk_stack": 0.20}},
        ],
    },
    # PALADIN — holy bruiser/support hybrid, tier-30 Warrior signature
    "Paladin": {
        "common": [
            {"id": "blessed_armor", "name": "Blessed Armor", "type": "passive",
             "desc": "+8% DEF, +5% Health", "effect": {"int_pct": 0.08, "hlt_pct": 0.05}},
            {"id": "righteous_will", "name": "Righteous Will", "type": "passive",
             "desc": "-8% stress gain", "effect": {"stress_reduce": 0.08}},
        ],
        "uncommon": [
            {"id": "lay_on_hands", "name": "Lay on Hands", "type": "active",
             "desc": "Heal the lowest-Health ally for 25% of their max Health", "cooldown": 4,
             "effect": {"heal_pct": 0.25, "mana_cost": 30}},
        ],
        "rare": [
            {"id": "consecration", "name": "Consecration", "type": "active",
             "desc": "Taunt all enemies for 2 rounds and cleanse your own afflictions", "cooldown": 6,
             "effect": {"taunt_duration": 2, "cleanse_self": True, "mana_cost": 35}},
        ],
        "epic": [
            {"id": "divine_shield", "name": "Divine Shield", "type": "active",
             "desc": "Shield the team for 30% damage reduction for 2 rounds", "cooldown": 6,
             "effect": {"team_dmg_reduce": 0.30, "duration": 2, "mana_cost": 40}},
        ],
        "legendary": [
            {"id": "last_rites", "name": "Last Rites", "type": "active",
             "desc": "Revive a fallen ally at 40% Health (once per fight)", "cooldown": 99,
             "effect": {"revive_pct": 0.40, "min_star": 6, "mana_cost": 50}},
        ],
    },

    # ═══════════════════════════════════════════════════════════════
    # BASE LINEAGE: SPEARMAN (reach/pierce DPS)
    # ═══════════════════════════════════════════════════════════════
    "Spearman": {
        "common": [
            {"id": "long_reach", "name": "Long Reach", "type": "passive",
             "desc": "+5% SPD, +5% ATK", "effect": {"agi_pct": 0.05, "str_pct": 0.05}},
            {"id": "piercing_thrust", "name": "Piercing Thrust", "type": "passive",
             "desc": "Ignore 10% of enemy DEF", "effect": {"armor_pen": 0.10}},
            {"id": "drilled_footing", "name": "Drilled Footing", "type": "passive",
             "desc": "+5% Health", "effect": {"hlt_pct": 0.05}},
        ],
        "uncommon": [
            {"id": "sweeping_strike", "name": "Sweeping Strike", "type": "active",
             "desc": "Hit 2 enemies for 80% ATK each", "cooldown": 3,
             "effect": {"multi_target": 2, "dmg_pct": 0.80, "mana_cost": 25}},
            {"id": "rally_the_line", "name": "Rally the Line", "type": "active",
             "desc": "Permanently boost team ATK 8% for the rest of the fight", "cooldown": 7,
             "effect": {"team_buff_pct": 0.08, "buff_stat": "strength", "mana_cost": 35}},
        ],
        "rare": [
            {"id": "impale", "name": "Impale", "type": "active",
             "desc": "300% ATK single target, ignore DEF", "cooldown": 5,
             "effect": {"dmg_pct": 3.0, "ignore_def": True, "mana_cost": 35}},
            {"id": "spear_wall", "name": "Spear Wall", "type": "active",
             "desc": "Reduce team damage taken 20% for 2 rounds", "cooldown": 5,
             "effect": {"team_dmg_reduce": 0.20, "duration": 2, "mana_cost": 30}},
        ],
        "epic": [
            {"id": "phalanx", "name": "Phalanx Formation", "type": "passive",
             "desc": "If adjacent to another Spearman/Warrior, both get +20% DEF",
             "effect": {"adjacent_def_pct": 0.20}},
        ],
        "legendary": [
            {"id": "dragon_lance", "name": "Dragon Lance", "type": "passive",
             "desc": "First strike each combat deals 500% damage",
             "effect": {"first_strike_mult": 5.0}},
        ],
    },
    # LANCER — mobile charger, tier-30 Spearman signature
    "Lancer": {
        "common": [
            {"id": "charge_step", "name": "Charge Step", "type": "passive",
             "desc": "+8% SPD", "effect": {"agi_pct": 0.08}},
            {"id": "lance_grip", "name": "Lance Grip", "type": "passive",
             "desc": "+6% ATK", "effect": {"str_pct": 0.06}},
        ],
        "uncommon": [
            {"id": "charging_lance", "name": "Charging Lance", "type": "active",
             "desc": "180% ATK, ignore 15% DEF", "cooldown": 3,
             "effect": {"dmg_pct": 1.8, "single_target": True, "ignore_def": True, "mana_cost": 25}},
        ],
        "rare": [
            {"id": "momentum", "name": "Momentum", "type": "passive",
             "desc": "+8% crit chance", "effect": {"crit_pct": 0.08}},
        ],
        "epic": [
            {"id": "skewer", "name": "Skewer", "type": "active",
             "desc": "Hit 3 enemies for 100% ATK each", "cooldown": 5,
             "effect": {"multi_target": 3, "dmg_pct": 1.0, "mana_cost": 35}},
        ],
        "legendary": [
            {"id": "wind_lance", "name": "Wind Lance", "type": "passive",
             "desc": "First strike each combat deals 500% damage",
             "effect": {"first_strike_mult": 5.0}},
        ],
    },
    # HALBERDIER — line-control, tier-30 Spearman signature
    "Halberdier": {
        "common": [
            {"id": "wide_arc", "name": "Wide Arc", "type": "passive",
             "desc": "+8% ATK", "effect": {"str_pct": 0.08}},
            {"id": "braced_haft", "name": "Braced Haft", "type": "passive",
             "desc": "+6% damage reduction", "effect": {"dmg_reduction_pct": 0.06}},
        ],
        "uncommon": [
            {"id": "cleaving_sweep", "name": "Cleaving Sweep", "type": "active",
             "desc": "Hit all enemies for 60% ATK", "cooldown": 4,
             "effect": {"aoe": True, "dmg_pct": 0.60, "mana_cost": 30}},
        ],
        "rare": [
            {"id": "anchor_point", "name": "Anchor Point", "type": "active",
             "desc": "Taunt all enemies for 2 rounds", "cooldown": 5,
             "effect": {"taunt_duration": 2, "mana_cost": 25}},
        ],
        "epic": [
            {"id": "halberd_storm", "name": "Halberd Storm", "type": "active",
             "desc": "Hit all enemies for 120% ATK", "cooldown": 6,
             "effect": {"aoe": True, "dmg_pct": 1.2, "mana_cost": 40}},
        ],
        "legendary": [
            {"id": "warlines_end", "name": "Warline's End", "type": "passive",
             "desc": "+20% DEF, +10% physical resist",
             "effect": {"int_pct": 0.20, "physical_resist_pct": 0.10}},
        ],
    },
    # DRAGOON — heavy striker, tier-30 Spearman signature
    "Dragoon": {
        "common": [
            {"id": "heavy_lance", "name": "Heavy Lance", "type": "passive",
             "desc": "+10% ATK", "effect": {"str_pct": 0.10}},
            {"id": "drake_hide", "name": "Drake Hide", "type": "passive",
             "desc": "+8% Health", "effect": {"hlt_pct": 0.08}},
        ],
        "uncommon": [
            {"id": "diving_strike", "name": "Diving Strike", "type": "active",
             "desc": "220% ATK, guaranteed crit", "cooldown": 4,
             "effect": {"dmg_pct": 2.2, "single_target": True, "guaranteed_crit": True, "mana_cost": 30}},
        ],
        "rare": [
            {"id": "wyvern_step", "name": "Wyvern Step", "type": "passive",
             "desc": "+8% dodge chance", "effect": {"dodge_pct": 0.08}},
        ],
        "epic": [
            {"id": "thunder_dive", "name": "Thunder Dive", "type": "active",
             "desc": "300% ATK single target, ignore DEF", "cooldown": 6,
             "effect": {"dmg_pct": 3.0, "ignore_def": True, "mana_cost": 40}},
        ],
        "legendary": [
            {"id": "dragons_descent", "name": "Dragon's Descent", "type": "passive",
             "desc": "Each kill grants +15% ATK for the rest of combat",
             "effect": {"kill_atk_stack": 0.15}},
        ],
    },

    # ═══════════════════════════════════════════════════════════════
    # BASE LINEAGE: THIEF (crit/evasion burst)
    # ═══════════════════════════════════════════════════════════════
    "Thief": {
        "common": [
            {"id": "nimble_feet", "name": "Nimble Feet", "type": "passive",
             "desc": "+10% dodge chance", "effect": {"dodge_pct": 0.10}},
            {"id": "quick_hands", "name": "Quick Hands", "type": "passive",
             "desc": "+10% SPD", "effect": {"agi_pct": 0.10}},
            {"id": "light_steps", "name": "Light Steps", "type": "passive",
             "desc": "+5% crit chance", "effect": {"crit_pct": 0.05}},
            {"id": "evasive_instinct", "name": "Evasive Instinct", "type": "passive",
             "desc": "+6% SPD, +4% dodge chance", "effect": {"agi_pct": 0.06, "dodge_pct": 0.04}},
        ],
        "uncommon": [
            {"id": "backstab", "name": "Backstab", "type": "active",
             "desc": "200% ATK damage, guaranteed crit", "cooldown": 4,
             "effect": {"dmg_pct": 2.0, "single_target": True, "guaranteed_crit": True, "mana_cost": 30}},
            {"id": "vital_strike", "name": "Vital Strike", "type": "active",
             "desc": "150% ATK, heal 25% of damage dealt", "cooldown": 4,
             "effect": {"dmg_pct": 1.5, "single_target": True, "lifesteal_pct": 0.25, "mana_cost": 25}},
        ],
        "rare": [
            {"id": "shadow_step", "name": "Shadow Step", "type": "passive",
             "desc": "30% chance to strike twice per round",
             "effect": {"double_strike": 0.30}},
        ],
        "epic": [
            {"id": "poison_blade", "name": "Poison Blade", "type": "passive",
             "desc": "Attacks apply 3% max Health poison for 3 rounds",
             "effect": {"poison_pct": 0.03, "poison_duration": 3}},
        ],
        "legendary": [
            {"id": "phantom_assassin", "name": "Phantom Assassin", "type": "passive",
             "desc": "If you kill an enemy, become untargetable for 1 round",
             "effect": {"kill_stealth": 1}},
        ],
    },
    # ASSASSIN — single-target execution, tier-30 Thief signature
    "Assassin": {
        "common": [
            {"id": "killers_eye", "name": "Killer's Eye", "type": "passive",
             "desc": "+8% crit chance", "effect": {"crit_pct": 0.08}},
            {"id": "silent_step", "name": "Silent Step", "type": "passive",
             "desc": "+8% dodge chance", "effect": {"dodge_pct": 0.08}},
        ],
        "uncommon": [
            {"id": "garrote", "name": "Garrote", "type": "active",
             "desc": "180% ATK, guaranteed crit", "cooldown": 3,
             "effect": {"dmg_pct": 1.8, "single_target": True, "guaranteed_crit": True, "mana_cost": 25}},
        ],
        "rare": [
            {"id": "mark_for_death", "name": "Mark for Death", "type": "active",
             "desc": "250% ATK, +80% damage if target is below 30% Health", "cooldown": 5,
             "effect": {"dmg_pct": 2.5, "single_target": True, "execute_bonus_pct": 0.80, "execute_threshold": 0.30, "mana_cost": 35}},
        ],
        "epic": [
            {"id": "vanish", "name": "Vanish", "type": "passive",
             "desc": "+15% dodge chance", "effect": {"dodge_pct": 0.15}},
        ],
        "legendary": [
            {"id": "one_inch_punch", "name": "Death's Door", "type": "passive",
             "desc": "If you kill an enemy, become untargetable for 1 round",
             "effect": {"kill_stealth": 1}},
        ],
    },
    # ROGUE — opportunistic skirmisher, tier-30 Thief signature
    "Rogue": {
        "common": [
            {"id": "cutpurse", "name": "Cutpurse Reflexes", "type": "passive",
             "desc": "+8% SPD", "effect": {"agi_pct": 0.08}},
            {"id": "rogue_grit", "name": "Rogue's Grit", "type": "passive",
             "desc": "+5% Health, +4% dodge chance", "effect": {"hlt_pct": 0.05, "dodge_pct": 0.04}},
        ],
        "uncommon": [
            {"id": "dirty_trick", "name": "Dirty Trick", "type": "active",
             "desc": "140% ATK, stun the target 1 round", "cooldown": 4,
             "effect": {"dmg_pct": 1.4, "single_target": True, "mana_cost": 25}},
        ],
        "rare": [
            {"id": "quick_fingers", "name": "Quick Fingers", "type": "passive",
             "desc": "30% chance to strike twice per round",
             "effect": {"double_strike": 0.30}},
        ],
        "epic": [
            {"id": "smoke_bomb", "name": "Smoke Bomb", "type": "active",
             "desc": "Permanently boost own dodge 15% for the rest of the fight, cleanse self", "cooldown": 6,
             "effect": {"team_buff_pct": 0.0, "cleanse_self": True, "mana_cost": 30}},
        ],
        "legendary": [
            {"id": "perfect_getaway", "name": "Perfect Getaway", "type": "passive",
             "desc": "If you kill an enemy, become untargetable for 1 round",
             "effect": {"kill_stealth": 1}},
        ],
    },
    # NINJA — speed/poison hybrid, tier-30 Thief signature
    "Ninja": {
        "common": [
            {"id": "shadow_clone_step", "name": "Shadow Clone Step", "type": "passive",
             "desc": "+10% SPD", "effect": {"agi_pct": 0.10}},
            {"id": "blade_focus", "name": "Blade Focus", "type": "passive",
             "desc": "+6% crit chance", "effect": {"crit_pct": 0.06}},
        ],
        "uncommon": [
            {"id": "kunai_throw", "name": "Kunai Throw", "type": "active",
             "desc": "Hit 2 enemies for 90% ATK each", "cooldown": 3,
             "effect": {"multi_target": 2, "dmg_pct": 0.90, "mana_cost": 25}},
        ],
        "rare": [
            {"id": "venom_strike", "name": "Venom Strike", "type": "passive",
             "desc": "Attacks apply 3% max Health poison for 3 rounds",
             "effect": {"poison_pct": 0.03, "poison_duration": 3}},
        ],
        "epic": [
            {"id": "shadow_clone", "name": "Shadow Clone Jutsu", "type": "passive",
             "desc": "30% chance to strike twice per round",
             "effect": {"double_strike": 0.30}},
        ],
        "legendary": [
            {"id": "art_of_the_unseen", "name": "Art of the Unseen", "type": "passive",
             "desc": "If you kill an enemy, become untargetable for 1 round",
             "effect": {"kill_stealth": 1}},
        ],
    },

    # ═══════════════════════════════════════════════════════════════
    # BASE LINEAGE: ARCHER (ranged crit/AoE)
    # ═══════════════════════════════════════════════════════════════
    "Archer": {
        "common": [
            {"id": "steady_aim", "name": "Steady Aim", "type": "passive",
             "desc": "+10% ATK", "effect": {"str_pct": 0.10}},
            {"id": "keen_eyes", "name": "Keen Eyes", "type": "passive",
             "desc": "+5% crit chance", "effect": {"crit_pct": 0.05}},
            {"id": "fletchers_calm", "name": "Fletcher's Calm", "type": "passive",
             "desc": "+5% dodge chance", "effect": {"dodge_pct": 0.05}},
        ],
        "uncommon": [
            {"id": "volley", "name": "Volley", "type": "active",
             "desc": "Hit all enemies for 50% ATK", "cooldown": 4,
             "effect": {"aoe": True, "dmg_pct": 0.50, "mana_cost": 30}},
            {"id": "piercing_shot", "name": "Piercing Shot", "type": "active",
             "desc": "180% ATK, ignore 15% DEF", "cooldown": 3,
             "effect": {"dmg_pct": 1.8, "single_target": True, "ignore_def": True, "mana_cost": 25}},
        ],
        "rare": [
            {"id": "headshot", "name": "Headshot", "type": "passive",
             "desc": "Crits deal 250% damage instead of 180%",
             "effect": {"crit_mult": 2.5}},
            {"id": "toxic_arrows", "name": "Toxic Arrows", "type": "passive",
             "desc": "Attacks apply 3% max Health poison for 3 rounds",
             "effect": {"poison_pct": 0.03, "poison_duration": 3}},
        ],
        "epic": [
            {"id": "rain_of_arrows", "name": "Rain of Arrows", "type": "active",
             "desc": "Hit all enemies for 120% ATK, +fear check", "cooldown": 6,
             "effect": {"aoe": True, "dmg_pct": 1.2, "fear_check": True, "mana_cost": 40}},
        ],
        "legendary": [
            {"id": "one_shot_one_kill", "name": "One Shot, One Kill", "type": "passive",
             "desc": "20% chance to instantly kill non-boss enemies",
             "effect": {"instant_kill": 0.20}},
        ],
    },
    # SNIPER — precision burst, tier-30 Archer signature
    "Sniper": {
        "common": [
            {"id": "scope_sight", "name": "Scope Sight", "type": "passive",
             "desc": "+8% crit chance", "effect": {"crit_pct": 0.08}},
            {"id": "patient_hand", "name": "Patient Hand", "type": "passive",
             "desc": "+8% ATK", "effect": {"str_pct": 0.08}},
        ],
        "uncommon": [
            {"id": "called_shot", "name": "Called Shot", "type": "active",
             "desc": "220% ATK, guaranteed crit", "cooldown": 4,
             "effect": {"dmg_pct": 2.2, "single_target": True, "guaranteed_crit": True, "mana_cost": 30}},
        ],
        "rare": [
            {"id": "long_shot", "name": "Long Shot", "type": "active",
             "desc": "280% ATK, ignore DEF", "cooldown": 5,
             "effect": {"dmg_pct": 2.8, "single_target": True, "ignore_def": True, "mana_cost": 35}},
        ],
        "epic": [
            {"id": "kill_shot", "name": "Kill Shot", "type": "active",
             "desc": "180% ATK, +100% damage if target below 30% Health", "cooldown": 5,
             "effect": {"dmg_pct": 1.8, "single_target": True, "execute_bonus_pct": 1.0, "execute_threshold": 0.30, "mana_cost": 35}},
        ],
        "legendary": [
            {"id": "headshot_legend", "name": "Dead Center", "type": "passive",
             "desc": "20% chance to instantly kill non-boss enemies",
             "effect": {"instant_kill": 0.20}},
        ],
    },
    # RANGER — wilderness skirmisher, tier-30 Archer signature
    "Ranger": {
        "common": [
            {"id": "tracker_eye", "name": "Tracker's Eye", "type": "passive",
             "desc": "+6% crit chance", "effect": {"crit_pct": 0.06}},
            {"id": "woodland_step", "name": "Woodland Step", "type": "passive",
             "desc": "+6% dodge chance", "effect": {"dodge_pct": 0.06}},
        ],
        "uncommon": [
            {"id": "twin_shot", "name": "Twin Shot", "type": "active",
             "desc": "Hit 2 enemies for 100% ATK each", "cooldown": 3,
             "effect": {"multi_target": 2, "dmg_pct": 1.0, "mana_cost": 25}},
        ],
        "rare": [
            {"id": "natures_grace", "name": "Nature's Grace", "type": "active",
             "desc": "Heal the lowest-Health ally for 20% of their max Health", "cooldown": 4,
             "effect": {"heal_pct": 0.20, "mana_cost": 30}},
        ],
        "epic": [
            {"id": "barrage", "name": "Barrage", "type": "active",
             "desc": "Hit all enemies for 100% ATK", "cooldown": 6,
             "effect": {"aoe": True, "dmg_pct": 1.0, "mana_cost": 40}},
        ],
        "legendary": [
            {"id": "apex_predator_shot", "name": "Apex Shot", "type": "passive",
             "desc": "20% chance to instantly kill non-boss enemies",
             "effect": {"instant_kill": 0.20}},
        ],
    },
    # CROSSBOWMAN — heavy ranged, tier-30 Archer signature
    "Crossbowman": {
        "common": [
            {"id": "loaded_bolt", "name": "Loaded Bolt", "type": "passive",
             "desc": "+10% ATK", "effect": {"str_pct": 0.10}},
            {"id": "steel_string", "name": "Steel String", "type": "passive",
             "desc": "+5% crit chance", "effect": {"crit_pct": 0.05}},
        ],
        "uncommon": [
            {"id": "heavy_bolt", "name": "Heavy Bolt", "type": "active",
             "desc": "200% ATK, ignore 15% DEF", "cooldown": 4,
             "effect": {"dmg_pct": 2.0, "single_target": True, "ignore_def": True, "mana_cost": 30}},
        ],
        "rare": [
            {"id": "rapid_reload", "name": "Rapid Reload", "type": "passive",
             "desc": "30% chance to strike twice per round",
             "effect": {"double_strike": 0.30}},
        ],
        "epic": [
            {"id": "siege_bolt", "name": "Siege Bolt", "type": "active",
             "desc": "350% ATK single target, ignore DEF", "cooldown": 7,
             "effect": {"dmg_pct": 3.5, "single_target": True, "ignore_def": True, "mana_cost": 45}},
        ],
        "legendary": [
            {"id": "executioners_bolt", "name": "Executioner's Bolt", "type": "passive",
             "desc": "20% chance to instantly kill non-boss enemies",
             "effect": {"instant_kill": 0.20}},
        ],
    },

    # ═══════════════════════════════════════════════════════════════
    # BASE LINEAGE: MAGE (burst caster)
    # ═══════════════════════════════════════════════════════════════
    "Mage": {
        "common": [
            {"id": "mana_shield", "name": "Mana Shield", "type": "passive",
             "desc": "+15% max Health", "effect": {"hlt_pct": 0.15}},
            {"id": "spark", "name": "Spark", "type": "active",
             "desc": "130% ATK to a single target", "cooldown": 2,
             "effect": {"dmg_pct": 1.3, "single_target": True, "mana_cost": 20}},
        ],
        "uncommon": [
            {"id": "arcane_blast", "name": "Arcane Blast", "type": "active",
             "desc": "200% ATK to single target", "cooldown": 3,
             "effect": {"dmg_pct": 2.0, "single_target": True, "mana_cost": 30}},
        ],
        "rare": [
            {"id": "chain_lightning", "name": "Chain Lightning", "type": "passive",
             "desc": "AoE damage increased by 25%", "effect": {"aoe_bonus": 0.25}},
            {"id": "mana_burn", "name": "Mana Burn", "type": "active",
             "desc": "180% ATK single target, ignore DEF", "cooldown": 3,
             "effect": {"dmg_pct": 1.8, "single_target": True, "ignore_def": True, "mana_cost": 30}},
        ],
        "epic": [
            {"id": "time_warp", "name": "Time Warp", "type": "active",
             "desc": "All allies act twice next round", "cooldown": 8,
             "effect": {"team_double_turn": True}},
        ],
        "legendary": [
            {"id": "meteor", "name": "Meteor", "type": "active",
             "desc": "400% ATK to all enemies, self-stun 1 round", "cooldown": 7,
             "effect": {"aoe": True, "dmg_pct": 4.0, "self_stun": 1}},
        ],
    },
    # SORCERER — raw damage caster, tier-30 Mage signature
    "Sorcerer": {
        "common": [
            {"id": "kindled_power", "name": "Kindled Power", "type": "passive",
             "desc": "+10% Health", "effect": {"hlt_pct": 0.10}},
            {"id": "spell_focus", "name": "Spell Focus", "type": "passive",
             "desc": "+5% crit chance", "effect": {"crit_pct": 0.05}},
        ],
        "uncommon": [
            {"id": "firebolt", "name": "Firebolt", "type": "active",
             "desc": "220% ATK to single target", "cooldown": 3,
             "effect": {"dmg_pct": 2.2, "single_target": True, "mana_cost": 30}},
        ],
        "rare": [
            {"id": "scorching_ray", "name": "Scorching Ray", "type": "active",
             "desc": "Hit 2 enemies for 130% ATK each", "cooldown": 4,
             "effect": {"multi_target": 2, "dmg_pct": 1.3, "mana_cost": 35}},
        ],
        "epic": [
            {"id": "firestorm", "name": "Firestorm", "type": "active",
             "desc": "Hit all enemies for 150% ATK", "cooldown": 7,
             "effect": {"aoe": True, "dmg_pct": 1.5, "mana_cost": 45}},
        ],
        "legendary": [
            {"id": "archmagic", "name": "Archmagic Surge", "type": "active",
             "desc": "350% ATK to all enemies", "cooldown": 8,
             "effect": {"aoe": True, "dmg_pct": 3.5, "mana_cost": 55}},
        ],
    },
    # WARLOCK — dark pact damage/drain, tier-30 Mage signature
    "Warlock": {
        "common": [
            {"id": "dark_pact", "name": "Dark Pact", "type": "passive",
             "desc": "+10% ATK, -4% Health", "effect": {"str_pct": 0.0, "int_pct": 0.10, "hlt_pct": -0.04}},
            {"id": "shadow_focus", "name": "Shadow Focus", "type": "passive",
             "desc": "+5% crit chance", "effect": {"crit_pct": 0.05}},
        ],
        "uncommon": [
            {"id": "drain_life", "name": "Drain Life", "type": "active",
             "desc": "200% ATK, heal 30% of damage dealt", "cooldown": 4,
             "effect": {"dmg_pct": 2.0, "single_target": True, "lifesteal_pct": 0.30, "mana_cost": 30}},
        ],
        "rare": [
            {"id": "curse", "name": "Curse", "type": "passive",
             "desc": "Attacks apply 3% max Health poison for 3 rounds",
             "effect": {"poison_pct": 0.03, "poison_duration": 3}},
        ],
        "epic": [
            {"id": "soul_burn", "name": "Soul Burn", "type": "active",
             "desc": "260% ATK, +60% damage if target below 30% Health", "cooldown": 6,
             "effect": {"dmg_pct": 2.6, "single_target": True, "execute_bonus_pct": 0.60, "execute_threshold": 0.30, "mana_cost": 40}},
        ],
        "legendary": [
            {"id": "demonic_pact", "name": "Demonic Pact", "type": "active",
             "desc": "300% ATK to all enemies, heal 20% of damage dealt", "cooldown": 8,
             "effect": {"aoe": True, "dmg_pct": 3.0, "lifesteal_pct": 0.20, "mana_cost": 55}},
        ],
    },
    # NECROMANCER — DoT/attrition, tier-30 Mage signature
    "Necromancer": {
        "common": [
            {"id": "death_chill", "name": "Death Chill", "type": "passive",
             "desc": "+8% Health", "effect": {"hlt_pct": 0.08}},
            {"id": "grim_focus", "name": "Grim Focus", "type": "passive",
             "desc": "+5% crit chance", "effect": {"crit_pct": 0.05}},
        ],
        "uncommon": [
            {"id": "withering_touch", "name": "Withering Touch", "type": "active",
             "desc": "160% ATK to single target", "cooldown": 3,
             "effect": {"dmg_pct": 1.6, "single_target": True, "mana_cost": 25}},
        ],
        "rare": [
            {"id": "plague_curse", "name": "Plague Curse", "type": "passive",
             "desc": "Attacks apply 4% max Health poison for 3 rounds",
             "effect": {"poison_pct": 0.04, "poison_duration": 3}},
        ],
        "epic": [
            {"id": "raise_dead", "name": "Raise Dead", "type": "active",
             "desc": "Revive a fallen ally at 35% Health (once per fight)", "cooldown": 99,
             "effect": {"revive_pct": 0.35, "min_star": 6, "mana_cost": 45}},
        ],
        "legendary": [
            {"id": "soul_harvest", "name": "Soul Harvest", "type": "passive",
             "desc": "Each kill grants +20% ATK for the rest of combat",
             "effect": {"kill_atk_stack": 0.20}},
        ],
    },
    # SUMMONER — pet/utility, tier-30 Mage signature
    "Summoner": {
        "common": [
            {"id": "bound_familiar", "name": "Bound Familiar", "type": "passive",
             "desc": "+10% Health", "effect": {"hlt_pct": 0.10}},
            {"id": "summoners_focus", "name": "Summoner's Focus", "type": "passive",
             "desc": "+5% ATK", "effect": {"str_pct": 0.0, "int_pct": 0.05}},
        ],
        "uncommon": [
            {"id": "spirit_bolt", "name": "Spirit Bolt", "type": "active",
             "desc": "170% ATK to single target", "cooldown": 3,
             "effect": {"dmg_pct": 1.7, "single_target": True, "mana_cost": 25}},
        ],
        "rare": [
            {"id": "guardian_spirit", "name": "Guardian Spirit", "type": "active",
             "desc": "Shield the team for 25% damage reduction for 2 rounds", "cooldown": 5,
             "effect": {"team_dmg_reduce": 0.25, "duration": 2, "mana_cost": 35}},
        ],
        "epic": [
            {"id": "summon_swarm", "name": "Summon Swarm", "type": "active",
             "desc": "Hit all enemies for 110% ATK", "cooldown": 6,
             "effect": {"aoe": True, "dmg_pct": 1.1, "mana_cost": 40}},
        ],
        "legendary": [
            {"id": "spirit_rebirth", "name": "Spirit Rebirth", "type": "active",
             "desc": "Revive a fallen ally at 45% Health (once per fight)", "cooldown": 99,
             "effect": {"revive_pct": 0.45, "min_star": 6, "mana_cost": 50}},
        ],
    },

    # ═══════════════════════════════════════════════════════════════
    # BASE LINEAGE: MAGIC ENGINEER (construct support, pinnacle class)
    # ═══════════════════════════════════════════════════════════════
    "Magic Engineer": {
        "common": [
            {"id": "reinforced_construct", "name": "Reinforced Construct", "type": "passive",
             "desc": "Construct absorbs 2 hits instead of 1", "effect": {"construct_hits": 2}},
            {"id": "tinkers_focus", "name": "Tinker's Focus", "type": "passive",
             "desc": "+6% ATK", "effect": {"str_pct": 0.0, "int_pct": 0.06}},
        ],
        "uncommon": [
            {"id": "repair_drone", "name": "Repair Drone", "type": "active",
             "desc": "Restore 15% Health to lowest-Health ally", "cooldown": 4,
             "effect": {"heal_pct": 0.15, "mana_cost": 25}},
            {"id": "overclock_strike", "name": "Overclock Strike", "type": "active",
             "desc": "170% ATK to single target", "cooldown": 3,
             "effect": {"dmg_pct": 1.7, "single_target": True, "mana_cost": 28}},
        ],
        "rare": [
            {"id": "emp_blast", "name": "EMP Blast", "type": "active",
             "desc": "Stun all enemies for 1 round", "cooldown": 6,
             "effect": {"enemy_stun": 1, "mana_cost": 35}},
        ],
        "epic": [
            {"id": "overcharge", "name": "Overcharge", "type": "passive",
             "desc": "Construct explodes on death dealing 200% ATK to all enemies",
             "effect": {"construct_explode_pct": 2.0}},
        ],
        "legendary": [
            {"id": "war_machine", "name": "War Machine", "type": "passive",
             "desc": "Construct attacks each round for 50% of your ATK",
             "effect": {"construct_attack_pct": 0.50}},
        ],
    },

    # ═══════════════════════════════════════════════════════════════
    # BASE LINEAGE: ACOLYTE (healer/support caster)
    # ═══════════════════════════════════════════════════════════════
    "Acolyte": {
        "common": [
            {"id": "novice_prayer", "name": "Novice Prayer", "type": "passive",
             "desc": "+10% Health", "effect": {"hlt_pct": 0.10}},
            {"id": "ward", "name": "Ward", "type": "passive",
             "desc": "+5% damage reduction", "effect": {"dmg_reduction_pct": 0.05}},
            {"id": "mend", "name": "Mend", "type": "active",
             "desc": "Heal the lowest-Health ally for 15% of their max Health", "cooldown": 3,
             "effect": {"heal_pct": 0.15, "mana_cost": 20}},
        ],
        "uncommon": [
            {"id": "calming_chant", "name": "Calming Chant", "type": "passive",
             "desc": "-10% stress gain", "effect": {"stress_reduce": 0.10}},
            {"id": "smite", "name": "Smite", "type": "active",
             "desc": "150% ATK to single target", "cooldown": 3,
             "effect": {"dmg_pct": 1.5, "single_target": True, "mana_cost": 25}},
        ],
        "rare": [
            {"id": "greater_heal", "name": "Greater Heal", "type": "active",
             "desc": "Heal the lowest-Health ally for 30% of their max Health", "cooldown": 5,
             "effect": {"heal_pct": 0.30, "mana_cost": 35}},
        ],
        "epic": [
            {"id": "purify", "name": "Purify", "type": "active",
             "desc": "Cleanse all your own afflictions and heal self 15%", "cooldown": 5,
             "effect": {"cleanse_self": True, "self_heal_pct": 0.15, "mana_cost": 30}},
        ],
        "legendary": [
            {"id": "resurrection", "name": "Resurrection", "type": "active",
             "desc": "Revive a fallen ally at 50% Health (once per fight)", "cooldown": 99,
             "effect": {"revive_pct": 0.50, "min_star": 6, "mana_cost": 50}},
        ],
    },
    # CLERIC — frontline healer, tier-30 Acolyte signature
    "Cleric": {
        "common": [
            {"id": "blessing", "name": "Blessing", "type": "passive",
             "desc": "+12% Health", "effect": {"hlt_pct": 0.12}},
            {"id": "faithful_heart", "name": "Faithful Heart", "type": "passive",
             "desc": "-8% stress gain", "effect": {"stress_reduce": 0.08}},
        ],
        "uncommon": [
            {"id": "heal", "name": "Heal", "type": "active",
             "desc": "Heal the lowest-Health ally for 20% of their max Health", "cooldown": 3,
             "effect": {"heal_pct": 0.20, "mana_cost": 25}},
        ],
        "rare": [
            {"id": "holy_light", "name": "Holy Light", "type": "active",
             "desc": "180% ATK to single target", "cooldown": 4,
             "effect": {"dmg_pct": 1.8, "single_target": True, "mana_cost": 30}},
        ],
        "epic": [
            {"id": "sanctuary", "name": "Sanctuary", "type": "active",
             "desc": "Shield the team for 30% damage reduction for 2 rounds", "cooldown": 6,
             "effect": {"team_dmg_reduce": 0.30, "duration": 2, "mana_cost": 40}},
        ],
        "legendary": [
            {"id": "miracle", "name": "Miracle", "type": "active",
             "desc": "Revive a fallen ally at 55% Health (once per fight)", "cooldown": 99,
             "effect": {"revive_pct": 0.55, "min_star": 6, "mana_cost": 50}},
        ],
    },
    # BARD — buff/utility, tier-30 Acolyte signature
    "Bard": {
        "common": [
            {"id": "inspiring_tune", "name": "Inspiring Tune", "type": "passive",
             "desc": "+5% ATK to all frontline allies", "effect": {"team_atk_pct": 0.05}},
            {"id": "quick_fingers_bard", "name": "Quick Fingers", "type": "passive",
             "desc": "+6% SPD", "effect": {"agi_pct": 0.06}},
        ],
        "uncommon": [
            {"id": "rousing_ballad", "name": "Rousing Ballad", "type": "active",
             "desc": "Permanently boost team ATK 8% for the rest of the fight", "cooldown": 6,
             "effect": {"team_buff_pct": 0.08, "buff_stat": "strength", "mana_cost": 30}},
        ],
        "rare": [
            {"id": "soothing_melody", "name": "Soothing Melody", "type": "active",
             "desc": "Heal the lowest-Health ally for 22% of their max Health", "cooldown": 4,
             "effect": {"heal_pct": 0.22, "mana_cost": 30}},
        ],
        "epic": [
            {"id": "warsong", "name": "Warsong", "type": "active",
             "desc": "Permanently boost team SPD 12% for the rest of the fight", "cooldown": 7,
             "effect": {"team_buff_pct": 0.12, "buff_stat": "agility", "mana_cost": 35}},
        ],
        "legendary": [
            {"id": "ballad_of_heroes", "name": "Ballad of Heroes", "type": "passive",
             "desc": "+15% ATK to all frontline allies", "effect": {"team_atk_pct": 0.15}},
        ],
    },
    # DRUID — nature hybrid damage/heal, tier-30 Acolyte signature
    "Druid": {
        "common": [
            {"id": "wild_growth", "name": "Wild Growth", "type": "passive",
             "desc": "+3% Health regen per round", "effect": {"regen_pct": 0.03}},
            {"id": "natures_touch", "name": "Nature's Touch", "type": "passive",
             "desc": "+8% Health", "effect": {"hlt_pct": 0.08}},
        ],
        "uncommon": [
            {"id": "thorn_whip", "name": "Thorn Whip", "type": "active",
             "desc": "150% ATK to single target", "cooldown": 3,
             "effect": {"dmg_pct": 1.5, "single_target": True, "mana_cost": 25}},
        ],
        "rare": [
            {"id": "rejuvenation", "name": "Rejuvenation", "type": "active",
             "desc": "Heal the lowest-Health ally for 25% of their max Health", "cooldown": 4,
             "effect": {"heal_pct": 0.25, "mana_cost": 30}},
        ],
        "epic": [
            {"id": "entangling_roots", "name": "Entangling Roots", "type": "active",
             "desc": "Stun all enemies for 1 round", "cooldown": 6,
             "effect": {"enemy_stun": 1, "mana_cost": 35}},
        ],
        "legendary": [
            {"id": "natures_wrath", "name": "Nature's Wrath", "type": "active",
             "desc": "Hit all enemies for 150% ATK", "cooldown": 8,
             "effect": {"aoe": True, "dmg_pct": 1.5, "mana_cost": 45}},
        ],
    },
    # MONK — melee/self-sustain hybrid, tier-30 Acolyte signature
    "Monk": {
        "common": [
            {"id": "iron_body", "name": "Iron Body", "type": "passive",
             "desc": "+8% Health, +5% damage reduction", "effect": {"hlt_pct": 0.08, "dmg_reduction_pct": 0.05}},
            {"id": "focused_breath", "name": "Focused Breath", "type": "passive",
             "desc": "+2% Health regen per round", "effect": {"regen_pct": 0.02}},
        ],
        "uncommon": [
            {"id": "palm_strike", "name": "Palm Strike", "type": "active",
             "desc": "170% ATK, heal self 10% of damage dealt", "cooldown": 3,
             "effect": {"dmg_pct": 1.7, "single_target": True, "lifesteal_pct": 0.10, "mana_cost": 25}},
        ],
        "rare": [
            {"id": "meditation", "name": "Meditation", "type": "active",
             "desc": "Heal self for 25% of max Health", "cooldown": 4,
             "effect": {"self_heal_pct": 0.25, "mana_cost": 25}},
        ],
        "epic": [
            {"id": "iron_fist_flurry", "name": "Iron Fist Flurry", "type": "active",
             "desc": "Hit 3 enemies for 100% ATK each", "cooldown": 5,
             "effect": {"multi_target": 3, "dmg_pct": 1.0, "mana_cost": 35}},
        ],
        "legendary": [
            {"id": "enlightenment", "name": "Enlightenment", "type": "passive",
             "desc": "+15% all stats", "effect": {"all_pct": 0.15}},
        ],
    },

    # ═══════════════════════════════════════════════════════════════
    # BASE LINEAGE: SPELLSWORD (hybrid melee/caster)
    # ═══════════════════════════════════════════════════════════════
    "Spellsword": {
        "common": [
            {"id": "enchanted_edge", "name": "Enchanted Edge", "type": "passive",
             "desc": "+8% ATK", "effect": {"str_pct": 0.0, "int_pct": 0.08}},
            {"id": "spell_armor", "name": "Spell Armor", "type": "passive",
             "desc": "+6% magic resist", "effect": {"magic_resist_pct": 0.06}},
        ],
        "uncommon": [
            {"id": "rune_slash", "name": "Rune Slash", "type": "active",
             "desc": "180% ATK to single target", "cooldown": 3,
             "effect": {"dmg_pct": 1.8, "single_target": True, "mana_cost": 25}},
        ],
        "rare": [
            {"id": "arcane_parry", "name": "Arcane Parry", "type": "passive",
             "desc": "+8% damage reduction", "effect": {"dmg_reduction_pct": 0.08}},
            {"id": "elemental_edge", "name": "Elemental Edge", "type": "active",
             "desc": "190% ATK single target, ignore 15% DEF", "cooldown": 4,
             "effect": {"dmg_pct": 1.9, "single_target": True, "ignore_def": True, "mana_cost": 32}},
        ],
        "epic": [
            {"id": "spellblade_flurry", "name": "Spellblade Flurry", "type": "active",
             "desc": "Hit 2 enemies for 140% ATK each, heal self 10% of damage dealt", "cooldown": 5,
             "effect": {"multi_target": 2, "dmg_pct": 1.4, "lifesteal_pct": 0.10, "mana_cost": 35}},
        ],
        "legendary": [
            {"id": "rune_ascendance", "name": "Rune Ascendance", "type": "passive",
             "desc": "+15% ATK, +10% magic resist",
             "effect": {"int_pct": 0.15, "magic_resist_pct": 0.10}},
        ],
    },
    # ELDRITCH KNIGHT — battlemage tank, tier-30 Spellsword signature
    "Eldritch Knight": {
        "common": [
            {"id": "warded_blade", "name": "Warded Blade", "type": "passive",
             "desc": "+8% DEF, +5% magic resist", "effect": {"int_pct": 0.08, "magic_resist_pct": 0.05}},
            {"id": "battle_focus", "name": "Battle Focus", "type": "passive",
             "desc": "+6% ATK", "effect": {"str_pct": 0.0, "int_pct": 0.06}},
        ],
        "uncommon": [
            {"id": "spellsteel_strike", "name": "Spellsteel Strike", "type": "active",
             "desc": "200% ATK to single target", "cooldown": 3,
             "effect": {"dmg_pct": 2.0, "single_target": True, "mana_cost": 30}},
        ],
        "rare": [
            {"id": "arcane_ward", "name": "Arcane Ward", "type": "active",
             "desc": "Shield the team for 25% damage reduction for 2 rounds", "cooldown": 5,
             "effect": {"team_dmg_reduce": 0.25, "duration": 2, "mana_cost": 35}},
        ],
        "epic": [
            {"id": "runic_bulwark", "name": "Runic Bulwark", "type": "passive",
             "desc": "+10% damage reduction, +10% magic resist",
             "effect": {"dmg_reduction_pct": 0.10, "magic_resist_pct": 0.10}},
        ],
        "legendary": [
            {"id": "spellblade_ascendant", "name": "Spellblade Ascendant", "type": "passive",
             "desc": "Each kill grants +15% ATK for the rest of combat",
             "effect": {"kill_atk_stack": 0.15}},
        ],
    },
    # RUNE BLADE — rune-empowered striker, tier-30 Spellsword signature
    "Rune Blade": {
        "common": [
            {"id": "etched_runes", "name": "Etched Runes", "type": "passive",
             "desc": "+10% ATK", "effect": {"str_pct": 0.0, "int_pct": 0.10}},
            {"id": "rune_ward", "name": "Rune Ward", "type": "passive",
             "desc": "+5% physical resist", "effect": {"physical_resist_pct": 0.05}},
        ],
        "uncommon": [
            {"id": "rune_burst", "name": "Rune Burst", "type": "active",
             "desc": "210% ATK to single target", "cooldown": 3,
             "effect": {"dmg_pct": 2.1, "single_target": True, "mana_cost": 30}},
        ],
        "rare": [
            {"id": "rune_chain", "name": "Rune Chain", "type": "active",
             "desc": "Hit 2 enemies for 130% ATK each", "cooldown": 4,
             "effect": {"multi_target": 2, "dmg_pct": 1.3, "mana_cost": 35}},
        ],
        "epic": [
            {"id": "rune_overload", "name": "Rune Overload", "type": "active",
             "desc": "320% ATK single target, ignore DEF", "cooldown": 6,
             "effect": {"dmg_pct": 3.2, "ignore_def": True, "mana_cost": 40}},
        ],
        "legendary": [
            {"id": "runeblade_apex", "name": "Runeblade Apex", "type": "passive",
             "desc": "+15% ATK, +10% physical resist",
             "effect": {"int_pct": 0.15, "physical_resist_pct": 0.10}},
        ],
    },

    # ═══════════════════════════════════════════════════════════════
    # SUPPORT-NAMED BUT COMBAT-CAPABLE BASE LINEAGES
    # ═══════════════════════════════════════════════════════════════
    "Medic": {
        "common": [
            {"id": "field_dressing", "name": "Field Dressing", "type": "active",
             "desc": "Heal the lowest-Health ally for 18% of their max Health", "cooldown": 3,
             "effect": {"heal_pct": 0.18, "mana_cost": 20}},
            {"id": "steady_hands_medic", "name": "Steady Hands", "type": "passive",
             "desc": "+8% Health", "effect": {"hlt_pct": 0.08}},
        ],
        "uncommon": [
            {"id": "triage", "name": "Triage", "type": "active",
             "desc": "Heal the lowest-Health ally for 28% of their max Health", "cooldown": 4,
             "effect": {"heal_pct": 0.28, "mana_cost": 30}},
        ],
        "rare": [
            {"id": "stabilize", "name": "Stabilize", "type": "active",
             "desc": "Cleanse own afflictions and heal self 15%", "cooldown": 4,
             "effect": {"cleanse_self": True, "self_heal_pct": 0.15, "mana_cost": 25}},
        ],
        "epic": [
            {"id": "emergency_surgery", "name": "Emergency Surgery", "type": "active",
             "desc": "Revive a fallen ally at 30% Health (once per fight)", "cooldown": 99,
             "effect": {"revive_pct": 0.30, "min_star": 6, "mana_cost": 40}},
        ],
        "legendary": [
            {"id": "miracle_worker_medic", "name": "Against All Odds", "type": "active",
             "desc": "Revive a fallen ally at 50% Health (once per fight)", "cooldown": 99,
             "effect": {"revive_pct": 0.50, "min_star": 6, "mana_cost": 50}},
        ],
    },
    "Scout": {
        "common": [
            {"id": "keen_senses", "name": "Keen Senses", "type": "passive",
             "desc": "+8% dodge chance", "effect": {"dodge_pct": 0.08}},
            {"id": "fleet_footed", "name": "Fleet-Footed", "type": "passive",
             "desc": "+8% SPD", "effect": {"agi_pct": 0.08}},
        ],
        "uncommon": [
            {"id": "snap_shot", "name": "Snap Shot", "type": "active",
             "desc": "160% ATK to single target", "cooldown": 3,
             "effect": {"dmg_pct": 1.6, "single_target": True, "mana_cost": 25}},
        ],
        "rare": [
            {"id": "evasive_maneuvers", "name": "Evasive Maneuvers", "type": "passive",
             "desc": "+10% dodge chance", "effect": {"dodge_pct": 0.10}},
        ],
        "epic": [
            {"id": "ambush_tactics", "name": "Ambush Tactics", "type": "active",
             "desc": "220% ATK, guaranteed crit", "cooldown": 5,
             "effect": {"dmg_pct": 2.2, "single_target": True, "guaranteed_crit": True, "mana_cost": 35}},
        ],
        "legendary": [
            {"id": "ghost_in_the_woods", "name": "Ghost in the Woods", "type": "passive",
             "desc": "+18% dodge chance, +8% SPD",
             "effect": {"dodge_pct": 0.18, "agi_pct": 0.08}},
        ],
    },
    "Tactician": {
        "common": [
            {"id": "battlefield_read", "name": "Battlefield Read", "type": "passive",
             "desc": "+5% ATK to all frontline allies", "effect": {"team_atk_pct": 0.05}},
            {"id": "composed_mind", "name": "Composed Mind", "type": "passive",
             "desc": "-8% stress gain", "effect": {"stress_reduce": 0.08}},
        ],
        "uncommon": [
            {"id": "flank_signal", "name": "Flank Signal", "type": "active",
             "desc": "Permanently boost team ATK 8% for the rest of the fight", "cooldown": 6,
             "effect": {"team_buff_pct": 0.08, "buff_stat": "strength", "mana_cost": 30}},
        ],
        "rare": [
            {"id": "disabling_order", "name": "Disabling Order", "type": "active",
             "desc": "Stun all enemies for 1 round", "cooldown": 6,
             "effect": {"enemy_stun": 1, "mana_cost": 35}},
        ],
        "epic": [
            {"id": "coordinated_strike", "name": "Coordinated Strike", "type": "active",
             "desc": "Permanently boost team SPD 12% for the rest of the fight", "cooldown": 7,
             "effect": {"team_buff_pct": 0.12, "buff_stat": "agility", "mana_cost": 35}},
        ],
        "legendary": [
            {"id": "grand_strategy", "name": "Grand Strategy", "type": "passive",
             "desc": "+15% ATK to all frontline allies", "effect": {"team_atk_pct": 0.15}},
        ],
    },
    "Merchant": {
        "common": [
            {"id": "haggle_swing", "name": "Coin Toss", "type": "active",
             "desc": "130% ATK to a single target", "cooldown": 2,
             "effect": {"dmg_pct": 1.3, "single_target": True, "mana_cost": 15}},
            {"id": "lucky_charm", "name": "Lucky Charm", "type": "passive",
             "desc": "+5% crit chance", "effect": {"crit_pct": 0.05}},
        ],
        "uncommon": [
            {"id": "gilded_gauntlet", "name": "Gilded Gauntlet", "type": "active",
             "desc": "170% ATK to single target", "cooldown": 3,
             "effect": {"dmg_pct": 1.7, "single_target": True, "mana_cost": 25}},
        ],
        "rare": [
            {"id": "appraisers_eye", "name": "Appraiser's Eye", "type": "passive",
             "desc": "+8% crit chance", "effect": {"crit_pct": 0.08}},
        ],
        "epic": [
            {"id": "hard_bargain", "name": "Hard Bargain", "type": "active",
             "desc": "200% ATK, +60% damage if target below 30% Health", "cooldown": 5,
             "effect": {"dmg_pct": 2.0, "single_target": True, "execute_bonus_pct": 0.60, "execute_threshold": 0.30, "mana_cost": 35}},
        ],
        "legendary": [
            {"id": "fortunes_favor", "name": "Fortune's Favor", "type": "passive",
             "desc": "+15% all stats", "effect": {"all_pct": 0.15}},
        ],
    },
    "Farmer": {
        "common": [
            {"id": "pitchfork_jab", "name": "Pitchfork Jab", "type": "active",
             "desc": "140% ATK to a single target", "cooldown": 2,
             "effect": {"dmg_pct": 1.4, "single_target": True, "mana_cost": 15}},
            {"id": "calloused_hands", "name": "Calloused Hands", "type": "passive",
             "desc": "+6% Health", "effect": {"hlt_pct": 0.06}},
        ],
        "uncommon": [
            {"id": "scarecrow_stand", "name": "Scarecrow Stand", "type": "active",
             "desc": "Force all enemies to target you for 2 rounds", "cooldown": 4,
             "effect": {"taunt_duration": 2, "mana_cost": 25}},
        ],
        "rare": [
            {"id": "harvest_swing", "name": "Harvest Swing", "type": "active",
             "desc": "Hit 2 enemies for 90% ATK each", "cooldown": 3,
             "effect": {"multi_target": 2, "dmg_pct": 0.90, "mana_cost": 25}},
        ],
        "epic": [
            {"id": "bountiful_resolve", "name": "Bountiful Resolve", "type": "passive",
             "desc": "+10% Health, +8% damage reduction",
             "effect": {"hlt_pct": 0.10, "dmg_reduction_pct": 0.08}},
        ],
        "legendary": [
            {"id": "harvest_moon", "name": "Harvest Moon", "type": "active",
             "desc": "Hit all enemies for 130% ATK", "cooldown": 7,
             "effect": {"aoe": True, "dmg_pct": 1.3, "mana_cost": 40}},
        ],
    },

    # ═══════════════════════════════════════════════════════════════
    # MORE BASE LINEAGES — the literal base name (Blacksmith, Alchemist,
    # Chef, Priest, Quartermaster) never fights, but every one of their
    # tier-30+ evolutions does (is_combat_class is True for all of them),
    # so the lineage still needs a real kit, just themed around the trade.
    # ═══════════════════════════════════════════════════════════════
    "Blacksmith": {
        "common": [
            {"id": "hammer_swing", "name": "Hammer Swing", "type": "active",
             "desc": "150% ATK to a single target", "cooldown": 2,
             "effect": {"dmg_pct": 1.5, "single_target": True, "mana_cost": 15}},
            {"id": "forge_calloused", "name": "Forge-Calloused", "type": "passive",
             "desc": "+8% damage reduction", "effect": {"dmg_reduction_pct": 0.08}},
        ],
        "uncommon": [
            {"id": "molten_edge", "name": "Molten Edge", "type": "active",
             "desc": "190% ATK to single target", "cooldown": 3,
             "effect": {"dmg_pct": 1.9, "single_target": True, "mana_cost": 25}},
        ],
        "rare": [
            {"id": "tempered_plate", "name": "Tempered Plate", "type": "passive",
             "desc": "+10% physical resist", "effect": {"physical_resist_pct": 0.10}},
        ],
        "epic": [
            {"id": "sledgehammer_crush", "name": "Sledgehammer Crush", "type": "active",
             "desc": "260% ATK single target, ignore DEF", "cooldown": 5,
             "effect": {"dmg_pct": 2.6, "ignore_def": True, "mana_cost": 35}},
        ],
        "legendary": [
            {"id": "masterwork", "name": "Masterwork", "type": "passive",
             "desc": "+15% ATK, +12% physical resist",
             "effect": {"str_pct": 0.15, "physical_resist_pct": 0.12}},
        ],
    },
    "Alchemist": {
        "common": [
            {"id": "acid_flask", "name": "Acid Flask", "type": "active",
             "desc": "140% ATK to a single target", "cooldown": 2,
             "effect": {"dmg_pct": 1.4, "single_target": True, "mana_cost": 15}},
            {"id": "tonic_resilience", "name": "Tonic Resilience", "type": "passive",
             "desc": "+8% Health", "effect": {"hlt_pct": 0.08}},
        ],
        "uncommon": [
            {"id": "caustic_brew", "name": "Caustic Brew", "type": "passive",
             "desc": "Attacks apply 3% max Health poison for 3 rounds",
             "effect": {"poison_pct": 0.03, "poison_duration": 3}},
        ],
        "rare": [
            {"id": "healing_draught", "name": "Healing Draught", "type": "active",
             "desc": "Heal the lowest-Health ally for 25% of their max Health", "cooldown": 4,
             "effect": {"heal_pct": 0.25, "mana_cost": 30}},
        ],
        "epic": [
            {"id": "volatile_mixture", "name": "Volatile Mixture", "type": "active",
             "desc": "Hit all enemies for 110% ATK", "cooldown": 6,
             "effect": {"aoe": True, "dmg_pct": 1.1, "mana_cost": 40}},
        ],
        "legendary": [
            {"id": "philosophers_elixir", "name": "Philosopher's Elixir", "type": "active",
             "desc": "Cleanse own afflictions and heal self 25%", "cooldown": 5,
             "effect": {"cleanse_self": True, "self_heal_pct": 0.25, "mana_cost": 35}},
        ],
    },
    "Chef": {
        "common": [
            {"id": "cleaver_chop", "name": "Cleaver Chop", "type": "active",
             "desc": "150% ATK to a single target", "cooldown": 2,
             "effect": {"dmg_pct": 1.5, "single_target": True, "mana_cost": 15}},
            {"id": "hearty_meal", "name": "Hearty Meal", "type": "passive",
             "desc": "+8% Health", "effect": {"hlt_pct": 0.08}},
        ],
        "uncommon": [
            {"id": "flambe", "name": "Flambé", "type": "active",
             "desc": "Hit 2 enemies for 90% ATK each", "cooldown": 3,
             "effect": {"multi_target": 2, "dmg_pct": 0.90, "mana_cost": 25}},
        ],
        "rare": [
            {"id": "secret_recipe", "name": "Secret Recipe", "type": "active",
             "desc": "Heal the lowest-Health ally for 22% of their max Health", "cooldown": 4,
             "effect": {"heal_pct": 0.22, "mana_cost": 30}},
        ],
        "epic": [
            {"id": "knife_flurry", "name": "Knife Flurry", "type": "active",
             "desc": "Hit 3 enemies for 100% ATK each", "cooldown": 5,
             "effect": {"multi_target": 3, "dmg_pct": 1.0, "mana_cost": 35}},
        ],
        "legendary": [
            {"id": "michelin_mastery", "name": "Michelin Mastery", "type": "passive",
             "desc": "+15% all stats", "effect": {"all_pct": 0.15}},
        ],
    },
    "Priest": {
        "common": [
            {"id": "minor_blessing", "name": "Minor Blessing", "type": "active",
             "desc": "Heal the lowest-Health ally for 15% of their max Health", "cooldown": 3,
             "effect": {"heal_pct": 0.15, "mana_cost": 20}},
            {"id": "devout_calm", "name": "Devout Calm", "type": "passive",
             "desc": "-10% stress gain", "effect": {"stress_reduce": 0.10}},
        ],
        "uncommon": [
            {"id": "holy_smite", "name": "Holy Smite", "type": "active",
             "desc": "160% ATK to single target", "cooldown": 3,
             "effect": {"dmg_pct": 1.6, "single_target": True, "mana_cost": 25}},
        ],
        "rare": [
            {"id": "absolution", "name": "Absolution", "type": "active",
             "desc": "Cleanse own afflictions and heal self 20%", "cooldown": 4,
             "effect": {"cleanse_self": True, "self_heal_pct": 0.20, "mana_cost": 30}},
        ],
        "epic": [
            {"id": "divine_intervention", "name": "Divine Intervention", "type": "active",
             "desc": "Shield the team for 28% damage reduction for 2 rounds", "cooldown": 6,
             "effect": {"team_dmg_reduce": 0.28, "duration": 2, "mana_cost": 38}},
        ],
        "legendary": [
            {"id": "sacred_rebirth", "name": "Sacred Rebirth", "type": "active",
             "desc": "Revive a fallen ally at 45% Health (once per fight)", "cooldown": 99,
             "effect": {"revive_pct": 0.45, "min_star": 6, "mana_cost": 50}},
        ],
    },
    "Quartermaster": {
        "common": [
            {"id": "supply_strike", "name": "Supply Strike", "type": "active",
             "desc": "140% ATK to a single target", "cooldown": 2,
             "effect": {"dmg_pct": 1.4, "single_target": True, "mana_cost": 15}},
            {"id": "well_equipped", "name": "Well-Equipped", "type": "passive",
             "desc": "+6% damage reduction", "effect": {"dmg_reduction_pct": 0.06}},
        ],
        "uncommon": [
            {"id": "requisition", "name": "Requisition", "type": "active",
             "desc": "Permanently boost team ATK 8% for the rest of the fight", "cooldown": 6,
             "effect": {"team_buff_pct": 0.08, "buff_stat": "strength", "mana_cost": 30}},
        ],
        "rare": [
            {"id": "field_resupply", "name": "Field Resupply", "type": "active",
             "desc": "Heal the lowest-Health ally for 22% of their max Health", "cooldown": 4,
             "effect": {"heal_pct": 0.22, "mana_cost": 30}},
        ],
        "epic": [
            {"id": "stockpile_reserves", "name": "Stockpile Reserves", "type": "passive",
             "desc": "+12% Health, +8% damage reduction",
             "effect": {"hlt_pct": 0.12, "dmg_reduction_pct": 0.08}},
        ],
        "legendary": [
            {"id": "logistics_mastery", "name": "Logistics Mastery", "type": "passive",
             "desc": "+15% all stats", "effect": {"all_pct": 0.15}},
        ],
    },
    "Classless": {
        "common": [
            {"id": "adaptable", "name": "Adaptable", "type": "passive",
             "desc": "+5% all stats", "effect": {"all_pct": 0.05}},
            {"id": "improvised_strike", "name": "Improvised Strike", "type": "active",
             "desc": "140% ATK to a single target", "cooldown": 2,
             "effect": {"dmg_pct": 1.4, "single_target": True, "mana_cost": 15}},
        ],
        "uncommon": [
            {"id": "jack_of_all_trades", "name": "Jack of All Trades", "type": "passive",
             "desc": "+6% ATK, +6% dodge chance", "effect": {"str_pct": 0.06, "dodge_pct": 0.06}},
        ],
        "rare": [
            {"id": "self_taught", "name": "Self-Taught", "type": "active",
             "desc": "190% ATK to single target, heal self 10% of damage dealt", "cooldown": 4,
             "effect": {"dmg_pct": 1.9, "single_target": True, "lifesteal_pct": 0.10, "mana_cost": 30}},
        ],
        "epic": [
            {"id": "unbroken_will", "name": "Unbroken Will", "type": "passive",
             "desc": "Survive one killing blow with 1 Health (once per fight)",
             "effect": {"death_save": 1}},
        ],
        "legendary": [
            {"id": "true_potential", "name": "True Potential", "type": "passive",
             "desc": "+20% all stats", "effect": {"all_pct": 0.20}},
        ],
    },
}

# Lineage resolution — maps every evolved class name back to the BASE
# lineage name whose SKILL_POOL entry it should fall back to when it
# doesn't have its own exact-match entry above (e.g. tier-60 pinnacle
# forms like "Templar" or "Archmage", and any base class without a
# kit yet like Blacksmith/Alchemist/Chef/Priest/Quartermaster — those
# stay on GENERIC_SKILLS since they're not combat-capable anyway).
# Built once from class_service.CLASS_EVOLUTIONS so it can't drift out
# of sync with the actual evolution tree.
_LINEAGE_MAP = None

def _build_lineage_map() -> dict:
    from services.class_service import CLASS_EVOLUTIONS
    mapping = {}
    for base, tiers in CLASS_EVOLUTIONS.items():
        tier30 = tiers.get(30, [])
        for name in tier30:
            mapping.setdefault(name, base)
        tier60 = tiers.get(60, {    "Tactician": {
        "common": [
            {"id": "tactician_strategic_assault", "name": "Strategic Assault", "type": "active", "desc": "Boosts all allies' attack power for a short duration.", "cooldown": 4, "effect": {"atk_pct": 0.2}},
        ],
        "uncommon": [
            {"id": "tactician_battle_plan", "name": "Battle Plan", "type": "passive", "desc": "The Tactician's intellect is unmatched, boosting all stats.", "effect": {"int_pct": 0.15, "lck_pct": 0.05}},
        ],
        "rare": [
            {"id": "tactician_flank_maneuver", "name": "Flank Maneuver", "type": "active", "desc": "Exposes an enemy's weakness, reducing their defense significantly.", "cooldown": 5, "effect": {"def_pct": -0.2}},
        ],
        "epic": [
            {"id": "tactician_prepared_mind", "name": "Prepared Mind", "type": "passive", "desc": "Always ready for anything, sometimes cleansing negative effects.", "effect": {"cleanse_self": True}},
        ],
        "legendary": [
            {"id": "tactician_coordinated_strike", "name": "Coordinated Strike", "type": "active", "desc": "Orders a focused attack, dealing moderate damage and buffing agility.", "cooldown": 3, "effect": {"atk_pct": 1.2, "agi_pct": 0.1}},
        ],
    },
    "Herbalist": {
        "common": [
            {"id": "herbalist_soothing_salve", "name": "Soothing Salve", "type": "active", "desc": "Heals the lowest health ally with a potent herbal remedy.", "cooldown": 3, "effect": {"heal_pct": 0.25}},
        ],
        "uncommon": [
            {"id": "herbalist_natural_resilience", "name": "Natural Resilience", "type": "passive", "desc": "The Herbalist's connection to nature grants increased health and self-healing.", "effect": {"hlt_pct": 0.15, "self_heal_pct": 0.05}},
        ],
        "rare": [
            {"id": "herbalist_toxic_extract", "name": "Toxic Extract", "type": "active", "desc": "Lobs a vial of potent toxins, dealing damage over time.", "cooldown": 4, "effect": {"atk_pct": 0.8, "mana_cost": 15}},
        ],
        "epic": [
            {"id": "herbalist_deep_roots", "name": "Deep Roots", "type": "passive", "desc": "Regenerates health each turn, drawing strength from the earth.", "effect": {"regen_pct": 0.05}},
        ],
        "legendary": [
            {"id": "herbalist_purifying_mist", "name": "Purifying Mist", "type": "active", "desc": "Releases a cleansing mist, removing debuffs from an ally.", "cooldown": 5, "effect": {"cleanse_self": True}},
        ],
    },
    "Black Market Baron": {
        "common": [
            {"id": "baron_bribe", "name": "Bribe", "type": "active", "desc": "Corrupts an enemy, reducing their attack and defense.", "cooldown": 5, "effect": {"atk_pct": -0.15, "def_pct": -0.15}},
        ],
        "uncommon": [
            {"id": "baron_shady_dealings", "name": "Shady Dealings", "type": "passive", "desc": "The Baron's influence increases luck and provides self-healing.", "effect": {"lck_pct": 0.2, "self_heal_pct": 0.03}},
        ],
        "rare": [
            {"id": "baron_contraband_delivery", "name": "Contraband Delivery", "type": "active", "desc": "Supplies an ally with illicit goods, boosting their attack.", "cooldown": 4, "effect": {"atk_pct": 0.25}},
        ],
        "epic": [
            {"id": "baron_insurance_policy", "name": "Insurance Policy", "type": "passive", "desc": "A hidden clause provides a full heal upon death.", "effect": {"death_heal": True}},
        ],
        "legendary": [
            {"id": "baron_black_powder_bomb", "name": "Black Powder Bomb", "type": "active", "desc": "Throws a volatile bomb, dealing massive damage to enemies.", "cooldown": 6, "effect": {"atk_pct": 2.0, "mana_cost": 30}},
        ],
    },
    "Archdruid": {
        "common": [
            {"id": "archdruid_natures_embrace", "name": "Nature's Embrace", "type": "active", "desc": "Calls upon nature to rapidly heal all injured allies.", "cooldown": 4, "effect": {"heal_pct": 0.3}},
        ],
        "uncommon": [
            {"id": "archdruid_wild_kinship", "name": "Wild Kinship", "type": "passive", "desc": "The Archdruid draws power from the wild, boosting intellect and health.", "effect": {"int_pct": 0.2, "hlt_pct": 0.1}},
        ],
        "rare": [
            {"id": "archdruid_thunderstorm", "name": "Thunderstorm", "type": "active", "desc": "Summons a powerful storm, striking all enemies with lightning.", "cooldown": 5, "effect": {"atk_pct": 1.5, "mana_cost": 25}},
        ],
        "epic": [
            {"id": "archdruid_verdant_aura", "name": "Verdant Aura", "type": "passive", "desc": "A healing aura surrounds the Archdruid, regenerating health for self.", "effect": {"regen_pct": 0.07}},
        ],
        "legendary": [
            {"id": "archdruid_bear_form", "name": "Bear Form", "type": "active", "desc": "Shapeshifts into a mighty bear, greatly increasing strength and defense.", "cooldown": 6, "effect": {"str_pct": 0.3, "def_pct": 0.2}},
        ],
    },
    "Grandmaster": {
        "common": [
            {"id": "grandmaster_fists_of_fury", "name": "Fists of Fury", "type": "active", "desc": "Unleashes a rapid barrage of strikes, dealing high damage.", "cooldown": 3, "effect": {"atk_pct": 1.8}},
        ],
        "uncommon": [
            {"id": "grandmaster_inner_peace", "name": "Inner Peace", "type": "passive", "desc": "The Grandmaster's focus enhances agility and strength.", "effect": {"agi_pct": 0.15, "str_pct": 0.1}},
        ],
        "rare": [
            {"id": "grandmaster_zen_meditation", "name": "Zen Meditation", "type": "active", "desc": "Enters a meditative state, healing self and cleansing all debuffs.", "cooldown": 5, "effect": {"self_heal_pct": 0.2, "cleanse_self": True}},
        ],
        "epic": [
            {"id": "grandmaster_master_strike", "name": "Master Strike", "type": "passive", "desc": "Every blow has a chance to be a devastating crushing blow.", "effect": {"crushing_blow": True}},
        ],
        "legendary": [
            {"id": "grandmaster_pressure_point", "name": "Pressure Point", "type": "active", "desc": "Strikes a vital point, dealing immense damage with precision.", "cooldown": 6, "effect": {"atk_pct": 2.5, "mana_cost": 30}},
        ],
    },
    "Advisor": {
        "common": [
            {"id": "advisor_strategic_counsel", "name": "Strategic Counsel", "type": "active", "desc": "Provides invaluable advice, boosting all allies' stats.", "cooldown": 5, "effect": {"atk_pct": 0.1, "def_pct": 0.1}},
        ],
        "uncommon": [
            {"id": "advisor_calculated_risk", "name": "Calculated Risk", "type": "passive", "desc": "The Advisor's foresight grants increased intellect and defense.", "effect": {"int_pct": 0.15, "def_pct": 0.1}},
        ],
        "rare": [
            {"id": "advisor_foresight", "name": "Foresight", "type": "active", "desc": "Predicts enemy movements, reducing their attack and agility.", "cooldown": 4, "effect": {"atk_pct": -0.15, "agi_pct": -0.15}},
        ],
        "epic": [
            {"id": "advisor_contingency_plan", "name": "Contingency Plan", "type": "passive", "desc": "A failsafe ensures a full heal upon defeat, once per battle.", "effect": {"death_heal": True}},
        ],
        "legendary": [
            {"id": "advisor_inspiring_speech", "name": "Inspiring Speech", "type": "active", "desc": "Delivers an uplifting speech, cleansing allies and providing a small heal.", "cooldown": 6, "effect": {"cleanse_self": True, "heal_pct": 0.1}},
        ],
    },
    "Trickster": {
        "common": [
            {"id": "trickster_smoke_bomb", "name": "Smoke Bomb", "type": "active", "desc": "Throws a smoke bomb, debuffing enemies and boosting own agility.", "cooldown": 4, "effect": {"agi_pct": -0.15, "self_heal_pct": 0.05}},
        ],
        "uncommon": [
            {"id": "trickster_nimble_fingers", "name": "Nimble Fingers", "type": "passive", "desc": "The Trickster's quickness boosts agility and luck.", "effect": {"agi_pct": 0.2, "lck_pct": 0.1}},
        ],
        "rare": [
            {"id": "trickster_decoy", "name": "Decoy", "type": "active", "desc": "Creates an illusionary decoy, drawing enemy attacks and boosting defense.", "cooldown": 5, "effect": {"def_pct": 0.25}},
        ],
        "epic": [
            {"id": "trickster_lucky_shot", "name": "Lucky Shot", "type": "passive", "desc": "Every attack has a chance to be a devastating crushing blow.", "effect": {"crushing_blow": True}},
        ],
        "legendary": [
            {"id": "trickster_backstab", "name": "Backstab", "type": "active", "desc": "Strikes from the shadows, dealing immense critical damage.", "cooldown": 3, "effect": {"atk_pct": 2.2, "mana_cost": 20}},
        ],
    },
    "Warlord": {
        "common": [
            {"id": "warlord_battle_cry", "name": "Battle Cry", "type": "active", "desc": "Lets out a powerful roar, greatly increasing all allies' strength.", "cooldown": 4, "effect": {"str_pct": 0.25}},
        ],
        "uncommon": [
            {"id": "warlord_unyielding_will", "name": "Unyielding Will", "type": "passive", "desc": "The Warlord's resolve grants increased health and strength.", "effect": {"hlt_pct": 0.2, "str_pct": 0.1}},
        ],
        "rare": [
            {"id": "warlord_intimidate", "name": "Intimidate", "type": "active", "desc": "Glares at an enemy, reducing their defense and attack.", "cooldown": 5, "effect": {"def_pct": -0.2, "atk_pct": -0.1}},
        ],
        "epic": [
            {"id": "warlord_berserker_rage", "name": "Berserker Rage", "type": "passive", "desc": "When near defeat, the Warlord becomes enraged, greatly boosting damage.", "effect": {"enrage": True}},
        ],
        "legendary": [
            {"id": "warlord_devastating_charge", "name": "Devastating Charge", "type": "active", "desc": "Charges an enemy, dealing massive damage and increasing own defense.", "cooldown": 6, "effect": {"atk_pct": 2.0, "def_pct": 0.15}},
        ],
    },
    "Blacksmith": {
        "common": [
            {"id": "blacksmith_reinforce_armor", "name": "Reinforce Armor", "type": "active", "desc": "Strengthens an ally's armor, significantly boosting their defense.", "cooldown": 4, "effect": {"def_pct": 0.3}},
        ],
        "uncommon": [
            {"id": "blacksmith_sturdy_build", "name": "Sturdy Build", "type": "passive", "desc": "The Blacksmith's physique grants increased defense and strength.", "effect": {"def_pct": 0.15, "str_pct": 0.1}},
        ],
        "rare": [
            {"id": "blacksmith_molten_strike", "name": "Molten Strike", "type": "active", "desc": "Imbues a weapon with molten heat, dealing fire damage.", "cooldown": 3, "effect": {"atk_pct": 1.3, "mana_cost": 10}},
        ],
        "epic": [
            {"id": "blacksmith_enduring_forge", "name": "Enduring Forge", "type": "passive", "desc": "The heat of the forge grants continuous health regeneration.", "effect": {"regen_pct": 0.04}},
        ],
        "legendary": [
            {"id": "blacksmith_sharpen_blade", "name": "Sharpen Blade", "type": "active", "desc": "Hones an ally's weapon to a razor edge, boosting their attack.", "cooldown": 5, "effect": {"atk_pct": 0.2}},
        ],
    },
    "Spearman": {
        "common": [
            {"id": "spearman_piercing_thrust", "name": "Piercing Thrust", "type": "active", "desc": "A precise thrust that bypasses armor, dealing high damage.", "cooldown": 3, "effect": {"atk_pct": 1.6}},
        ],
        "uncommon": [
            {"id": "spearman_disciplined_stance", "name": "Disciplined Stance", "type": "passive", "desc": "The Spearman's training grants increased strength and defense.", "effect": {"str_pct": 0.15, "def_pct": 0.1}},
        ],
        "rare": [
            {"id": "spearman_brace_for_impact", "name": "Brace for Impact", "type": "active", "desc": "Braces with the spear, greatly increasing personal defense.", "cooldown": 4, "effect": {"def_pct": 0.25}},
        ],
        "epic": [
            {"id": "spearman_crit_vulnerability", "name": "Vulnerability Strike", "type": "passive", "desc": "Every attack has a chance to strike a vital point.", "effect": {"crushing_blow": True}},
        ],
        "legendary": [
            {"id": "spearman_sweeping_strike", "name": "Sweeping Strike", "type": "active", "desc": "Swings the spear in a wide arc, damaging multiple enemies.", "cooldown": 5, "effect": {"atk_pct": 1.1, "mana_cost": 15}},
        ],
    },
    "Master Farmer": {
        "common": [
            {"id": "farmer_fertile_ground", "name": "Fertile Ground", "type": "passive", "desc": "Allies gain increased maximum health and regeneration.", "effect": {"hlt_pct": 0.1, "regen_pct": 0.03}},
        ],
        "uncommon": [
            {"id": "farmer_bountiful_harvest", "name": "Bountiful Harvest", "type": "active", "desc": "Heals the lowest health ally with a burst of natural energy.", "cooldown": 4, "effect": {"heal_pct": 0.3}},
        ],
        "rare": [
            {"id": "farmer_rooted_resilience", "name": "Rooted Resilience", "type": "passive", "desc": "Gains bonus defense and occasionally cleanses self of debuffs.", "effect": {"def_pct": 0.15, "cleanse_self": True}},
        ],
        "epic": [
            {"id": "farmer_farmhands_fury", "name": "Farmhand's Fury", "type": "active", "desc": "A powerful strike using farming tools, with a crushing blow chance.", "cooldown": 3, "effect": {"atk_pct": 1.2, "crushing_blow": True}},
        ],
        "legendary": [
            {"id": "farmer_seed_of_life", "name": "Seed of Life", "type": "passive", "desc": "Upon defeat, heals the lowest health ally for a significant amount.", "effect": {"death_heal": True, "heal_pct": 0.4}},
        ],
    },
    "Forager": {
        "common": [
            {"id": "forager_swift_scavenger", "name": "Swift Scavenger", "type": "passive", "desc": "Increased agility and luck, making them harder to hit.", "effect": {"agi_pct": 0.15, "lck_pct": 0.1}},
        ],
        "uncommon": [
            {"id": "forager_herbal_remedy", "name": "Herbal Remedy", "type": "active", "desc": "Consumes wild herbs, healing self for a portion of max health.", "cooldown": 4, "effect": {"self_heal_pct": 0.25}},
        ],
        "rare": [
            {"id": "forager_trailblazer", "name": "Trailblazer", "type": "passive", "desc": "Gains a small bonus to attack and defense in the wilderness.", "effect": {"atk_pct": 0.05, "def_pct": 0.05}},
        ],
        "epic": [
            {"id": "forager_quick_strike", "name": "Quick Strike", "type": "active", "desc": "A rapid attack, striking enemies before they can react.", "cooldown": 2, "effect": {"atk_pct": 1.1}},
        ],
        "legendary": [
            {"id": "forager_survival_instinct", "name": "Survival Instinct", "type": "passive", "desc": "Heightened senses grant a chance to avoid incoming damage.", "effect": {"agi_pct": 0.1}},
        ],
    },
    "Vanguard": {
        "common": [
            {"id": "vanguard_shield_wall", "name": "Shield Wall", "type": "passive", "desc": "Greatly increased defense, protecting allies behind them.", "effect": {"def_pct": 0.25}},
        ],
        "uncommon": [
            {"id": "vanguard_taunt", "name": "Taunt", "type": "active", "desc": "Draws enemy aggression, forcing them to attack the Vanguard.", "cooldown": 5, "effect": {"def_pct": 0.1}},
        ],
        "rare": [
            {"id": "vanguard_bulwark", "name": "Bulwark", "type": "passive", "desc": "Possesses immense vitality, increasing maximum health significantly.", "effect": {"hlt_pct": 0.2}},
        ],
        "epic": [
            {"id": "vanguard_guard_stance", "name": "Guard Stance", "type": "active", "desc": "Adopts a defensive stance, reducing incoming damage for a short time.", "cooldown": 4, "effect": {"def_pct": 0.2}},
        ],
        "legendary": [
            {"id": "vanguard_unyielding_resolve", "name": "Unyielding Resolve", "type": "passive", "desc": "Becomes more resilient and powerful as health diminishes.", "effect": {"str_pct": 0.1, "def_pct": 0.1}},
        ],
    },
    "Warrior": {
        "common": [
            {"id": "warrior_mighty_blow", "name": "Mighty Blow", "type": "active", "desc": "Unleashes a devastating attack, dealing massive damage to a single foe.", "cooldown": 3, "effect": {"atk_pct": 1.8}},
        ],
        "uncommon": [
            {"id": "warrior_battle_hardened", "name": "Battle Hardened", "type": "passive", "desc": "Gains increased strength and maximum health from countless battles.", "effect": {"str_pct": 0.1, "hlt_pct": 0.1}},
        ],
        "rare": [
            {"id": "warrior_whirlwind", "name": "Whirlwind", "type": "active", "desc": "Spins weapon in a deadly arc, damaging all nearby enemies.", "cooldown": 4, "effect": {"atk_pct": 1.0}},
        ],
        "epic": [
            {"id": "warrior_enraged_strike", "name": "Enraged Strike", "type": "passive", "desc": "Sometimes enters a furious rage, dealing extra damage with attacks.", "effect": {"enrage": True}},
        ],
        "legendary": [
            {"id": "warrior_adrenaline_rush", "name": "Adrenaline Rush", "type": "active", "desc": "Heals from battle wounds and gains temporary strength.", "cooldown": 5, "effect": {"self_heal_pct": 0.15, "str_pct": 0.1}},
        ],
    },
    "Dragon Knight": {
        "common": [
            {"id": "dk_dragons_breath", "name": "Dragon's Breath", "type": "active", "desc": "Unleashes a cone of fire, scorching multiple enemies.", "cooldown": 4, "effect": {"atk_pct": 1.3, "mana_cost": 30}},
        ],
        "uncommon": [
            {"id": "dk_draconic_scales", "name": "Draconic Scales", "type": "passive", "desc": "Tough scales grant increased defense and magical resilience.", "effect": {"def_pct": 0.15, "hlt_pct": 0.05}},
        ],
        "rare": [
            {"id": "dk_flaming_weapon", "name": "Flaming Weapon", "type": "passive", "desc": "Infuses weapon with fire, dealing bonus damage on every strike.", "effect": {"atk_pct": 0.1}},
        ],
        "epic": [
            {"id": "dk_wyrms_vigor", "name": "Wyrm's Vigor", "type": "active", "desc": "Channels draconic vitality, healing self and boosting strength.", "cooldown": 5, "effect": {"self_heal_pct": 0.2, "str_pct": 0.1}},
        ],
        "legendary": [
            {"id": "dk_dragonheart", "name": "Dragonheart", "type": "passive", "desc": "Possesses a dragon's heart, granting immense health and regeneration.", "effect": {"hlt_pct": 0.1, "regen_pct": 0.05}},
        ],
    },
    "Scout": {
        "common": [
            {"id": "scout_aimed_shot", "name": "Aimed Shot", "type": "active", "desc": "Fires a precise shot, dealing significant damage to a single target.", "cooldown": 3, "effect": {"atk_pct": 1.7}},
        ],
        "uncommon": [
            {"id": "scout_evasion", "name": "Evasion", "type": "passive", "desc": "Exceptional agility makes them incredibly hard to hit.", "effect": {"agi_pct": 0.2}},
        ],
        "rare": [
            {"id": "scout_poison_arrow", "name": "Poison Arrow", "type": "active", "desc": "Shoots an arrow coated in potent venom, inflicting damage over time.", "cooldown": 4, "effect": {"atk_pct": 0.8}},
        ],
        "epic": [
            {"id": "scout_eagle_eye", "name": "Eagle Eye", "type": "passive", "desc": "Unparalleled vision grants increased critical hit chance and damage.", "effect": {"lck_pct": 0.15}},
        ],
        "legendary": [
            {"id": "scout_fleet_footed", "name": "Fleet Footed", "type": "passive", "desc": "Moves with incredible speed, further enhancing agility.", "effect": {"agi_pct": 0.1}},
        ],
    },
    "Commander": {
        "common": [
            {"id": "commander_inspiring_presence", "name": "Inspiring Presence", "type": "passive", "desc": "Allies within range gain a bonus to their attack power.", "effect": {"str_pct": 0.1}},
        ],
        "uncommon": [
            {"id": "commander_rallying_cry", "name": "Rallying Cry", "type": "active", "desc": "Lets out a powerful cry, healing and empowering all allies.", "cooldown": 5, "effect": {"heal_pct": 0.15, "atk_pct": 0.1}},
        ],
        "rare": [
            {"id": "commander_tactical_advantage", "name": "Tactical Advantage", "type": "passive", "desc": "Applies strategic insights, increasing allies' defensive capabilities.", "effect": {"def_pct": 0.1}},
        ],
        "epic": [
            {"id": "commander_order_advance", "name": "Order: Advance!", "type": "active", "desc": "Commands allies to advance, boosting their attack and agility.", "cooldown": 4, "effect": {"atk_pct": 0.1, "agi_pct": 0.1}},
        ],
        "legendary": [
            {"id": "commander_iron_discipline", "name": "Iron Discipline", "type": "passive", "desc": "Possesses unwavering resolve, granting increased health and defense.", "effect": {"hlt_pct": 0.1, "def_pct": 0.05}},
        ],
    },
    "Demonologist": {
        "common": [
            {"id": "demonologist_soul_siphon", "name": "Soul Siphon", "type": "active", "desc": "Drains life force from an enemy, dealing damage and healing the caster.", "cooldown": 3, "effect": {"atk_pct": 1.2, "self_heal_pct": 0.1, "mana_cost": 20}},
        ],
        "uncommon": [
            {"id": "demonologist_demonic_pact", "name": "Demonic Pact", "type": "passive", "desc": "Forges a pact for immense power, boosting intelligence.", "effect": {"int_pct": 0.2}},
        ],
        "rare": [
            {"id": "demonologist_curse_of_weakness", "name": "Curse of Weakness", "type": "active", "desc": "Inflicts a curse, weakening an enemy's defenses.", "cooldown": 4, "effect": {"mana_cost": 25}},
        ],
        "epic": [
            {"id": "demonologist_infernal_gate", "name": "Infernal Gate", "type": "passive", "desc": "Opens minor rifts, channeling demonic energy to boost attack.", "effect": {"atk_pct": 0.1, "int_pct": 0.05}},
        ],
        "legendary": [
            {"id": "demonologist_abyssal_ward", "name": "Abyssal Ward", "type": "passive", "desc": "Surrounds self with dark energy, regenerating mana over time.", "effect": {"int_pct": 0.1}},
        ],
    },
    "Shadowblade": {
        "common": [
            {"id": "shadowblade_backstab", "name": "Backstab", "type": "active", "desc": "Strikes from the shadows, dealing massive critical damage.", "cooldown": 3, "effect": {"atk_pct": 2.0, "lck_pct": 0.2}},
        ],
        "uncommon": [
            {"id": "shadowblade_shrouded_step", "name": "Shrouded Step", "type": "passive", "desc": "Moves with impossible silence, greatly increasing agility and evasion.", "effect": {"agi_pct": 0.2}},
        ],
        "rare": [
            {"id": "shadowblade_poisoned_edge", "name": "Poisoned Edge", "type": "passive", "desc": "Coats blades in potent poison, dealing damage over time.", "effect": {"atk_pct": 0.1}},
        ],
        "epic": [
            {"id": "shadowblade_smoke_bomb", "name": "Smoke Bomb", "type": "active", "desc": "Throws a smoke bomb, disorienting enemies and boosting own agility.", "cooldown": 4, "effect": {"agi_pct": 0.15}},
        ],
        "legendary": [
            {"id": "shadowblade_assassinate", "name": "Assassinate", "type": "passive", "desc": "Excels at finishing off weakened foes, dealing bonus damage.", "effect": {"atk_pct": 0.15, "lck_pct": 0.05}},
        ],
    },
    "Beast Tamer": {
        "common": [
            {"id": "beast_tamer_call_companion", "name": "Call Companion", "type": "passive", "desc": "Always fights alongside a loyal animal companion, boosting overall strength.", "effect": {"str_pct": 0.1, "hlt_pct": 0.05}},
        ],
        "uncommon": [
            {"id": "beast_tamer_feral_slash", "name": "Feral Slash", "type": "active", "desc": "Commands companion to unleash a savage attack, with a crushing blow chance.", "cooldown": 3, "effect": {"atk_pct": 1.4, "crushing_blow": True}},
        ],
        "rare": [
            {"id": "beast_tamer_natures_bond", "name": "Nature's Bond", "type": "passive", "desc": "A deep connection to nature grants regeneration to both tamer and companion.", "effect": {"regen_pct": 0.04, "self_heal_pct": 0.02}},
        ],
        "epic": [
            {"id": "beast_tamer_protective_roar", "name": "Protective Roar", "type": "active", "desc": "Companion roars, drawing enemy attention and boosting defenses.", "cooldown": 5, "effect": {"def_pct": 0.15}},
        ],
        "legendary": [
            {"id": "beast_tamer_wild_instincts", "name": "Wild Instincts", "type": "passive", "desc": "Sharpens senses for both tamer and companion, increasing agility and luck.", "effect": {"agi_pct": 0.1, "lck_pct": 0.05}},
        ],
    },
    "Shadowmaster": {
        "common": [
            {"id": "shadowmaster_shadow_strike", "name": "Shadow Strike", "type": "active", "desc": "Strikes from shadows, dealing damage and draining life.", "cooldown": 4, "effect": {"atk_pct": 1.8, "self_heal_pct": 0.3}},
        ],
        "uncommon": [
            {"id": "shadowmaster_cloak_of_darkness", "name": "Cloak of Darkness", "type": "active", "desc": "Vanish into shadows, regenerating health while hidden.", "cooldown": 6, "effect": {"regen_pct": 0.1, "mana_cost": 30}},
        ],
        "rare": [
            {"id": "shadowmaster_twilight_veil", "name": "Twilight Veil", "type": "passive", "desc": "Permanently shrouded in darkness, increasing agility and luck.", "effect": {"agi_pct": 0.15, "lck_pct": 0.1}},
        ],
        "epic": [
            {"id": "shadowmaster_soul_siphon", "name": "Soul Siphon", "type": "active", "desc": "Drains enemy life force, healing self significantly.", "cooldown": 5, "effect": {"atk_pct": 1.2, "self_heal_pct": 0.5}},
        ],
        "legendary": [
            {"id": "shadowmaster_master_of_shadows", "name": "Master of Shadows", "type": "passive", "desc": "Gains increased intelligence and a chance for crushing blows.", "effect": {"int_pct": 0.2, "crushing_blow": True}},
        ],
    },
    "Field Medic": {
        "common": [
            {"id": "fieldmedic_triage", "name": "Triage", "type": "active", "desc": "Rapidly heals the most injured ally, keeping them in the fight.", "cooldown": 3, "effect": {"heal_pct": 0.4}},
        ],
        "uncommon": [
            {"id": "fieldmedic_combat_readiness", "name": "Combat Readiness", "type": "passive", "desc": "Enhanced defenses and health ensure the medic's survival.", "effect": {"def_pct": 0.15, "hlt_pct": 0.1}},
        ],
        "rare": [
            {"id": "fieldmedic_emergency_patch", "name": "Emergency Patch", "type": "active", "desc": "Cleanses own debuffs and heals the most injured ally.", "cooldown": 5, "effect": {"cleanse_self": True, "heal_pct": 0.2}},
        ],
        "epic": [
            {"id": "fieldmedic_medical_expertise", "name": "Medical Expertise", "type": "passive", "desc": "The medic's healing abilities are enhanced, increasing intellect and regeneration.", "effect": {"int_pct": 0.2, "regen_pct": 0.05}},
        ],
        "legendary": [
            {"id": "fieldmedic_life_giver", "name": "Life Giver", "type": "active", "desc": "Provides a powerful burst of healing to a critical ally.", "cooldown": 6, "effect": {"heal_pct": 0.6, "mana_cost": 40}},
        ],
    },
    "Dragoon": {
        "common": [
            {"id": "dragoon_dragons_descent", "name": "Dragon's Descent", "type": "active", "desc": "Leaps and strikes foes with overwhelming force, crushing impact.", "cooldown": 4, "effect": {"atk_pct": 2.0, "crushing_blow": True}},
        ],
        "uncommon": [
            {"id": "dragoon_lance_charge", "name": "Lance Charge", "type": "active", "desc": "Charges forward, dealing damage and entering a temporary enraged state.", "cooldown": 5, "effect": {"atk_pct": 1.5, "enrage": True}},
        ],
        "rare": [
            {"id": "dragoon_wyrmskin_armor", "name": "Wyrmskin Armor", "type": "passive", "desc": "Tough scales provide significant defense and increased maximum health.", "effect": {"def_pct": 0.25, "hlt_pct": 0.15}},
        ],
        "epic": [
            {"id": "dragoon_aerial_acumen", "name": "Aerial Acumen", "type": "passive", "desc": "Enhanced agility and luck from aerial combat experience.", "effect": {"agi_pct": 0.15, "lck_pct": 0.1}},
        ],
        "legendary": [
            {"id": "dragoon_draconic_fury", "name": "Draconic Fury", "type": "passive", "desc": "Unleashes inner draconic strength, boosting attack power and damage.", "effect": {"str_pct": 0.2, "atk_pct": 0.1}},
        ],
    },
    "Marksman": {
        "common": [
            {"id": "marksman_headshot", "name": "Headshot", "type": "active", "desc": "A precision shot, dealing massive damage with crushing blow potential.", "cooldown": 4, "effect": {"atk_pct": 2.2, "crushing_blow": True}},
        ],
        "uncommon": [
            {"id": "marksman_quickdraw", "name": "Quickdraw", "type": "passive", "desc": "Faster reflexes and increased luck for rapid, critical attacks.", "effect": {"agi_pct": 0.2, "lck_pct": 0.15}},
        ],
        "rare": [
            {"id": "marksman_hunters_mark", "name": "Hunter's Mark", "type": "active", "desc": "Marks a target, dealing damage and making them vulnerable.", "cooldown": 3, "effect": {"atk_pct": 1.3, "mana_cost": 20}},
        ],
        "epic": [
            {"id": "marksman_eagle_eye", "name": "Eagle Eye", "type": "passive", "desc": "Unparalleled vision grants increased intelligence and attack power.", "effect": {"int_pct": 0.15, "atk_pct": 0.1}},
        ],
        "legendary": [
            {"id": "marksman_steady_aim", "name": "Steady Aim", "type": "passive", "desc": "Solid stance increases strength and defense, preventing disruption.", "effect": {"str_pct": 0.1, "def_pct": 0.1}},
        ],
    },
    "Summoner": {
        "common": [
            {"id": "summoner_call_lesser_spirit", "name": "Call Lesser Spirit", "type": "active", "desc": "Summons a minor spirit to attack a foe, dealing damage.", "cooldown": 3, "effect": {"atk_pct": 1.2, "mana_cost": 25}},
        ],
        "uncommon": [
            {"id": "summoner_ethereal_bond", "name": "Ethereal Bond", "type": "passive", "desc": "Strong connection to spirits increases the summoner's intellect and health.", "effect": {"int_pct": 0.2, "hlt_pct": 0.1}},
        ],
        "rare": [
            {"id": "summoner_spirit_shield", "name": "Spirit Shield", "type": "active", "desc": "Summons a protective spirit, granting temporary defense and self-healing.", "cooldown": 6, "effect": {"def_pct": 0.3, "self_heal_pct": 0.1}},
        ],
        "epic": [
            {"id": "summoner_arcane_mastery", "name": "Arcane Mastery", "type": "passive", "desc": "Deep understanding of magic enhances intellect and luck.", "effect": {"int_pct": 0.15, "lck_pct": 0.1}},
        ],
        "legendary": [
            {"id": "summoner_greater_summon", "name": "Greater Summon", "type": "active", "desc": "Calls forth a powerful spirit, unleashing a devastating attack.", "cooldown": 8, "effect": {"atk_pct": 2.5, "mana_cost": 50}},
        ],
    },
    "Crusader": {
        "common": [
            {"id": "crusader_holy_smite", "name": "Holy Smite", "type": "active", "desc": "Strikes an enemy with divine force, healing the crusader.", "cooldown": 4, "effect": {"atk_pct": 1.5, "self_heal_pct": 0.25}},
        ],
        "uncommon": [
            {"id": "crusader_divine_aegis", "name": "Divine Aegis", "type": "active", "desc": "Forms a holy shield, boosting defense and cleansing self.", "cooldown": 5, "effect": {"def_pct": 0.3, "cleanse_self": True}},
        ],
        "rare": [
            {"id": "crusader_faiths_bulwark", "name": "Faith's Bulwark", "type": "passive", "desc": "Unwavering faith grants immense health and physical defense.", "effect": {"hlt_pct": 0.2, "def_pct": 0.15}},
        ],
        "epic": [
            {"id": "crusader_zealous_charge", "name": "Zealous Charge", "type": "active", "desc": "Charges into battle, damaging foes and entering an enraged state.", "cooldown": 6, "effect": {"atk_pct": 1.7, "enrage": True}},
        ],
        "legendary": [
            {"id": "crusader_martyrs_resolve", "name": "Martyr's Resolve", "type": "passive", "desc": "Gains strength and heals upon taking fatal damage.", "effect": {"death_heal": True, "str_pct": 0.15}},
        ],
    },
    "Surgeon": {
        "common": [
            {"id": "surgeon_precision_incision", "name": "Precision Incision", "type": "active", "desc": "A surgical strike dealing high damage with crushing blow potential.", "cooldown": 3, "effect": {"atk_pct": 1.9, "crushing_blow": True}},
        ],
        "uncommon": [
            {"id": "surgeon_sterile_field", "name": "Sterile Field", "type": "active", "desc": "Cleanses own ailments and provides minor self-healing.", "cooldown": 4, "effect": {"cleanse_self": True, "self_heal_pct": 0.1}},
        ],
        "rare": [
            {"id": "surgeon_medical_resilience", "name": "Medical Resilience", "type": "passive", "desc": "The surgeon's body is resilient, increasing health and regeneration.", "effect": {"hlt_pct": 0.15, "regen_pct": 0.05}},
        ],
        "epic": [
            {"id": "surgeon_organ_harvest", "name": "Organ Harvest", "type": "active", "desc": "Extracts vital essence from an enemy, dealing damage and healing self.", "cooldown": 5, "effect": {"atk_pct": 1.3, "self_heal_pct": 0.35}},
        ],
        "legendary": [
            {"id": "surgeon_aseptic_technique", "name": "Aseptic Technique", "type": "passive", "desc": "Increases precision and speed, boosting intellect and agility.", "effect": {"int_pct": 0.15, "agi_pct": 0.1}},
        ],
    },
    "Alchemist": {
        "common": [
            {"id": "alchemist_volatile_concoction", "name": "Volatile Concoction", "type": "active", "desc": "Hurls a damaging potion at foes, causing an explosion.", "cooldown": 3, "effect": {"atk_pct": 1.6, "mana_cost": 25}},
        ],
        "uncommon": [
            {"id": "alchemist_healing_elixir", "name": "Healing Elixir", "type": "active", "desc": "Throws a healing potion to the most injured ally.", "cooldown": 4, "effect": {"heal_pct": 0.3, "mana_cost": 30}},
        ],
        "rare": [
            {"id": "alchemist_alchemical_resilience", "name": "Alchemical Resilience", "type": "passive", "desc": "Potions enhance natural defenses and regeneration.", "effect": {"def_pct": 0.15, "regen_pct": 0.05}},
        ],
        "epic": [
            {"id": "alchemist_transmutation", "name": "Transmutation", "type": "passive", "desc": "Mastery of elements increases intellect and luck.", "effect": {"int_pct": 0.2, "lck_pct": 0.1}},
        ],
        "legendary": [
            {"id": "alchemist_berserker_brew", "name": "Berserker Brew", "type": "active", "desc": "Drinks a potent brew, entering an enraged state.", "cooldown": 6, "effect": {"enrage": True, "mana_cost": 35}},
        ],
    },
    "Juggernaut": {
        "common": [
            {"id": "juggernaut_ground_slam", "name": "Ground Slam", "type": "active", "desc": "Slams the ground, dealing massive damage and a crushing blow.", "cooldown": 4, "effect": {"atk_pct": 2.1, "crushing_blow": True}},
        ],
        "uncommon": [
            {"id": "juggernaut_unstoppable_force", "name": "Unstoppable Force", "type": "passive", "desc": "Immense strength and defense make the juggernaut unstoppable.", "effect": {"str_pct": 0.25, "def_pct": 0.2}},
        ],
        "rare": [
            {"id": "juggernaut_rampage", "name": "Rampage", "type": "active", "desc": "Goes on a destructive rampage, dealing damage and becoming enraged.", "cooldown": 5, "effect": {"atk_pct": 1.6, "enrage": True}},
        ],
        "epic": [
            {"id": "juggernaut_thick_hide", "name": "Thick Hide", "type": "passive", "desc": "Tough skin grants increased health and passive regeneration.", "effect": {"hlt_pct": 0.25, "regen_pct": 0.05}},
        ],
        "legendary": [
            {"id": "juggernaut_last_stand", "name": "Last Stand", "type": "passive", "desc": "Upon death, heals self and gains temporary defense.", "effect": {"death_heal": True, "def_pct": 0.1}},
        ],
    },
    "Nightstalker": {
        "common": [
            {"id": "nightstalker_ambush", "name": "Ambush", "type": "active", "desc": "Surprise attack from stealth, dealing massive crushing damage.", "cooldown": 4, "effect": {"atk_pct": 2.3, "crushing_blow": True}},
        ],
        "uncommon": [
            {"id": "nightstalker_shadow_step", "name": "Shadow Step", "type": "active", "desc": "Teleports behind an enemy, delivering a swift, powerful strike.", "cooldown": 3, "effect": {"atk_pct": 1.7, "mana_cost": 20}},
        ],
        "rare": [
            {"id": "nightstalker_night_vision", "name": "Night Vision", "type": "passive", "desc": "Enhanced senses grant superior agility and luck in darkness.", "effect": {"agi_pct": 0.2, "lck_pct": 0.15}},
        ],
        "epic": [
            {"id": "nightstalker_cloak_of_deception", "name": "Cloak of Deception", "type": "passive", "desc": "Shrouded in deceit, gaining defense and cunning.", "effect": {"def_pct": 0.1, "int_pct": 0.15}},
        ],
        "legendary": [
            {"id": "nightstalker_preys_demise", "name": "Prey's Demise", "type": "passive", "desc": "Focuses on weak points, increasing attack power and strength.", "effect": {"atk_pct": 0.15, "str_pct": 0.1}},
        ],
    },
    "Grand Summoner": {
        "common": [
            {"id": "mystic_bond", "name": "Mystic Bond", "type": "passive", "desc": "Summoned allies gain increased health and magical power.", "effect": {"hlt_pct": 0.1, "int_pct": 0.1}},
        ],
        "uncommon": [
            {"id": "ethereal_ally", "name": "Ethereal Ally", "type": "active", "desc": "Summons a temporary ethereal minion to fight alongside.", "cooldown": 5, "effect": {"atk_pct": 0.8}},
        ],
        "rare": [
            {"id": "arcane_echoes", "name": "Arcane Echoes", "type": "passive", "desc": "Reduces summon cooldowns, increasing magical efficiency.", "effect": {"int_pct": 0.15}},
        ],
        "epic": [
            {"id": "sacrificial_pact", "name": "Sacrificial Pact", "type": "active", "desc": "Sacrifice a minion for a burst of self-healing and damage.", "cooldown": 8, "effect": {"atk_pct": 1.2, "self_heal_pct": 0.2}},
        ],
        "legendary": [
            {"id": "legions_might", "name": "Legion's Might", "type": "passive", "desc": "Gains power from each active summoned minion.", "effect": {"str_pct": 0.05, "int_pct": 0.05}},
        ],
    },
    "Spy": {
        "common": [
            {"id": "silent_strike", "name": "Silent Strike", "type": "passive", "desc": "Increases critical hit chance and critical damage.", "effect": {"lck_pct": 0.15, "agi_pct": 0.05}},
        ],
        "uncommon": [
            {"id": "vulnerable_point", "name": "Vulnerable Point", "type": "active", "desc": "Strikes an enemy's weakness, dealing damage and reducing defense.", "cooldown": 4, "effect": {"atk_pct": 1.2, "def_pct": -0.15}},
        ],
        "rare": [
            {"id": "elusive_footwork", "name": "Elusive Footwork", "type": "passive", "desc": "Increases dodge chance after taking damage.", "effect": {"agi_pct": 0.1}},
        ],
        "epic": [
            {"id": "shadow_veil", "name": "Shadow Veil", "type": "active", "desc": "Vanish from sight, becoming untargetable and healing slightly.", "cooldown": 7, "effect": {"self_heal_pct": 0.1, "agi_pct": 0.2}},
        ],
        "legendary": [
            {"id": "intel_report", "name": "Intel Report", "type": "passive", "desc": "Reveals enemy weaknesses, increasing damage dealt to them.", "effect": {"atk_pct": 0.1}},
        ],
    },
    "Trader": {
        "common": [
            {"id": "resourceful", "name": "Resourceful", "type": "passive", "desc": "Generates extra resources or gold each turn.", "effect": {"lck_pct": 0.1}},
        ],
        "uncommon": [
            {"id": "market_advantage", "name": "Market Advantage", "type": "active", "desc": "Buffs an ally's primary stat for a short duration.", "cooldown": 6, "effect": {"str_pct": 0.15, "int_pct": 0.15}},
        ],
        "rare": [
            {"id": "bargain_hunter", "name": "Bargain Hunter", "type": "passive", "desc": "Reduces item costs and enhances their effects.", "effect": {"lck_pct": 0.15}},
        ],
        "epic": [
            {"id": "shrewd_deal", "name": "Shrewd Deal", "type": "active", "desc": "Removes all debuffs from self, cleansing negative effects.", "cooldown": 10, "effect": {"cleanse_self": True}},
        ],
        "legendary": [
            {"id": "steady_income", "name": "Steady Income", "type": "passive", "desc": "Allies gain a small amount of healing over time.", "effect": {"regen_pct": 0.03}},
        ],
    },
    "Smuggler": {
        "common": [
            {"id": "contraband_cache", "name": "Contraband Cache", "type": "passive", "desc": "Chance to find rare items after combat.", "effect": {"lck_pct": 0.2}},
        ],
        "uncommon": [
            {"id": "hidden_detonator", "name": "Hidden Detonator", "type": "active", "desc": "Throws a concealed explosive, dealing area damage to enemies.", "cooldown": 5, "effect": {"atk_pct": 0.9}},
        ],
        "rare": [
            {"id": "desperate_dodge", "name": "Desperate Dodge", "type": "passive", "desc": "Increased evasion when health is low.", "effect": {"agi_pct": 0.15}},
        ],
        "epic": [
            {"id": "smoke_screen", "name": "Smoke Screen", "type": "active", "desc": "Deploys a smoke screen, cleansing self and gaining speed.", "cooldown": 7, "effect": {"cleanse_self": True, "agi_pct": 0.15}},
        ],
        "legendary": [
            {"id": "opportunist", "name": "Opportunist", "type": "passive", "desc": "Deals bonus damage to debuffed enemies.", "effect": {"atk_pct": 0.1}},
        ],
    },
    "Weaponsmith": {
        "common": [
            {"id": "master_armorer", "name": "Master Armorer", "type": "passive", "desc": "Allies gain bonus attack damage and defense.", "effect": {"str_pct": 0.07, "def_pct": 0.07}},
        ],
        "uncommon": [
            {"id": "sharpen_edge", "name": "Sharpen Edge", "type": "active", "desc": "Grants a massive temporary damage buff to an ally.", "cooldown": 6, "effect": {"atk_pct": 0.5}},
        ],
        "rare": [
            {"id": "sundering_blow", "name": "Sundering Blow", "type": "passive", "desc": "Has a chance to deal massive crushing blow damage.", "effect": {"crushing_blow": True}},
        ],
        "epic": [
            {"id": "reinforce_armor", "name": "Reinforce Armor", "type": "active", "desc": "Provides a temporary defense buff to an ally.", "cooldown": 5, "effect": {"def_pct": 0.2}},
        ],
        "legendary": [
            {"id": "True_craftsmanship", "name": "True Craftsmanship", "type": "passive", "desc": "Gains bonus stats based on equipped weapon rarity.", "effect": {"str_pct": 0.1, "def_pct": 0.05}},
        ],
    },
    "Infiltrator": {
        "common": [
            {"id": "isolated_prey", "name": "Isolated Prey", "type": "passive", "desc": "Increased critical damage against isolated targets.", "effect": {"atk_pct": 0.15, "lck_pct": 0.1}},
        ],
        "uncommon": [
            {"id": "systems_sabotage", "name": "Systems Sabotage", "type": "active", "desc": "Deals damage and reduces an enemy's attack power.", "cooldown": 4, "effect": {"atk_pct": 1.1, "str_pct": -0.1}},
        ],
        "rare": [
            {"id": "fluid_movement", "name": "Fluid Movement", "type": "passive", "desc": "Gains Agility after successfully dodging an attack.", "effect": {"agi_pct": 0.1}},
        ],
        "epic": [
            {"id": "disorienting_gas", "name": "Disorienting Gas", "type": "active", "desc": "Damages enemies and reduces their accuracy.", "cooldown": 6, "effect": {"atk_pct": 0.8, "agi_pct": -0.1}},
        ],
        "legendary": [
            {"id": "first_strike", "name": "First Strike", "type": "passive", "desc": "Starts combat with a temporary stealth buff.", "effect": {"agi_pct": 0.1}},
        ],
    },
    "Priest": {
        "common": [
            {"id": "divine_grace", "name": "Divine Grace", "type": "passive", "desc": "Increased healing done by the Priest.", "effect": {"heal_pct": 0.2}},
        ],
        "uncommon": [
            {"id": "healing_prayer", "name": "Healing Prayer", "type": "active", "desc": "Heals the lowest health ally for a significant amount.", "cooldown": 3, "effect": {"heal_pct": 0.3}},
        ],
        "rare": [
            {"id": "holy_ward", "name": "Holy Ward", "type": "passive", "desc": "Allies gain a small amount of magic resistance.", "effect": {"def_pct": 0.08}},
        ],
        "epic": [
            {"id": "sacred_aegis", "name": "Sacred Aegis", "type": "active", "desc": "Protects an ally from a portion of incoming damage.", "cooldown": 8, "effect": {"def_pct": 0.3}},
        ],
        "legendary": [
            {"id": "purification_aura", "name": "Purification Aura", "type": "passive", "desc": "Allies gain a small amount of health regeneration.", "effect": {"regen_pct": 0.05}},
        ],
    },
    "Grand Strategist": {
        "common": [
            {"id": "coordinated_effort", "name": "Coordinated Effort", "type": "passive", "desc": "All allies gain a small bonus to all stats.", "effect": {"str_pct": 0.05, "int_pct": 0.05}},
        ],
        "uncommon": [
            {"id": "tactical_maneuver", "name": "Tactical Maneuver", "type": "active", "desc": "Buffs all allies' attack and defense temporarily.", "cooldown": 7, "effect": {"str_pct": 0.15, "def_pct": 0.15}},
        ],
        "rare": [
            {"id": "calculated_risk", "name": "Calculated Risk", "type": "passive", "desc": "Reduces enemy critical hit chance against allies.", "effect": {"def_pct": 0.1}},
        ],
        "epic": [
            {"id": "exploit_weakness", "name": "Exploit Weakness", "type": "active", "desc": "Debuffs an enemy's defense, making them vulnerable.", "cooldown": 4, "effect": {"def_pct": -0.2}},
        ],
        "legendary": [
            {"id": "strategic_reserves", "name": "Strategic Reserves", "type": "passive", "desc": "Reduces cooldowns for all allies' active skills.", "effect": {"int_pct": 0.1}},
        ],
    },
    "Butcher": {
        "common": [
            {"id": "grave_feast", "name": "Grave Feast", "type": "passive", "desc": "Heals a portion of health on killing blows.", "effect": {"death_heal": True}},
        ],
        "uncommon": [
            {"id": "flesh_render", "name": "Flesh Render", "type": "active", "desc": "Deals damage and applies a bleeding effect to the target.", "cooldown": 4, "effect": {"atk_pct": 1.3, "regen_pct": -0.05}},
        ],
        "rare": [
            {"id": "bloodlust", "name": "Bloodlust", "type": "passive", "desc": "Becomes enraged when health is low, increasing damage.", "effect": {"enrage": True}},
        ],
        "epic": [
            {"id": "harvesters_hook", "name": "Harvester's Hook", "type": "active", "desc": "Pulls an enemy closer, dealing damage.", "cooldown": 6, "effect": {"atk_pct": 1.5}},
        ],
        "legendary": [
            {"id": "tenderize", "name": "Tenderize", "type": "passive", "desc": "Attacks reduce enemy defense slightly.", "effect": {"atk_pct": 0.08, "def_pct": -0.05}},
        ],
    },
    "Wyvern Rider": {
        "common": [
            {"id": "aerial_superiority", "name": "Aerial Superiority", "type": "passive", "desc": "Increased damage from aerial attacks and improved mobility.", "effect": {"atk_pct": 0.1, "agi_pct": 0.05}},
        ],
        "uncommon": [
            {"id": "swooping_strike", "name": "Swooping Strike", "type": "active", "desc": "Performs a dive bomb, dealing area damage to enemies.", "cooldown": 5, "effect": {"atk_pct": 1.1}},
        ],
        "rare": [
            {"id": "taloned_grip", "name": "Taloned Grip", "type": "passive", "desc": "Wyvern's attacks have a chance to stun enemies.", "effect": {"lck_pct": 0.1}},
        ],
        "epic": [
            {"id": "skyfall_barrage", "name": "Skyfall Barrage", "type": "active", "desc": "Pelts enemies with a barrage of piercing feathers.", "cooldown": 4, "effect": {"atk_pct": 0.9}},
        ],
        "legendary": [
            {"id": "dragonkin_bond", "name": "Dragonkin Bond", "type": "passive", "desc": "Gains bonus Agility and Defense while mounted.", "effect": {"agi_pct": 0.1, "def_pct": 0.08}},
        ],
    },
    "Arbalist": {
        "common": [
            {"id": "arbalist_piercing_shot", "name": "Piercing Shot", "type": "active", "desc": "Fires a powerful bolt, ignoring enemy defenses and dealing massive damage.", "cooldown": 4, "effect": {"atk_pct": 2.0, "def_pct": -0.2}},
        ],
        "uncommon": [
            {"id": "arbalist_keen_aim", "name": "Keen Aim", "type": "passive", "desc": "Increased precision grants a higher chance to land critical hits.", "effect": {"lck_pct": 0.15, "atk_pct": 0.1}},
        ],
        "rare": [
            {"id": "arbalist_volley", "name": "Volley", "type": "active", "desc": "Unleashes a flurry of arrows, hitting multiple enemies in an area.", "cooldown": 5, "effect": {"atk_pct": 1.2}},
        ],
        "epic": [
            {"id": "arbalist_rapid_reload", "name": "Rapid Reload", "type": "passive", "desc": "The Arbalist's attacks are swifter, reducing cooldowns for active skills.", "effect": {"agi_pct": 0.1, "str_pct": 0.05}},
        ],
        "legendary": [
            {"id": "arbalist_crippling_bolt", "name": "Crippling Bolt", "type": "active", "desc": "A specialized bolt that slows and weakens a single target's defense.", "cooldown": 3, "effect": {"atk_pct": 0.8, "def_pct": -0.15}},
        ],
    },
    "Confessor": {
        "common": [
            {"id": "confessor_divine_grace", "name": "Divine Grace", "type": "active", "desc": "Heals the most injured ally with a burst of holy light.", "cooldown": 4, "effect": {"heal_pct": 0.3}},
        ],
        "uncommon": [
            {"id": "confessor_aegis_of_faith", "name": "Aegis of Faith", "type": "passive", "desc": "A holy aura grants nearby allies increased defense.", "effect": {"def_pct": 0.15}},
        ],
        "rare": [
            {"id": "confessor_exorcism", "name": "Exorcism", "type": "active", "desc": "Cleanses all debuffs from an ally and deals minor holy damage.", "cooldown": 6, "effect": {"cleanse_self": True, "atk_pct": 0.5}},
        ],
        "epic": [
            {"id": "confessor_righteous_fury", "name": "Righteous Fury", "type": "passive", "desc": "Attacks have a chance to deal bonus holy damage.", "effect": {"atk_pct": 0.15, "int_pct": 0.1}},
        ],
        "legendary": [
            {"id": "confessor_holy_word", "name": "Holy Word", "type": "active", "desc": "Inspires allies, granting a temporary boost to their strength.", "cooldown": 5, "effect": {"str_pct": 0.2, "mana_cost": 25}},
        ],
    },
    "Gourmet": {
        "common": [
            {"id": "gourmet_savory_feast", "name": "Savory Feast", "type": "active", "desc": "Prepares a delicious meal, healing and boosting allies' max HP.", "cooldown": 6, "effect": {"heal_pct": 0.15, "hlt_pct": 0.1}},
        ],
        "uncommon": [
            {"id": "gourmet_culinary_inspiration", "name": "Culinary Inspiration", "type": "passive", "desc": "The Gourmet's presence subtly increases allies' stats.", "effect": {"str_pct": 0.05, "def_pct": 0.05}},
        ],
        "rare": [
            {"id": "gourmet_spicy_surprise", "name": "Spicy Surprise", "type": "active", "desc": "Throws a spicy dish at enemies, dealing fire damage and lowering defense.", "cooldown": 4, "effect": {"atk_pct": 1.0, "def_pct": -0.1}},
        ],
        "epic": [
            {"id": "gourmet_well_fed", "name": "Well-Fed", "type": "passive", "desc": "The Gourmet is always well-nourished, granting increased health and regeneration.", "effect": {"hlt_pct": 0.1, "regen_pct": 0.02}},
        ],
        "legendary": [
            {"id": "gourmet_garnish_of_distraction", "name": "Garnish of Distraction", "type": "active", "desc": "Creates a tantalizing distraction, confusing a single enemy.", "cooldown": 5, "effect": {"int_pct": -0.2, "mana_cost": 15}},
        ],
    },
    "Conjurer": {
        "common": [
            {"id": "conjurer_summon_imp", "name": "Summon Imp", "type": "active", "desc": "Conjures a mischievous imp to fight alongside the Conjurer.", "cooldown": 7, "effect": {"atk_pct": 0.7, "mana_cost": 30}},
        ],
        "uncommon": [
            {"id": "conjurer_arcane_attunement", "name": "Arcane Attunement", "type": "passive", "desc": "The Conjurer's connection to magic empowers their spells.", "effect": {"int_pct": 0.15, "lck_pct": 0.05}},
        ],
        "rare": [
            {"id": "conjurer_fireball", "name": "Fireball", "type": "active", "desc": "Launches a fiery projectile, dealing moderate damage to an enemy.", "cooldown": 3, "effect": {"atk_pct": 1.3}},
        ],
        "epic": [
            {"id": "conjurer_ethereal_barrier", "name": "Ethereal Barrier", "type": "passive", "desc": "A shimmering magical shield passively protects the Conjurer.", "effect": {"def_pct": 0.1}},
        ],
        "legendary": [
            {"id": "conjurer_arcane_blast", "name": "Arcane Blast", "type": "active", "desc": "Unleashes a burst of raw magic, damaging all nearby foes.", "cooldown": 6, "effect": {"atk_pct": 1.0, "mana_cost": 25}},
        ],
    },
    "Master Chef": {
        "common": [
            {"id": "masterchef_gourmet_gourmand", "name": "Gourmet Gourmand", "type": "active", "desc": "Prepares a perfect dish, healing an ally and boosting all their stats.", "cooldown": 5, "effect": {"heal_pct": 0.25, "str_pct": 0.1}},
        ],
        "uncommon": [
            {"id": "masterchef_culinary_resilience", "name": "Culinary Resilience", "type": "passive", "desc": "The Master Chef's constitution is exceptional, granting self-healing.", "effect": {"self_heal_pct": 0.05, "hlt_pct": 0.1}},
        ],
        "rare": [
            {"id": "masterchef_flaming_wok", "name": "Flaming Wok", "type": "active", "desc": "Wields a flaming wok, dealing area fire damage to enemies.", "cooldown": 4, "effect": {"atk_pct": 1.5}},
        ],
        "epic": [
            {"id": "masterchef_palate_cleanser", "name": "Palate Cleanser", "type": "passive", "desc": "A refreshing aura that provides minor regeneration to all allies.", "effect": {"regen_pct": 0.03}},
        ],
        "legendary": [
            {"id": "masterchef_grand_banquet", "name": "Grand Banquet", "type": "active", "desc": "Hosts a grand banquet, greatly healing and buffing all allies.", "cooldown": 8, "effect": {"heal_pct": 0.2, "def_pct": 0.15}},
        ],
    },
    "Harvest Lord": {
        "common": [
            {"id": "harvestlord_thorn_whip", "name": "Thorn Whip", "type": "active", "desc": "Summons thorny vines to lash an enemy, dealing damage.", "cooldown": 3, "effect": {"atk_pct": 1.2}},
        ],
        "uncommon": [
            {"id": "harvestlord_fertile_aura", "name": "Fertile Aura", "type": "passive", "desc": "The Harvest Lord's presence invigorates allies, granting health regeneration.", "effect": {"regen_pct": 0.04}},
        ],
        "rare": [
            {"id": "harvestlord_lifebloom", "name": "Lifebloom", "type": "active", "desc": "Calls forth a burst of nature's energy, healing all allies.", "cooldown": 6, "effect": {"heal_pct": 0.2}},
        ],
        "epic": [
            {"id": "harvestlord_deep_roots", "name": "Deep Roots", "type": "passive", "desc": "The Harvest Lord is sturdy and resilient, increasing max health.", "effect": {"hlt_pct": 0.15}},
        ],
        "legendary": [
            {"id": "harvestlord_blight_seed", "name": "Blight Seed", "type": "active", "desc": "Hurls a blighted seed, dealing damage and reducing enemy defense.", "cooldown": 5, "effect": {"atk_pct": 0.9, "def_pct": -0.1}},
        ],
    },
    "Classless": {
        "common": [
            {"id": "classless_basic_strike", "name": "Basic Strike", "type": "active", "desc": "A fundamental attack dealing modest damage to a single foe.", "cooldown": 2, "effect": {"atk_pct": 1.0}},
        ],
        "uncommon": [
            {"id": "classless_adaptable_training", "name": "Adaptable Training", "type": "passive", "desc": "Through diverse experiences, gains minor boosts to all stats.", "effect": {"str_pct": 0.03, "def_pct": 0.03}},
        ],
        "rare": [
            {"id": "classless_quick_patch", "name": "Quick Patch", "type": "active", "desc": "A hasty self-repair, restoring a small amount of health.", "cooldown": 4, "effect": {"self_heal_pct": 0.1}},
        ],
        "epic": [
            {"id": "classless_scrappy_resolve", "name": "Scrappy Resolve", "type": "passive", "desc": "Driven by sheer will, occasionally lands a more impactful blow.", "effect": {"lck_pct": 0.07, "atk_pct": 0.05}},
        ],
        "legendary": [
            {"id": "classless_unconventional_tactic", "name": "Unconventional Tactic", "type": "active", "desc": "Deals damage and briefly boosts own agility for next turn.", "cooldown": 5, "effect": {"atk_pct": 1.1, "agi_pct": 0.1}},
        ],
    },
    "Deathcaller": {
        "common": [
            {"id": "deathcaller_soul_siphon", "name": "Soul Siphon", "type": "active", "desc": "Drains life force from an enemy, dealing damage and healing the Deathcaller.", "cooldown": 4, "effect": {"atk_pct": 1.2, "self_heal_pct": 0.1}},
        ],
        "uncommon": [
            {"id": "deathcaller_necromantic_fortitude", "name": "Necromantic Fortitude", "type": "passive", "desc": "The Deathcaller's unholy resilience grants increased maximum health.", "effect": {"hlt_pct": 0.15}},
        ],
        "rare": [
            {"id": "deathcaller_curse_of_decay", "name": "Curse of Decay", "type": "active", "desc": "Inflicts a potent curse, weakening an enemy's defenses.", "cooldown": 5, "effect": {"def_pct": -0.2, "mana_cost": 20}},
        ],
        "epic": [
            {"id": "deathcaller_reapers_touch", "name": "Reaper's Touch", "type": "passive", "desc": "Attacks have a chance to deal crushing, bonus dark damage.", "effect": {"crushing_blow": True, "atk_pct": 0.1}},
        ],
        "legendary": [
            {"id": "deathcaller_raise_skeletal_minion", "name": "Raise Skeletal Minion", "type": "active", "desc": "Summons a skeletal minion to fight for the Deathcaller.", "cooldown": 8, "effect": {"atk_pct": 0.8, "mana_cost": 35}},
        ],
    },
    "Grand Alchemist": {
        "common": [
            {"id": "grandalchemist_volatile_brew", "name": "Volatile Brew", "type": "active", "desc": "Hurls an explosive concoction, dealing area damage to enemies.", "cooldown": 4, "effect": {"atk_pct": 1.3}},
        ],
        "uncommon": [
            {"id": "grandalchemist_master_elixirs", "name": "Master Elixirs", "type": "passive", "desc": "Allies benefit from passive health regeneration from alchemical elixirs.", "effect": {"regen_pct": 0.03}},
        ],
        "rare": [
            {"id": "grandalchemist_transmuting_serum", "name": "Transmuting Serum", "type": "active", "desc": "Applies a serum to an ally, significantly boosting their defense temporarily.", "cooldown": 6, "effect": {"def_pct": 0.25, "mana_cost": 20}},
        ],
        "epic": [
            {"id": "grandalchemist_alchemical_insight", "name": "Alchemical Insight", "type": "passive", "desc": "The Alchemist's intellect is unparalleled, boosting their spell power.", "effect": {"int_pct": 0.15}},
        ],
        "legendary": [
            {"id": "grandalchemist_noxious_gas", "name": "Noxious Gas", "type": "active", "desc": "Releases a cloud of noxious gas, damaging and weakening enemies.", "cooldown": 5, "effect": {"atk_pct": 0.7, "str_pct": -0.1}},
        ],
    },
    "Bounty Hunter": {
        "common": [
            {"id": "bountyhunter_mark_for_death", "name": "Mark for Death", "type": "active", "desc": "Designates a target, dealing high damage and increasing future damage taken.", "cooldown": 5, "effect": {"atk_pct": 1.8, "def_pct": -0.15}},
        ],
        "uncommon": [
            {"id": "bountyhunter_keen_senses", "name": "Keen Senses", "type": "passive", "desc": "The hunter's senses are sharp, increasing critical hit chance.", "effect": {"lck_pct": 0.1, "agi_pct": 0.05}},
        ],
        "rare": [
            {"id": "bountyhunter_net_trap", "name": "Net Trap", "type": "active", "desc": "Deploys a net trap, damaging an enemy and reducing their agility.", "cooldown": 4, "effect": {"atk_pct": 0.9, "agi_pct": -0.2}},
        ],
        "epic": [
            {"id": "bountyhunter_swift_pursuit", "name": "Swift Pursuit", "type": "passive", "desc": "Always on the move, boosting the hunter's speed and evasion.", "effect": {"agi_pct": 0.15}},
        ],
        "legendary": [
            {"id": "bountyhunter_execute", "name": "Execute", "type": "active", "desc": "A devastating strike against a weakened foe, dealing crushing damage.", "cooldown": 6, "effect": {"crushing_blow": True, "atk_pct": 1.5}},
        ],
    },
    "Spymaster": {
        "common": [
            {"id": "spymaster_info_network", "name": "Information Network", "type": "passive", "desc": "Gains crucial insights; boosts intellect and agility.", "effect": {"int_pct": 0.1, "agi_pct": 0.1}},
        ],
        "uncommon": [
            {"id": "spymaster_infiltrate", "name": "Infiltrate", "type": "active", "desc": "Strike from shadows; deals damage, reduces enemy defenses.", "cooldown": 4, "effect": {"atk_pct": 1.2, "mana_cost": 20}},
        ],
        "rare": [
            {"id": "spymaster_shadow_veil", "name": "Shadow Veil", "type": "passive", "desc": "Elusive and unseen; grants dodge chance and agility.", "effect": {"agi_pct": 0.15, "lck_pct": 0.05}},
        ],
        "epic": [
            {"id": "spymaster_critical_intel", "name": "Critical Intel", "type": "active", "desc": "Exposes weaknesses; boosts self critical chance against marked foe.", "cooldown": 5, "effect": {"lck_pct": 0.25, "mana_cost": 25}},
        ],
        "legendary": [
            {"id": "spymaster_master_disguise", "name": "Master of Disguise", "type": "passive", "desc": "Blends seamlessly; high luck, slight defense boost.", "effect": {"lck_pct": 0.1, "def_pct": 0.05}},
        ],
    },
    "Prophet": {
        "common": [
            {"id": "prophet_foresight", "name": "Foresight", "type": "passive", "desc": "Peers into future; boosts intellect and luck.", "effect": {"int_pct": 0.1, "lck_pct": 0.1}},
        ],
        "uncommon": [
            {"id": "prophet_divine_vision", "name": "Divine Vision", "type": "active", "desc": "Reveals destiny; heals lowest ally, cleanses debuffs.", "cooldown": 5, "effect": {"heal_pct": 0.2, "cleanse_self": True, "mana_cost": 25}},
        ],
        "rare": [
            {"id": "prophet_oracles_guidance", "name": "Oracle's Guidance", "type": "passive", "desc": "Whispers of fate; allies gain minor stat boosts.", "effect": {"int_pct": 0.08, "str_pct": 0.08}},
        ],
        "epic": [
            {"id": "prophet_prophecy_doom", "name": "Prophecy of Doom", "type": "active", "desc": "Foretells downfall; deals damage, reduces enemy attack.", "cooldown": 4, "effect": {"atk_pct": 1.3, "mana_cost": 20}},
        ],
        "legendary": [
            {"id": "prophet_unwavering_faith", "name": "Unwavering Faith", "type": "passive", "desc": "Faith protects; boosts self-heal and max HP.", "effect": {"self_heal_pct": 0.05, "hlt_pct": 0.1}},
        ],
    },
    "Ninja": {
        "common": [
            {"id": "ninja_fleet_footed", "name": "Fleet-footed", "type": "passive", "desc": "Swift and silent; boosts agility and critical chance.", "effect": {"agi_pct": 0.15, "lck_pct": 0.08}},
        ],
        "uncommon": [
            {"id": "ninja_shuriken_flurry", "name": "Shuriken Flurry", "type": "active", "desc": "Rapid blade assault; deals area damage, chance to bleed.", "cooldown": 3, "effect": {"atk_pct": 1.1, "mana_cost": 15}},
        ],
        "rare": [
            {"id": "ninja_smoke_bomb_mastery", "name": "Smoke Bomb Mastery", "type": "passive", "desc": "Vanishes in mist; grants dodge chance and agility.", "effect": {"agi_pct": 0.1, "lck_pct": 0.05}},
        ],
        "epic": [
            {"id": "ninja_silent_strike", "name": "Silent Strike", "type": "active", "desc": "Lethal precision; high single target damage, guaranteed critical.", "cooldown": 4, "effect": {"atk_pct": 1.8, "crushing_blow": True, "mana_cost": 25}},
        ],
        "legendary": [
            {"id": "ninja_opportunist", "name": "Opportunist", "type": "passive", "desc": "Exploits weakness; boosts damage against vulnerable foes.", "effect": {"atk_pct": 0.15, "lck_pct": 0.05}},
        ],
    },
    "Chef": {
        "common": [
            {"id": "chef_culinary_master", "name": "Culinary Master", "type": "passive", "desc": "Master of flavor; boosts healing received and max HP.", "effect": {"hlt_pct": 0.1, "regen_pct": 0.02}},
        ],
        "uncommon": [
            {"id": "chef_hearty_stew", "name": "Hearty Stew", "type": "active", "desc": "Nourishing meal; heals all allies, grants minor defense.", "cooldown": 5, "effect": {"heal_pct": 0.25, "mana_cost": 30}},
        ],
        "rare": [
            {"id": "chef_iron_stomach", "name": "Iron Stomach", "type": "passive", "desc": "Resilient digestive system; resists debuffs, minor HP regen.", "effect": {"def_pct": 0.05, "regen_pct": 0.03}},
        ],
        "epic": [
            {"id": "chef_spicy_surprise", "name": "Spicy Surprise", "type": "active", "desc": "Unexpected kick; deals damage, briefly reduces enemy defense.", "cooldown": 3, "effect": {"atk_pct": 1.0, "mana_cost": 15}},
        ],
        "legendary": [
            {"id": "chef_gourmets_touch", "name": "Gourmet's Touch", "type": "passive", "desc": "Enhanced dishes; allies gain minor stats when healed.", "effect": {"hlt_pct": 0.05, "str_pct": 0.05}},
        ],
    },
    "General": {
        "common": [
            {"id": "general_strategic_mind", "name": "Strategic Mind", "type": "passive", "desc": "Brilliant tactician; boosts intellect and defense for self.", "effect": {"int_pct": 0.1, "def_pct": 0.1}},
        ],
        "uncommon": [
            {"id": "general_rallying_cry", "name": "Rallying Cry", "type": "active", "desc": "Inspiring command; boosts all allies' attack and defense.", "cooldown": 6, "effect": {"atk_pct": 0.2, "def_pct": 0.2, "mana_cost": 30}},
        ],
        "rare": [
            {"id": "general_iron_discipline", "name": "Iron Discipline", "type": "passive", "desc": "Unwavering resolve; increases team's resistance to debuffs.", "effect": {"def_pct": 0.15}},
        ],
        "epic": [
            {"id": "general_coordinated_assault", "name": "Coordinated Assault", "type": "active", "desc": "Precision strike; deals damage, marks target for more ally damage.", "cooldown": 5, "effect": {"atk_pct": 1.4, "mana_cost": 25}},
        ],
        "legendary": [
            {"id": "general_unyielding_presence", "name": "Unyielding Presence", "type": "passive", "desc": "Commanding aura; boosts max HP and provides minor regeneration.", "effect": {"hlt_pct": 0.15, "regen_pct": 0.03}},
        ],
    },
    "Quartermaster": {
        "common": [
            {"id": "quartermaster_resourceful", "name": "Resourceful", "type": "passive", "desc": "Always prepared; boosts luck and provides mana regeneration.", "effect": {"lck_pct": 0.1, "regen_pct": 0.02}},
        ],
        "uncommon": [
            {"id": "quartermaster_supply_drop", "name": "Supply Drop", "type": "active", "desc": "Essential provisions; heals lowest ally, grants temporary defense.", "cooldown": 4, "effect": {"heal_pct": 0.2, "def_pct": 0.1, "mana_cost": 20}},
        ],
        "rare": [
            {"id": "quartermaster_efficient_logistics", "name": "Efficient Logistics", "type": "passive", "desc": "Optimized movement; reduces cooldowns for allies.", "effect": {"agi_pct": 0.1, "lck_pct": 0.05}},
        ],
        "epic": [
            {"id": "quartermaster_tactical_reposition", "name": "Tactical Reposition", "type": "active", "desc": "Strategic relocation; moves ally, grants them a shield.", "cooldown": 5, "effect": {"heal_pct": 0.15, "mana_cost": 25}},
        ],
        "legendary": [
            {"id": "quartermaster_prepared_anything", "name": "Prepared for Anything", "type": "passive", "desc": "Well-stocked; boosts max HP and provides minor defense.", "effect": {"hlt_pct": 0.1, "def_pct": 0.08}},
        ],
    },
    "Magic Engineer": {
        "common": [
            {"id": "magic_engineer_arcane_tinkerer", "name": "Arcane Tinkerer", "type": "passive", "desc": "Master of enchantments; boosts intellect and mana regen.", "effect": {"int_pct": 0.15, "regen_pct": 0.03}},
        ],
        "uncommon": [
            {"id": "magic_engineer_mana_turret", "name": "Mana Turret", "type": "active", "desc": "Deploys arcane turret; deals continuous magic damage.", "cooldown": 4, "effect": {"atk_pct": 1.0, "mana_cost": 20}},
        ],
        "rare": [
            {"id": "magic_engineer_shield_generator", "name": "Shield Generator", "type": "passive", "desc": "Protective energy field; periodically shields lowest HP ally.", "effect": {"def_pct": 0.1, "hlt_pct": 0.05}},
        ],
        "epic": [
            {"id": "magic_engineer_overcharge", "name": "Overcharge", "type": "active", "desc": "Unleashes raw power; deals massive damage, high mana cost.", "cooldown": 6, "effect": {"atk_pct": 2.0, "crushing_blow": True, "mana_cost": 40}},
        ],
        "legendary": [
            {"id": "magic_engineer_defensive_matrix", "name": "Defensive Matrix", "type": "passive", "desc": "Reinforced plating; boosts defense and spell resistance.", "effect": {"def_pct": 0.12, "int_pct": 0.05}},
        ],
    },
    "High Confessor": {
        "common": [
            {"id": "high_confessor_divine_aura", "name": "Divine Aura", "type": "passive", "desc": "Holy presence; boosts max HP and provides minor regeneration.", "effect": {"hlt_pct": 0.1, "regen_pct": 0.03}},
        ],
        "uncommon": [
            {"id": "high_confessor_penance", "name": "Penance", "type": "active", "desc": "Absolves sins; deals damage to enemy, heals lowest ally.", "cooldown": 4, "effect": {"atk_pct": 0.8, "heal_pct": 0.15, "mana_cost": 20}},
        ],
        "rare": [
            {"id": "high_confessor_sacred_shield", "name": "Sacred Shield", "type": "passive", "desc": "Blessed protection; periodically shields lowest health ally.", "effect": {"def_pct": 0.1, "hlt_pct": 0.05}},
        ],
        "epic": [
            {"id": "high_confessor_absolution", "name": "Absolution", "type": "active", "desc": "Forgives transgressions; cleanses ally debuffs, grants defense.", "cooldown": 5, "effect": {"cleanse_self": True, "def_pct": 0.15, "mana_cost": 25}},
        ],
        "legendary": [
            {"id": "high_confessor_zealots_resolve", "name": "Zealot's Resolve", "type": "passive", "desc": "Fanatical devotion; boosts attack/defense when allies are low.", "effect": {"enrage": True, "str_pct": 0.1}},
        ],
    },
    "Templar": {
        "common": [
            {"id": "templar_holy_vows", "name": "Holy Vows", "type": "passive", "desc": "Sacred oath; boosts defense and resilience.", "effect": {"def_pct": 0.15, "hlt_pct": 0.05}},
        ],
        "uncommon": [
            {"id": "templar_divine_smite", "name": "Divine Smite", "type": "active", "desc": "Consecrated strike; deals holy damage, chance to stun.", "cooldown": 3, "effect": {"atk_pct": 1.3, "mana_cost": 15}},
        ],
        "rare": [
            {"id": "templar_bulwark_faith", "name": "Bulwark of Faith", "type": "passive", "desc": "Unwavering protection; greatly boosts defense and max HP.", "effect": {"def_pct": 0.2, "hlt_pct": 0.1}},
        ],
        "epic": [
            {"id": "templar_sacred_challenge", "name": "Sacred Challenge", "type": "active", "desc": "Draws aggression; taunts enemies, reduces damage taken.", "cooldown": 5, "effect": {"def_pct": 0.25, "enrage": True, "mana_cost": 25}},
        ],
        "legendary": [
            {"id": "templar_righteous_fury", "name": "Righteous Fury", "type": "passive", "desc": "Vengeful spirit; boosts attack when taking damage.", "effect": {"enrage": True, "atk_pct": 0.1}},
        ],
    },
    "Chaplain": {
        "common": [
            {"id": "chaplain_guiding_light", "name": "Guiding Light", "type": "passive", "desc": "Beacon of hope; boosts intellect and healing potency.", "effect": {"int_pct": 0.1, "heal_pct": 0.05}},
        ],
        "uncommon": [
            {"id": "chaplain_lay_on_hands", "name": "Lay on Hands", "type": "active", "desc": "Healing touch; heals a single ally for a large amount.", "cooldown": 4, "effect": {"heal_pct": 0.4, "mana_cost": 25}},
        ],
        "rare": [
            {"id": "chaplain_spiritual_fortitude", "name": "Spiritual Fortitude", "type": "passive", "desc": "Inner strength; boosts allies' max HP and resistance.", "effect": {"hlt_pct": 0.08, "def_pct": 0.08}},
        ],
        "epic": [
            {"id": "chaplain_divine_intervention", "name": "Divine Intervention", "type": "active", "desc": "Miraculous revival; revives a fallen ally with some HP.", "cooldown": 8, "effect": {"death_heal": True, "mana_cost": 50}},
        ],
        "legendary": [
            {"id": "chaplain_benediction", "name": "Benediction", "type": "passive", "desc": "Blessings bestowed; periodically cleanses debuffs from allies.", "effect": {"cleanse_self": True, "regen_pct": 0.02}},
        ],
    },
    "Bloodrager": {
        "common": [
            {"id": "bloodrager_blood_frenzy", "name": "Blood Frenzy", "type": "active", "desc": "Deals damage to foe, enters a state of primal rage.", "cooldown": 4, "effect": {"atk_pct": 1.2, "enrage": True}},
        ],
        "uncommon": [
            {"id": "bloodrager_sanguine_resilience", "name": "Sanguine Resilience", "type": "passive", "desc": "Gains defense and health when critically wounded in battle.", "effect": {"def_pct": 0.15, "hlt_pct": 0.1}},
        ],
        "rare": [
            {"id": "bloodrager_gushing_wound", "name": "Gushing Wound", "type": "active", "desc": "Strikes foe, siphoning their life force to heal self.", "cooldown": 3, "effect": {"atk_pct": 0.8, "self_heal_pct": 0.15}},
        ],
        "epic": [
            {"id": "bloodrager_reapers_harvest", "name": "Reaper's Harvest", "type": "passive", "desc": "Heals significantly upon defeating an enemy combatant.", "effect": {"death_heal": True}},
        ],
        "legendary": [
            {"id": "bloodrager_primal_roar", "name": "Primal Roar", "type": "active", "desc": "Unleashes a terrifying roar, empowering self and damaging foes.", "cooldown": 5, "effect": {"atk_pct": 0.7, "str_pct": 0.2}},
        ],
    },
    "Siege Master": {
        "common": [
            {"id": "siegemaster_ballista_shot", "name": "Ballista Shot", "type": "active", "desc": "Fires a devastating bolt, dealing massive damage to a single target.", "cooldown": 4, "effect": {"atk_pct": 1.8, "crushing_blow": True}},
        ],
        "uncommon": [
            {"id": "siegemaster_reinforced_plating", "name": "Reinforced Plating", "type": "passive", "desc": "Fortified armor provides superior damage resistance and health.", "effect": {"def_pct": 0.2, "hlt_pct": 0.1}},
        ],
        "rare": [
            {"id": "siegemaster_barricade", "name": "Barricade", "type": "active", "desc": "Erects a temporary barrier, increasing self defense.", "cooldown": 6, "effect": {"def_pct": 0.3}},
        ],
        "epic": [
            {"id": "siegemaster_explosive_payload", "name": "Explosive Payload", "type": "passive", "desc": "Attacks sometimes explode, dealing extra damage.", "effect": {"atk_pct": 0.1, "lck_pct": 0.05}},
        ],
        "legendary": [
            {"id": "siegemaster_catapult_barrage", "name": "Catapult Barrage", "type": "active", "desc": "Launches a volley of projectiles, damaging multiple enemies.", "cooldown": 5, "effect": {"atk_pct": 1.0}},
        ],
    },
    "Glaive Lord": {
        "common": [
            {"id": "glaivelord_whirling_death", "name": "Whirling Death", "type": "active", "desc": "Spins glaive rapidly, damaging all nearby enemies.", "cooldown": 3, "effect": {"atk_pct": 0.9}},
        ],
        "uncommon": [
            {"id": "glaivelord_agile_footwork", "name": "Agile Footwork", "type": "passive", "desc": "Nimble movements increase agility and evasion in combat.", "effect": {"agi_pct": 0.2}},
        ],
        "rare": [
            {"id": "glaivelord_serrated_edge", "name": "Serrated Edge", "type": "active", "desc": "Deep cut, dealing damage and causing target to bleed.", "cooldown": 4, "effect": {"atk_pct": 1.3, "crushing_blow": True}},
        ],
        "epic": [
            {"id": "glaivelord_momentum", "name": "Momentum", "type": "passive", "desc": "Gains attack power with each successful strike.", "effect": {"atk_pct": 0.15}},
        ],
        "legendary": [
            {"id": "glaivelord_glaive_ricochet", "name": "Glaive Ricochet", "type": "active", "desc": "Throws glaive, bouncing between multiple targets for damage.", "cooldown": 5, "effect": {"atk_pct": 1.1}},
        ],
    },
    "Tracker": {
        "common": [
            {"id": "tracker_pinpoint_shot", "name": "Pinpoint Shot", "type": "active", "desc": "Fires an arrow with extreme precision for high damage.", "cooldown": 3, "effect": {"atk_pct": 1.6, "crushing_blow": True}},
        ],
        "uncommon": [
            {"id": "tracker_keen_eyesight", "name": "Keen Eyesight", "type": "passive", "desc": "Enhanced vision grants increased luck and critical chance.", "effect": {"lck_pct": 0.15}},
        ],
        "rare": [
            {"id": "tracker_caltrops", "name": "Caltrops", "type": "active", "desc": "Deploys sharp caltrops, damaging and slowing enemies.", "cooldown": 4, "effect": {"atk_pct": 0.6}},
        ],
        "epic": [
            {"id": "tracker_wilderness_survival", "name": "Wilderness Survival", "type": "passive", "desc": "Adapts to environment, gaining health regeneration over time.", "effect": {"regen_pct": 0.05}},
        ],
        "legendary": [
            {"id": "tracker_hunters_mark", "name": "Hunter's Mark", "type": "active", "desc": "Marks a foe, making them vulnerable to subsequent attacks.", "cooldown": 5, "effect": {"atk_pct": 0.8}},
        ],
    },
    "Zenith": {
        "common": [
            {"id": "zenith_divine_smite", "name": "Divine Smite", "type": "active", "desc": "Calls down holy energy, dealing radiant damage to an enemy.", "cooldown": 3, "effect": {"atk_pct": 1.1}},
        ],
        "uncommon": [
            {"id": "zenith_holy_aura", "name": "Holy Aura", "type": "passive", "desc": "Emits a protective aura, boosting self defense and health.", "effect": {"def_pct": 0.15, "hlt_pct": 0.1}},
        ],
        "rare": [
            {"id": "zenith_healing_light", "name": "Healing Light", "type": "active", "desc": "Bathes an ally in light, restoring their health significantly.", "cooldown": 3, "effect": {"heal_pct": 0.25}},
        ],
        "epic": [
            {"id": "zenith_sacred_ward", "name": "Sacred Ward", "type": "passive", "desc": "Protection from negative effects, cleansing self periodically.", "effect": {"cleanse_self": True}},
        ],
        "legendary": [
            {"id": "zenith_benediction", "name": "Benediction", "type": "active", "desc": "Bestows a blessing, increasing an ally's strength temporarily.", "cooldown": 5, "effect": {"str_pct": 0.2}},
        ],
    },
    "Shadow Broker": {
        "common": [
            {"id": "shadowbroker_shadow_strike", "name": "Shadow Strike", "type": "active", "desc": "Emerges from shadows, dealing a devastating critical blow.", "cooldown": 4, "effect": {"atk_pct": 1.7, "crushing_blow": True}},
        ],
        "uncommon": [
            {"id": "shadowbroker_evasive_maneuvers", "name": "Evasive Maneuvers", "type": "passive", "desc": "Master of evasion, increasing agility and avoiding attacks.", "effect": {"agi_pct": 0.25}},
        ],
        "rare": [
            {"id": "shadowbroker_smoke_bomb", "name": "Smoke Bomb", "type": "active", "desc": "Throws a smoke bomb, obscuring vision and damaging foes.", "cooldown": 3, "effect": {"atk_pct": 0.5}},
        ],
        "epic": [
            {"id": "shadowbroker_dark_bargain", "name": "Dark Bargain", "type": "passive", "desc": "Gains power from defeated foes, healing self slightly.", "effect": {"death_heal": True}},
        ],
        "legendary": [
            {"id": "shadowbroker_backstab", "name": "Backstab", "type": "active", "desc": "Exploits enemy's weak points, dealing massive damage.", "cooldown": 5, "effect": {"atk_pct": 1.5}},
        ],
    },
    "Spellsword": {
        "common": [
            {"id": "spellsword_arcane_slash", "name": "Arcane Slash", "type": "active", "desc": "Infuses blade with magic, dealing hybrid damage to an enemy.", "cooldown": 3, "effect": {"atk_pct": 1.0, "int_pct": 0.1}},
        ],
        "uncommon": [
            {"id": "spellsword_enchanted_blade", "name": "Enchanted Blade", "type": "passive", "desc": "Weapon glows with magic, increasing attack and intellect.", "effect": {"atk_pct": 0.1, "int_pct": 0.1}},
        ],
        "rare": [
            {"id": "spellsword_elemental_surge", "name": "Elemental Surge", "type": "active", "desc": "Unleashes elemental energy, damaging and empowering self.", "cooldown": 4, "effect": {"atk_pct": 0.9, "str_pct": 0.15}},
        ],
        "epic": [
            {"id": "spellsword_mana_shield", "name": "Mana Shield", "type": "passive", "desc": "Converts incoming damage into magical energy, boosting defense.", "effect": {"def_pct": 0.2}},
        ],
        "legendary": [
            {"id": "spellsword_spell_reflection", "name": "Spell Reflection", "type": "active", "desc": "Projects a magical barrier, cleansing self and damaging foe.", "cooldown": 5, "effect": {"atk_pct": 0.7, "cleanse_self": True}},
        ],
    },
    "Saint": {
        "common": [
            {"id": "saint_holy_word", "name": "Holy Word", "type": "active", "desc": "Utters a sacred word, healing an ally significantly.", "cooldown": 2, "effect": {"heal_pct": 0.3}},
        ],
        "uncommon": [
            {"id": "saint_divine_grace", "name": "Divine Grace", "type": "passive", "desc": "Bathed in divine light, constantly regenerating health.", "effect": {"regen_pct": 0.08}},
        ],
        "rare": [
            {"id": "saint_mass_cleanse", "name": "Mass Cleanse", "type": "active", "desc": "Purifies self and allies of all harmful effects.", "cooldown": 6, "effect": {"cleanse_self": True}},
        ],
        "epic": [
            {"id": "saint_martyrdom", "name": "Martyrdom", "type": "passive", "desc": "Upon defeat, heals all allies for a portion of health.", "effect": {"death_heal": True}},
        ],
        "legendary": [
            {"id": "saint_sanctuary", "name": "Sanctuary", "type": "active", "desc": "Creates a protective zone, granting an ally increased defense.", "cooldown": 5, "effect": {"def_pct": 0.25}},
        ],
    },
    "Warlock": {
        "common": [
            {"id": "warlock_soul_drain", "name": "Soul Drain", "type": "active", "desc": "Saps life force from an enemy, healing self.", "cooldown": 3, "effect": {"atk_pct": 0.9, "self_heal_pct": 0.1}},
        ],
        "uncommon": [
            {"id": "warlock_dark_pact", "name": "Dark Pact", "type": "passive", "desc": "Forges a pact, gaining formidable magical intellect.", "effect": {"int_pct": 0.25}},
        ],
        "rare": [
            {"id": "warlock_curse_of_weakness", "name": "Curse of Weakness", "type": "active", "desc": "Inflicts a curse, damaging and weakening an enemy.", "cooldown": 4, "effect": {"atk_pct": 0.7}},
        ],
        "epic": [
            {"id": "warlock_corrupting_presence", "name": "Corrupting Presence", "type": "passive", "desc": "Emanates dark energy, slowly draining enemy health.", "effect": {"atk_pct": 0.05}},
        ],
        "legendary": [
            {"id": "warlock_shadow_bolt", "name": "Shadow Bolt", "type": "active", "desc": "Hurls a bolt of pure shadow energy, dealing magic damage.", "cooldown": 2, "effect": {"atk_pct": 1.2}},
        ],
    },
    "Master Smith": {
        "common": [
            {"id": "mastersmith_hammer_slam", "name": "Hammer Slam", "type": "active", "desc": "Slams hammer down, dealing damage and stunning foes.", "cooldown": 3, "effect": {"atk_pct": 1.0}},
        ],
        "uncommon": [
            {"id": "mastersmith_heavy_armor", "name": "Heavy Armor", "type": "passive", "desc": "Wears incredibly thick, reinforced armor for defense and health.", "effect": {"def_pct": 0.25, "hlt_pct": 0.15}},
        ],
        "rare": [
            {"id": "mastersmith_sharpen_weapon", "name": "Sharpen Weapon", "type": "active", "desc": "Improves an ally's weapon, increasing their attack.", "cooldown": 4, "effect": {"str_pct": 0.2}},
        ],
        "epic": [
            {"id": "mastersmith_fortify", "name": "Fortify", "type": "passive", "desc": "Bolsters defenses, increasing health and defense permanently.", "effect": {"hlt_pct": 0.1, "def_pct": 0.1}},
        ],
        "legendary": [
            {"id": "mastersmith_repair_armor", "name": "Repair Armor", "type": "active", "desc": "Mends own armor, restoring health and removing debuffs.", "cooldown": 5, "effect": {"self_heal_pct": 0.2, "cleanse_self": True}},
        ],
    },
    "Logistics Officer": {
        "common": [
            {"id": "logistics_supply_drop", "name": "Supply Drop", "type": "active", "desc": "Delivers vital supplies, healing the lowest health ally significantly.", "cooldown": 4, "effect": {"heal_pct": 0.25}},
        ],
        "uncommon": [
            {"id": "logistics_efficient_planning", "name": "Efficient Planning", "type": "passive", "desc": "Meticulous planning grants all allies a small permanent defense boost.", "effect": {"def_pct": 0.05}},
        ],
        "rare": [
            {"id": "logistics_expedited_orders", "name": "Expedited Orders", "type": "active", "desc": "Issues rapid commands, allowing the officer to strike swiftly.", "cooldown": 3, "effect": {"atk_pct": 1.1}},
        ],
        "epic": [
            {"id": "logistics_strategic_redeployment", "name": "Strategic Redeployment", "type": "passive", "desc": "Optimizes team positioning, granting all allies increased maximum health.", "effect": {"hlt_pct": 0.08}},
        ],
        "legendary": [
            {"id": "logistics_emergency_protocol", "name": "Emergency Protocol", "type": "active", "desc": "Activates emergency protocols, cleansing self of all harmful effects.", "cooldown": 5, "effect": {"cleanse_self": True}},
        ],
    },
    "Guildmaster": {
        "common": [
            {"id": "guildmaster_rallying_cry", "name": "Rallying Cry", "type": "active", "desc": "Inspires self and allies, entering a temporary state of enrage.", "cooldown": 4, "effect": {"enrage": True}},
        ],
        "uncommon": [
            {"id": "guildmaster_leadership_presence", "name": "Leadership Presence", "type": "passive", "desc": "The Guildmaster's presence strengthens allies' resolve and defense.", "effect": {"def_pct": 0.07, "str_pct": 0.03}},
        ],
        "rare": [
            {"id": "guildmaster_strategic_alliance", "name": "Strategic Alliance", "type": "active", "desc": "Calls upon allies for a coordinated attack, dealing crushing damage.", "cooldown": 5, "effect": {"crushing_blow": True}},
        ],
        "epic": [
            {"id": "guildmaster_guild_benefits", "name": "Guild Benefits", "type": "passive", "desc": "Regular guild contributions provide passive health regeneration for all.", "effect": {"regen_pct": 0.03}},
        ],
        "legendary": [
            {"id": "guildmaster_veterans_wisdom", "name": "Veteran's Wisdom", "type": "active", "desc": "Drawing on years of experience, the Guildmaster cleanses own debuffs.", "cooldown": 4, "effect": {"cleanse_self": True}},
        ],
    },
    "Strategist": {
        "common": [
            {"id": "strategist_vulnerable_point", "name": "Vulnerable Point", "type": "active", "desc": "Identifies and exploits a weakness, dealing precise, high damage.", "cooldown": 3, "effect": {"atk_pct": 1.4}},
        ],
        "uncommon": [
            {"id": "strategist_calculated_risk", "name": "Calculated Risk", "type": "passive", "desc": "Weighing options, the strategist gains a permanent boost to intellect.", "effect": {"int_pct": 0.1}},
        ],
        "rare": [
            {"id": "strategist_tactical_retreat", "name": "Tactical Retreat", "type": "active", "desc": "Executes a quick maneuver, healing self and escaping harm.", "cooldown": 5, "effect": {"self_heal_pct": 0.2}},
        ],
        "epic": [
            {"id": "strategist_battlefield_awareness", "name": "Battlefield Awareness", "type": "passive", "desc": "Always observing, the strategist boosts own agility and luck.", "effect": {"agi_pct": 0.05, "lck_pct": 0.05}},
        ],
        "legendary": [
            {"id": "strategist_disruptive_tactics", "name": "Disruptive Tactics", "type": "active", "desc": "Employs a disruptive maneuver, dealing damage and consuming much mana.", "cooldown": 4, "effect": {"atk_pct": 1.2, "mana_cost": 20}},
        ],
    },
    "Spellweaver": {
        "common": [
            {"id": "spellweaver_arcane_bolt", "name": "Arcane Bolt", "type": "active", "desc": "Hurls a concentrated bolt of arcane energy at an enemy.", "cooldown": 2, "effect": {"atk_pct": 1.0, "mana_cost": 10}},
        ],
        "uncommon": [
            {"id": "spellweaver_mana_flow", "name": "Mana Flow", "type": "passive", "desc": "The Spellweaver's inherent connection to magic boosts intellect.", "effect": {"int_pct": 0.1}},
        ],
        "rare": [
            {"id": "spellweaver_weave_of_protection", "name": "Weave of Protection", "type": "active", "desc": "Weaves a protective spell, cleansing self of harmful effects.", "cooldown": 4, "effect": {"cleanse_self": True, "mana_cost": 15}},
        ],
        "epic": [
            {"id": "spellweaver_mastery_of_elements", "name": "Mastery of Elements", "type": "passive", "desc": "Profound understanding of magic grants increased spell potency.", "effect": {"int_pct": 0.15}},
        ],
        "legendary": [
            {"id": "spellweaver_cataclysm", "name": "Cataclysm", "type": "active", "desc": "Unleashes a devastating burst of raw arcane power, dealing massive damage.", "cooldown": 6, "effect": {"atk_pct": 2.0, "mana_cost": 40}},
        ],
    },
    "Philosopher": {
        "common": [
            {"id": "philosopher_socratic_dialogue", "name": "Socratic Dialogue", "type": "active", "desc": "Engages an enemy in deep thought, causing them to falter.", "cooldown": 4, "effect": {"atk_pct": 0.8, "mana_cost": 10}},
        ],
        "uncommon": [
            {"id": "philosopher_enlightened_mind", "name": "Enlightened Mind", "type": "passive", "desc": "Deep contemplation enhances the philosopher's intellect and wisdom.", "effect": {"int_pct": 0.15}},
        ],
        "rare": [
            {"id": "philosopher_moral_compass", "name": "Moral Compass", "type": "active", "desc": "Restores clarity and focus, cleansing self of debilitating effects.", "cooldown": 5, "effect": {"cleanse_self": True}},
        ],
        "epic": [
            {"id": "philosopher_stoic_resolve", "name": "Stoic Resolve", "type": "passive", "desc": "Unwavering resolve grants increased health and defensive capabilities.", "effect": {"hlt_pct": 0.1, "def_pct": 0.05}},
        ],
        "legendary": [
            {"id": "philosopher_existential_question", "name": "Existential Question", "type": "active", "desc": "Forces an enemy to confront their existence, dealing a crushing blow.", "cooldown": 6, "effect": {"crushing_blow": True, "mana_cost": 25}},
        ],
    },
    "Warden": {
        "common": [
            {"id": "warden_stone_skin", "name": "Stone Skin", "type": "active", "desc": "Hardens skin, shrugging off damage and healing self.", "cooldown": 4, "effect": {"self_heal_pct": 0.2, "mana_cost": 15}},
        ],
        "uncommon": [
            {"id": "warden_guardians_stance", "name": "Guardian's Stance", "type": "passive", "desc": "The Warden's unwavering stance grants increased health and defense.", "effect": {"hlt_pct": 0.12, "def_pct": 0.08}},
        ],
        "rare": [
            {"id": "warden_root_bind", "name": "Root Bind", "type": "active", "desc": "Summons spectral roots to ensnare and damage an enemy.", "cooldown": 3, "effect": {"atk_pct": 0.9, "mana_cost": 10}},
        ],
        "epic": [
            {"id": "warden_natures_resilience", "name": "Nature's Resilience", "type": "passive", "desc": "Drawing on nature's strength, the Warden gains constant health regeneration.", "effect": {"regen_pct": 0.05}},
        ],
        "legendary": [
            {"id": "warden_last_stand", "name": "Last Stand", "type": "active", "desc": "Refuses to yield, entering a furious state of enrage.", "cooldown": 5, "effect": {"enrage": True, "mana_cost": 20}},
        ],
    },
    "Veteran": {
        "common": [
            {"id": "veteran_battle_hardened_strike", "name": "Battle-Hardened Strike", "type": "active", "desc": "Delivers a powerful strike, honed by countless battles, dealing high damage.", "cooldown": 3, "effect": {"atk_pct": 1.3}},
        ],
        "uncommon": [
            {"id": "veteran_unwavering_grit", "name": "Unwavering Grit", "type": "passive", "desc": "Years of combat instill unwavering grit, boosting health and defense.", "effect": {"hlt_pct": 0.1, "def_pct": 0.05}},
        ],
        "rare": [
            {"id": "veteran_field_medic", "name": "Field Medic", "type": "active", "desc": "Quickly bandages wounds, healing self and removing minor ailments.", "cooldown": 5, "effect": {"self_heal_pct": 0.2, "cleanse_self": True}},
        ],
        "epic": [
            {"id": "veteran_seasoned_instincts", "name": "Seasoned Instincts", "type": "passive", "desc": "Decades of experience sharpen instincts, increasing agility and luck.", "effect": {"agi_pct": 0.07, "lck_pct": 0.03}},
        ],
        "legendary": [
            {"id": "veteran_finishing_blow", "name": "Finishing Blow", "type": "active", "desc": "Executes a precise, decisive strike, often dealing a crushing blow.", "cooldown": 4, "effect": {"crushing_blow": True, "atk_pct": 1.1}},
        ],
    },
    "Merchant": {
        "common": [
            {"id": "merchant_bribe", "name": "Bribe", "type": "active", "desc": "\"Convinces\" an enemy to falter, dealing minor damage and costing mana.", "cooldown": 3, "effect": {"atk_pct": 0.7, "mana_cost": 10}},
        ],
        "uncommon": [
            {"id": "merchant_wealthy_patron", "name": "Wealthy Patron", "type": "passive", "desc": "The Merchant's vast wealth grants them increased luck and influence.", "effect": {"lck_pct": 0.1}},
        ],
        "rare": [
            {"id": "merchant_dealmaker", "name": "Dealmaker", "type": "active", "desc": "Strikes a shrewd deal, healing the lowest health ally significantly.", "cooldown": 4, "effect": {"heal_pct": 0.3}},
        ],
        "epic": [
            {"id": "merchant_efficient_logistics", "name": "Efficient Logistics", "type": "passive", "desc": "Masterful logistics grant heightened agility and keen intellect.", "effect": {"agi_pct": 0.05, "int_pct": 0.05}},
        ],
        "legendary": [
            {"id": "merchant_market_crash", "name": "Market Crash", "type": "active", "desc": "Causes economic turmoil, dealing damage and disrupting foes.", "cooldown": 5, "effect": {"atk_pct": 1.5, "mana_cost": 20}},
        ],
    },
    "Arcane Lord": {
        "common": [
            {"id": "arcane_lord_dark_pact", "name": "Dark Pact", "type": "active", "desc": "Unleashes forbidden magic, dealing immense damage at a high mana cost.", "cooldown": 3, "effect": {"atk_pct": 1.8, "mana_cost": 30}},
        ],
        "uncommon": [
            {"id": "arcane_lord_forbidden_knowledge", "name": "Forbidden Knowledge", "type": "passive", "desc": "Delving into forbidden lore grants unparalleled intellect.", "effect": {"int_pct": 0.25}},
        ],
        "rare": [
            {"id": "arcane_lord_soul_siphon", "name": "Soul Siphon", "type": "active", "desc": "Drains life essence from an enemy, dealing damage and healing self.", "cooldown": 4, "effect": {"atk_pct": 1.0, "self_heal_pct": 0.15}},
        ],
        "epic": [
            {"id": "arcane_lord_arcane_mastery", "name": "Arcane Mastery", "type": "passive", "desc": "Absolute mastery over arcane energies further empowers all spells.", "effect": {"int_pct": 0.1}},
        ],
        "legendary": [
            {"id": "arcane_lord_apocalyptic_vision", "name": "Apocalyptic Vision", "type": "active", "desc": "Manifests a vision of doom, delivering a devastating crushing blow.", "cooldown": 7, "effect": {"crushing_blow": True, "mana_cost": 50}},
        ],
    },
    "Mystic Vanguard": {
        "common": [
            {"id": "mystic_vanguard_holy_smite", "name": "Holy Smite", "type": "active", "desc": "Calls down divine wrath, smiting an enemy with holy energy.", "cooldown": 3, "effect": {"atk_pct": 1.2, "mana_cost": 10}},
        ],
        "uncommon": [
            {"id": "mystic_vanguard_divine_aegis", "name": "Divine Aegis", "type": "passive", "desc": "Protected by divine power, the Vanguard gains defense and regeneration.", "effect": {"def_pct": 0.1, "regen_pct": 0.03}},
        ],
        "rare": [
            {"id": "mystic_vanguard_healing_light", "name": "Healing Light", "type": "active", "desc": "Channels pure light, healing the most wounded ally.", "cooldown": 4, "effect": {"heal_pct": 0.2, "mana_cost": 15}},
        ],
        "epic": [
            {"id": "mystic_vanguard_vanguards_oath", "name": "Vanguard's Oath", "type": "passive", "desc": "Sworn to protect, the Vanguard gains increased health and strength.", "effect": {"hlt_pct": 0.1, "str_pct": 0.05}},
        ],
        "legendary": [
            {"id": "mystic_vanguard_sacred_intervention", "name": "Sacred Intervention", "type": "active", "desc": "Calls upon sacred powers, cleansing self of all curses and ailments.", "cooldown": 5, "effect": {"cleanse_self": True, "mana_cost": 20}},
        ],
    },
    "Artificer": {
        "common": [
            {"id": "mechanized_upgrade", "name": "Mechanized Upgrade", "type": "passive", "desc": "Allies gain increased defenses from Artificer's constant tinkering.", "effect": {"def_pct": 0.15}},
        ],
        "uncommon": [
            {"id": "deploy_turret", "name": "Deploy Turret", "type": "active", "desc": "Deploys a temporary turret, attacking the nearest enemy for damage.", "cooldown": 4, "effect": {"atk_pct": 1.2}},
        ],
        "rare": [
            {"id": "overcharge_core", "name": "Overcharge Core", "type": "active", "desc": "Overcharges an ally's systems, significantly boosting their next attack.", "cooldown": 5, "effect": {"atk_pct": 1.8, "mana_cost": 25}},
        ],
        "epic": [
            {"id": "adaptive_shielding", "name": "Adaptive Shielding", "type": "passive", "desc": "Artificer's advanced shields provide constant, minor health regeneration.", "effect": {"regen_pct": 0.05}},
        ],
        "legendary": [
            {"id": "experimental_grenade", "name": "Experimental Grenade", "type": "active", "desc": "Hurls a grenade, dealing damage and reducing enemy defenses.", "cooldown": 3, "effect": {"atk_pct": 0.8, "mana_cost": 15}},
        ],
    },
    "Maestro": {
        "common": [
            {"id": "inspiring_melody", "name": "Inspiring Melody", "type": "active", "desc": "Plays an uplifting tune, healing the lowest health ally.", "cooldown": 3, "effect": {"heal_pct": 0.2}},
        ],
        "uncommon": [
            {"id": "harmonic_resonance", "name": "Harmonic Resonance", "type": "passive", "desc": "Maestro's presence strengthens allies, increasing their attack power.", "effect": {"str_pct": 0.1}},
        ],
        "rare": [
            {"id": "discordant_note", "name": "Discordant Note", "type": "active", "desc": "Unleashes a jarring sound, damaging and disrupting an enemy.", "cooldown": 4, "effect": {"atk_pct": 1.0, "mana_cost": 20}},
        ],
        "epic": [
            {"id": "virtuoso_performance", "name": "Virtuoso Performance", "type": "passive", "desc": "Maestro's skill occasionally grants allies a burst of luck.", "effect": {"lck_pct": 0.15}},
        ],
        "legendary": [
            {"id": "crescendo_of_hope", "name": "Crescendo of Hope", "type": "active", "desc": "A powerful song that cleanses negative effects from the Maestro.", "cooldown": 5, "effect": {"cleanse_self": True, "self_heal_pct": 0.1}},
        ],
    },
    "Mage": {
        "common": [
            {"id": "fireball", "name": "Fireball", "type": "active", "desc": "Launches a blazing fireball, incinerating a single enemy for high damage.", "cooldown": 3, "effect": {"atk_pct": 1.5, "mana_cost": 25}},
        ],
        "uncommon": [
            {"id": "arcane_mastery", "name": "Arcane Mastery", "type": "passive", "desc": "The Mage's profound knowledge boosts their intelligence and spell power.", "effect": {"int_pct": 0.2}},
        ],
        "rare": [
            {"id": "blizzard", "name": "Blizzard", "type": "active", "desc": "Summons a chilling storm, damaging all enemies in an area.", "cooldown": 5, "effect": {"atk_pct": 0.7, "mana_cost": 30}},
        ],
        "epic": [
            {"id": "mana_font", "name": "Mana Font", "type": "passive", "desc": "The Mage draws ambient energy, regenerating mana over time.", "effect": {"regen_pct": 0.05}},
        ],
        "legendary": [
            {"id": "stone_skin", "name": "Stone Skin", "type": "active", "desc": "Casts a protective barrier, increasing the Mage's defense temporarily.", "cooldown": 4, "effect": {"def_pct": 0.2, "mana_cost": 15}},
        ],
    },
    "Trade Prince": {
        "common": [
            {"id": "profitable_ventures", "name": "Profitable Ventures", "type": "passive", "desc": "The Trade Prince's wealth grants increased health and luck.", "effect": {"hlt_pct": 0.1, "lck_pct": 0.1}},
        ],
        "uncommon": [
            {"id": "call_mercenaries", "name": "Call Mercenaries", "type": "active", "desc": "Hires temporary muscle, boosting an ally's attack power.", "cooldown": 5, "effect": {"atk_pct": 1.5, "mana_cost": 20}},
        ],
        "rare": [
            {"id": "shrewd_negotiator", "name": "Shrewd Negotiator", "type": "passive", "desc": "The Trade Prince always finds an advantage, boosting agility.", "effect": {"agi_pct": 0.15}},
        ],
        "epic": [
            {"id": "market_crash", "name": "Market Crash", "type": "active", "desc": "Manipulates the market, dealing damage and weakening enemies.", "cooldown": 4, "effect": {"atk_pct": 1.0, "mana_cost": 25}},
        ],
        "legendary": [
            {"id": "resourceful_barter", "name": "Resourceful Barter", "type": "passive", "desc": "Turns disadvantages into gains, occasionally restoring mana.", "effect": {"regen_pct": 0.05}},
        ],
    },
    "Adventurer": {
        "common": [
            {"id": "jack_of_all_trades", "name": "Jack of All Trades", "type": "passive", "desc": "The Adventurer's varied experiences grant a bonus to all stats.", "effect": {"str_pct": 0.05, "def_pct": 0.05}},
        ],
        "uncommon": [
            {"id": "quick_potion", "name": "Quick Potion", "type": "active", "desc": "Chugs a potion, healing oneself and removing negative effects.", "cooldown": 4, "effect": {"self_heal_pct": 0.2, "cleanse_self": True}},
        ],
        "rare": [
            {"id": "keen_eye", "name": "Keen Eye", "type": "passive", "desc": "Years of exploration improve agility and critical luck.", "effect": {"agi_pct": 0.1, "lck_pct": 0.1}},
        ],
        "epic": [
            {"id": "daring_strike", "name": "Daring Strike", "type": "active", "desc": "A bold attack that deals increased damage to an enemy.", "cooldown": 3, "effect": {"atk_pct": 1.3, "mana_cost": 15}},
        ],
        "legendary": [
            {"id": "survival_instincts", "name": "Survival Instincts", "type": "passive", "desc": "Hardened by the wild, the Adventurer gains bonus health and defense.", "effect": {"hlt_pct": 0.1, "def_pct": 0.1}},
        ],
    },
    "Phantom": {
        "common": [
            {"id": "ethereal_form", "name": "Ethereal Form", "type": "passive", "desc": "The Phantom's ghostly nature grants superior agility and evasion.", "effect": {"agi_pct": 0.2}},
        ],
        "uncommon": [
            {"id": "haunting_strike", "name": "Haunting Strike", "type": "active", "desc": "Strikes from the shadows, dealing damage and lowering enemy defense.", "cooldown": 3, "effect": {"atk_pct": 1.2, "mana_cost": 20}},
        ],
        "rare": [
            {"id": "spectral_touch", "name": "Spectral Touch", "type": "passive", "desc": "Phantom attacks have a chance to deal crushing, critical damage.", "effect": {"crushing_blow": True}},
        ],
        "epic": [
            {"id": "vanish", "name": "Vanish", "type": "active", "desc": "Fades from sight, cleansing negative effects and restoring some health.", "cooldown": 5, "effect": {"cleanse_self": True, "self_heal_pct": 0.15}},
        ],
        "legendary": [
            {"id": "lingering_presence", "name": "Lingering Presence", "type": "passive", "desc": "Even near defeat, the Phantom's essence provides a final burst of healing.", "effect": {"death_heal": True}},
        ],
    },
    "Oracle": {
        "common": [
            {"id": "prophetic_vision", "name": "Prophetic Vision", "type": "active", "desc": "Foresight guides an ally, significantly boosting their next attack.", "cooldown": 4, "effect": {"atk_pct": 1.8, "mana_cost": 25}},
        ],
        "uncommon": [
            {"id": "divine_guidance", "name": "Divine Guidance", "type": "passive", "desc": "The Oracle's insight enhances intelligence and luck for the team.", "effect": {"int_pct": 0.1, "lck_pct": 0.1}},
        ],
        "rare": [
            {"id": "healing_word", "name": "Healing Word", "type": "active", "desc": "Speaks a word of comfort, restoring health to the lowest ally.", "cooldown": 3, "effect": {"heal_pct": 0.25, "mana_cost": 15}},
        ],
        "epic": [
            {"id": "celestial_shield", "name": "Celestial Shield", "type": "active", "desc": "Conjures a shield of light, increasing an ally's defense.", "cooldown": 5, "effect": {"def_pct": 0.2, "mana_cost": 20}},
        ],
        "legendary": [
            {"id": "aura_of_serenity", "name": "Aura of Serenity", "type": "passive", "desc": "The Oracle's calming presence grants allies minor health regeneration.", "effect": {"regen_pct": 0.05}},
        ],
    },
    "Nature's Chosen": {
        "common": [
            {"id": "verdant_aura", "name": "Verdant Aura", "type": "passive", "desc": "A healing aura from nature constantly restores allies' health.", "effect": {"regen_pct": 0.07}},
        ],
        "uncommon": [
            {"id": "thorn_whip", "name": "Thorn Whip", "type": "active", "desc": "Summons a thorny vine, dealing damage and entangling an enemy.", "cooldown": 3, "effect": {"atk_pct": 1.1, "mana_cost": 15}},
        ],
        "rare": [
            {"id": "wild_growth", "name": "Wild Growth", "type": "passive", "desc": "Nature's essence enhances the chosen one's maximum health.", "effect": {"hlt_pct": 0.2}},
        ],
        "epic": [
            {"id": "nature_s_embrace", "name": "Nature's Embrace", "type": "active", "desc": "Calls upon nature's healing, restoring significant health to an ally.", "cooldown": 4, "effect": {"heal_pct": 0.3, "mana_cost": 25}},
        ],
        "legendary": [
            {"id": "primal_instinct", "name": "Primal Instinct", "type": "passive", "desc": "Taps into primal rage, occasionally entering an enraged state.", "effect": {"enrage": True}},
        ],
    },
    "Lancer": {
        "common": [
            {"id": "impaling_strike", "name": "Impaling Strike", "type": "passive", "desc": "The Lancer's thrusts have a chance to deal crushing damage.", "effect": {"crushing_blow": True}},
        ],
        "uncommon": [
            {"id": "valiant_charge", "name": "Valiant Charge", "type": "active", "desc": "Charges an enemy, dealing damage and boosting the Lancer's defense.", "cooldown": 4, "effect": {"atk_pct": 1.3, "def_pct": 0.15}},
        ],
        "rare": [
            {"id": "shield_wall", "name": "Shield Wall", "type": "passive", "desc": "Standing firm, the Lancer gains a permanent increase to defense.", "effect": {"def_pct": 0.15}},
        ],
        "epic": [
            {"id": "piercing_thrust", "name": "Piercing Thrust", "type": "active", "desc": "A precise strike that bypasses enemy defenses for high damage.", "cooldown": 3, "effect": {"atk_pct": 1.4, "mana_cost": 20}},
        ],
        "legendary": [
            {"id": "steadfast_resolve", "name": "Steadfast Resolve", "type": "passive", "desc": "Unwavering determination grants increased health and minor regeneration.", "effect": {"hlt_pct": 0.1, "regen_pct": 0.03}},
        ],
    },
    "Divine Sentinel": {
        "common": [
            {"id": "holy_bulwark", "name": "Holy Bulwark", "type": "passive", "desc": "Blessed by divine power, the Sentinel gains immense defense and health.", "effect": {"def_pct": 0.2, "hlt_pct": 0.1}},
        ],
        "uncommon": [
            {"id": "divine_protection", "name": "Divine Protection", "type": "active", "desc": "Shields an ally with holy light, healing them and boosting their defense.", "cooldown": 4, "effect": {"heal_pct": 0.2, "def_pct": 0.1}},
        ],
        "rare": [
            {"id": "righteous_fury", "name": "Righteous Fury", "type": "passive", "desc": "The Sentinel's conviction fuels their attacks, increasing strength.", "effect": {"str_pct": 0.15}},
        ],
        "epic": [
            {"id": "sacred_shield", "name": "Sacred Shield", "type": "active", "desc": "Invokes a sacred shield, healing the Sentinel and cleansing ailments.", "cooldown": 5, "effect": {"self_heal_pct": 0.25, "cleanse_self": True}},
        ],
        "legendary": [
            {"id": "martyr_s_blessing", "name": "Martyr's Blessing", "type": "passive", "desc": "Upon defeat, the Sentinel heals a nearby ally as a final act of devotion.", "effect": {"death_heal": True}},
        ],
    },
    "Rune Master": {
        "common": [
            {"id": "rm_runic_knowledge", "name": "Runic Knowledge", "type": "passive", "desc": "Deep understanding of runes boosts intellect and luck.", "effect": {"int_pct": 0.15, "lck_pct": 0.1}},
        ],
        "uncommon": [
            {"id": "rm_rune_of_warding", "name": "Rune of Warding", "type": "active", "desc": "Places a protective rune on the lowest health ally.", "cooldown": 5, "effect": {"def_pct": 0.25}},
        ],
        "rare": [
            {"id": "rm_arcane_barrage", "name": "Arcane Barrage", "type": "active", "desc": "Unleashes a volley of arcane energy at an enemy.", "cooldown": 3, "effect": {"atk_pct": 1.7, "mana_cost": 25}},
        ],
        "epic": [
            {"id": "rm_mana_conduit", "name": "Mana Conduit", "type": "passive", "desc": "Continuously regenerates mana each turn.", "effect": {"regen_pct": 0.05}},
        ],
        "legendary": [
            {"id": "rm_rune_of_power", "name": "Rune of Power", "type": "active", "desc": "Empowers an ally, increasing their strength and intelligence.", "cooldown": 6, "effect": {"str_pct": 0.2, "int_pct": 0.2}},
        ],
    },
    "Lich": {
        "common": [
            {"id": "lich_soul_drain", "name": "Soul Drain", "type": "active", "desc": "Drains life from an enemy, healing the Lich.", "cooldown": 4, "effect": {"atk_pct": 1.4, "self_heal_pct": 0.3}},
        ],
        "uncommon": [
            {"id": "lich_undying_will", "name": "Undying Will", "type": "passive", "desc": "Upon an ally's death, the Lich heals significantly.", "effect": {"death_heal": True}},
        ],
        "rare": [
            {"id": "lich_curse_of_frailty", "name": "Curse of Frailty", "type": "active", "desc": "Curses an enemy, reducing their defensive capabilities.", "cooldown": 5, "effect": {"def_pct": -0.2}},
        ],
        "epic": [
            {"id": "lich_necrotic_aura", "name": "Necrotic Aura", "type": "passive", "desc": "The Lich's presence saps life, slightly increasing health.", "effect": {"hlt_pct": 0.15}},
        ],
        "legendary": [
            {"id": "lich_grasp_of_death", "name": "Grasp of Death", "type": "active", "desc": "A chilling attack that deals crushing damage and saps strength.", "cooldown": 6, "effect": {"crushing_blow": True, "str_pct": -0.15}},
        ],
    },
    "Rune Blade": {
        "common": [
            {"id": "rb_arcane_edge", "name": "Arcane Edge", "type": "passive", "desc": "Weapon imbued with runes, increasing attack and intelligence.", "effect": {"atk_pct": 0.1, "int_pct": 0.05}},
        ],
        "uncommon": [
            {"id": "rb_runic_slash", "name": "Runic Slash", "type": "active", "desc": "A powerful sword strike that empowers the Rune Blade.", "cooldown": 3, "effect": {"atk_pct": 1.6, "str_pct": 0.15}},
        ],
        "rare": [
            {"id": "rb_woven_runes", "name": "Woven Runes", "type": "passive", "desc": "Defensive runes woven into armor, boosting health and defense.", "effect": {"hlt_pct": 0.15, "def_pct": 0.1}},
        ],
        "epic": [
            {"id": "rb_spell_ward", "name": "Spell Ward", "type": "active", "desc": "Cleanses self of debuffs and creates a magical defense.", "cooldown": 5, "effect": {"cleanse_self": True, "def_pct": 0.2}},
        ],
        "legendary": [
            {"id": "rb_empowered_strike", "name": "Empowered Strike", "type": "active", "desc": "A devastating blow with a chance for massive damage.", "cooldown": 4, "effect": {"crushing_blow": True, "atk_pct": 1.8}},
        ],
    },
    "Scavenger": {
        "common": [
            {"id": "sc_opportunist", "name": "Opportunist", "type": "passive", "desc": "Always finding openings, increasing luck and attack power.", "effect": {"lck_pct": 0.15, "atk_pct": 0.08}},
        ],
        "uncommon": [
            {"id": "sc_makeshift_trap", "name": "Makeshift Trap", "type": "active", "desc": "Deploys a trap that reduces an enemy's defense.", "cooldown": 5, "effect": {"def_pct": -0.2}},
        ],
        "rare": [
            {"id": "sc_resourceful", "name": "Resourceful", "type": "passive", "desc": "Able to quickly recover, granting health regeneration.", "effect": {"regen_pct": 0.03}},
        ],
        "epic": [
            {"id": "sc_scavenged_bomb", "name": "Scavenged Bomb", "type": "active", "desc": "Hurls a crude bomb, damaging and weakening enemies.", "cooldown": 4, "effect": {"atk_pct": 1.3, "def_pct": -0.1}},
        ],
        "legendary": [
            {"id": "sc_quick_hands", "name": "Quick Hands", "type": "passive", "desc": "Agile and nimble, boosting agility and evasion.", "effect": {"agi_pct": 0.15, "lck_pct": 0.05}},
        ],
    },
    "Medic": {
        "common": [
            {"id": "med_triage", "name": "Triage", "type": "active", "desc": "Quickly heals the most injured ally on the battlefield.", "cooldown": 3, "effect": {"heal_pct": 0.25}},
        ],
        "uncommon": [
            {"id": "med_field_medic", "name": "Field Medic", "type": "passive", "desc": "Experienced in battle, increasing intellect and health.", "effect": {"int_pct": 0.1, "hlt_pct": 0.1}},
        ],
        "rare": [
            {"id": "med_stim_pack", "name": "Stim Pack", "type": "active", "desc": "Administers a potent stimulant, boosting an ally's stats.", "cooldown": 5, "effect": {"str_pct": 0.15, "agi_pct": 0.15}},
        ],
        "epic": [
            {"id": "med_vitality_aura", "name": "Vitality Aura", "type": "passive", "desc": "A soothing presence that enhances the Medic's healing power.", "effect": {"int_pct": 0.15, "hlt_pct": 0.05}},
        ],
        "legendary": [
            {"id": "med_emergency_response", "name": "Emergency Response", "type": "active", "desc": "A rapid, powerful heal for the most critical ally.", "cooldown": 6, "effect": {"heal_pct": 0.4}},
        ],
    },
    "Wild Master": {
        "common": [
            {"id": "wm_primal_instinct", "name": "Primal Instinct", "type": "passive", "desc": "Taps into primal urges, boosting strength and agility.", "effect": {"str_pct": 0.1, "agi_pct": 0.1}},
        ],
        "uncommon": [
            {"id": "wm_roar_of_the_wild", "name": "Roar of the Wild", "type": "active", "desc": "Lets out a terrifying roar, enraging the Wild Master.", "cooldown": 4, "effect": {"enrage": True, "atk_pct": 0.25}},
        ],
        "rare": [
            {"id": "wm_natures_resilience", "name": "Nature's Resilience", "type": "passive", "desc": "Hardened by nature, increasing health and defense.", "effect": {"hlt_pct": 0.15, "def_pct": 0.1}},
        ],
        "epic": [
            {"id": "wm_thorn_whip", "name": "Thorn Whip", "type": "active", "desc": "Whips an enemy with thorny vines, dealing damage and slowing.", "cooldown": 3, "effect": {"atk_pct": 1.5, "agi_pct": -0.1}},
        ],
        "legendary": [
            {"id": "wm_healing_herbs", "name": "Healing Herbs", "type": "active", "desc": "Applies natural poultices, healing the lowest health ally.", "cooldown": 5, "effect": {"heal_pct": 0.3}},
        ],
    },
    "Elementalist": {
        "common": [
            {"id": "ele_elemental_attunement", "name": "Elemental Attunement", "type": "passive", "desc": "Deep connection to elements boosts intelligence and luck.", "effect": {"int_pct": 0.15, "lck_pct": 0.08}},
        ],
        "uncommon": [
            {"id": "ele_fireball", "name": "Fireball", "type": "active", "desc": "Hurls a searing fireball, dealing significant damage.", "cooldown": 3, "effect": {"atk_pct": 1.8, "mana_cost": 20}},
        ],
        "rare": [
            {"id": "ele_stone_skin", "name": "Stone Skin", "type": "passive", "desc": "Elemental protection hardens skin, increasing defense and health.", "effect": {"def_pct": 0.15, "hlt_pct": 0.1}},
        ],
        "epic": [
            {"id": "ele_frost_nova", "name": "Frost Nova", "type": "active", "desc": "Unleashes a burst of frost, damaging and slowing enemies.", "cooldown": 4, "effect": {"atk_pct": 1.2, "agi_pct": -0.15}},
        ],
        "legendary": [
            {"id": "ele_lightning_strike", "name": "Lightning Strike", "type": "active", "desc": "Calls down a bolt of lightning for massive damage.", "cooldown": 5, "effect": {"crushing_blow": True, "atk_pct": 2.0}},
        ],
    },
    "Armorer": {
        "common": [
            {"id": "arm_reinforced_plating", "name": "Reinforced Plating", "type": "passive", "desc": "Expertly crafted armor provides superior defense and health.", "effect": {"def_pct": 0.2, "hlt_pct": 0.15}},
        ],
        "uncommon": [
            {"id": "arm_shield_wall", "name": "Shield Wall", "type": "active", "desc": "Braces behind a shield, vastly increasing personal defense.", "cooldown": 4, "effect": {"def_pct": 0.4}},
        ],
        "rare": [
            {"id": "arm_master_craftsman", "name": "Master Craftsman", "type": "passive", "desc": "Knowledge of materials boosts strength and defense.", "effect": {"str_pct": 0.08, "def_pct": 0.08}},
        ],
        "epic": [
            {"id": "arm_weapon_polish", "name": "Weapon Polish", "type": "active", "desc": "Polishes weapon to a keen edge, boosting attack power.", "cooldown": 3, "effect": {"atk_pct": 0.2}},
        ],
        "legendary": [
            {"id": "arm_taunt", "name": "Taunt", "type": "active", "desc": "Draws enemy attention, enraging self and increasing defense.", "cooldown": 5, "effect": {"enrage": True, "def_pct": 0.25}},
        ],
    },
    "Mercenary": {
        "common": [
            {"id": "mer_battle_hardened", "name": "Battle Hardened", "type": "passive", "desc": "Years of combat increase strength and health.", "effect": {"str_pct": 0.15, "hlt_pct": 0.1}},
        ],
        "uncommon": [
            {"id": "mer_focused_strike", "name": "Focused Strike", "type": "active", "desc": "A precise attack with a high chance for crushing damage.", "cooldown": 4, "effect": {"atk_pct": 1.7, "crushing_blow": True}},
        ],
        "rare": [
            {"id": "mer_quick_reflexes", "name": "Quick Reflexes", "type": "passive", "desc": "Sharp instincts boost agility and luck.", "effect": {"agi_pct": 0.1, "lck_pct": 0.05}},
        ],
        "epic": [
            {"id": "mer_grenade_toss", "name": "Grenade Toss", "type": "active", "desc": "Hurls a grenade, damaging and debuffing enemies.", "cooldown": 5, "effect": {"atk_pct": 1.3, "def_pct": -0.15}},
        ],
        "legendary": [
            {"id": "mer_adrenaline_rush", "name": "Adrenaline Rush", "type": "active", "desc": "A burst of adrenaline, enraging and boosting attack power.", "cooldown": 6, "effect": {"enrage": True, "atk_pct": 0.3}},
        ],
    },
    "Pikemaster": {
        "common": [
            {"id": "pm_extended_reach", "name": "Extended Reach", "type": "passive", "desc": "Mastery of the pike grants increased attack range and agility.", "effect": {"atk_pct": 0.1, "agi_pct": 0.05}},
        ],
        "uncommon": [
            {"id": "pm_impale", "name": "Impale", "type": "active", "desc": "A piercing thrust that damages and weakens an enemy's defense.", "cooldown": 3, "effect": {"atk_pct": 1.6, "def_pct": -0.15}},
        ],
        "rare": [
            {"id": "pm_phalanx_training", "name": "Phalanx Training", "type": "passive", "desc": "Rigorous training provides enhanced defense and health.", "effect": {"def_pct": 0.15, "hlt_pct": 0.1}},
        ],
        "epic": [
            {"id": "pm_sweeping_pike", "name": "Sweeping Pike", "type": "active", "desc": "A wide sweep with the pike, damaging and slowing enemies.", "cooldown": 4, "effect": {"atk_pct": 1.4, "agi_pct": -0.1}},
        ],
        "legendary": [
            {"id": "pm_brace_for_impact", "name": "Brace for Impact", "type": "active", "desc": "Braces against incoming attacks, cleansing and boosting defense.", "cooldown": 5, "effect": {"def_pct": 0.25, "cleanse_self": True}},
        ],
    },
    "Crossbowman": {
        "common": [
            {"id": "crossbow_piercing_shot", "name": "Piercing Shot", "type": "active", "desc": "Fires a bolt that ignores enemy defense for massive damage.", "cooldown": 3, "effect": {"atk_pct": 1.8, "def_pct": -0.2}},
        ],
        "uncommon": [
            {"id": "crossbow_rapid_fire", "name": "Rapid Fire", "type": "active", "desc": "Unleashes a flurry of bolts, dealing moderate damage multiple times.", "cooldown": 2, "effect": {"atk_pct": 1.2, "agi_pct": 0.1}},
        ],
        "rare": [
            {"id": "crossbow_eagle_eye", "name": "Eagle Eye", "type": "passive", "desc": "Enhances vision, increasing accuracy and critical hit chance.", "effect": {"lck_pct": 0.15, "agi_pct": 0.1}},
        ],
        "epic": [
            {"id": "crossbow_pinning_shot", "name": "Pinning Shot", "type": "active", "desc": "A precision shot that slows the enemy, reducing their actions.", "cooldown": 4, "effect": {"atk_pct": 1.0, "agi_pct": -0.2}},
        ],
        "legendary": [
            {"id": "crossbow_steady_aim", "name": "Steady Aim", "type": "passive", "desc": "Focuses for increased damage and strength during sustained attacks.", "effect": {"atk_pct": 0.1, "str_pct": 0.1}},
        ],
    },
    "Plague Doctor": {
        "common": [
            {"id": "pd_contagion", "name": "Contagion", "type": "active", "desc": "Inflicts a spreading disease, dealing damage over time to enemies.", "cooldown": 3, "effect": {"atk_pct": 0.5, "regen_pct": -0.05}},
        ],
        "uncommon": [
            {"id": "pd_leech_field", "name": "Leech Field", "type": "active", "desc": "Creates an aura that drains enemy health to heal the weakest ally.", "cooldown": 4, "effect": {"atk_pct": 0.7, "heal_pct": 0.1}},
        ],
        "rare": [
            {"id": "pd_sanitize", "name": "Sanitize", "type": "active", "desc": "Removes all negative status effects from a targeted ally.", "cooldown": 5, "effect": {"cleanse_self": True, "heal_pct": 0.05}},
        ],
        "epic": [
            {"id": "pd_miasma", "name": "Miasma", "type": "passive", "desc": "A noxious aura that constantly weakens nearby enemies' defense.", "effect": {"def_pct": -0.1, "int_pct": 0.05}},
        ],
        "legendary": [
            {"id": "pd_field_medic", "name": "Field Medic", "type": "passive", "desc": "Provides continuous minor healing to the entire party.", "effect": {"regen_pct": 0.02, "int_pct": 0.05}},
        ],
    },
    "Hero": {
        "common": [
            {"id": "hero_heroic_strike", "name": "Heroic Strike", "type": "active", "desc": "A powerful blow that deals significant damage to a single foe.", "cooldown": 3, "effect": {"atk_pct": 1.7, "crushing_blow": True}},
        ],
        "uncommon": [
            {"id": "hero_stand_united", "name": "Stand United", "type": "active", "desc": "Inspires allies, increasing their defense and resolve for a short time.", "cooldown": 4, "effect": {"def_pct": 0.2, "int_pct": 0.1}},
        ],
        "rare": [
            {"id": "hero_inspiring_presence", "name": "Inspiring Presence", "type": "passive", "desc": "The Hero's mere presence increases all allies' strength and spirit.", "effect": {"str_pct": 0.05, "int_pct": 0.05}},
        ],
        "epic": [
            {"id": "hero_last_stand", "name": "Last Stand", "type": "passive", "desc": "When gravely wounded, the Hero fights harder, gaining defense and attack.", "effect": {"enrage": True, "def_pct": 0.1}},
        ],
        "legendary": [
            {"id": "hero_valiant_charge", "name": "Valiant Charge", "type": "active", "desc": "Charges into battle, dealing damage and temporarily boosting self-defense.", "cooldown": 3, "effect": {"atk_pct": 1.3, "def_pct": 0.15}},
        ],
    },
    "Sous Chef": {
        "common": [
            {"id": "chef_hearty_meal", "name": "Hearty Meal", "type": "active", "desc": "Prepares a delicious meal, restoring significant health to a single ally.", "cooldown": 4, "effect": {"heal_pct": 0.3}},
        ],
        "uncommon": [
            {"id": "chef_spicy_seasoning", "name": "Spicy Seasoning", "type": "active", "desc": "Adds a kick to an ally's dish, temporarily boosting their attack power.", "cooldown": 3, "effect": {"atk_pct": 0.2, "str_pct": 0.1}},
        ],
        "rare": [
            {"id": "chef_gourmet_platter", "name": "Gourmet Platter", "type": "passive", "desc": "Regularly prepares delightful dishes, offering minor stat boosts to all allies.", "effect": {"str_pct": 0.03, "def_pct": 0.03}},
        ],
        "epic": [
            {"id": "chef_chefs_resolve", "name": "Chef's Resolve", "type": "passive", "desc": "A sturdy cook, gaining increased health and defense from constant kitchen work.", "effect": {"hlt_pct": 0.1, "def_pct": 0.05}},
        ],
        "legendary": [
            {"id": "chef_kitchen_knife_fury", "name": "Kitchen Knife Fury", "type": "active", "desc": "A rapid flurry of knife strikes, dealing quick damage to an enemy.", "cooldown": 2, "effect": {"atk_pct": 1.0, "agi_pct": 0.05}},
        ],
    },
    "Bishop": {
        "common": [
            {"id": "bishop_divine_heal", "name": "Divine Heal", "type": "active", "desc": "Calls upon divine power to restore significant health to an ally.", "cooldown": 3, "effect": {"heal_pct": 0.25}},
        ],
        "uncommon": [
            {"id": "bishop_holy_shield", "name": "Holy Shield", "type": "active", "desc": "Envelops an ally in holy light, granting them increased defense.", "cooldown": 4, "effect": {"def_pct": 0.2, "int_pct": 0.05}},
        ],
        "rare": [
            {"id": "bishop_smite", "name": "Smite", "type": "active", "desc": "Channels divine wrath, smiting an enemy with a burst of holy damage.", "cooldown": 2, "effect": {"atk_pct": 1.5}},
        ],
        "epic": [
            {"id": "bishop_aura_of_faith", "name": "Aura of Faith", "type": "passive", "desc": "A constant aura of divine energy, slowly regenerating party health.", "effect": {"regen_pct": 0.03, "int_pct": 0.05}},
        ],
        "legendary": [
            {"id": "bishop_martyrdom", "name": "Martyrdom", "type": "passive", "desc": "Upon falling in battle, the Bishop's sacrifice heals all remaining allies.", "effect": {"death_heal": True, "int_pct": 0.1}},
        ],
    },
    "Troubadour": {
        "common": [
            {"id": "troubadour_inspiring_ballad", "name": "Inspiring Ballad", "type": "active", "desc": "Plays an uplifting tune, boosting allies' attack and agility.", "cooldown": 3, "effect": {"str_pct": 0.15, "agi_pct": 0.1}},
        ],
        "uncommon": [
            {"id": "troubadour_discordant_melody", "name": "Discordant Melody", "type": "active", "desc": "A jarring tune that weakens enemy defenses and lowers their resolve.", "cooldown": 3, "effect": {"def_pct": -0.15, "int_pct": -0.1}},
        ],
        "rare": [
            {"id": "troubadour_healing_lullaby", "name": "Healing Lullaby", "type": "active", "desc": "Sings a soothing lullaby, restoring health and calming an ally.", "cooldown": 4, "effect": {"heal_pct": 0.15, "cleanse_self": True}},
        ],
        "epic": [
            {"id": "troubadour_charming_aura", "name": "Charming Aura", "type": "passive", "desc": "A natural charm that slightly reduces enemy attack and luck.", "effect": {"str_pct": -0.05, "lck_pct": -0.05}},
        ],
        "legendary": [
            {"id": "troubadour_quick_wit", "name": "Quick Wit", "type": "passive", "desc": "Sharp mind and nimble fingers, granting increased agility and intellect.", "effect": {"agi_pct": 0.1, "int_pct": 0.1}},
        ],
    },
    "Poisoner": {
        "common": [
            {"id": "poisoner_venomous_strike", "name": "Venomous Strike", "type": "active", "desc": "A precise strike that inflicts potent poison, dealing damage over time.", "cooldown": 3, "effect": {"atk_pct": 1.2, "regen_pct": -0.07}},
        ],
        "uncommon": [
            {"id": "poisoner_cloud_of_nausea", "name": "Cloud of Nausea", "type": "active", "desc": "Releases a noxious cloud, reducing enemy attack and agility.", "cooldown": 4, "effect": {"str_pct": -0.1, "agi_pct": -0.1}},
        ],
        "rare": [
            {"id": "poisoner_toxic_brew", "name": "Toxic Brew", "type": "passive", "desc": "Mastery of toxins, increasing the potency and duration of all poisons.", "effect": {"int_pct": 0.15, "lck_pct": 0.05}},
        ],
        "epic": [
            {"id": "poisoner_shadow_blend", "name": "Shadow Blend", "type": "active", "desc": "Vanishes into shadows, then reappears with a critical strike.", "cooldown": 5, "effect": {"atk_pct": 1.5, "crushing_blow": True}},
        ],
        "legendary": [
            {"id": "poisoner_lingering_toxin", "name": "Lingering Toxin", "type": "passive", "desc": "Poisons applied by the Poisoner linger longer, dealing more total damage.", "effect": {"regen_pct": -0.03, "int_pct": 0.05}},
        ],
    },
    "Brewmaster": {
        "common": [
            {"id": "brewmaster_drunken_haze", "name": "Drunken Haze", "type": "active", "desc": "Sprays ale, causing enemies to miss attacks while boosting own defense.", "cooldown": 3, "effect": {"def_pct": 0.15, "lck_pct": -0.1}},
        ],
        "uncommon": [
            {"id": "brewmaster_stout_heart", "name": "Stout Heart", "type": "passive", "desc": "Years of brewing have granted immense health and unwavering defense.", "effect": {"hlt_pct": 0.2, "def_pct": 0.1}},
        ],
        "rare": [
            {"id": "brewmaster_flaming_brew", "name": "Flaming Brew", "type": "active", "desc": "Hurls a flaming barrel, dealing area-of-effect damage to enemies.", "cooldown": 4, "effect": {"atk_pct": 1.3, "str_pct": 0.05}},
        ],
        "epic": [
            {"id": "brewmaster_liquid_courage", "name": "Liquid Courage", "type": "active", "desc": "Drinks a potent brew, restoring health and temporarily boosting attack.", "cooldown": 3, "effect": {"self_heal_pct": 0.15, "atk_pct": 0.1}},
        ],
        "legendary": [
            {"id": "brewmaster_tipsy_resilience", "name": "Tipsy Resilience", "type": "passive", "desc": "The Brewmaster's tipsy state grants a chance to shrug off debuffs.", "effect": {"cleanse_self": True, "def_pct": 0.05}},
        ],
    },
    "Apothecary": {
        "common": [
            {"id": "apothecary_restorative_salve", "name": "Restorative Salve", "type": "active", "desc": "Applies a healing salve, restoring health and removing debuffs.", "cooldown": 4, "effect": {"heal_pct": 0.2, "cleanse_self": True}},
        ],
        "uncommon": [
            {"id": "apothecary_stimulating_draught", "name": "Stimulating Draught", "type": "active", "desc": "Administers a potent draught, boosting an ally's agility and strength.", "cooldown": 3, "effect": {"agi_pct": 0.15, "str_pct": 0.1}},
        ],
        "rare": [
            {"id": "apothecary_antidote_expertise", "name": "Antidote Expertise", "type": "passive", "desc": "Mastery of antidotes, granting the party increased resistance to all debuffs.", "effect": {"def_pct": 0.05, "int_pct": 0.1}},
        ],
        "epic": [
            {"id": "apothecary_alchemical_fire", "name": "Alchemical Fire", "type": "active", "desc": "Hurls a flask of alchemical fire, dealing damage to an enemy.", "cooldown": 2, "effect": {"atk_pct": 1.2, "int_pct": 0.05}},
        ],
        "legendary": [
            {"id": "apothecary_emergency_supplies", "name": "Emergency Supplies", "type": "passive", "desc": "Always prepared, occasionally providing a small emergency heal to the party.", "effect": {"regen_pct": 0.03, "lck_pct": 0.05}},
        ],
    },
    "Deadeye": {
        "common": [
            {"id": "deadeye_headshot", "name": "Headshot", "type": "active", "desc": "A perfectly aimed shot dealing immense damage, often critical.", "cooldown": 4, "effect": {"atk_pct": 2.2, "crushing_blow": True}},
        ],
        "uncommon": [
            {"id": "deadeye_marked_for_death", "name": "Marked for Death", "type": "active", "desc": "Designates an enemy, causing them to take increased damage from all sources.", "cooldown": 5, "effect": {"def_pct": -0.2, "lck_pct": -0.1}},
        ],
        "rare": [
            {"id": "deadeye_precision_training", "name": "Precision Training", "type": "passive", "desc": "Years of training grant unmatched precision, boosting critical chance and damage.", "effect": {"lck_pct": 0.2, "str_pct": 0.05}},
        ],
        "epic": [
            {"id": "deadeye_quickdraw", "name": "Quickdraw", "type": "active", "desc": "A lightning-fast draw and shot, dealing moderate damage quickly.", "cooldown": 2, "effect": {"atk_pct": 1.1, "agi_pct": 0.1}},
        ],
        "legendary": [
            {"id": "deadeye_unflinching_focus", "name": "Unflinching Focus", "type": "passive", "desc": "Focuses intently, allowing attacks to bypass a portion of enemy defense.", "effect": {"str_pct": 0.1, "int_pct": 0.05}},
        ],
    },
    "Hoarder": {
        "common": [
            {"id": "hoarderPackRat", "name": "Pack Rat", "type": "passive", "desc": "Increased health and luck from collected trinkets.", "effect": {"hlt_pct": 0.1, "lck_pct": 0.05}},
        ],
        "uncommon": [
            {"id": "hoarderBarterSavvy", "name": "Barter Savvy", "type": "passive", "desc": "Gains bonus gold after each combat encounter.", "effect": {"lck_pct": 0.1}},
        ],
        "rare": [
            {"id": "hoarderJunkToss", "name": "Junk Toss", "type": "active", "desc": "Hurl collected items at an enemy, dealing varied damage.", "cooldown": 3, "effect": {"atk_pct": 1.2, "mana_cost": 15}},
        ],
        "epic": [
            {"id": "hoarderDeepPockets", "name": "Deep Pockets", "type": "passive", "desc": "Increased inventory space, leading to minor stat boosts.", "effect": {"str_pct": 0.03, "def_pct": 0.03}},
        ],
        "legendary": [
            {"id": "hoarderEmergencyStash", "name": "Emergency Stash", "type": "active", "desc": "Consume a stored item for a powerful self-heal.", "cooldown": 5, "effect": {"self_heal_pct": 0.3, "cleanse_self": True}},
        ],
    },
    "Miracle Worker": {
        "common": [
            {"id": "miracleDivineIntervention", "name": "Divine Intervention", "type": "active", "desc": "Randomly heal an ally or damage an enemy with divine power.", "cooldown": 4, "effect": {"heal_pct": 0.25, "atk_pct": 1.0}},
        ],
        "uncommon": [
            {"id": "miracleSecondChance", "name": "Second Chance", "type": "passive", "desc": "Low chance to fully revive a fallen ally.", "effect": {"death_heal": True}},
        ],
        "rare": [
            {"id": "miracleBlessing", "name": "Blessing of the Fates", "type": "active", "desc": "Bestow a temporary, powerful, random stat buff on an ally.", "cooldown": 6, "effect": {"str_pct": 0.2, "def_pct": 0.2}},
        ],
        "epic": [
            {"id": "miracleHolyAura", "name": "Holy Aura", "type": "passive", "desc": "Allies gain minor health regeneration over time.", "effect": {"regen_pct": 0.05}},
        ],
        "legendary": [
            {"id": "miracleCleansingWave", "name": "Cleansing Wave", "type": "active", "desc": "Cleanse all negative effects from the entire party.", "cooldown": 7, "effect": {"cleanse_self": True}},
        ],
    },
    "Apex Predator": {
        "common": [
            {"id": "apexPredatoryInstinct", "name": "Predatory Instinct", "type": "passive", "desc": "Increased critical hit chance and damage against vulnerable foes.", "effect": {"atk_pct": 0.15, "lck_pct": 0.1}},
        ],
        "uncommon": [
            {"id": "apexPounce", "name": "Pounce", "type": "active", "desc": "Leap onto a foe, dealing massive damage and a crushing blow.", "cooldown": 4, "effect": {"crushing_blow": True, "atk_pct": 1.8}},
        ],
        "rare": [
            {"id": "apexTrophyHunter", "name": "Trophy Hunter", "type": "passive", "desc": "Gains permanent strength after defeating an enemy.", "effect": {"str_pct": 0.02}},
        ],
        "epic": [
            {"id": "apexMarkPrey", "name": "Mark Prey", "type": "active", "desc": "Mark a target, increasing all damage taken by them.", "cooldown": 5, "effect": {"atk_pct": 0.2}},
        ],
        "legendary": [
            {"id": "apexBloodFeast", "name": "Blood Feast", "type": "passive", "desc": "Regenerates health after landing a killing blow.", "effect": {"self_heal_pct": 0.15}},
        ],
    },
    "Rogue": {
        "common": [
            {"id": "rogueShadowStep", "name": "Shadow Step", "type": "passive", "desc": "High evasion chance and critical hit chance while unseen.", "effect": {"agi_pct": 0.15, "lck_pct": 0.08}},
        ],
        "uncommon": [
            {"id": "rogueBackstab", "name": "Backstab", "type": "active", "desc": "Strike from the shadows, dealing bonus critical damage.", "cooldown": 3, "effect": {"atk_pct": 1.5, "crushing_blow": True}},
        ],
        "rare": [
            {"id": "rogueVenomousStrike", "name": "Venomous Strike", "type": "passive", "desc": "Basic attacks have a chance to apply a damaging poison debuff.", "effect": {"atk_pct": 0.05}},
        ],
        "epic": [
            {"id": "rogueSmokeBomb", "name": "Smoke Bomb", "type": "active", "desc": "Vanish from sight, gaining temporary evasion and cleansing debuffs.", "cooldown": 5, "effect": {"cleanse_self": True, "agi_pct": 0.3}},
        ],
        "legendary": [
            {"id": "roguePickpocket", "name": "Pickpocket", "type": "passive", "desc": "Steals a small amount of gold from defeated enemies.", "effect": {"lck_pct": 0.05}},
        ],
    },
    "Tycoon": {
        "common": [
            {"id": "tycoonGoldenTouch", "name": "Golden Touch", "type": "passive", "desc": "Generates bonus gold after each combat encounter.", "effect": {"lck_pct": 0.1}},
        ],
        "uncommon": [
            {"id": "tycoonBribe", "name": "Bribe", "type": "active", "desc": "Bribe an enemy, temporarily charming them to fight for you.", "cooldown": 6, "effect": {"mana_cost": 30, "hlt_pct": 0.05}},
        ],
        "rare": [
            {"id": "tycoonAssetManagement", "name": "Asset Management", "type": "passive", "desc": "Allies gain a small stat boost for every 1000 gold owned.", "effect": {"str_pct": 0.01, "def_pct": 0.01}},
        ],
        "epic": [
            {"id": "tycoonCorporateSponsorship", "name": "Corporate Sponsorship", "type": "active", "desc": "Invest in equipment, granting a temporary party-wide defense buff.", "cooldown": 8, "effect": {"def_pct": 0.2}},
        ],
        "legendary": [
            {"id": "tycoonHostileTakeover", "name": "Hostile Takeover", "type": "passive", "desc": "Recovers health and mana when an ally is defeated.", "effect": {"self_heal_pct": 0.2, "mana_cost": -25}},
        ],
    },
    "Farmer": {
        "common": [
            {"id": "farmerHeartyStock", "name": "Hearty Stock", "type": "passive", "desc": "Increased health and natural regeneration.", "effect": {"hlt_pct": 0.15, "regen_pct": 0.03}},
        ],
        "uncommon": [
            {"id": "farmerHealingHerbs", "name": "Healing Herbs", "type": "active", "desc": "Plant a healing herb, restoring health to the lowest ally.", "cooldown": 3, "effect": {"heal_pct": 0.3}},
        ],
        "rare": [
            {"id": "farmerEarthBond", "name": "Earth Bond", "type": "passive", "desc": "Allies gain bonus defense from natural environments.", "effect": {"def_pct": 0.1}},
        ],
        "epic": [
            {"id": "farmerScarecrowDistraction", "name": "Scarecrow Distraction", "type": "active", "desc": "Deploy a scarecrow, drawing enemy aggro and protecting allies.", "cooldown": 5, "effect": {"hlt_pct": 0.2}},
        ],
        "legendary": [
            {"id": "farmerBountifulHarvest", "name": "Bountiful Harvest", "type": "passive", "desc": "Harvests extra resources from defeated foes.", "effect": {"lck_pct": 0.08}},
        ],
    },
    "Beastmaster": {
        "common": [
            {"id": "beastmasterLoyalCompanion", "name": "Loyal Companion", "type": "passive", "desc": "Summons a loyal animal companion to fight alongside.", "effect": {"hlt_pct": 0.2, "atk_pct": 0.1}},
        ],
        "uncommon": [
            {"id": "beastmasterCoordinatedAssault", "name": "Coordinated Assault", "type": "active", "desc": "Command beast to attack, dealing focused damage with you.", "cooldown": 3, "effect": {"atk_pct": 1.5}},
        ],
        "rare": [
            {"id": "beastmasterPackLeader", "name": "Pack Leader", "type": "passive", "desc": "Beasts gain increased stats for every Beastmaster level.", "effect": {"str_pct": 0.05, "def_pct": 0.05}},
        ],
        "epic": [
            {"id": "beastmasterFeralRoar", "name": "Feral Roar", "type": "active", "desc": "Inspires all animal allies to enrage, boosting their power.", "cooldown": 6, "effect": {"enrage": True}},
        ],
        "legendary": [
            {"id": "beastmasterAnimalBond", "name": "Animal Bond", "type": "passive", "desc": "Heals a percentage of health when a summoned beast is defeated.", "effect": {"self_heal_pct": 0.1}},
        ],
    },
    "Runesmith": {
        "common": [
            {"id": "runesmithElementalInfusion", "name": "Elemental Infusion", "type": "passive", "desc": "Basic attacks have a chance to apply elemental debuffs.", "effect": {"atk_pct": 0.07}},
        ],
        "uncommon": [
            {"id": "runesmithWardingRune", "name": "Warding Rune", "type": "active", "desc": "Engrave a defensive rune, granting temporary shield to an ally.", "cooldown": 4, "effect": {"def_pct": 0.25}},
        ],
        "rare": [
            {"id": "runesmithArcaneFlow", "name": "Arcane Flow", "type": "passive", "desc": "Gains bonus mana regeneration from elemental damage dealt.", "effect": {"mana_cost": -10}},
        ],
        "epic": [
            {"id": "runesmithPowerGlyph", "name": "Power Glyph", "type": "active", "desc": "Carve a potent offensive rune, empowering your next attack.", "cooldown": 5, "effect": {"atk_pct": 1.7, "crushing_blow": True}},
        ],
        "legendary": [
            {"id": "runesmithElementalResistance", "name": "Elemental Resistance", "type": "passive", "desc": "Allies gain increased resistance to elemental damage.", "effect": {"def_pct": 0.1}},
        ],
    },
    "Chief Medical Officer": {
        "common": [
            {"id": "cmoTriage", "name": "Triage", "type": "active", "desc": "Swiftly heal the lowest health ally significantly.", "cooldown": 3, "effect": {"heal_pct": 0.4}},
        ],
        "uncommon": [
            {"id": "cmoSterilization", "name": "Sterilization Protocol", "type": "passive", "desc": "Allies are immune to most debuffs.", "effect": {"cleanse_self": True}},
        ],
        "rare": [
            {"id": "cmoStimPack", "name": "Stim-Pack", "type": "active", "desc": "Grant an ally temporary attack and speed boost.", "cooldown": 5, "effect": {"str_pct": 0.2, "agi_pct": 0.2}},
        ],
        "epic": [
            {"id": "cmoFieldMedic", "name": "Field Medic", "type": "passive", "desc": "Every turn, the lowest health ally receives a small heal.", "effect": {"regen_pct": 0.07}},
        ],
        "legendary": [
            {"id": "cmoDefibrillate", "name": "Defibrillate", "type": "active", "desc": "Revive a fallen ally with partial health.", "cooldown": 10, "effect": {"death_heal": True, "heal_pct": 0.3}},
        ],
    },
    "Iron Chef": {
        "common": [
            {"id": "ironChefCulinaryPrep", "name": "Culinary Prep", "type": "passive", "desc": "Prepares a random buffing dish at the start of combat.", "effect": {"hlt_pct": 0.05, "str_pct": 0.05}},
        ],
        "uncommon": [
            {"id": "ironChefGourmetFeast", "name": "Gourmet Feast", "type": "active", "desc": "Serve a delicious meal, healing all allies.", "cooldown": 6, "effect": {"heal_pct": 0.2}},
        ],
        "rare": [
            {"id": "ironChefFoodPoisoning", "name": "Food Poisoning", "type": "passive", "desc": "Enemies struck by chef's attacks suffer damage over time.", "effect": {"atk_pct": 0.05}},
        ],
        "epic": [
            {"id": "ironChefSpiceBomb", "name": "Spice Bomb", "type": "active", "desc": "Throw a pungent spice bomb, debuffing enemy defense.", "cooldown": 4, "effect": {"def_pct": -0.15}},
        ],
        "legendary": [
            {"id": "ironChefSelfServe", "name": "Self-Serve", "type": "passive", "desc": "Gains bonus stats after consuming one of own dishes.", "effect": {"self_heal_pct": 0.05, "str_pct": 0.05}},
        ],
    },
    "Voidwalker": {
        "common": [
            {"id": "voidwalker_void_step", "name": "Void Step", "type": "active", "desc": "Teleports, deals damage, and reduces enemy defense. Strikes from the shadows.", "cooldown": 4, "effect": {"atk_pct": 1.2, "def_pct": -0.15}},
        ],
        "uncommon": [
            {"id": "voidwalker_shadow_embrace", "name": "Shadow Embrace", "type": "passive", "desc": "Briefly gains defense after being hit. Embraces the darkness.", "effect": {"def_pct": 0.1}},
        ],
        "rare": [
            {"id": "voidwalker_entropy_drain", "name": "Entropy Drain", "type": "active", "desc": "Siphons enemy life force, restoring own health. A dark bargain.", "cooldown": 3, "effect": {"atk_pct": 0.8, "self_heal_pct": 0.5}},
        ],
        "epic": [
            {"id": "voidwalker_oblivion_gaze", "name": "Oblivion Gaze", "type": "passive", "desc": "Confuses foes, increasing miss chance. Gaze into the void.", "effect": {"agi_pct": 0.15}},
        ],
        "legendary": [
            {"id": "voidwalker_void_anchor", "name": "Void Anchor", "type": "active", "desc": "Roots enemy, dealing damage over time. Anchored to the abyss.", "cooldown": 5, "effect": {"atk_pct": 0.6, "regen_pct": -0.03}},
        ],
    },
    "Aegis": {
        "common": [
            {"id": "aegis_bulwark_stance", "name": "Bulwark Stance", "type": "passive", "desc": "Improves defenses and max health. A steadfast protector, unyielding.", "effect": {"def_pct": 0.2, "hlt_pct": 0.1}},
        ],
        "uncommon": [
            {"id": "aegis_shield_bash", "name": "Shield Bash", "type": "active", "desc": "Bashes enemy with shield, dealing damage and stunning them momentarily.", "cooldown": 4, "effect": {"atk_pct": 1.0}},
        ],
        "rare": [
            {"id": "aegis_divine_aegis", "name": "Divine Aegis", "type": "active", "desc": "Shields lowest health ally, absorbing damage. Divine protection granted.", "cooldown": 5, "effect": {"heal_pct": 0.3}},
        ],
        "epic": [
            {"id": "aegis_unyielding_resolve", "name": "Unyielding Resolve", "type": "passive", "desc": "Increases defense significantly when below 30% health. Never surrender!", "effect": {"def_pct": 0.25}},
        ],
        "legendary": [
            {"id": "aegis_challenging_roar", "name": "Challenging Roar", "type": "active", "desc": "Taunts all enemies, forcing their attacks. Protects the vulnerable.", "cooldown": 6, "effect": {"enrage": True}},
        ],
    },
    "Halberdier": {
        "common": [
            {"id": "halberdier_sweeping_strike", "name": "Sweeping Strike", "type": "active", "desc": "Swings halberd in wide arc, damaging multiple foes. Clears the way.", "cooldown": 3, "effect": {"atk_pct": 0.8}},
        ],
        "uncommon": [
            {"id": "halberdier_impale", "name": "Impale", "type": "active", "desc": "Impales enemy, dealing massive damage and causing them to bleed.", "cooldown": 4, "effect": {"atk_pct": 1.7, "regen_pct": -0.02}},
        ],
        "rare": [
            {"id": "halberdier_polearm_mastery", "name": "Polearm Mastery", "type": "passive", "desc": "Enhances weapon attacks, increasing damage and critical chance.", "effect": {"str_pct": 0.15, "lck_pct": 0.1}},
        ],
        "epic": [
            {"id": "halberdier_staggering_blow", "name": "Staggering Blow", "type": "passive", "desc": "Regular attacks sometimes stun enemies. Disrupts enemy formations.", "effect": {"crushing_blow": True}},
        ],
        "legendary": [
            {"id": "halberdier_phalanx_formation", "name": "Phalanx Formation", "type": "active", "desc": "Forms a defensive line, boosting nearby allies' defense. Holds the line!", "cooldown": 5, "effect": {"def_pct": 0.2}},
        ],
    },
    "Pathfinder": {
        "common": [
            {"id": "pathfinder_marked_shot", "name": "Marked Shot", "type": "active", "desc": "Marks target, increasing damage taken. Pinpoint accuracy.", "cooldown": 3, "effect": {"atk_pct": 1.0, "def_pct": -0.1}},
        ],
        "uncommon": [
            {"id": "pathfinder_camouflage", "name": "Camouflage", "type": "passive", "desc": "Blends into environment, improving evasion and reducing target priority.", "effect": {"agi_pct": 0.2}},
        ],
        "rare": [
            {"id": "pathfinder_caltrop_trap", "name": "Caltrop Trap", "type": "active", "desc": "Deploys caltrops, damaging and slowing enemies. Area denial.", "cooldown": 4, "effect": {"atk_pct": 0.5, "agi_pct": -0.1}},
        ],
        "epic": [
            {"id": "pathfinder_keen_eyesight", "name": "Keen Eyesight", "type": "passive", "desc": "Sharpens senses, improving critical strike chance and overall accuracy.", "effect": {"lck_pct": 0.15, "str_pct": 0.05}},
        ],
        "legendary": [
            {"id": "pathfinder_first_aid", "name": "First Aid", "type": "active", "desc": "Applies quick bandages, healing an ally. Essential field medic.", "cooldown": 5, "effect": {"heal_pct": 0.25}},
        ],
    },
    "Transmuter": {
        "common": [
            {"id": "transmuter_elemental_infusion", "name": "Elemental Infusion", "type": "active", "desc": "Infuses ally with elemental power, boosting attack or defense.", "cooldown": 4, "effect": {"str_pct": 0.15, "def_pct": 0.15}},
        ],
        "uncommon": [
            {"id": "transmuter_alchemical_vapors", "name": "Alchemical Vapors", "type": "active", "desc": "Unleashes noxious vapors, damaging foes and weakening their stats.", "cooldown": 5, "effect": {"atk_pct": 0.7, "str_pct": -0.1}},
        ],
        "rare": [
            {"id": "transmuter_stone_skin", "name": "Stone Skin", "type": "passive", "desc": "Hardens skin, increasing resilience and maximum health. Durable and tough.", "effect": {"def_pct": 0.15, "hlt_pct": 0.08}},
        ],
        "epic": [
            {"id": "transmuter_rejuvenating_ooze", "name": "Rejuvenating Ooze", "type": "passive", "desc": "Emits healing aura, restoring health to self and allies over time.", "effect": {"regen_pct": 0.03}},
        ],
        "legendary": [
            {"id": "transmuter_shifting_form", "name": "Shifting Form", "type": "active", "desc": "Temporarily shifts form, greatly boosting either attack or defense.", "cooldown": 6, "effect": {"str_pct": 0.3}},
        ],
    },
    "Eldritch Knight": {
        "common": [
            {"id": "eldritch_knight_arcane_strike", "name": "Arcane Strike", "type": "active", "desc": "Infused weapon attack, dealing magic damage to multiple enemies.", "cooldown": 3, "effect": {"atk_pct": 1.1, "int_pct": 0.1}},
        ],
        "uncommon": [
            {"id": "eldritch_knight_spell_ward", "name": "Spell Ward", "type": "passive", "desc": "Magical defenses are enhanced, reducing incoming spell damage.", "effect": {"int_pct": 0.15}},
        ],
        "rare": [
            {"id": "eldritch_knight_mana_shield", "name": "Mana Shield", "type": "active", "desc": "Generates a magical shield, absorbing incoming damage. Mana fueled.", "cooldown": 4, "effect": {"heal_pct": 0.2, "mana_cost": 15}},
        ],
        "epic": [
            {"id": "eldritch_knight_battlemages_focus", "name": "Battlemage's Focus", "type": "passive", "desc": "Harmonizes physical and magical prowess, boosting strength and intelligence.", "effect": {"str_pct": 0.1, "int_pct": 0.1}},
        ],
        "legendary": [
            {"id": "eldritch_knight_disrupting_blade", "name": "Disrupting Blade", "type": "active", "desc": "Strikes with arcane energy, damaging and silencing enemy spellcasters.", "cooldown": 5, "effect": {"atk_pct": 1.3}},
        ],
    },
    "Shinobi": {
        "common": [
            {"id": "shinobi_shadow_strike", "name": "Shadow Strike", "type": "active", "desc": "Emerges from shadows to strike, dealing huge damage and weakening foe.", "cooldown": 4, "effect": {"atk_pct": 1.8, "def_pct": -0.15}},
        ],
        "uncommon": [
            {"id": "shinobi_fleet_footed", "name": "Fleet Footed", "type": "passive", "desc": "Moves with incredible speed, enhancing evasion and overall agility.", "effect": {"agi_pct": 0.25}},
        ],
        "rare": [
            {"id": "shinobi_poisoned_shuriken", "name": "Poisoned Shuriken", "type": "active", "desc": "Hurls a poisoned shuriken, dealing damage and lingering poison over time.", "cooldown": 3, "effect": {"atk_pct": 0.7, "regen_pct": -0.04}},
        ],
        "epic": [
            {"id": "shinobi_vanish", "name": "Vanish", "type": "active", "desc": "Disappears from sight, becoming untargetable and empowering next strike.", "cooldown": 6, "effect": {"agi_pct": 0.3}},
        ],
        "legendary": [
            {"id": "shinobi_critical_opening", "name": "Critical Opening", "type": "passive", "desc": "Exploits weaknesses, increasing critical hit chance against debuffed foes.", "effect": {"lck_pct": 0.2}},
        ],
    },
    "Champion": {
        "common": [
            {"id": "champion_heroic_strike", "name": "Heroic Strike", "type": "active", "desc": "Unleashes a mighty blow, capable of crushing foes. For glory!", "cooldown": 3, "effect": {"atk_pct": 1.5, "crushing_blow": True}},
        ],
        "uncommon": [
            {"id": "champion_unyielding_spirit", "name": "Unyielding Spirit", "type": "passive", "desc": "Bolsters health and heals upon landing critical hits. Never gives up.", "effect": {"hlt_pct": 0.15, "self_heal_pct": 0.05}},
        ],
        "rare": [
            {"id": "champion_inspiring_presence", "name": "Inspiring Presence", "type": "active", "desc": "Inspires allies, granting them a temporary boost to attack power.", "cooldown": 5, "effect": {"str_pct": 0.15}},
        ],
        "epic": [
            {"id": "champion_last_stand", "name": "Last Stand", "type": "passive", "desc": "Fights harder when gravely wounded, boosting defense and damage.", "effect": {"def_pct": 0.2, "str_pct": 0.1}},
        ],
        "legendary": [
            {"id": "champion_glorious_charge", "name": "Glorious Charge", "type": "active", "desc": "Charges into battle, damaging an enemy and entering a powerful rage.", "cooldown": 4, "effect": {"atk_pct": 1.2, "enrage": True}},
        ],
    },
    "Guild Master": {
        "common": [
            {"id": "guild_master_tactical_command", "name": "Tactical Command", "type": "active", "desc": "Issues a command, boosting an ally's next action. Strategic advantage.", "cooldown": 3, "effect": {"str_pct": 0.2}},
        ],
        "uncommon": [
            {"id": "guild_master_resourceful", "name": "Resourceful", "type": "passive", "desc": "Optimizes resource acquisition, increasing gold rewards from combat.", "effect": {"lck_pct": 0.1}},
        ],
        "rare": [
            {"id": "guild_master_rallying_cry", "name": "Rallying Cry", "type": "active", "desc": "Inspires allies, providing a small burst of healing to all.", "cooldown": 5, "effect": {"heal_pct": 0.1}},
        ],
        "epic": [
            {"id": "guild_master_experienced_leader", "name": "Experienced Leader", "type": "passive", "desc": "Allies benefit from leadership, gaining a small stat boost. United!", "effect": {"str_pct": 0.05, "def_pct": 0.05}},
        ],
        "legendary": [
            {"id": "guild_master_emergency_funds", "name": "Emergency Funds", "type": "active", "desc": "Provides immediate mana to an ally. For unexpected expenses!", "cooldown": 4, "effect": {"int_pct": 0.15}},
        ],
    },
    "Hierophant": {
        "common": [
            {"id": "hierophant_divine_light", "name": "Divine Light", "type": "active", "desc": "Bathes ally in divine light, restoring a large amount of health.", "cooldown": 3, "effect": {"heal_pct": 0.4}},
        ],
        "uncommon": [
            {"id": "hierophant_holy_smite", "name": "Holy Smite", "type": "active", "desc": "Strikes enemy with holy energy. Especially potent against unholy foes.", "cooldown": 2, "effect": {"atk_pct": 1.2}},
        ],
        "rare": [
            {"id": "hierophant_aura_of_purity", "name": "Aura of Purity", "type": "passive", "desc": "Emits a purifying aura, occasionally cleansing allies of negative effects.", "effect": {"cleanse_self": True}},
        ],
        "epic": [
            {"id": "hierophant_sacred_vigor", "name": "Sacred Vigor", "type": "passive", "desc": "Enhances all healing received by allies. Blessings of restoration.", "effect": {"heal_pct": 0.15}},
        ],
        "legendary": [
            {"id": "hierophant_benediction", "name": "Benediction", "type": "active", "desc": "Blesses an ally, granting defense and immunity to debuffs temporarily.", "cooldown": 6, "effect": {"def_pct": 0.2}},
        ],
    },
    "Forge Lord": {
        "common": [
            {"id": "forge_lord_molten_core", "name": "Molten Core", "type": "passive", "desc": "Core burns, increasing defense and granting minor health regeneration.", "effect": {"def_pct": 0.15, "regen_pct": 0.03}},
        ],
        "uncommon": [
            {"id": "forge_lord_hammer_ancients", "name": "Hammer of the Ancients", "type": "active", "desc": "Unleashes a devastating blow, dealing massive damage with crushing force.", "cooldown": 4, "effect": {"atk_pct": 2.0, "crushing_blow": True}},
        ],
        "rare": [
            {"id": "forge_lord_forged_fire", "name": "Forged in Fire", "type": "passive", "desc": "Hardened by heat, permanently increasing strength and defense.", "effect": {"str_pct": 0.1, "def_pct": 0.05}},
        ],
        "epic": [
            {"id": "forge_lord_aegis_ash", "name": "Aegis of Ash", "type": "active", "desc": "Summons an ash shield, healing self and boosting defense temporarily.", "cooldown": 3, "effect": {"self_heal_pct": 0.15, "def_pct": 0.2}},
        ],
        "legendary": [
            {"id": "forge_lord_unbreakable_will", "name": "Unbreakable Will", "type": "active", "desc": "Enters a frenzy, gaining immense power and becoming enraged.", "cooldown": 5, "effect": {"enrage": True, "atk_pct": 0.5}},
        ],
    },

})
        for branch_names in tier60.values():
            for name in branch_names:
                mapping.setdefault(name, base)
    return mapping

def _resolve_lineage(hero_class: str) -> str:
    global _LINEAGE_MAP
    if _LINEAGE_MAP is None:
        _LINEAGE_MAP = _build_lineage_map()
    return _LINEAGE_MAP.get(hero_class, hero_class)

# Generic skills for any class with no kit above (and no lineage fallback
# either) — mostly the non-combat support classes (Blacksmith, Alchemist,
# Chef, Priest, Quartermaster and their evolutions) which is harmless,
# since they never enter combat in the first place.
GENERIC_SKILLS = {
    "common": [
        {"id": "tough", "name": "Tough", "type": "passive",
         "desc": "+8% Health", "effect": {"hlt_pct": 0.08}},
        {"id": "determined", "name": "Determined", "type": "passive",
         "desc": "+5% all stats", "effect": {"all_pct": 0.05}},
        {"id": "calm_mind", "name": "Calm Mind", "type": "passive",
         "desc": "-10% stress gain", "effect": {"stress_reduce": 0.10}},
        {"id": "steady_hands", "name": "Steady Hands", "type": "passive",
         "desc": "+5% crit chance", "effect": {"crit_add": 0.05}},
        {"id": "light_footed", "name": "Light Footed", "type": "passive",
         "desc": "+5% dodge chance", "effect": {"dodge_add": 0.05}},
        # A common-tier active so even a 1-star's first roll has a real
        # shot at an active skill, not just the uncommon+ ones below.
        {"id": "quick_strike", "name": "Quick Strike", "type": "active",
         "desc": "130% ATK to a single target", "cooldown": 2, "mana_cost": 15,
         "effect": {"dmg_pct": 1.3, "single_target": True}},
    ],
    "uncommon": [
        {"id": "survivor", "name": "Survivor", "type": "passive",
         "desc": "+15% Health, -5% ATK", "effect": {"hlt_pct": 0.15, "str_pct": -0.05}},
        {"id": "field_medic", "name": "Field Medic", "type": "passive",
         "desc": "Restore 3% Health to self each round", "effect": {"regen_pct": 0.03}},
        {"id": "power_strike", "name": "Power Strike", "type": "active",
         "desc": "150% ATK to a single target", "cooldown": 3, "mana_cost": 25,
         "effect": {"dmg_pct": 1.5, "single_target": True}},
    ],
    "rare": [
        {"id": "iron_will", "name": "Iron Will", "type": "passive",
         "desc": "Immune to fear stun", "effect": {"fear_immune": True}},
        {"id": "hardy", "name": "Hardy", "type": "passive",
         "desc": "+10% damage reduction", "effect": {"dmg_reduction_pct": 0.10}},
        {"id": "focused_assault", "name": "Focused Assault", "type": "active",
         "desc": "180% ATK to a single target, guaranteed crit", "cooldown": 4, "mana_cost": 35,
         "effect": {"dmg_pct": 1.8, "single_target": True, "guaranteed_crit": True}},
    ],
    "epic": [
        {"id": "martyrdom", "name": "Martyrdom", "type": "passive",
         "desc": "On death, fully heal all allies", "effect": {"death_heal": True}},
    ],
    "legendary": [
        {"id": "chosen_one", "name": "Chosen One", "type": "passive",
         "desc": "+25% all stats, immune to fear", "effect": {"all_pct": 0.25, "fear_immune": True}},
    ],
}

# Seals and Runes used to be rolled here at birth — they're now Relics
# (services/relics_service.py): loot dropped from bosses/events, then
# equipped onto any hero whose CURRENT star meets the relic's min_star.
# Genius/Prodigy talent is retired entirely — the aptitude/talent growth
# system (level_service.talent_score) now covers that "secretly OP low
# rarity" narrative beat more thoroughly.

# Boss-drop exclusive skills — never rolled naturally
BOSS_DROP_SKILLS = [
    {"id": "boss_slayer", "name": "Boss Slayer", "rarity": "epic", "type": "passive",
     "desc": "+50% damage to bosses", "effect": {"boss_dmg_pct": 0.50}},
    {"id": "tower_sense", "name": "Tower Sense", "rarity": "legendary", "type": "passive",
     "desc": "Team takes 15% less damage on all floors", "effect": {"team_dmg_reduce": 0.15}},
    {"id": "deaths_embrace", "name": "Death's Embrace", "rarity": "legendary", "type": "passive",
     "desc": "When an ally dies, gain their ATK for the rest of combat",
     "effect": {"inherit_atk": True}},
    {"id": "floor_master", "name": "Floor Master", "rarity": "legendary", "type": "passive",
     "desc": "+2% all stats per 10 floors survived (permanent)",
     "effect": {"floor_scaling": 0.02}},
]


def roll_skill_rarity() -> str:
    """Roll a skill rarity using weighted RNG."""
    rarities = list(SKILL_RARITY_WEIGHTS.keys())
    weights = list(SKILL_RARITY_WEIGHTS.values())
    return random.choices(rarities, weights=weights, k=1)[0]


def _eligible(skill: dict, hero_star: int) -> bool:
    """Some skills (e.g. revive) are deliberately gated to only the
    strongest heroes — too powerful a tool to hand a non-godlike figure.
    min_star lives on the effect dict; absent means no restriction."""
    return skill.get("effect", {}).get("min_star", 1) <= hero_star


def get_skill_for_class(hero_class: str, rarity: str = None, hero_star: int = 7) -> dict | None:
    """Get a random skill for a class at a given rarity. Resolution order:
    exact match in SKILL_POOL -> lineage base's SKILL_POOL entry -> GENERIC_SKILLS.
    hero_star filters out anything above the hero's reach (e.g. revive_pct
    skills require min_star 6) — defaults to 7 (unrestricted) for any
    caller that doesn't have a star on hand."""
    if rarity is None:
        rarity = roll_skill_rarity()

    pool = SKILL_POOL.get(hero_class)
    if pool is None:
        pool = SKILL_POOL.get(_resolve_lineage(hero_class))
    if pool is None:
        pool = GENERIC_SKILLS

    skills = [s for s in pool.get(rarity, []) if _eligible(s, hero_star)] if isinstance(pool, dict) else []

    # If no class-specific skill at this rarity, try generic
    if not skills:
        skills = [s for s in GENERIC_SKILLS.get(rarity, []) if _eligible(s, hero_star)]

    if not skills:
        return None

    skill = random.choice(skills).copy()
    skill["rarity"] = rarity
    skill["tier"] = "Beginner"
    skill["level"] = 1
    skill["xp"] = 0
    skill["max_xp"] = 100
    return skill


def _get_any_active_skill_for_class(hero_class: str, hero_star: int = 7) -> dict | None:
    """Scans every rarity tier (common -> legendary) for the first 'active'
    skill in this class's pool — used to guarantee 3★+ heroes get at least
    one active skill at birth. Several class pools only have an active
    skill starting at 'uncommon', and common-rarity rolls dominate at low
    star — without this, a caster could end up with passive-only skills,
    which combined with basic attacks now always scaling off Strength (see
    calc_damage's force_strength) would leave their Intelligence with
    nothing to actually do."""
    pool = SKILL_POOL.get(hero_class) or SKILL_POOL.get(_resolve_lineage(hero_class)) or GENERIC_SKILLS
    if not isinstance(pool, dict):
        return None
    for rarity in ["common", "uncommon", "rare", "epic", "legendary"]:
        for s in pool.get(rarity, []):
            if s.get("type") == "active" and _eligible(s, hero_star):
                skill = s.copy()
                skill["rarity"] = rarity
                skill["tier"] = "Beginner"
                skill["level"] = 1
                skill["xp"] = 0
                skill["max_xp"] = 100
                return skill
    return None


def assign_initial_skills(hero_class: str, birth_star: int) -> list[dict]:
    """Assign starting skills to a new hero. Higher star = better chance of rare skills."""
    skills = []

    # Everyone gets 1 skill at birth
    # Higher star heroes get a rarity bonus
    rarity_bonus = {1: 0, 2: 0, 3: 5, 4: 10, 5: 20, 6: 30, 7: 50}
    bonus = rarity_bonus.get(birth_star, 0)

    # Roll with bonus applied
    skill = get_skill_for_class(hero_class, hero_star=birth_star)
    if skill and bonus > 0:
        # Chance to upgrade rarity
        if random.randint(0, 100) < bonus:
            rarity_order = ["common", "uncommon", "rare", "epic", "legendary"]
            idx = rarity_order.index(skill["rarity"])
            if idx < len(rarity_order) - 1:
                upgraded = get_skill_for_class(hero_class, rarity_order[idx + 1], hero_star=birth_star)
                if upgraded:
                    skill = upgraded

    if skill:
        skills.append(skill)

    # 4★+ heroes get a second skill
    if birth_star >= 4:
        skill2 = get_skill_for_class(hero_class, hero_star=birth_star)
        if skill2 and skill2["id"] != skills[0]["id"]:
            skills.append(skill2)

    # 6★+ heroes get a third skill
    if birth_star >= 6 and len(skills) >= 2:
        skill3 = get_skill_for_class(hero_class, hero_star=birth_star)
        if skill3 and skill3["id"] not in [s["id"] for s in skills]:
            skills.append(skill3)

    # 3★+ are guaranteed at least one active skill — see
    # _get_any_active_skill_for_class for why this matters now that basic
    # attacks always scale off Strength regardless of class.
    if birth_star >= 3 and not any(s.get("type") == "active" for s in skills):
        guaranteed_active = _get_any_active_skill_for_class(hero_class, hero_star=birth_star)
        if guaranteed_active and guaranteed_active["id"] not in [s["id"] for s in skills]:
            skills.append(guaranteed_active)

    for s in skills:
        if "tier" not in s:
            s["tier"] = "Beginner"
            s["level"] = 1
            s["xp"] = 0
            s["max_xp"] = 100

    return skills


# ─── Weapon Art ──────────────────────────────────────────────────────
#
# A bonus active skill tied to the WEAPON TYPE itself, not the class or
# rarity roll — granted on top of a hero's normal skill list, for free,
# for as long as they have a matching-type weapon equipped (see
# class_service.get_weapon_affinity for the hard equip restriction and
# combat_service.resolve_hero_stats for where this gets granted). Every
# class sharing a weapon type shares its Art — a Knight and a Berserker
# both holding a Sword get the same Cross Slash; they're already
# distinct via their own class kit.
WEAPON_ART_SKILLS = {
    "Sword": {"id": "art_sword", "name": "Cross Slash", "type": "active",
              "desc": "190% ATK to a single target", "cooldown": 3,
              "effect": {"dmg_pct": 1.9, "single_target": True, "mana_cost": 25}},
    "Spear": {"id": "art_spear", "name": "Piercing Lunge", "type": "active",
              "desc": "170% ATK, ignore 20% DEF", "cooldown": 3,
              "effect": {"dmg_pct": 1.7, "single_target": True, "ignore_def": True, "mana_cost": 25}},
    "Tome": {"id": "art_staff", "name": "Arcane Discharge", "type": "active",
              "desc": "190% ATK to a single target", "cooldown": 3,
              "effect": {"dmg_pct": 1.9, "single_target": True, "mana_cost": 25}},
    "Bow": {"id": "art_bow", "name": "Eagle Eye Shot", "type": "active",
            "desc": "200% ATK, guaranteed crit", "cooldown": 4,
            "effect": {"dmg_pct": 2.0, "single_target": True, "guaranteed_crit": True, "mana_cost": 30}},
    "Dagger": {"id": "art_dagger", "name": "Twin Fang", "type": "active",
               "desc": "Hit 2 enemies for 90% ATK each, heal 15% of damage dealt", "cooldown": 3,
               "effect": {"multi_target": 2, "dmg_pct": 0.9, "lifesteal_pct": 0.15, "mana_cost": 25}},
}

def get_weapon_art_skill(weapon_type: str) -> dict | None:
    art = WEAPON_ART_SKILLS.get(weapon_type)
    if not art:
        return None
    skill = art.copy()
    skill["rarity"] = "art"
    skill["tier"] = "Beginner"
    skill["level"] = 1
    skill["xp"] = 0
    skill["max_xp"] = 100
    return skill


def get_boss_drop_skill() -> dict | None:
    """Roll for a boss-drop exclusive skill. 15% chance on boss kill."""
    if random.random() < 0.15:
        skill = random.choice(BOSS_DROP_SKILLS).copy()
        return skill
    return None


def apply_passive_skills(hero: dict, skills: list[dict]) -> dict:
    """Apply passive skill effects to hero stats before combat."""
    h = hero.copy()
    for skill in skills:
        if skill.get("type") != "passive":
            continue
        eff = skill.get("effect", {})

        if "str_pct" in eff:
            h["strength"] = int(h["strength"] * (1 + eff["str_pct"]))
        if "int_pct" in eff:
            h["intelligence"] = int(h["intelligence"] * (1 + eff["int_pct"]))
        if "agi_pct" in eff:
            h["agility"] = int(h["agility"] * (1 + eff["agi_pct"]))
        if "hlt_pct" in eff:
            h["max_health"] = int(h["max_health"] * (1 + eff["hlt_pct"]))
            h["health"] = int(h["health"] * (1 + eff["hlt_pct"]))
        if "all_pct" in eff:
            mult = 1 + eff["all_pct"]
            h["strength"] = int(h["strength"] * mult)
            h["intelligence"] = int(h["intelligence"] * mult)
            h["agility"] = int(h["agility"] * mult)
            h["max_health"] = int(h["max_health"] * mult)
            h["health"] = int(h["health"] * mult)
        if "crit_pct" in eff:
            h["crit_chance"] = h.get("crit_chance", 0.05) + eff["crit_pct"]
        if "dodge_pct" in eff:
            h["dodge_chance"] = h.get("dodge_chance", 0.0) + eff["dodge_pct"]
        if "armor_pen" in eff:
            h["armor_pen"] = h.get("armor_pen", 0) + eff["armor_pen"]
        if "fear_immune" in eff:
            h["fear_immune"] = True
        if "death_save" in eff:
            h["death_save"] = eff["death_save"]
        if "regen_pct" in eff:
            h["regen_pct"] = h.get("regen_pct", 0.0) + eff["regen_pct"]
        if "dmg_reduction_pct" in eff:
            h["dmg_reduction_pct"] = h.get("dmg_reduction_pct", 0.0) + eff["dmg_reduction_pct"]
        if "physical_resist_pct" in eff:
            h["physical_resist_pct"] = h.get("physical_resist_pct", 0.0) + eff["physical_resist_pct"]
        if "magic_resist_pct" in eff:
            h["magic_resist_pct"] = h.get("magic_resist_pct", 0.0) + eff["magic_resist_pct"]

    return h

# ─── Active skill mana costs ───────────────────────────────────────
#
# mana_cost is an optional key on an active skill's effect dict — falls
# back to a flat default for any skill that doesn't specify one.
DEFAULT_SKILL_MANA_COST = 25

def get_skill_mana_cost(skill: dict) -> int:
    return skill.get("effect", {}).get("mana_cost", DEFAULT_SKILL_MANA_COST)

# Effect-key combos this version's combat dispatcher (combat_service.py
# _execute_active_skill) does NOT know how to resolve yet — Time Warp's
# extra-turn and Meteor's self-stun need a second action-queue concept, and
# Suppressing Fire's speed debuff needs a temp-stat-with-restore mechanism,
# none of which exist yet. Excluded from the castable pool rather than
# silently no-oping a turn away when picked.
UNHANDLED_ACTIVE_EFFECT_KEYS = {"team_double_turn", "self_stun", "enemy_spd_debuff"}

def is_skill_executable(skill: dict) -> bool:
    if skill.get("type") != "active":
        return False
    return not UNHANDLED_ACTIVE_EFFECT_KEYS.intersection(skill.get("effect", {}).keys())
