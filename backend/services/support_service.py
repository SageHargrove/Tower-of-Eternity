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

The full branch map lives in SUPPORT_EVOLUTIONS_SPEC.md (docs/). In short:
every support's evolution BRANCH selects its mechanic, MASTERY (star + evo
stage, cap 9) scales it, and Lv.60 capstones add a twist. Combat boons apply
per fight on the Tower path only (Arena passes apply_support_boons=False).
Floors are never revealed ahead (user rule) — Scout hunts beasts instead.
"""
from collections import defaultdict
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

# ── MASTERY ladders (index = mastery 0-9). Mastery = star + evolution stage,
# NOT pure star (see get_support_tiers): a hero's investment (leveling → evolving
# their support class) raises their facility output, so power isn't 100% pull
# luck. star sets the floor (1-7); +1 at 1st evo (Lv.30), +2 at 2nd evo (Lv.60),
# capped at 9. So a grinded, fully-evolved 3★ reaches tier 5 ("strong"), a
# fully-evolved 7★ reaches the new tier-9 ceiling, and a raw 7★ is still tier 7.
FEAST_PCT       = [0, 2, 4, 6, 9, 12, 16, 22, 28, 35]        # Chef: +% all stats at floor entry
SHIELD_PCT      = [0, 0, 2, 4, 6, 9, 13, 18, 24, 30]         # Medic: +% max HP entering fights
INCOME_BONUS    = [0, .05, .10, .16, .24, .35, .50, .75, 1.05, 1.4]  # Merchant/Farmer: extra passive mult
CRAFT_DISCOUNT  = [0, 4, 8, 12, 18, 25, 33, 45, 55, 65]      # Blacksmith: % off crafting gold (never free)
BREW_BONUS      = [0, .005, .01, .015, .02, .03, .045, .07, .095, .12]  # Alchemist: extra brew rate/assignee tick
# Combat-engine boons (applied per fight; excluded from Arena/PvP like the
# Chef/Medic pipeline). See combat_service.
PRIEST_SAVES    = [0, 0, 0, 0, 0, 0, 1, 2, 2, 2]             # Priest: death-save charges/hero/fight — HARD-CAPPED at 2 (user rule); 1 at mastery 6, 2 at 7+
TACTICIAN_MANA  = [0, 4, 8, 12, 16, 22, 30, 40, 52, 66]      # Tactician: bonus opening mana/hero (+guaranteed first strike when >0)
# Quartermaster (→ Vault): a light opening BARRIER + emergency FIELD KITS (user
# picked "both"). Kept modest on each since they stack — must not outshine the
# Medic's HP ceiling. Barrier = % damage reduction for the first rounds (blunts
# the alpha strike, never wasted even at full HP). Kits = a team pool of one-shot
# heals that fire when a hero drops below the threshold mid-fight (attrition
# insurance — only spends on a genuinely hurt hero, never a wasted top-up).
QM_BARRIER_PCT    = [0, .05, .08, .11, .14, .18, .22, .28, .34, .40]  # damage-reduction magnitude
QM_BARRIER_ROUNDS = [0, 2, 2, 2, 2, 3, 3, 3, 3, 4]                 # active rounds of the barrier
QM_KIT_CHARGES    = [0, 0, 0, 1, 1, 1, 2, 2, 3, 3]                 # emergency heals per fight (team pool)
QM_KIT_HEAL_PCT   = [0, 0, 0, .18, .20, .24, .24, .30, .34, .40]   # heal as % max HP when a kit fires
QM_KIT_THRESHOLD  = 0.35                                            # a kit fires when a hero first drops below this HP fraction

# ═══ WAVE 1 — per-BRANCH combat mechanics (see SUPPORT_EVOLUTIONS_SPEC.md) ═══
# The branch a support evolved into selects WHICH mechanic; mastery scales it.
# Unevolved = a weak GENERIC (its own small ladder, so a high-mastery-but-
# unevolved hero can't get a strong "generic"). The existing ladders above are
# reused as one branch each: FEAST_PCT=Chef/Sous Chef, SHIELD_PCT=Medic/Surgeon,
# PRIEST_SAVES=Priest/Oracle, TACTICIAN_MANA=Tactician/Strategist, QM_*=QM.
GEN_FEAST_PCT   = [0, 1, 2, 3, 3, 4, 5, 6, 7, 8]            # unevolved Chef: tiny all-stat feast
GEN_SHIELD_PCT  = [0, 0, 1, 2, 3, 4, 5, 6, 7, 8]            # unevolved Medic: tiny max-HP
GEN_MANA        = [0, 2, 3, 4, 6, 8, 10, 13, 16, 20]        # unevolved Tactician: small opening mana (NO first strike)
GEN_BARRIER_PCT = [0, .03, .04, .05, .07, .09, .11, .13, .15, .18]  # unevolved QM: small barrier
# Chef · Butcher → Iron Chef: War Rations (offense-skewed feast)
WAR_STR_PCT     = [0, 3, 6, 10, 14, 18, 24, 30, 38, 46]     # +% strength
WAR_CRIT        = [0, .02, .03, .04, .05, .07, .09, .11, .13, .16]  # +crit chance
# Medic · Herbalist → Miracle Worker: Regen Salves (per-round % max-HP heal)
MEDIC_REGEN_PCT = [0, .01, .02, .03, .04, .05, .06, .08, .10, .12]
# Priest · Chaplain → Saint: Blessing (physical + magic resistance)
BLESSING_RESIST = [0, .03, .05, .07, .09, .12, .15, .19, .24, .30]
# Tactician · Commander → General: Battle Formation (+% all six combat stats)
FORMATION_PCT   = [0, 2, 3, 5, 7, 9, 12, 15, 19, 24]

# ═══ WAVE 3 (part 1) — beast systems (Bestiary) ═══
# Scout · Pathfinder → Ranger: Master of the Hunt — better capture + bigger catch.
SCOUT_CAPTURE     = [0, .02, .03, .05, .07, .09, .12, .15, .19, .24]  # +additive capture chance
SCOUT_BEAST_POWER = [0, .05, .10, .15, .22, .30, .40, .52, .66, .82]  # +% power on captured beasts
# Farmer · Beast Tamer: Menagerie — tamed beasts guard harder (combat pet is a later sub-wave).
BEAST_DEF_MULT    = [0, .10, .18, .28, .40, .55, .72, .95, 1.25, 1.6]  # +% defense from guarding beasts

# ═══ WAVE 3 (part 2) — remaining combat branches ═══
MEDIC_POISON_PCT  = [0, .02, .03, .04, .05, .06, .08, .10, .12, .15]  # Field Medic (Toxin Kit): poison tick as % target max HP (dur 3)
ADVISOR_CRIT      = [0, .03, .05, .07, .09, .12, .15, .19, .24, .30]  # Tactician · Advisor (War Council): +crit
SMITH_DR_PCT      = [0, .02, .03, .05, .07, .09, .12, .15, .19, .24]  # Blacksmith · Armorer (Tempered Plate): team flat damage-reduction
SABOTAGE_PCT      = [0, .04, .06, .09, .12, .16, .20, .25, .31, .38]  # Scout · Spy (Sabotage): enemies start with -% stats/HP

# ═══ WAVE 3 (part 3) — final signatures + Lv.60 CAPSTONE twists ═══
MARK_PCT          = [0, .06, .09, .12, .16, .20, .25, .31, .38, .46]  # Scout · Tracker (Predator's Mark): shred the strongest enemy's defenses
DRAUGHT_PCT       = [0, 2, 3, 5, 7, 9, 12, 15, 19, 24]               # Alchemist · Poisoner (Combat Draughts): +% str/int at fight start
LOYALTY_BONUS     = [0, 1, 1, 2, 2, 3, 3, 4, 5, 6]                    # Priest · Confessor (Absolution): extra loyalty per shrine pulse
RUNEWORK_PCT      = [0, 4, 7, 10, 14, 18, 23, 29, 36, 44]             # Blacksmith · Artificer (Runework): +% Athenaeum insight rate
SMUGGLER_DISC     = [0, 3, 5, 8, 11, 14, 18, 22, 27, 33]              # Merchant · Smuggler (Black Market): % off Market shop purchases
# Capstones (require evolution stage 2, i.e. the Lv.60 class). Flat twists —
# mastery already scaled the signature; the capstone changes WHAT it does.
CAP_WELLFED_REGEN   = 0.02   # Master Chef: team regen_pct while feasted
CAP_MORALE_BOOST    = 12     # Iron Chef: fight-start morale surge
CAP_STITCH_PCT      = 0.45   # Chief Medical Officer: once/fight emergency stitch (% max HP)
CAP_BLESSING_HEAL   = 0.15   # Saint: fight-start holy mending (% max HP)
CAP_HASTE_AGI       = 0.25   # Grand Strategist: +% agility rounds 1-2
CAP_LASTSTAND_PCT   = 0.08   # General: survivors +% str/int per fallen ally
CAP_SNOWBALL_PCT    = 0.05   # Warlord: killer +% strength per kill (this fight)
CAP_HOARD_LOOT_PCT  = 0.20   # Hoarder: +% gold/materials from floors
CAP_WARCHEST_GOLD   = 0.15   # Tycoon: +% bonus on floor gold
CAP_SMITH_RARITY    = 0.25   # Master Smith: chance a craft comes out +1 rarity
CAP_ELITE_HUNT      = 0.5    # Ranger: captured beasts +50% MORE power, Alpha epithet
CAP_MARK_ARMOR_PEN  = 0.20   # Infiltrator: team +armor pen vs the marked
CAP_CALM_STRESS     = 2      # High Confessor: -stress per shrine pulse
CAP_TRANSMUTE_GOLD  = 40     # Philosopher: Lab transmutes gold/level/tick (Transmuter signature is aether)


# class name → list of every lineage it belongs to: {base, branch, stage}.
# A name can appear in MORE THAN ONE tree (e.g. 'Ranger' is both Archer's and
# Scout's; 'Warlord' is Spearman's and Tactician's), and heroes only store
# hero_class (no base-class column), so the name alone is ambiguous — we
# disambiguate by the FACILITY the hero is assigned to (a Ranger in the Bestiary
# is unambiguously the Scout Ranger). branch=None means the unevolved base class.
_CLASS_LINEAGES = None

def _build_maps():
    global _CLASS_LINEAGES
    if _CLASS_LINEAGES is not None:
        return
    lineages = defaultdict(list)
    for base, tiers in CLASS_EVOLUTIONS.items():
        lineages[base].append({"base": base, "branch": None, "stage": 0})
        for root in tiers.get(30, []):                       # Lv.30 branch roots
            lineages[root].append({"base": base, "branch": root, "stage": 1})
        for root, names in tiers.get(60, {}).items():        # Lv.60 capstones inherit their root's branch
            for name in names:
                lineages[name].append({"base": base, "branch": root, "stage": 2})
    _CLASS_LINEAGES = dict(lineages)


def _support_entry(hero_class: str, facility_type: str):
    """Resolve (base, branch, stage) for a hero of hero_class ASSIGNED to
    facility_type — picking the lineage whose base owns that facility, so a
    collision name resolves correctly. None if this hero isn't a support of
    that facility's class."""
    _build_maps()
    for e in _CLASS_LINEAGES.get(hero_class, []):
        if SUPPORT_FACILITY.get(e["base"]) == facility_type:
            return e
    return None


