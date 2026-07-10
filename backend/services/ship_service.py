"""Magic battleships — built at the Skydock, one vessel per base.

The third pillar of power (heroes = who, base = where, ship = how you
project it): a status symbol in the World, and the core of raid offense
once raids land. Tier art lives at frontend/public/images/battleships/
ship_{tier}.png.

Builder gate (the Magic Engineer's signature value, without hard-locking
players out): tiers 1-2 can be built by an APPRENTICE — any living hero
with high Mental aptitude assigned to the Skydock. Tier 3+ hulls require
a true Magic Engineer assigned there.
"""
from database import db

APPRENTICE_MENTAL_APT = 70

SHIP_TIERS = {
    1: {"name": "Skiff", "cost": 8000, "crew": 2, "defense": 5,
        "requires": "apprentice",
        "desc": "A patched-together flying dinghy held aloft by a single stubborn rune. It flies. Mostly."},
    2: {"name": "Corvette", "cost": 20000, "crew": 4, "defense": 12,
        "requires": "apprentice",
        "desc": "A real vessel — one arcane cannon, a proper deck, and enough hull to survive its own landings."},
    3: {"name": "Frigate", "cost": 45000, "crew": 6, "defense": 25,
        "requires": "engineer",
        "desc": "A true warship. Cannon battery, armored prow, and a keel-array that hums loud enough to announce you."},
    4: {"name": "Dreadnought", "cost": 90000, "crew": 9, "defense": 45,
        "requires": "engineer",
        "desc": "A multi-deck monster veined with glowing circuitry. Docking it politely is no longer possible."},
    5: {"name": "Leviathan", "cost": 150000, "crew": 12, "defense": 80,
        "requires": "engineer",
        "desc": "A floating fortress ringed by orbiting sigils. Less a ship than a declaration."},
}


def _skydock_builders(conn) -> dict:
    """Who's staffing the Skydock: a real Magic Engineer, and/or an
    apprentice-grade mind (any hero with high Mental aptitude)."""
    dock = conn.execute("SELECT id FROM facilities WHERE type = 'Skydock' AND base_id = 1").fetchone()
    if not dock:
        return {"skydock_built": False, "has_engineer": False, "has_apprentice": False}
    rows = conn.execute("""
        SELECT h.hero_class, h.apt_mental, h.name FROM facility_assignments fa
        JOIN heroes h ON fa.hero_id = h.id
        WHERE fa.facility_id = ? AND h.is_alive = 1
    """, (dock["id"],)).fetchall()
    has_engineer = any(r["hero_class"] == "Magic Engineer" for r in rows)
    apprentice = next((r["name"] for r in rows if (r["apt_mental"] or 0) >= APPRENTICE_MENTAL_APT and r["hero_class"] != "Magic Engineer"), None)
    return {"skydock_built": True, "has_engineer": has_engineer, "has_apprentice": apprentice is not None, "apprentice_name": apprentice}


def _ensure_columns(conn):
    for col, ddl in (
        ("ship_tier", "INTEGER DEFAULT 0"),
        ("ship_name", "TEXT"),
        # Refit: a free point-allocation pool across Speed/Firepower/Armor.
        # NO auto tier-up — tier is the hull class, set at build; refit makes
        # each ship unique (design decision, Skydock chat 2026-07-07).
        ("ship_refit_json", "TEXT DEFAULT '{}'"),
        ("ship_refit_points", "INTEGER DEFAULT 0"),
    ):
        try:
            conn.execute(f"ALTER TABLE base ADD COLUMN {col} {ddl}")
        except Exception:
            pass


# ─── Refit ───────────────────────────────────────────────────────────
# Each hull tier grants a base pool at build time; more points are bought
# with gold at a rising price. Points move freely between the three
# categories (deallocate and reallocate at will) — the pool is the limit.

REFIT_STATS = ("speed", "fire", "armor")
REFIT_POOL_PER_TIER = 3           # granted when a new hull is laid
REFIT_POINT_BASE_COST = 4000      # gold; cost = base * (owned_points + 1)
REFIT_POINT_CAP = 30


def _refit_state(base_row) -> tuple[dict, int]:
    import json as _json
    try:
        alloc = _json.loads(base_row["ship_refit_json"] or "{}")
    except Exception:
        alloc = {}
    alloc = {s: int(alloc.get(s, 0)) for s in REFIT_STATS}
    return alloc, int(base_row["ship_refit_points"] or 0)


