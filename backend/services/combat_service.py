"""
Combat Service — Deterministic simulation with class effects, level scaling,
skills, fear mechanics, legacy bonuses, and bond effects.
"""
import random
import json
from dataclasses import dataclass, field
from services.class_service import apply_class_combat_modifiers
from services.level_service import apply_level_to_stats

@dataclass
class CombatUnit:
    id: int
    name: str
    hp: int
    max_hp: int
    attack: int
    defense: int
    speed: int
    morale: int
    stress: int
    trauma: int = 0
    hero_class: str = "Classless"
    is_hero: bool = True
    alive: bool = True
    is_ranged: bool = False
    is_aoe: bool = False
    has_construct: bool = False
    construct_active: bool = False
    crit_chance: float = 0.05
    dodge_chance: float = 0.0
    kills: int = 0
    fear_immune: bool = False
    fear_stunned: bool = False
    death_save: int = 0
    armor_pen: float = 0.0
    skills: list = field(default_factory=list)
    portrait_path: str = ""

    def __post_init__(self):
        self.log_name = self.name if self.is_hero else f"[{self.name}]"
        if self.has_construct:
            self.construct_active = True

def make_enemies(floor_number: int, count: int = None, team_power: float = 0) -> list[CombatUnit]:
    """
    Generate enemies for a floor. Adaptive difficulty:
    team_power is the average star rank of the team (0 = no scaling).
    """
    scale = 1 + (floor_number * 0.12)

    # Adaptive scaling — stronger teams face harder enemies
    if team_power > 3:
        adaptive_bonus = 1 + ((team_power - 3) * 0.15)  # +15% per star above 3
        scale *= adaptive_bonus

    # name, hp_m, def_m, spd_m, archetype
    enemy_types = [
        ("Corpse Rat", 1.0, 1.0, 1.5, "swarm"),
        ("Grave Scarab", 1.0, 1.0, 1.6, "swarm"),
        ("Plague Crawler", 1.0, 1.0, 1.3, "pack"),
        ("Abyssal Spider", 1.0, 1.0, 1.4, "pack"),
        ("Hollow Knight", 1.2, 1.1, 0.9, "normal"),
        ("Bone Warden", 1.0, 1.3, 0.8, "normal"),
        ("Flame Wraith", 0.9, 0.6, 1.4, "normal"),
        ("Shriek Shade", 0.7, 0.5, 1.6, "normal"),
        ("Stone Golem", 1.5, 1.8, 0.5, "elite"),
        ("Dread Brute", 1.8, 1.2, 0.7, "elite"),
        ("Abyssal Lurker", 1.3, 0.9, 1.8, "elite"),
    ]

    etype = random.choice(enemy_types)
    name, hp_m, def_m, spd_m, archetype = etype

    if count is None:
        if archetype == "swarm":
            count = random.randint(4, 5)
        elif archetype == "pack":
            count = random.randint(3, 4)
        elif archetype == "elite":
            count = 1
        else: # normal
            count = random.randint(1, min(3, 1 + floor_number // 10))

    # Apply archetype modifiers
    atk_m = 1.0
    if archetype == "swarm":
        atk_m = 0.5
        hp_m *= 0.5
        def_m *= 0.3
    elif archetype == "pack":
        atk_m = 0.4
        hp_m *= 0.4
        def_m *= 0.4
    elif archetype == "elite":
        atk_m = 1.5
        hp_m *= 1.5
        def_m *= 1.5

    enemies = []
    for i in range(count):
        enemies.append(CombatUnit(
            id=-(i+1), 
            name=f"{name} {i+1}" if count > 1 else name,
            hp=max(1, int(80 * scale * hp_m)), max_hp=max(1, int(80 * scale * hp_m)),
            attack=max(1, int(8 * scale * atk_m)), defense=int(5 * scale * def_m),
            speed=int(10 * scale * spd_m),
            morale=100, stress=0, is_hero=False,
            portrait_path=f"static/enemies/{name.lower().replace(' ', '_')}.png"
        ))
    return enemies


def make_boss(floor_number: int, zone_theme: str = "", is_miniboss: bool = False) -> list[CombatUnit]:
    """Create a boss or miniboss enemy."""
    scale = 1 + (floor_number * 0.12)
    
    if zone_theme:
        from services.llm_service import generate_boss_enemy
        boss_data = generate_boss_enemy(zone_theme, floor_number, is_miniboss)
        name = boss_data.get("name", "Unknown Boss")
        mod = {
            "name": boss_data.get("modifier", "Enraged"),
            "hp": boss_data.get("hp_multiplier", 1.2),
            "atk": boss_data.get("atk_multiplier", 1.2),
            "def": boss_data.get("def_multiplier", 1.0),
            "spd": boss_data.get("spd_multiplier", 1.0)
        }
    else:
        boss_names = [
            "The Hollow King", "Dread Sentinel", "Abyssal Warden",
            "The Shattered One", "Lord of Ash", "The Undying",
            "Nightmare Colossus", "The Tower's Hunger",
        ]
        name = boss_names[min(len(boss_names) - 1, floor_number // 10 - 1)]
        boss_modifiers = [
            {"name": "Enraged", "atk": 1.5, "def": 0.7, "spd": 1.0, "hp": 1.0},
            {"name": "Armored", "atk": 1.0, "def": 2.0, "spd": 0.8, "hp": 1.0},
            {"name": "Colossal", "atk": 1.0, "def": 1.0, "spd": 0.7, "hp": 1.8},
            {"name": "Frenzied", "atk": 1.2, "def": 1.0, "spd": 1.5, "hp": 1.0},
            {"name": "Vampiric", "atk": 1.1, "def": 1.1, "spd": 1.1, "hp": 1.1},
            {"name": "Cursed", "atk": 1.3, "def": 0.8, "spd": 1.2, "hp": 0.9},
        ]
        mod = random.choice(boss_modifiers)

    if is_miniboss and not zone_theme:
        name = f"Lieutenant of {name}"
    
    if is_miniboss:
        power = 2.5 + (floor_number / 40)
    else:
        power = 4.5 + (floor_number / 30)

    boss_title = f"{mod['name']} {name}"

    boss = CombatUnit(
        id=-99, name=boss_title,
        hp=int(300 * scale * power * mod['hp']), max_hp=int(300 * scale * power * mod['hp']),
        attack=int(20 * scale * (power * 0.5) * mod['atk']), defense=int(15 * scale * (power * 0.4) * mod['def']),
        speed=int(8 * scale * mod['spd']),
        morale=100, stress=0, is_hero=False,
        portrait_path=f"static/enemies/{name.lower().replace(' ', '_')}.png"
    )
    return [boss]


def _fear_check(unit: CombatUnit, log: list) -> bool:
    """
    Check if a hero is paralyzed by fear this round.
    Based on trauma + stress levels.
    Returns True if the hero is fear-stunned.
    """
    if unit.fear_immune or not unit.is_hero:
        return False

    trauma = unit.trauma
    stress = unit.stress

    # Fear chance: 0% below 40 trauma, scales up
    if trauma < 40:
        return False
    elif trauma < 60:
        chance = 0.08 + (stress * 0.001)
    elif trauma < 80:
        chance = 0.15 + (stress * 0.002)
    else:
        chance = 0.25 + (stress * 0.003)

    if random.random() < chance:
        unit.fear_stunned = True
        fear_lines = [
            f"  ✗ {unit.name} freezes — the trauma overwhelms them.",
            f"  ✗ {unit.name}'s hands tremble. They cannot move.",
            f"  ✗ {unit.name} screams and covers their eyes. Fear takes hold.",
            f"  ✗ {unit.name} is paralyzed by terror. The memories are too much.",
        ]
        log.append(random.choice(fear_lines))
        return True

    return False


def calc_damage(attacker: CombatUnit, defender: CombatUnit) -> tuple[int, bool]:
    effective_def = defender.defense * (1 - attacker.armor_pen)
    base = attacker.attack * (100 / (100 + max(0, effective_def)))

    if attacker.is_hero and attacker.morale < 40:
        morale_factor = 0.5 + (attacker.morale / 80)
        base *= morale_factor

    variance = random.uniform(0.85, 1.15)
    damage = max(1, int(base * variance))

    is_crit = random.random() < attacker.crit_chance
    if is_crit:
        damage = int(damage * 1.8)

    return damage, is_crit

def run_combat(heroes: list[dict], floor_number: int, is_boss: bool = False, is_miniboss: bool = False, zone_theme: str = "") -> dict:
    log = []
    turns = []
    morale_changes = {h["id"]: 0 for h in heroes}
    kill_counts = {h["id"]: 0 for h in heroes}
    stress_changes = {h["id"]: 0 for h in heroes}

    # Apply level scaling → class modifiers → synergy → equipment → legacy bonuses → skill passives
    processed = []
    
    # Calculate synergies on active team
    synergy_counts = {}
    for h in heroes:
        sg = h.get("synergy_group")
        if sg:
            synergy_counts[sg] = synergy_counts.get(sg, 0) + 1
    # Fetch relics
    try:
        from services.relic_service import get_all_relics, apply_relic_stats
        relics = get_all_relics()
    except Exception:
        relics = []

    # Fetch bonds
    try:
        from services.bonds_service import get_team_bonds_multiplier
        hero_ids = [h["id"] for h in heroes]
        bond_totals = get_team_bonds_multiplier(hero_ids)
    except Exception:
        bond_totals = {h["id"]: 0 for h in heroes}

    # Pre-pass for support class buffs (Tactician, Scout, etc)
    team_atk_mult = 1.0
    team_def_mult = 1.0
    team_spd_mult = 1.0
    for h in heroes:
        mods = apply_class_combat_modifiers(h)
        if "team_atk_mult" in mods: team_atk_mult *= mods["team_atk_mult"]
        if "team_def_mult" in mods: team_def_mult *= mods["team_def_mult"]
        if "team_spd_mult" in mods: team_spd_mult *= mods["team_spd_mult"]

    for h in heroes:
        scaled = apply_level_to_stats(h)
        modified = apply_class_combat_modifiers(scaled)
        
        # Apply team class buffs
        if team_atk_mult > 1.0: modified["attack"] = int(modified["attack"] * team_atk_mult)
        if team_def_mult > 1.0: modified["defense"] = int(modified["defense"] * team_def_mult)
        if team_spd_mult > 1.0: modified["speed"] = int(modified["speed"] * team_spd_mult)
        
        # Apply synergy buff
        sg = modified.get("synergy_group")
        if sg and synergy_counts.get(sg, 0) > 1:
            multiplier = 1.0 + (0.05 * synergy_counts[sg])
            modified["max_hp"] = int(modified["max_hp"] * multiplier)
            modified["hp"] = modified["max_hp"]
            modified["attack"] = int(modified["attack"] * multiplier)
            modified["defense"] = int(modified["defense"] * multiplier)
            modified["speed"] = int(modified["speed"] * multiplier)

        # Apply equipment bonuses
        try:
            from services.equipment_service import apply_equipment_stats
            modified = apply_equipment_stats(modified)
        except Exception:
            pass

        # Apply legacy bonuses
        try:
            from services.legacy_service import apply_legacy_bonuses
            modified = apply_legacy_bonuses(modified)
        except Exception:
            pass
            
        # Apply relic stats
        if relics:
            modified = apply_relic_stats(modified, relics)
            
        # Apply Base Floor LP stats
        try:
            from services.base_service import get_floor_lp
            from database import db
            with db() as conn:
                lp_data = get_floor_lp(conn, modified.get("base_floor", 1))
                lp_mult = 1.0 + (lp_data["stat_bonus_pct"] / 100.0)
                modified["max_hp"] = int(modified["max_hp"] * lp_mult)
                modified["hp"] = min(modified["max_hp"], modified["hp"])
                modified["attack"] = int(modified["attack"] * lp_mult)
                modified["defense"] = int(modified["defense"] * lp_mult)
                modified["speed"] = int(modified["speed"] * lp_mult)
        except Exception:
            pass

        # Apply bond stats
        bond_lvl = bond_totals.get(modified["id"], 0)
        if bond_lvl > 0:
            bond_mult = 1.0 + (0.01 * bond_lvl)
            modified["max_hp"] = int(modified["max_hp"] * bond_mult)
            modified["hp"] = min(modified["max_hp"], modified["hp"])
            modified["attack"] = int(modified["attack"] * bond_mult)
            modified["defense"] = int(modified["defense"] * bond_mult)
            modified["speed"] = int(modified["speed"] * bond_mult)

        # Apply passive skills and traits
        if "skills" in h and h["skills"]:
            from services.skills_service import apply_passive_skills
            hero_skills = json.loads(h.get("skills", "[]")) if isinstance(h.get("skills"), str) else h.get("skills", [])
            modified = apply_passive_skills(modified, hero_skills)
            
        if "traits" in h and h["traits"]:
            from services.skills_service import apply_passive_skills
            hero_traits = json.loads(h.get("traits", "[]")) if isinstance(h.get("traits"), str) else h.get("traits", [])
            # Traits use the exact same effect dict structure as passive skills!
            modified = apply_passive_skills(modified, hero_traits)

        # Remove raw string payload to avoid confusion later, but keep as python list for UI/Combat logic if needed
        if "skills" in modified:
            modified["_skills"] = hero_skills if 'hero_skills' in locals() else []
            del modified["skills"]
        if "traits" in modified:
            modified["_traits"] = hero_traits if 'hero_traits' in locals() else []
            del modified["traits"]
        processed.append(modified)

    combatants_heroes = []
    construct_id = -100
    for h in processed:
        hero_unit = CombatUnit(
            id=h["id"], name=h["name"],
            hp=h["hp"], max_hp=h["max_hp"],
            attack=h["attack"], defense=h["defense"],
            speed=h["speed"], morale=h["morale"], stress=h["stress"],
            trauma=h.get("trauma", 0),
            hero_class=h.get("hero_class", "Classless"),
            is_ranged=h.get("is_ranged", False),
            is_aoe=h.get("is_aoe", False),
            has_construct=h.get("has_construct", False),
            crit_chance=h.get("crit_chance", 0.05),
            dodge_chance=h.get("dodge_chance", 0.0),
            fear_immune=h.get("fear_immune", False),
            death_save=h.get("death_save", 0),
            armor_pen=h.get("armor_pen", 0.0),
            skills=h.get("_skills", []),
            portrait_path=h.get("portrait_path", "")
        )
        combatants_heroes.append(hero_unit)
        
        # Summon construct if the hero has the has_construct flag
        if h.get("has_construct"):
            c_hp = int(h["max_hp"] * 1.5)
            c_atk = int(h["attack"] * 0.8)
            c_def = int(h["defense"] * 1.5)
            c_spd = int(h["speed"] * 0.7)
            construct_unit = CombatUnit(
                id=construct_id, name=f"{h['name']}'s Construct",
                hp=c_hp, max_hp=c_hp, attack=c_atk, defense=c_def, speed=c_spd,
                morale=100, stress=0, hero_class="Construct", fear_immune=True
            )
            combatants_heroes.append(construct_unit)
            construct_id -= 1
            log.append(f"  {hero_unit.name} deploys a massive Construct to the frontline!")

    # Generate enemies (adaptive difficulty)
    avg_star = sum(h.get("birth_star", 1) for h in heroes) / max(1, len(heroes))
    if is_boss or is_miniboss:
        enemies = make_boss(floor_number, zone_theme, is_miniboss)
        log.append(f"🔥💀🔥 {'MINIBOSS' if is_miniboss else 'BOSS'} FLOOR {floor_number} 🔥💀🔥")
        log.append(f"  {enemies[0].name} emerges from the darkness.")
    else:
        enemies = make_enemies(floor_number, team_power=avg_star)

    initial_state = {
        "heroes": [
            {"id": h.id, "name": h.name, "hero_class": h.hero_class, "max_hp": h.max_hp, "hp": h.hp, "portrait_path": h.portrait_path}
            for h in combatants_heroes
        ],
        "enemies": [
            {"id": e.id, "name": e.name, "max_hp": e.max_hp, "hp": e.hp, "portrait_path": e.portrait_path}
            for e in enemies
        ]
    }

    log.append(f"Floor {floor_number}: {len(combatants_heroes)} heroes vs {len(enemies)} enemies.")

    # Log class composition
    class_summary = ", ".join([f"{h.name}({h.hero_class})" for h in combatants_heroes])
    log.append(f"  Party: {class_summary}")

    # Explicit 2-Front, 3-Back Formation
    frontline = combatants_heroes[:2]
    backline  = combatants_heroes[2:]

    all_units = combatants_heroes + enemies
    max_rounds = 30
    
    damage_dealt_stats = {h.id: 0 for h in combatants_heroes}

    for round_num in range(1, max_rounds + 1):
        all_units.sort(key=lambda u: u.speed + random.uniform(0, 2), reverse=True)

        alive_heroes  = [u for u in combatants_heroes if u.alive]
        alive_enemies = [u for u in enemies if u.alive]
        if not alive_heroes or not alive_enemies:
            break

        # ─── Fear checks at start of each round ───
        for hero in alive_heroes:
            hero.fear_stunned = False  # Reset from last round
            _fear_check(hero, log)

        alive_frontline = [h for h in frontline if h.alive]

        for attacker in all_units:
            if not attacker.alive:
                continue

            # Fear-stunned heroes skip their turn
            if attacker.is_hero and attacker.fear_stunned:
                stress_changes[attacker.id] = stress_changes.get(attacker.id, 0) + 5
                continue

            if attacker.is_hero:
                targets = [u for u in alive_enemies if u.alive]
                if not targets:
                    break

                if attacker.is_aoe:
                    # Mage hits all enemies
                    log.append(f"  ✦ {attacker.name} ({attacker.hero_class}) casts — hits all enemies!")
                    for target in targets:
                        damage, is_crit = calc_damage(attacker, target)
                        damage_dealt_stats[attacker.id] += damage
                        target.hp -= damage
                        crit_text = " CRIT!" if is_crit else ""
                        log_msg = f"    → {target.log_name} takes {damage}{crit_text} [{max(0,target.hp)}/{target.max_hp}]"
                        log.append(log_msg)
                        turns.append({"round": round_num, "attacker_id": attacker.id, "target_id": target.id, "damage": damage, "is_crit": is_crit, "target_hp": max(0, target.hp), "log": log_msg})
                        if target.hp <= 0:
                            target.alive = False
                            attacker.kills += 1
                            kill_counts[attacker.id] = kill_counts.get(attacker.id, 0) + 1
                            log.append(f"    ✦ {target.log_name} falls.")
                            for h in combatants_heroes:
                                if h.alive:
                                    morale_changes[h.id] = morale_changes.get(h.id, 0) + random.randint(2, 5)
                else:
                    alive_frontline_enemies = [e for e in enemies[:2] if e.alive]
                    alive_backline_enemies = [e for e in enemies[2:] if e.alive]
                    
                    if attacker.hero_class == "Assassin" and alive_backline_enemies:
                        target = random.choice(alive_backline_enemies)
                    else:
                        # Front-to-Back targeting for heroes
                        if alive_frontline_enemies:
                            # Match index or random frontliner
                            idx = combatants_heroes.index(attacker) % len(alive_frontline_enemies)
                            target = alive_frontline_enemies[idx]
                        elif alive_backline_enemies:
                            target = random.choice(alive_backline_enemies)
                        else:
                            continue

                    # Dodge check
                    if random.random() < target.dodge_chance and not attacker.is_hero:
                        log.append(f"  {target.name} dodges!")
                        continue

                    damage, is_crit = calc_damage(attacker, target)
                    damage_dealt_stats[attacker.id] += damage

                    # Construct absorbs first hit for Magic Engineer
                    if target.is_hero and target.has_construct and target.construct_active:
                        target.construct_active = False
                        log.append(f"  {target.name}'s construct absorbs the hit!")
                        continue

                    target.hp -= damage
                    crit_text = " CRIT!" if is_crit else ""
                    log_msg = f"  {attacker.log_name} hits {target.log_name} for {damage}{crit_text} [{max(0,target.hp)}/{target.max_hp}]"
                    log.append(log_msg)
                    turns.append({"round": round_num, "attacker_id": attacker.id, "target_id": target.id, "damage": damage, "is_crit": is_crit, "target_hp": max(0, target.hp), "log": log_msg})

                    if target.hp <= 0:
                        target.alive = False
                        attacker.kills += 1
                        kill_counts[attacker.id] = kill_counts.get(attacker.id, 0) + 1
                        log.append(f"  ✦ {target.log_name} falls.")
                        morale_changes[attacker.id] = morale_changes.get(attacker.id, 0) + random.randint(2, 5)

            else:
                alive_frontline = [h for h in frontline if h.alive]
                alive_backline = [h for h in backline if h.alive]
                
                if alive_frontline:
                    idx = enemies.index(attacker) % len(alive_frontline)
                    target = alive_frontline[idx]
                elif alive_backline:
                    target = random.choice(alive_backline)
                else:
                    continue

                # Dodge check for thief
                if random.random() < target.dodge_chance:
                    log.append(f"  {target.name} dodges {attacker.log_name}'s attack!")
                    continue

                # Construct check
                if target.has_construct and target.construct_active:
                    target.construct_active = False
                    log.append(f"  {target.name}'s construct absorbs the hit!")
                    continue

                damage, is_crit = calc_damage(attacker, target)
                target.hp -= damage
                crit_text = " CRIT!" if is_crit else ""
                log_msg = f"  {attacker.log_name} hits {target.log_name} for {damage}{crit_text} [{max(0,target.hp)}/{target.max_hp}]"
                log.append(log_msg)
                turns.append({"round": round_num, "attacker_id": attacker.id, "target_id": target.id, "damage": damage, "is_crit": is_crit, "target_hp": max(0, target.hp), "log": log_msg})

                if target.hp <= 0:
                    # Death save check
                    if target.death_save > 0:
                        target.death_save -= 1
                        target.hp = 1
                        log.append(f"  ✦ {target.log_name} refuses to fall! (Undying Will)")
                        continue

                    target.alive = False
                    log.append(f"  ✦ {target.log_name} has fallen.")
                    # Witness death — morale crash + trauma spike + fear stress
                    for h in combatants_heroes:
                        if h.alive:
                            morale_changes[h.id] = morale_changes.get(h.id, 0) - random.randint(8, 18)
                            stress_changes[h.id] = stress_changes.get(h.id, 0) + random.randint(5, 12)
                            log.append(f"    {h.name}'s morale wavers...")

        alive_heroes  = [u for u in combatants_heroes if u.alive]
        alive_enemies = [u for u in enemies if u.alive]
        if not alive_heroes or not alive_enemies:
            break

    alive_heroes  = [u for u in combatants_heroes if u.alive]
    dead_heroes   = [u for u in combatants_heroes if not u.alive]
    heroes_won    = len(alive_heroes) > 0 and len([u for u in enemies if u.alive]) == 0

    if heroes_won:
        log.append(f"✓ Victory. {len(alive_heroes)} hero(es) survived.")
        if is_boss:
            log.append(f"  ═══ BOSS DEFEATED ═══")
        for h in alive_heroes:
            morale_changes[h.id] = morale_changes.get(h.id, 0) - random.randint(3, 10)
    else:
        log.append(f"✗ Defeat. All heroes fell on floor {floor_number}.")

    skill_upgrades = {}
    if heroes_won:
        for h in alive_heroes:
            for s in getattr(h, '_skills', []):
                if s.get("level", 1) >= 10:
                    # Chance to upgrade
                    chance = 0.20 if is_boss else 0.05
                    if random.random() < chance:
                        tiers = ["Beginner", "Intermediate", "Advanced", "Legendary"]
                        current_tier = s.get("tier", "Beginner")
                        if current_tier in tiers:
                            idx = tiers.index(current_tier)
                            if idx < len(tiers) - 1:
                                new_tier = tiers[idx + 1]
                                skill_upgrades.setdefault(h.id, []).append({
                                    "skill_id": s["id"],
                                    "skill_name": s["name"],
                                    "new_tier": new_tier
                                })
                                log.append(f"  ✦ {h.name}'s {s['name']} ascended to {new_tier} tier!")

    result = {
        "winner": "heroes" if heroes_won else "enemies",
        "is_boss": is_boss,
        "initial_state": initial_state,
        "surviving_heroes": [
            {
                "id": h.id,
                "hp": max(0, h.hp),
                "morale_delta": morale_changes.get(h.id, 0),
                "kills_gained": kill_counts.get(h.id, 0),
                "stress_delta": stress_changes.get(h.id, 0),
            }
            for h in alive_heroes
        ],
        "dead_heroes": [h.id for h in dead_heroes],
        "skill_upgrades": skill_upgrades,
        "log": log,
        "turns": turns,
        "rounds": round_num,
        "combat_metrics": damage_dealt_stats
    }

    if heroes_won:
        try:
            from database import db
            with db() as conn:
                base_info = conn.execute("SELECT global_buffs FROM base WHERE id = 1").fetchone()
                buffs = __import__('json').loads(base_info["global_buffs"] or "{}") if base_info else {}
            from services.equipment_service import generate_equipment_drop
            drop_bonus = buffs.get("drop_boost", 0) * 0.05
            equip = generate_equipment_drop(floor_number, is_boss, drop_bonus)
            if equip:
                result["equipment_drop"] = equip
            
            # Guaranteed Drops
            result["gold_gained"] = int(300 * (1 + (floor_number/10)))
            result["supplies_gained"] = random.randint(2, 5)
            
            mats = ["Slime Core", "Iron Ore", "Goblin Ear", "Monster Bone", "Mystic Dust"]
            drops = {}
            for _ in range(random.randint(1, 3)):
                mat = random.choice(mats)
                drops[mat] = drops.get(mat, 0) + 1
            result["materials_gained"] = drops

            if is_boss:
                result["gold_gained"] += int(1500 * (1 + (floor_number/10)))
                result["supplies_gained"] += 10
                for _ in range(5):
                    mat = random.choice(mats)
                    drops[mat] = drops.get(mat, 0) + 1
                result["materials_gained"] = drops
        except Exception as e:
            print(f"Error generating drop: {e}")

    return result