def _mastery(star: int, class_stage: int, level: int) -> int:
    """star + evolution stage (capped 9). Stage comes from the CLASS only —
    the evolution gate (level_service.evolution_gate_level) holds a hero's
    level at 30/60 until they pick a path, so an unevolved hero must never
    collect the milestone credit from raw level."""
    return min(9, max(1, min(7, star)) + class_stage)


def _resolve_supports(conn=None) -> dict:
    """{base_class: {'mastery': int, 'branch': str|None}} for the BEST-mastery
    living assignee at each support's facility (that hero sets both the mastery
    AND which evolution branch's mechanic is active — one facility, one dominant
    specialist). branch is None for an unevolved base-class hero (generic).
    Fail-safe: {} on any error."""
    _build_maps()
    def _query(c):
        rows = c.execute("""
            SELECT h.hero_class, h.birth_star, h.current_star, h.level, f.type AS facility_type
            FROM facility_assignments fa
            JOIN heroes h ON fa.hero_id = h.id
            JOIN facilities f ON fa.facility_id = f.id
            WHERE h.is_alive = 1
        """).fetchall()
        best = {}
        for r in rows:
            entry = _support_entry(r["hero_class"], r["facility_type"])
            if entry is None:
                continue
            base = entry["base"]
            star = r["current_star"] or r["birth_star"] or 1
            mastery = _mastery(star, entry["stage"], r["level"])
            cur = best.get(base)
            if cur is None or mastery > cur["mastery"]:
                # stage is the CLASS stage (0/1/2) — capstones gate on actually
                # holding the Lv.60 class, not on a level milestone.
                best[base] = {"mastery": mastery, "branch": entry["branch"], "stage": entry["stage"]}
        return best
    try:
        if conn is not None:
            return _query(conn)
        with db() as c:
            return _query(c)
    except Exception:
        return {}