def allocate_refit(stat: str, delta: int) -> dict:
    if stat not in REFIT_STATS:
        raise ValueError("Refit points go to Speed, Firepower, or Armor.")
    if delta not in (-1, 1):
        raise ValueError("One point at a time — the fitters are careful people.")
    import json as _json
    with db() as conn:
        _ensure_columns(conn)
        base = conn.execute("SELECT ship_tier, ship_refit_json, ship_refit_points FROM base WHERE id = 1").fetchone()
        if not (base["ship_tier"] or 0):
            raise ValueError("Lay a keel first — there is nothing to refit.")
        alloc, pool = _refit_state(base)
        spent = sum(alloc.values())
        if delta > 0 and spent >= pool:
            raise ValueError("No refit points left — buy one, or free one from another category.")
        if delta < 0 and alloc[stat] <= 0:
            raise ValueError(f"No points allocated to {stat}.")
        alloc[stat] += delta
        conn.execute("UPDATE base SET ship_refit_json = ? WHERE id = 1", (_json.dumps(alloc),))
    return {"ok": True, "refit": alloc, "unspent": pool - sum(alloc.values())}


def _refit_discount_pct(conn) -> int:
    """Skywrights guild boon, synced from the world server (see
    /base/guild_boons). 0 when guildless or the column doesn't exist yet."""
    try:
        row = conn.execute("SELECT guild_refit_discount_pct FROM base WHERE id = 1").fetchone()
        return int(row["guild_refit_discount_pct"] or 0)
    except Exception:
        return 0


def buy_refit_point() -> dict:
    with db() as conn:
        _ensure_columns(conn)
        base = conn.execute("SELECT gold, ship_tier, ship_refit_points FROM base WHERE id = 1").fetchone()
        if not (base["ship_tier"] or 0):
            raise ValueError("Lay a keel first — there is nothing to refit.")
        pool = int(base["ship_refit_points"] or 0)
        if pool >= REFIT_POINT_CAP:
            raise ValueError("The hull holds no more fittings — the fitters refuse.")
        cost = REFIT_POINT_BASE_COST * (pool + 1)
        cost = int(round(cost * (1 - min(50, _refit_discount_pct(conn)) / 100.0)))
        if base["gold"] < cost:
            raise ValueError(f"Not enough gold. The fitters ask {cost:,}g for the next point.")
        conn.execute("UPDATE base SET gold = gold - ?, ship_refit_points = ship_refit_points + 1 WHERE id = 1", (cost,))
    return {"ok": True, "points": pool + 1, "cost": cost}


def get_ship_status() -> dict:
    with db() as conn:
        _ensure_columns(conn)
        base = conn.execute("SELECT gold, ship_tier, ship_name FROM base WHERE id = 1").fetchone()
        builders = _skydock_builders(conn)
        tier = base["ship_tier"] or 0
        current = SHIP_TIERS.get(tier)
        nxt = SHIP_TIERS.get(tier + 1)

        can_build = False
        blocker = None
        if nxt:
            if not builders["skydock_built"]:
                blocker = "Build the Skydock first."
            elif nxt["requires"] == "engineer" and not builders["has_engineer"]:
                blocker = "A Magic Engineer must be assigned to the Skydock to build this hull."
            elif nxt["requires"] == "apprentice" and not (builders["has_engineer"] or builders["has_apprentice"]):
                blocker = f"Assign a Magic Engineer — or any hero with {APPRENTICE_MENTAL_APT}+ Mental aptitude — to the Skydock."
            elif base["gold"] < nxt["cost"]:
                blocker = f"Not enough gold ({nxt['cost']:,}g needed)."
            else:
                can_build = True

        full = conn.execute("SELECT ship_refit_json, ship_refit_points FROM base WHERE id = 1").fetchone()
        alloc, pool = _refit_state(full)
        return {
            "tier": tier,
            "ship": ({"tier": tier, **current} if current else None),
            "ship_name": base["ship_name"],
            "next": ({"tier": tier + 1, **nxt} if nxt else None),
            "can_build": can_build,
            "blocker": blocker,
            "builders": builders,
            "refit": {
                "allocated": alloc, "pool": pool, "unspent": pool - sum(alloc.values()),
                "next_point_cost": (int(round(REFIT_POINT_BASE_COST * (pool + 1) * (1 - min(50, _refit_discount_pct(conn)) / 100.0)))
                                    if pool < REFIT_POINT_CAP else None),
                "cap": REFIT_POINT_CAP,
            },
        }


