"""
SUPPORT-CLASS REVAMP — star-scaled facility output.

Design (user-approved): supports shouldn't be "safe filler" — a high-star
support hero should ENABLE progression from their facility, scaling the whole
ladder (3★ nice → 5★ strong → 7★ insane), such that a roster of strong
supports + weak fighters can out-climb a lone high-star fighter. Two rules
from the user: crafting classes (Blacksmith/Alchemist) make things CHEAPER /
BETTER, never free; and no "attached hero" slots — everything flows from a
hero being ASSIGNED TO THEIR OWN FACILITY.

A hero only counts while alive and assigned to the facility matching their
lineage (evolved classes trace back to their base: Head Chef → Chef). The
BEST star among matching assignees sets the tier.

Wired so far:
  Chef → Dining Hall   feast: +% ALL stats applied in the combat stat pipeline
  Medic → Infirmary    field dressing: +% max HP entering every fight
  Merchant → Market    +passive gold multiplier (time_service)
  Farmer → Farm        +passive ingredients multiplier (time_service)
  Blacksmith → Forge   % off crafting gold costs (routers/crafting.py)
  Alchemist → Lab      faster passive brewing (alchemist_service)
  Scout → Bestiary     reveals floor types N floors beyond the deepest climb

Deferred (need combat-engine hooks; see memory notes): Priest death-insurance,
Tactician bonus first turn, Quartermaster mid-climb resupply.
"""
from database import db
from services.class_service import SUPPORT_BASE_CLASSES, CLASS_EVOLUTIONS

# Which facility each support lineage draws its power from.
SUPPORT_FACILITY = {
    'Chef': 'Dining Hall',
    'Medic': 'Infirmary',
    'Scout': 'Bestiary',
    'Blacksmith': 'Forge',
    'Quartermaster': 'Vault',
    'Tactician': 'Training Grounds',
    'Priest': 'Shrine',
    'Alchemist': 'Alchemist Lab',
    'Merchant': 'Market',
    'Farmer': 'Farm',
}

# ── Star ladders (index = star 1-7; index 0 = no matching hero assigned) ──
FEAST_PCT       = [0, 2, 4, 6, 9, 12, 16, 22]          # Chef: +% all stats at floor entry
SHIELD_PCT      = [0, 0, 2, 4, 6, 9, 13, 18]           # Medic: +% max HP entering fights
INCOME_BONUS    = [0, .05, .10, .16, .24, .35, .50, .75]  # Merchant/Farmer: extra passive mult
CRAFT_DISCOUNT  = [0, 4, 8, 12, 18, 25, 33, 45]        # Blacksmith: % off crafting gold
BREW_BONUS      = [0, .005, .01, .015, .02, .03, .045, .07]  # Alchemist: extra brew rate/assignee tick
SCOUT_FLOORS    = [0, 1, 1, 2, 3, 4, 6, 10]            # floors beyond deepest climb revealed


_LINEAGE_MAP = None

def _lineage_base(hero_class: str) -> str:
    """Trace an evolved class back to its base ('Culinary Master' → 'Chef').
    Base classes map to themselves; unknown classes return themselves."""
    global _LINEAGE_MAP
    if _LINEAGE_MAP is None:
        m = {}
        for base, tiers in CLASS_EVOLUTIONS.items():
            for name in tiers.get(30, []):
                m.setdefault(name, base)
            for branch in tiers.get(60, {}).values():
                for name in branch:
                    m.setdefault(name, base)
        _LINEAGE_MAP = m
    return _LINEAGE_MAP.get(hero_class, hero_class)


def get_support_tiers(conn=None) -> dict:
    """{base_class: best_star} for every support lineage with a living hero
    assigned to its matching facility. Fail-safe: {} on any error."""
    def _query(c):
        rows = c.execute("""
            SELECT h.hero_class, h.birth_star, h.current_star, f.type AS facility_type
            FROM facility_assignments fa
            JOIN heroes h ON fa.hero_id = h.id
            JOIN facilities f ON fa.facility_id = f.id
            WHERE h.is_alive = 1
        """).fetchall()
        tiers = {}
        for r in rows:
            base = _lineage_base(r["hero_class"])
            if SUPPORT_FACILITY.get(base) != r["facility_type"]:
                continue
            star = max(1, min(7, r["current_star"] or r["birth_star"] or 1))
            tiers[base] = max(tiers.get(base, 0), star)
        return tiers
    try:
        if conn is not None:
            return _query(conn)
        with db() as c:
            return _query(c)
    except Exception:
        return {}


def get_support_effects(conn=None) -> dict:
    """Resolved effect numbers for every wired system, from the tier table."""
    t = get_support_tiers(conn)
    return {
        "tiers": t,
        "feast_stat_pct": FEAST_PCT[t.get("Chef", 0)],
        "medic_shield_pct": SHIELD_PCT[t.get("Medic", 0)],
        "merchant_income_bonus": INCOME_BONUS[t.get("Merchant", 0)],
        "farmer_income_bonus": INCOME_BONUS[t.get("Farmer", 0)],
        "craft_discount_pct": CRAFT_DISCOUNT[t.get("Blacksmith", 0)],
        "brew_bonus": BREW_BONUS[t.get("Alchemist", 0)],
        "scout_reveal_floors": SCOUT_FLOORS[t.get("Scout", 0)],
    }
