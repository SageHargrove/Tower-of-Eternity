"""
Local-backend side of the Raid (PvP base siege) system — the same
split-of-responsibilities as routers/arena.py: this backend computes
snapshots from (and applies outcomes to) the player's own local save; the
separately-hosted arena_server owns matchmaking, the world map, and siege
resolution, and never touches any save file. The client is the courier
between the two.

Flow:
  1. GET  /raid/defense_snapshot     → client submits it to arena POST /arena/raid/submit_defense
  2. POST /raid/pay_scout            → then arena POST /arena/raid/scout reveals the target
  3. arena POST /arena/raid/attack   → returns spoils/result
  4. POST /raid/apply_attack_result  → attacker applies stolen loot locally
     GET  arena /arena/raid/events   → defender learns what happened offline
  5. POST /raid/apply_raid_event     → defender applies losses / captures locally
  6. arena /arena/raid/claim_prisoner → POST /raid/integrate_prisoner creates the
     captive locally — Rebellious Phase if they loved their old master
  7. POST /raid/prisoner/{id}/win_over → gold+gifts+time grind rebellion to 0
"""
import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from database import db
from services.combat_service import resolve_hero_stats
from services.ship_service import get_base_defense

router = APIRouter()

SCOUT_GOLD_COST = 750
SCOUT_AETHER_COST = 3

# ─── Scouting power vs counter-intelligence ───────────────────────
# Scouting isn't a flat info-dump: the arena server grades every scout
# attempt as attacker recon power minus defender counter-intel, and the
# resulting tier (0-4) decides how much of the defense report is revealed
# (see arena_server/raids.py build_scout_report). Both numbers are computed
# HERE from the local save — recon rides along with /raid/pay_scout, and
# counter-intel is baked into the defense snapshot.
#
# The Scout class line is the recon specialist: the Spy branch peaks at
# espionage, and Thieves have a knack for it too. The SAME ranks make a
# hero a counter-spy at home (it takes one to catch one).
SCOUT_CLASS_RANKS = {
    "Spymaster": 50, "Infiltrator": 45, "Ranger": 40,
    "Spy": 35, "Tracker": 30, "Pathfinder": 30,
    "Scout": 20, "Thief": 12,
}
COUNTER_SPY_FACTOR = 0.8       # counter-spying is a shade weaker than spying
SHIP_RECON_PER_TIER = 4        # aerial reconnaissance from the battleship
MAGE_TOWER_SCRY_PER_LEVEL = 1.5   # scrying the target from afar
MAGE_TOWER_WARD_PER_LEVEL = 1.0   # warding the home base against the same
WALL_PATROL_PER_LEVEL = 0.5
BASTION_PATROL_PER_LEVEL = 1.0


def _best_scout(conn) -> dict | None:
    """The roster's best recon asset: class rank + level + tactical aptitude."""
    rows = conn.execute(
        """SELECT id, name, hero_class, level, apt_tactical FROM heroes
           WHERE is_alive = 1 AND COALESCE(is_captured, 0) = 0 AND COALESCE(rebellion, 0) = 0"""
    ).fetchall()
    best, best_score = None, 0.0
    for r in rows:
        rank = SCOUT_CLASS_RANKS.get(r["hero_class"], 0)
        if rank <= 0:
            continue
        score = rank + r["level"] + (r["apt_tactical"] or 50) / 4.0
        if score > best_score:
            best, best_score = r, score
    return {"hero": dict(best), "score": best_score} if best else None


def compute_scout_power(conn) -> dict:
    """Attacker-side recon rating: best scouting hero + Mage Tower scrying
    + battleship aerial recon. Returns the breakdown for the UI."""
    scout = _best_scout(conn)
    hero_score = scout["score"] if scout else 0.0
    mage = conn.execute("SELECT level FROM facilities WHERE type = 'Mage Tower' AND base_id = 1").fetchone()
    scry = (mage["level"] if mage else 0) * MAGE_TOWER_SCRY_PER_LEVEL
    from services.ship_service import _ensure_columns
    _ensure_columns(conn)
    ship_tier = conn.execute("SELECT ship_tier FROM base WHERE id = 1").fetchone()["ship_tier"] or 0
    aerial = ship_tier * SHIP_RECON_PER_TIER
    return {
        "total": round(hero_score + scry + aerial, 1),
        "breakdown": {
            "scout_hero": ({"name": scout["hero"]["name"], "hero_class": scout["hero"]["hero_class"],
                            "score": round(hero_score, 1)} if scout else None),
            "mage_tower_scrying": round(scry, 1),
            "ship_aerial_recon": round(aerial, 1),
        },
    }


