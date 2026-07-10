"""
Siege resolution for PvP base raids.

Attacker power  = attacking team's combat stats + attacking battleship firepower.
Defender power  = defending team's combat stats + Wall + Garrison + defending
                  battleship + the Bastion's arcane cannons (all of which the
                  defender's local backend already folded into the base_defense
                  rating it submitted — see backend/services/ship_service.py's
                  get_base_defense()).

Rather than deciding the fight by comparing two abstract power numbers, the
base/ship advantages are converted into stat multipliers on the actual hero
units and the fight is resolved by the same real combat simulation arena
duels use (combat.resolve_arena_fight → backend run_combat). The overall
stats are heavily shifted by the Base/Ship advantages, but a genuinely
stronger squad can still crack a well-walled weaker one.
"""
import copy
import random

from combat import resolve_arena_fight

# Server-authoritative tier → firepower mapping (clients submit only the
# tier). Mirrors backend ship_service.SHIP_TIERS defense ratings: a hull's
# guns hit harder than its armor rates, hence the 1.5x.
SHIP_FIREPOWER = {0: 0, 1: 8, 2: 18, 3: 38, 4: 68, 5: 120}

# Raid Specialists — classes whose buffs apply ONLY during sieges, on either
# side. Commander/General are the Tactician line's war-leaders (Tactician →
# Commander @30 → General); the Magic Engineer mans the Bastion cannons in
# person when defending.
SIEGE_CLASS_BUFFS = {
    # class: (attacking_bonus, defending_bonus) as fractional stat buffs
    "Commander": (0.30, 0.30),
    "General": (0.45, 0.45),
    "Tactician": (0.10, 0.10),        # the base class gets a taste of its future identity
    "Magic Engineer": (0.0, 0.35),    # bastion cannons — defense only
}

# Siege traits (see backend traits_service.TRAITS_POOL) — massive, but only here.
SIEGE_TRAIT_BUFFS = {
    "siegebreaker": (0.25, 0.0),
    "bulwark": (0.0, 0.25),
}

# How hard base/ship ratings shift the fight: rating → team-wide stat mult.
# Soft-capped so a maxed fortress (~300+ rating) is daunting, not unbeatable.
RATING_MULT_CAP = 2.25
RATING_SOFT_DIVISOR = 220.0


def rating_to_mult(rating: float) -> float:
    return min(RATING_MULT_CAP, 1.0 + max(0.0, rating) / RATING_SOFT_DIVISOR)


# ─── Tiered scouting ──────────────────────────────────────────────
# A scout attempt is graded: net = attacker recon power (best Scout-line
# hero + Mage Tower scrying + battleship aerial recon) minus the target's
# counter-intel (Wall/Bastion patrols, Mage Tower wards, counter-spy
# heroes). Both sides' ratings come from their own local backends. The net
# sets the intel tier — what the report actually reveals:
#   0  scouts turned away — only a vague strength impression
#   1  fuzzed defense total + defender count
#   2  exact defense breakdown + ship tier + defender classes/levels
#   3  + defender names, HP — the classic full report
#   4  deep infiltration: + each defender's skills/traits + exact lootable
SCOUT_TIER_THRESHOLDS = [0, 25, 50, 80]  # net >= threshold → that tier (index+1)

SCOUT_TIER_LABELS = {
    0: "Turned Away — your scouts were spotted and saw almost nothing.",
    1: "Distant Observation — rough numbers from outside the walls.",
    2: "Perimeter Survey — the fortifications, counted and measured.",
    3: "Inside Report — faces and names from within the walls.",
    4: "Deep Infiltration — a complete dossier, down to the vault ledger.",
}


def _fuzz(value: float, pct: float, rng: random.Random) -> int:
    return max(0, int(value * (1 + rng.uniform(-pct, pct))))


def _strength_impression(total: float) -> str:
    if total < 40:
        return "lightly defended"
    if total < 100:
        return "moderately defended"
    if total < 180:
        return "heavily fortified"
    return "a fortress bristling with defenses"