def get_support_tiers(conn=None) -> dict:
    """{base_class: best_MASTERY}. Mastery = star + evolution stage (capped 9).
    Backward-compatible flat view of _resolve_supports."""
    return {b: v["mastery"] for b, v in _resolve_supports(conn).items()}


def get_support_branches(conn=None) -> dict:
    """{base_class: branch_key|None} — which evolution branch's mechanic is active
    at each facility (None = unevolved generic). Drives per-branch mechanics."""
    return {b: v["branch"] for b, v in _resolve_supports(conn).items()}


def get_support_effects(conn=None) -> dict:
    """Resolved effect numbers for every wired system. Wave 1 combat classes
    (Chef/Medic/Priest/Tactician/Quartermaster) are now BRANCH-resolved: the
    active branch selects the mechanic, mastery scales it, unevolved = a weak
    generic. Economy classes (Merchant/Farmer/Blacksmith/Alchemist) + Scout stay
    mastery-only until their waves. See SUPPORT_EVOLUTIONS_SPEC.md."""
    resolved = _resolve_supports(conn)
    t = {b: v["mastery"] for b, v in resolved.items()}
    branches = {b: v["branch"] for b, v in resolved.items()}
    stages = {b: v.get("stage", 0) for b, v in resolved.items()}

    def m(base):
        return t.get(base, 0)

    def cap(base):
        """True when the facility's dominant specialist holds a Lv.60 class —
        unlocks that branch's capstone twist."""
        return stages.get(base, 0) >= 2

    fx = {
        "tiers": t,
        "branches": branches,
        "stages": stages,
        # ── economy: branch-gated below (primary branch OR unevolved gets the
        #    core output; the OTHER branches' specialties are Wave 3) ──
        "merchant_income_bonus": 0, "farmer_income_bonus": 0,
        "craft_discount_pct": 0, "brew_bonus": 0,
        "chef_larder_ingredient_bonus": 0,   # Chef · Forager → Full Larder (boosts Farm)
        "vault_gold_bonus": 0,               # Quartermaster · Merchant → War Chest (Vault makes gold)
        # ── beast systems (Bestiary) ──
        "scout_capture_bonus": 0,            # Scout · Pathfinder → Master of the Hunt
        "scout_beast_power_pct": 0,          # Scout · Pathfinder → bigger catches (Ranger)
        "farmer_beast_defense_mult": 0,      # Farmer · Beast Tamer → Menagerie
        # ── remaining combat branches ──
        "medic_poison_pct": 0,               # Medic · Field Medic → Toxin Kit (poison-on-hit)
        "advisor_crit": 0, "advisor_str_pct": 0,  # Tactician · Advisor → War Council
        "smith_dmg_reduction_pct": 0,        # Blacksmith · Armorer → Tempered Plate (team DR)
        "scout_sabotage_pct": 0,             # Scout · Spy → Sabotage (enemy debuff)
        # ── final signatures ──
        "scout_mark_pct": 0,                 # Scout · Tracker → Predator's Mark
        "scout_mark_armor_pen": 0,           # Infiltrator capstone
        "alch_draught_pct": 0,               # Alchemist · Poisoner → Combat Draughts
        "alch_enemy_poison": 0,              # Brewmaster capstone: enemies start poisoned
        "alch_transmute_gold": 0,            # Alchemist · Transmuter → Lab transmutes gold (per level per tick)
        "priest_loyalty_bonus": 0,           # Priest · Confessor → Absolution (per shrine pulse)
        "priest_calm_stress": 0,             # High Confessor capstone
        "smith_research_pct": 0,             # Blacksmith · Artificer → Runework (insight rate)
        "smuggler_discount_pct": 0,          # Merchant · Smuggler → Black Market (shop discount)
        # ── capstone twists (Lv.60) ──
        "chef_wellfed_regen": 0,             # Master Chef
        "chef_morale_boost": 0,              # Iron Chef
        "medic_stitch_pct": 0,               # Chief Medical Officer (once/fight)
        "medic_cleanse": False,              # Miracle Worker: hero DOTs expire twice as fast
        "priest_foresee": 0,                 # Prophet: team pool of dodged fatal blows
        "priest_blessing_heal": 0,           # Saint: fight-start mending
        "tact_haste_agi": 0,                 # Grand Strategist
        "tact_laststand_pct": 0,             # General
        "tact_snowball_pct": 0,              # Warlord
        "qm_hoard_loot_pct": 0,              # Hoarder
        "qm_warchest_gold_pct": 0,           # Tycoon
        "qm_kit_mana": False,                # Guildmaster: kits also restore mana + cleanse
        "smith_rarity_chance": 0,            # Master Smith
        "scout_elite_hunt": 0,               # Ranger
        # ── Chef: Sous Chef=Grand Feast · Butcher=War Rations · Forager=(economy, deferred) · none=weak feast ──
        "feast_stat_pct": 0, "war_str_pct": 0, "war_crit": 0.0,
        # ── Medic: Surgeon=max-HP shield · Herbalist=regen · Field Medic=(poison, deferred) · none=weak shield ──
        "medic_shield_pct": 0, "medic_regen_pct": 0.0,
        # ── Priest: Oracle=death-saves · Chaplain=blessing resist · Confessor=(loyalty, deferred) ──
        "priest_death_saves": 0, "blessing_resist_pct": 0.0,
        # ── Tactician: Strategist=gambit(mana+first strike) · Commander=formation · Advisor=(deferred) · none=small mana ──
        "tactician_bonus_mana": 0, "tactician_first_strike": False, "formation_pct": 0,
        # ── Quartermaster: Scavenger/Hoarder=barrier · Logistics/Guildmaster=kits · Merchant=(gold, deferred) ──
        "quartermaster_barrier_pct": 0, "quartermaster_barrier_rounds": 2,
        "quartermaster_kit_charges": 0, "quartermaster_kit_heal_pct": 0.0,
        "quartermaster_kit_threshold": QM_KIT_THRESHOLD,
    }

    # Chef — Sous Chef/Butcher are combat (above); Forager is economy (Full Larder).
    cb, cm = branches.get("Chef"), m("Chef")
    if cb == "Butcher":
        fx["war_str_pct"] = WAR_STR_PCT[cm]; fx["war_crit"] = WAR_CRIT[cm]
        if cap("Chef"):
            fx["chef_morale_boost"] = CAP_MORALE_BOOST          # Iron Chef: fearless
    elif cb == "Sous Chef":
        fx["feast_stat_pct"] = FEAST_PCT[cm]
        if cap("Chef"):
            fx["chef_wellfed_regen"] = CAP_WELLFED_REGEN        # Master Chef: well-fed regen
    elif cb == "Forager":
        fx["chef_larder_ingredient_bonus"] = INCOME_BONUS[cm]   # boosts Farm output
        # Gourmet capstone (consumables clear stress/trauma) needs the consumable
        # pipeline — still deferred.
    elif cb is None and cm:
        fx["feast_stat_pct"] = GEN_FEAST_PCT[cm]                # unevolved: weak feast

    # ── Economy classes: the primary branch (or unevolved) gets the facility's
    #    CORE output; the exotic branches' specialties (black market, transmute,
    #    armor/rune quality, beast pet) are Wave 3, hence 0 for now. ──
    mb_, mm_ = branches.get("Merchant"), m("Merchant")
    if mb_ in ("Trader", None):
        fx["merchant_income_bonus"] = INCOME_BONUS[mm_]
        # Trader capstones (Guild Master / Trade Prince share the branch key —
        # merged): a further income kicker at Lv.60.
        if mb_ == "Trader" and cap("Merchant"):
            fx["merchant_income_bonus"] = round(fx["merchant_income_bonus"] * 1.25, 3)
    elif mb_ == "Smuggler":
        fx["smuggler_discount_pct"] = SMUGGLER_DISC[mm_]        # Black Market: shop discount
        if cap("Merchant"):                                      # Baron/Broker merged: contraband gold
            fx["merchant_income_bonus"] = round(INCOME_BONUS[mm_] * 0.5, 3)
    fb_, fm_ = branches.get("Farmer"), m("Farmer")
    if fb_ in ("Master Farmer", None):
        fx["farmer_income_bonus"] = INCOME_BONUS[fm_]
        if fb_ == "Master Farmer" and cap("Farmer"):             # Harvest Lord / Nature's Chosen merged
            fx["farmer_income_bonus"] = round(fx["farmer_income_bonus"] * 1.25, 3)
    ab_, am_ = branches.get("Alchemist"), m("Alchemist")
    if ab_ in ("Apothecary", None):
        fx["brew_bonus"] = BREW_BONUS[am_]
        if ab_ == "Apothecary" and cap("Alchemist"):             # Grand Alchemist: brews even faster
            fx["brew_bonus"] = round(fx["brew_bonus"] * 1.5, 4)
    elif ab_ == "Poisoner":
        fx["alch_draught_pct"] = DRAUGHT_PCT[am_]               # Combat Draughts
        if cap("Alchemist"):                                     # Brewmaster: enemies start poisoned
            fx["alch_enemy_poison"] = MEDIC_POISON_PCT[am_] * 0.6
    elif ab_ == "Transmuter":
        fx["alch_transmute_gold"] = int(20 + 4 * am_)           # Lab transmutes gold/level/tick
        if cap("Alchemist"):                                     # Philosopher: gold-from-lead surge
            fx["alch_transmute_gold"] = CAP_TRANSMUTE_GOLD + 6 * am_
    bb_, bm_ = branches.get("Blacksmith"), m("Blacksmith")
    if bb_ in ("Weaponsmith", None):
        fx["craft_discount_pct"] = CRAFT_DISCOUNT[bm_]          # Weaponsmith/unevolved: cheaper crafting
        if bb_ == "Weaponsmith" and cap("Blacksmith"):
            fx["smith_rarity_chance"] = CAP_SMITH_RARITY        # Master Smith: +1 rarity chance
    elif bb_ == "Armorer":
        fx["smith_dmg_reduction_pct"] = SMITH_DR_PCT[bm_]       # Tempered Plate — team damage-reduction
        # Forge Lord capstone folds into the DR ladder's top end (mastery 8-9).
    elif bb_ == "Artificer":
        fx["smith_research_pct"] = RUNEWORK_PCT[bm_]            # Runework: faster Athenaeum insight

    # ── beast branches (Bestiary): Scout·Pathfinder (Master of the Hunt) and
    #    Farmer·Beast Tamer (Menagerie). Farmer's combat pet is a later sub-wave. ──
    sb_, sm_ = branches.get("Scout"), m("Scout")
    if sb_ == "Pathfinder":
        fx["scout_capture_bonus"] = SCOUT_CAPTURE[sm_]
        fx["scout_beast_power_pct"] = SCOUT_BEAST_POWER[sm_]
        if cap("Scout"):
            fx["scout_elite_hunt"] = CAP_ELITE_HUNT             # Ranger: Alpha catches
    elif sb_ == "Tracker":
        fx["scout_mark_pct"] = MARK_PCT[sm_]                    # Predator's Mark
        if cap("Scout"):
            fx["scout_mark_armor_pen"] = CAP_MARK_ARMOR_PEN     # Infiltrator
    elif sb_ == "Spy":
        fx["scout_sabotage_pct"] = SABOTAGE_PCT[sm_]            # Sabotage — enemies start weakened
        # Spymaster capstone (afflicted start) folds into sabotage's top end.
    fbt_, fbm_ = branches.get("Farmer"), m("Farmer")
    if fbt_ == "Beast Tamer":
        fx["farmer_beast_defense_mult"] = BEAST_DEF_MULT[fbm_]

    # Medic
    mb, mm = branches.get("Medic"), m("Medic")
    if mb == "Field Medic":
        fx["medic_poison_pct"] = MEDIC_POISON_PCT[mm]
        if cap("Medic"):
            fx["alch_enemy_poison"] = max(fx["alch_enemy_poison"], MEDIC_POISON_PCT[mm] * 0.6)  # Plague Doctor: enemies start afflicted
    elif mb == "Herbalist":
        fx["medic_regen_pct"] = MEDIC_REGEN_PCT[mm]
        if cap("Medic"):
            fx["medic_cleanse"] = True                      # Miracle Worker: DOTs burn off fast
    elif mb == "Surgeon":
        fx["medic_shield_pct"] = SHIELD_PCT[mm]
        if cap("Medic"):
            fx["medic_stitch_pct"] = CAP_STITCH_PCT         # CMO: once/fight emergency stitch
    elif mb is None and mm:
        fx["medic_shield_pct"] = GEN_SHIELD_PCT[mm]         # unevolved: weak shield

    # Priest
    pb, pm = branches.get("Priest"), m("Priest")
    if pb == "Oracle":
        fx["priest_death_saves"] = PRIEST_SAVES[pm]
        if cap("Priest"):
            fx["priest_foresee"] = 1                        # Prophet: dodge one fatal blow outright
    elif pb == "Chaplain":
        fx["blessing_resist_pct"] = BLESSING_RESIST[pm]
        if cap("Priest"):
            fx["priest_blessing_heal"] = CAP_BLESSING_HEAL  # Saint: fight-start mending
    elif pb == "Confessor":
        fx["priest_loyalty_bonus"] = LOYALTY_BONUS[pm]      # Absolution: deeper devotion
        if cap("Priest"):
            fx["priest_calm_stress"] = CAP_CALM_STRESS      # High Confessor: calm the roster

    # Tactician
    tb, tm = branches.get("Tactician"), m("Tactician")
    if tb == "Strategist":
        fx["tactician_bonus_mana"] = TACTICIAN_MANA[tm]; fx["tactician_first_strike"] = True
        if cap("Tactician"):
            fx["tact_haste_agi"] = CAP_HASTE_AGI            # Grand Strategist: opening haste
    elif tb == "Commander":
        fx["formation_pct"] = FORMATION_PCT[tm]
        if cap("Tactician"):
            fx["tact_laststand_pct"] = CAP_LASTSTAND_PCT    # General: last stand
    elif tb == "Advisor":
        fx["advisor_crit"] = ADVISOR_CRIT[tm]; fx["advisor_str_pct"] = WAR_STR_PCT[tm]  # War Council: rage + crit
        if cap("Tactician"):
            fx["tact_snowball_pct"] = CAP_SNOWBALL_PCT      # Warlord: kills snowball
    elif tb is None and tm:
        fx["tactician_bonus_mana"] = GEN_MANA[tm]           # unevolved: small mana, no first strike

    # Quartermaster
    qb, qm_ = branches.get("Quartermaster"), m("Quartermaster")
    if qb in ("Scavenger", None) and qm_:
        pct = QM_BARRIER_PCT[qm_] if qb == "Scavenger" else GEN_BARRIER_PCT[qm_]
        fx["quartermaster_barrier_pct"] = pct
        fx["quartermaster_barrier_rounds"] = QM_BARRIER_ROUNDS[qm_]
        if qb == "Scavenger" and cap("Quartermaster"):
            fx["qm_hoard_loot_pct"] = CAP_HOARD_LOOT_PCT     # Hoarder: richer floors
    elif qb == "Logistics Officer":
        fx["quartermaster_kit_charges"] = QM_KIT_CHARGES[qm_]
        fx["quartermaster_kit_heal_pct"] = QM_KIT_HEAL_PCT[qm_]
        if cap("Quartermaster"):
            fx["qm_kit_mana"] = True                         # Guildmaster: kits restore mana + cleanse
    elif qb == "Merchant":                                   # War Chest — Vault makes gold
        fx["vault_gold_bonus"] = INCOME_BONUS[qm_]
        if cap("Quartermaster"):
            fx["qm_warchest_gold_pct"] = CAP_WARCHEST_GOLD   # Tycoon: cut of floor gold

    return fx