def compute_counter_intel(conn, defenders: list[dict]) -> dict:
    """Defender-side anti-scout rating: Wall/Bastion patrols, Mage Tower
    wards, and the best counter-spy among the defending five."""
    ratings = {}
    for ftype, per_level, key in (("Wall", WALL_PATROL_PER_LEVEL, "wall_patrols"),
                                  ("Bastion", BASTION_PATROL_PER_LEVEL, "bastion_patrols"),
                                  ("Mage Tower", MAGE_TOWER_WARD_PER_LEVEL, "mage_tower_wards")):
        row = conn.execute("SELECT level FROM facilities WHERE type = ? AND base_id = 1", (ftype,)).fetchone()
        ratings[key] = round((row["level"] if row else 0) * per_level, 1)
    counter_spy, spy_score = None, 0.0
    for h in defenders:
        rank = SCOUT_CLASS_RANKS.get(h.get("hero_class"), 0)
        if rank <= 0:
            continue
        score = (rank + h.get("level", 1) + (h.get("apt_tactical") or 50) / 4.0) * COUNTER_SPY_FACTOR
        if score > spy_score:
            counter_spy, spy_score = h, score
    ratings["counter_spy"] = ({"name": counter_spy.get("name"), "hero_class": counter_spy.get("hero_class"),
                               "score": round(spy_score, 1)} if counter_spy else None)
    return {
        "total": round(sum(v for v in (ratings["wall_patrols"], ratings["bastion_patrols"],
                                       ratings["mage_tower_wards"], spy_score)), 1),
        "breakdown": ratings,
    }

# A captive whose loyalty to their original master was at least this enters
# the Rebellious Phase; below it they were unhappy enough to just defect.
REBELLIOUS_AFFINITY_THRESHOLD = 30

# Winning over a rebellious prisoner: a massive commitment of time, gifts,
# and base resources — each session costs gold (scaling with how dug-in they
# are) and chips a modest amount off their rebellion.
WIN_OVER_BASE_GOLD = 300
WIN_OVER_GOLD_PER_REBELLION = 15
WIN_OVER_REDUCTION = (8, 15)  # rebellion chipped per session (random range)


@router.get("/defense_snapshot")
def defense_snapshot():
    """Everything the arena server needs to defend this base in absentia:
    the hypothetical strongest defending team (top 5 living heroes, fully
    stat-resolved), the base_defense breakdown (Wall/Garrison+Bastion/Ship/
    Beasts — see ship_service.get_base_defense), the docked ship tier, and
    the lootable resources a successful raider steals a % of."""
    with db() as conn:
        rows = conn.execute(
            """SELECT * FROM heroes
               WHERE is_alive = 1 AND COALESCE(is_captured, 0) = 0 AND COALESCE(rebellion, 0) = 0
               ORDER BY (level * 10 + strength + intelligence + endurance) DESC
               LIMIT 5"""
        ).fetchall()
        if not rows:
            raise HTTPException(status_code=400, detail="No living heroes to defend the base")
        defenders = resolve_hero_stats([dict(r) for r in rows])
        # get_base_defense also ensures the ship_tier column exists (see
        # ship_service._ensure_columns) — call it before selecting the column.
        defense = get_base_defense(conn)
        base = conn.execute("SELECT gold, ingredients, ship_tier FROM base WHERE id = 1").fetchone()
        counter_intel = compute_counter_intel(conn, defenders)
    return {
        "defenders": defenders,
        "base_defense": defense,
        "ship_tier": base["ship_tier"] or 0,
        "lootable": {"gold": base["gold"], "ingredients": base["ingredients"]},
        "counter_intel": counter_intel,
    }


class PayScoutRequest(BaseModel):
    currency: str = "gold"  # "gold" or "aether"


@router.get("/scout_power")
def scout_power():
    """Preview the base's current recon rating and what's feeding it —
    useful before spending anything, and for the raid UI's intel panel."""
    with db() as conn:
        return compute_scout_power(conn)