def build_scout_report(defense: dict, scout_power: float, seed: str) -> dict:
    """Assemble the intel a scout attempt of this strength actually gets.
    Fuzzing is seeded per (scout, target, defense-version) so re-scouting
    the same defense repeats the same wrong numbers instead of letting the
    client average the noise away."""
    counter = float((defense.get("counter_intel") or {}).get("total", 0) or 0)
    net = float(scout_power or 0) - counter
    tier = 0
    for i, threshold in enumerate(SCOUT_TIER_THRESHOLDS):
        if net >= threshold:
            tier = i + 1
    rng = random.Random(seed)

    base_defense = defense.get("base_defense", {})
    defenders = defense.get("defenders", [])[:5]
    total = float(base_defense.get("total", 0) or 0)

    report = {
        "tier": tier,
        "tier_label": SCOUT_TIER_LABELS[tier],
        "net_intel": round(net, 1),
        "counter_intel_detected": counter > 0 and tier <= 2,  # low tiers only learn they WERE watched
    }
    if tier == 0:
        report["impression"] = f"The base looks {_strength_impression(total)}."
        return report

    report["defender_count"] = len(defenders)
    if tier == 1:
        report["base_defense"] = {"total_estimate": _fuzz(total, 0.30, rng)}
        report["impression"] = f"The base looks {_strength_impression(total)}."
        return report

    report["base_defense"] = base_defense
    report["ship_tier"] = defense.get("ship_tier", 0)
    detail_keys_by_tier = {
        2: ("hero_class", "level"),
        3: ("name", "hero_class", "level", "max_health"),
        4: ("name", "hero_class", "level", "max_health", "strength", "intelligence",
            "agility", "endurance"),
    }
    keys = detail_keys_by_tier[min(tier, 4)]
    out_defenders = []
    for h in defenders:
        d = {k: h.get(k) for k in keys}
        if tier >= 4:
            d["skills"] = [s.get("name") for s in (h.get("_skills") or []) if isinstance(s, dict)]
            d["traits"] = [t.get("name") for t in (h.get("_traits") or []) if isinstance(t, dict)]
        out_defenders.append(d)
    report["defenders"] = out_defenders

    if tier >= 3:
        lootable = defense.get("lootable", {})
        pct = 0.0 if tier >= 4 else 0.20
        report["lootable_estimate"] = {
            "gold": _fuzz(float(lootable.get("gold", 0) or 0), pct, rng),
            "ingredients": _fuzz(float(lootable.get("ingredients", 0) or 0), pct, rng),
        }
    return report


def _siege_bonus(hero: dict, attacking: bool) -> float:
    idx = 0 if attacking else 1
    bonus = SIEGE_CLASS_BUFFS.get(hero.get("hero_class", ""), (0.0, 0.0))[idx]
    for t in hero.get("_traits", []) or []:
        bonus += SIEGE_TRAIT_BUFFS.get(t.get("id"), (0.0, 0.0))[idx]
    return bonus


SIEGE_SCALED_STATS = ("strength", "intelligence", "endurance", "defense", "max_health", "health")


def _scale_team(team: list[dict], team_mult: float, attacking: bool, log: list) -> list[dict]:
    scaled = []
    for h in team:
        h = copy.deepcopy(h)
        mult = team_mult * (1.0 + _siege_bonus(h, attacking))
        spec = _siege_bonus(h, attacking)
        if spec > 0:
            role = "leads the assault" if attacking else "anchors the defense"
            log.append(f"  ⚔ Raid Specialist: {h.get('name', '?')} ({h.get('hero_class', '?')}) {role} (+{int(spec * 100)}% siege stats).")
        if mult != 1.0:
            for stat in SIEGE_SCALED_STATS:
                if stat in h and isinstance(h[stat], (int, float)):
                    h[stat] = int(h[stat] * mult)
        scaled.append(h)
    return scaled


def resolve_siege(attacker_team: list[dict], attacker_ship_tier: int,
                  defender_team: list[dict], base_defense: dict, defender_ship_tier: int) -> dict:
    """Run the siege as a real multi-unit combat sim with both sides' units
    scaled by their siege advantages. Returns the run_combat result dict plus
    a power-summary block for the client's siege report screen."""
    log = []

    attacker_rating = SHIP_FIREPOWER.get(int(attacker_ship_tier or 0), 0)
    # The defender's submitted base_defense total already includes wall,
    # garrison (bastion cannons), docked ship, and beasts.
    defender_rating = float(base_defense.get("total", 0) or 0)

    atk_mult = rating_to_mult(attacker_rating)
    def_mult = rating_to_mult(defender_rating)

    log.append("🏰 SIEGE COMMENCES")
    log.append(f"  Attacker firepower: battleship tier {attacker_ship_tier} (+{int((atk_mult - 1) * 100)}% assault stats).")
    log.append(
        f"  Defender fortifications: wall {base_defense.get('wall', 0)}, garrison {base_defense.get('garrison', 0)}, "
        f"ship {base_defense.get('ship', 0)}, beasts {base_defense.get('beasts', 0)} "
        f"(+{int((def_mult - 1) * 100)}% defense stats)."
    )

    attackers = _scale_team(attacker_team, atk_mult, attacking=True, log=log)
    defenders = _scale_team(defender_team, def_mult, attacking=False, log=log)

    result = resolve_arena_fight(attackers, defenders)
    result["log"] = log + (result.get("log") or [])
    result["siege"] = {
        "attacker_ship_tier": attacker_ship_tier,
        "attacker_ship_firepower": attacker_rating,
        "attacker_stat_mult": round(atk_mult, 3),
        "defender_base_defense": base_defense,
        "defender_ship_tier": defender_ship_tier,
        "defender_stat_mult": round(def_mult, 3),
    }
    return result