def build_next_tier() -> dict:
    with db() as conn:
        _ensure_columns(conn)
        base = conn.execute("SELECT gold, ship_tier FROM base WHERE id = 1").fetchone()
        tier = (base["ship_tier"] or 0) + 1
        nxt = SHIP_TIERS.get(tier)
        if not nxt:
            raise ValueError("Your ship is already the greatest hull the Skydock can produce.")

        builders = _skydock_builders(conn)
        if not builders["skydock_built"]:
            raise ValueError("Build the Skydock first.")
        if nxt["requires"] == "engineer" and not builders["has_engineer"]:
            raise ValueError("A Magic Engineer must be assigned to the Skydock to build this hull.")
        if nxt["requires"] == "apprentice" and not (builders["has_engineer"] or builders["has_apprentice"]):
            raise ValueError(f"Assign a Magic Engineer — or any hero with {APPRENTICE_MENTAL_APT}+ Mental aptitude — to the Skydock.")
        if base["gold"] < nxt["cost"]:
            raise ValueError(f"Not enough gold. Need {nxt['cost']:,}g.")

        # a new hull grants its share of the refit pool
        conn.execute(
            "UPDATE base SET gold = gold - ?, ship_tier = ?, "
            "ship_refit_points = COALESCE(ship_refit_points, 0) + ? WHERE id = 1",
            (nxt["cost"], tier, REFIT_POOL_PER_TIER))

    return {"ok": True, "tier": tier, "name": nxt["name"], "refit_points_granted": REFIT_POOL_PER_TIER}


def rename_ship(name: str) -> dict:
    name = (name or "").strip()[:40]
    if not name:
        raise ValueError("Give the ship a name.")
    with db() as conn:
        _ensure_columns(conn)
        if not (conn.execute("SELECT ship_tier FROM base WHERE id = 1").fetchone()["ship_tier"] or 0):
            raise ValueError("Build a ship first.")
        conn.execute("UPDATE base SET ship_name = ? WHERE id = 1", (name,))
    return {"ok": True, "name": name}


def get_base_defense(conn) -> dict:
    """Combined defense rating for the coming raid system: the Wall is the
    outer fortification (flat rating per level), the Bastion multiplies its
    garrison's strength, and the docked ship adds its firepower."""
    _ensure_columns(conn)
    wall = conn.execute("SELECT level FROM facilities WHERE type = 'Wall' AND base_id = 1").fetchone()
    bastion = conn.execute("SELECT id, level FROM facilities WHERE type = 'Bastion' AND base_id = 1").fetchone()
    ship_tier = conn.execute("SELECT ship_tier FROM base WHERE id = 1").fetchone()["ship_tier"] or 0

    wall_rating = (wall["level"] * 10) if wall else 0
    garrison_rating = 0
    if bastion:
        rows = conn.execute("""
            SELECT h.level, h.hero_class FROM facility_assignments fa
            JOIN heroes h ON fa.hero_id = h.id
            WHERE fa.facility_id = ? AND h.is_alive = 1
        """, (bastion["id"],)).fetchall()
        # Arcane cannons: every garrisoned hero contributes their level,
        # doubled while a Magic Engineer serves in the Bastion.
        engineer = any(r["hero_class"] == "Magic Engineer" for r in rows)
        garrison_rating = sum(r["level"] for r in rows) * (2 if engineer else 1) + bastion["level"] * 5
    ship_rating = SHIP_TIERS.get(ship_tier, {}).get("defense", 0)
    # Refit fittings harden the hull: Firepower and Armor both raise the
    # docked ship's contribution (Speed pays off on expeditions instead).
    if ship_tier:
        full = conn.execute("SELECT ship_refit_json, ship_refit_points FROM base WHERE id = 1").fetchone()
        alloc, _pool = _refit_state(full)
        ship_rating += alloc.get("fire", 0) * 3 + alloc.get("armor", 0) * 2

    # Captured beasts guarding the grounds (Bestiary, floor 30+).
    from services.endgame_service import bestiary_defense
    beast_rating = bestiary_defense(conn)

    return {
        "wall": wall_rating,
        "garrison": garrison_rating,
        "ship": ship_rating,
        "beasts": beast_rating,
        "total": wall_rating + garrison_rating + ship_rating + beast_rating,
    }
