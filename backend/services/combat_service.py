import random
import math
from dataclasses import dataclass, field

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
    is_hero: bool = True
    alive: bool = True
    log_name: str = ""

    def __post_init__(self):
        self.log_name = self.name if self.is_hero else f"[{self.name}]"

def make_enemies(floor_number: int, count: int = None) -> list[CombatUnit]:
    """Generate enemies scaled to floor number."""
    scale = 1 + (floor_number * 0.08)
    if count is None:
        count = random.randint(1, min(4, 1 + floor_number // 5))

    enemy_types = [
        ("Hollow Knight", 1.2, 1.1, 0.9),
        ("Plague Crawler", 0.8, 0.7, 1.3),
        ("Stone Golem",    1.5, 1.8, 0.5),
        ("Shriek Shade",   0.7, 0.5, 1.6),
        ("Bone Warden",    1.0, 1.3, 0.8),
    ]

    enemies = []
    for i in range(count):
        etype = random.choice(enemy_types)
        name, hp_m, def_m, spd_m = etype
        enemies.append(CombatUnit(
            id=-(i+1),
            name=name,
            hp=int(80 * scale * hp_m),
            max_hp=int(80 * scale * hp_m),
            attack=int(8 * scale),
            defense=int(5 * scale * def_m),
            speed=int(10 * scale * spd_m),
            morale=100,
            stress=0,
            is_hero=False,
        ))
    return enemies

def calc_damage(attacker: CombatUnit, defender: CombatUnit) -> int:
    """
    Damage formula: ATK * (100 / (100 + DEF)) + variance
    Morale affects attacker: below 40 morale = reduced effectiveness
    """
    base = attacker.attack * (100 / (100 + defender.defense))

    # Morale penalty for heroes
    if attacker.is_hero and attacker.morale < 40:
        morale_factor = 0.5 + (attacker.morale / 80)
        base *= morale_factor

    # Variance ±15%
    variance = random.uniform(0.85, 1.15)
    damage = max(1, int(base * variance))

    # Small crit chance (5%)
    if random.random() < 0.05:
        damage = int(damage * 1.8)
        return damage, True  # crit

    return damage, False

def run_combat(heroes: list[dict], floor_number: int, is_boss: bool = False) -> dict:
    """
    Main combat loop. Returns outcome dict with:
    - winner: 'heroes' or 'enemies'
    - surviving_heroes: list of hero ids with updated stats
    - dead_heroes: list of hero ids
    - log: list of event strings
    - morale_changes: dict of hero_id -> morale delta
    """
    log = []
    morale_changes = {h["id"]: 0 for h in heroes}

    # Build combat units
    combatants_heroes = [
        CombatUnit(
            id=h["id"],
            name=h["name"],
            hp=h["hp"],
            max_hp=h["max_hp"],
            attack=h["attack"],
            defense=h["defense"],
            speed=h["speed"],
            morale=h["morale"],
            stress=h["stress"],
            is_hero=True,
        )
        for h in heroes
    ]

    enemy_count = 1 if is_boss else None
    enemies = make_enemies(floor_number, count=enemy_count)
    if is_boss:
        # Boss is significantly stronger
        for e in enemies:
            e.hp = int(e.hp * 2.5)
            e.max_hp = e.hp
            e.attack = int(e.attack * 2)
            e.name = f"BOSS: {e.name}"

    log.append(f"Floor {floor_number}: {len(combatants_heroes)} heroes vs {len(enemies)} enemies.")

    # Speed-sorted initiative
    all_units = combatants_heroes + enemies
    max_rounds = 30

    for round_num in range(1, max_rounds + 1):
        # Sort by speed (+ small random tiebreak)
        all_units.sort(key=lambda u: u.speed + random.uniform(0, 2), reverse=True)

        alive_heroes = [u for u in all_units if u.is_hero and u.alive]
        alive_enemies = [u for u in all_units if not u.is_hero and u.alive]

        if not alive_heroes or not alive_enemies:
            break

        for attacker in all_units:
            if not attacker.alive:
                continue

            # Pick target
            if attacker.is_hero:
                targets = [u for u in alive_enemies if u.alive]
            else:
                targets = [u for u in alive_heroes if u.alive]

            if not targets:
                break

            # Target lowest HP (basic AI)
            target = min(targets, key=lambda u: u.hp)

            damage, is_crit = calc_damage(attacker, target)
            target.hp -= damage
            crit_text = " (CRITICAL!)" if is_crit else ""
            log.append(f"  {attacker.log_name} hits {target.log_name} for {damage} dmg{crit_text}. [{target.hp}/{target.max_hp} HP]")

            if target.hp <= 0:
                target.alive = False
                log.append(f"  ✦ {target.log_name} has fallen.")

                # Morale impact on surviving heroes when a hero dies
                if target.is_hero:
                    for h in combatants_heroes:
                        if h.alive:
                            morale_changes[h.id] -= random.randint(8, 18)
                            log.append(f"    {h.name}'s morale wavers...")
                else:
                    # Killing an enemy gives small morale boost
                    if attacker.is_hero:
                        morale_changes[attacker.id] += random.randint(3, 7)

        # Check end condition
        alive_heroes = [u for u in combatants_heroes if u.alive]
        alive_enemies = [u for u in enemies if u.alive]
        if not alive_heroes or not alive_enemies:
            break

    # Determine outcome
    alive_heroes = [u for u in combatants_heroes if u.alive]
    dead_heroes = [u for u in combatants_heroes if not u.alive]
    heroes_won = len(alive_heroes) > 0 and len([u for u in enemies if u.alive]) == 0

    if heroes_won:
        log.append(f"✓ Victory. {len(alive_heroes)} hero(es) survived.")
        # Stress from combat (even in victory)
        for h in alive_heroes:
            morale_changes[h.id] -= random.randint(3, 10)
    else:
        log.append(f"✗ Defeat. All heroes fell on floor {floor_number}.")

    return {
        "winner": "heroes" if heroes_won else "enemies",
        "surviving_heroes": [
            {
                "id": h.id,
                "hp": max(0, h.hp),
                "morale_delta": morale_changes.get(h.id, 0),
            }
            for h in alive_heroes
        ],
        "dead_heroes": [h.id for h in dead_heroes],
        "log": log,
        "rounds": round_num,
    }