@router.post("/pay_scout")
def pay_scout(req: PayScoutRequest):
    """Charge the scouting fee locally before the client asks the arena
    server to reveal a target (same client-side economy split as the
    Training Market's gems). Returns the save's recon rating — the client
    forwards it as scout_power to arena POST /arena/raid/scout, where it's
    checked against the target's counter-intel to set the intel tier."""
    with db() as conn:
        base = conn.execute("SELECT gold, aether FROM base WHERE id = 1").fetchone()
        power = compute_scout_power(conn)
        if req.currency == "aether":
            if (base["aether"] or 0) < SCOUT_AETHER_COST:
                raise HTTPException(status_code=400, detail=f"Not enough Aether (need {SCOUT_AETHER_COST}).")
            conn.execute("UPDATE base SET aether = aether - ? WHERE id = 1", (SCOUT_AETHER_COST,))
            return {"ok": True, "paid": {"aether": SCOUT_AETHER_COST}, "scout_power": power}
        if base["gold"] < SCOUT_GOLD_COST:
            raise HTTPException(status_code=400, detail=f"Not enough gold (need {SCOUT_GOLD_COST:,}g).")
        conn.execute("UPDATE base SET gold = gold - ? WHERE id = 1", (SCOUT_GOLD_COST,))
        return {"ok": True, "paid": {"gold": SCOUT_GOLD_COST}, "scout_power": power}


class ApplyAttackResultRequest(BaseModel):
    won: bool
    gold_stolen: int = 0
    ingredients_stolen: int = 0


@router.post("/apply_attack_result")
def apply_attack_result(req: ApplyAttackResultRequest):
    """Attacker applies a finished raid locally: bank the spoils of war."""
    with db() as conn:
        if req.won and (req.gold_stolen or req.ingredients_stolen):
            conn.execute(
                "UPDATE base SET gold = gold + ?, ingredients = ingredients + ? WHERE id = 1",
                (max(0, req.gold_stolen), max(0, req.ingredients_stolen)),
            )
    return {"ok": True}


class ApplyRaidEventRequest(BaseModel):
    event_type: str      # "raided" | "hero_captured"
    payload: dict


@router.post("/apply_raid_event")
def apply_raid_event(req: ApplyRaidEventRequest):
    """Defender-side application of what the arena inbox reported happened
    while they were away: resource losses from a lost defense, and heroes
    carried off as prisoners."""
    with db() as conn:
        if req.event_type == "raided":
            gold_lost = max(0, int(req.payload.get("gold_lost", 0) or 0))
            ing_lost = max(0, int(req.payload.get("ingredients_lost", 0) or 0))
            if gold_lost or ing_lost:
                conn.execute(
                    "UPDATE base SET gold = MAX(0, gold - ?), ingredients = MAX(0, ingredients - ?) WHERE id = 1",
                    (gold_lost, ing_lost),
                )
            return {"ok": True, "applied": {"gold_lost": gold_lost, "ingredients_lost": ing_lost}}

        if req.event_type == "hero_captured":
            hero_id = req.payload.get("hero_id")
            hero = conn.execute("SELECT id, name FROM heroes WHERE id = ?", (hero_id,)).fetchone()
            if not hero:
                return {"ok": True, "applied": None}  # already gone / different save
            # Captured, not dead — alive in someone else's dungeon. Off the
            # roster, off any team or facility.
            conn.execute(
                "UPDATE heroes SET is_captured = 1, is_on_team = 0, team_position = 0, is_team_leader = 0 WHERE id = ?",
                (hero_id,),
            )
            conn.execute("DELETE FROM facility_assignments WHERE hero_id = ?", (hero_id,))
            return {"ok": True, "applied": {"captured": hero["name"]}}

    raise HTTPException(status_code=400, detail=f"Unknown raid event type: {req.event_type}")


class IntegratePrisonerRequest(BaseModel):
    prisoner: dict          # full hero snapshot from arena /arena/raid/claim_prisoner
    original_master: str


@router.post("/integrate_prisoner")
def integrate_prisoner(req: IntegratePrisonerRequest):
    """Create the captured hero on this save. They keep their original
    loyalty: a captive who had high affinity with their old master enters
    the Rebellious Phase — cannot be deployed until their rebellion is
    ground down to 0 via /raid/prisoner/{id}/win_over."""
    h = req.prisoner
    if not isinstance(h, dict) or not h.get("name"):
        raise HTTPException(status_code=400, detail="Malformed prisoner snapshot")

    original_affinity = int(h.get("affinity", 50) or 0)
    rebellion = original_affinity if original_affinity >= REBELLIOUS_AFFINITY_THRESHOLD else 0

    skills = h.get("_skills", h.get("skills", []))
    traits = h.get("_traits", h.get("traits", []))
    with db() as conn:
        cursor = conn.execute(
            """INSERT INTO heroes (
                name, title, backstory, personality, portrait_path, gender,
                birth_star, hero_class, level, skills, traits,
                health, max_health, strength, intelligence, defense, endurance,
                agility, willpower, luck, morale, stress,
                affinity, is_prisoner, rebellion, original_master
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                h.get("name"), h.get("title"), h.get("backstory"), h.get("personality"),
                h.get("portrait_path", ""), h.get("gender", "unknown"),
                int(h.get("birth_star", 1) or 1), h.get("hero_class", "Classless"),
                int(h.get("level", 1) or 1),
                json.dumps(skills if isinstance(skills, list) else []),
                json.dumps(traits if isinstance(traits, list) else []),
                h.get("max_health", 100), h.get("max_health", 100),
                h.get("strength", 10), h.get("intelligence", 5), h.get("defense", 5),
                h.get("endurance", h.get("defense", 5)), h.get("agility", 10),
                h.get("willpower", 6), h.get("luck", 5),
                # Dragged to an enemy base in chains — nobody arrives cheerful.
                40, 60,
                0,  # affinity to their NEW master starts at zero
                1, rebellion, req.original_master,
            ),
        )
        hero_id = cursor.lastrowid
    return {
        "ok": True,
        "hero_id": hero_id,
        "rebellious": rebellion > 0,
        "rebellion": rebellion,
        "message": (
            f"{h.get('name')} glares from the holding cell — their loyalty to {req.original_master} runs deep. "
            "It will take time, gifts, and resources to win them over."
            if rebellion > 0 else
            f"{h.get('name')} shrugs off their old allegiance and joins your roster."
        ),
    }


@router.get("/prisoners")
def list_prisoners():
    """Current captives and how close each is to breaking."""
    with db() as conn:
        rows = conn.execute(
            """SELECT id, name, hero_class, level, rebellion, original_master, affinity
               FROM heroes
               WHERE is_alive = 1 AND COALESCE(is_prisoner, 0) = 1
               ORDER BY rebellion DESC"""
        ).fetchall()
    return {"prisoners": [dict(r) for r in rows]}


@router.post("/prisoner/{hero_id}/win_over")
def win_over_prisoner(hero_id: int):
    """One session of the loyalty-breaking grind: costs gold (scaling with
    how rebellious they still are), chips their rebellion down, and builds
    a little affinity toward their new master. At rebellion 0 they fully
    integrate and become deployable."""
    import random
    with db() as conn:
        hero = conn.execute(
            "SELECT * FROM heroes WHERE id = ? AND is_alive = 1 AND COALESCE(is_prisoner, 0) = 1",
            (hero_id,),
        ).fetchone()
        if not hero:
            raise HTTPException(status_code=404, detail="No such prisoner")
        rebellion = hero["rebellion"] or 0
        if rebellion <= 0:
            raise HTTPException(status_code=400, detail=f"{hero['name']} is already won over.")

        cost = WIN_OVER_BASE_GOLD + rebellion * WIN_OVER_GOLD_PER_REBELLION
        base = conn.execute("SELECT gold FROM base WHERE id = 1").fetchone()
        if base["gold"] < cost:
            raise HTTPException(status_code=400, detail=f"Not enough gold — this session costs {cost:,}g.")

        reduction = random.randint(*WIN_OVER_REDUCTION)
        new_rebellion = max(0, rebellion - reduction)
        new_affinity = min(100, (hero["affinity"] or 0) + 3)
        conn.execute("UPDATE base SET gold = gold - ? WHERE id = 1", (cost,))
        conn.execute(
            "UPDATE heroes SET rebellion = ?, affinity = ? WHERE id = ?",
            (new_rebellion, new_affinity, hero_id),
        )
    won_over = new_rebellion == 0
    return {
        "ok": True,
        "gold_spent": cost,
        "rebellion": new_rebellion,
        "won_over": won_over,
        "message": (
            f"{hero['name']}'s resolve finally breaks — they pledge themselves to your banner!"
            if won_over else
            f"{hero['name']} softens slightly. Rebellion {rebellion} → {new_rebellion}."
        ),
    }
