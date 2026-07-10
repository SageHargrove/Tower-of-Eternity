"""THE SKY CHARTS — expeditions.

Dispatch the Skydock hull on timed lanes for offline rewards. There is one
ship, so one lane can be underway at a time. State lives in
base.expeditions_json (same additive pattern as daily_dungeon_json):

    {"lane": "trade_run", "ship_tier": 2, "crew": [ids...],
     "crew_names": [...], "departed_at": iso, "returns_at": iso}

Rewards scale with hull tier and crew size. Recall early pays half spoils.
"""
from database import db
from services.ship_service import SHIP_TIERS
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException
import json
import random

LANES = {
    "aether_drift": {
        "name": "AETHER DRIFT", "hours": 8, "min_tier": 1, "reward": "aether",
        "desc": "A slow sweep of the violet shallows. Low risk, steady essence.",
        "tone": "violet",
    },
    "trade_run": {
        "name": "TRADE RUN", "hours": 8, "min_tier": 1, "reward": "gold",
        "desc": "Haul goods between spire markets. Firepower discourages pirates.",
        "tone": "gold",
    },
    "deep_sky_hunt": {
        "name": "DEEP SKY HUNT", "hours": 12, "min_tier": 3, "reward": "materials",
        "desc": "Past the last beacon. Something out there drops embercores.",
        "tone": "red",
    },
}

MATS = ["iron_shard", "dark_crystal", "worn_leather", "spirit_dust", "ancient_bone", "elemental_stone"]


def _ensure_column(conn):
    try:
        conn.execute("ALTER TABLE base ADD COLUMN expeditions_json TEXT")
    except Exception:
        pass


def _state(conn) -> dict:
    _ensure_column(conn)
    row = conn.execute("SELECT expeditions_json FROM base WHERE id = 1").fetchone()
    try:
        return json.loads(row["expeditions_json"]) if row and row["expeditions_json"] else {}
    except (json.JSONDecodeError, TypeError):
        return {}


def _save(conn, state: dict):
    conn.execute("UPDATE base SET expeditions_json = ? WHERE id = 1", (json.dumps(state),))


def _ship_tier(conn) -> int:
    try:
        row = conn.execute("SELECT ship_tier FROM base WHERE id = 1").fetchone()
        return row["ship_tier"] or 0
    except Exception:
        return 0


def _crew_factor(crew_count: int) -> float:
    return 1.0 + 0.15 * max(0, crew_count - 1)


def _roll_reward(lane_key: str, ship_tier: int, crew_count: int) -> dict:
    """Full-spoils reward for a lane. Returns {kind, amount|drops}."""
    factor = _crew_factor(crew_count)
    kind = LANES[lane_key]["reward"]
    if kind == "gold":
        return {"kind": "gold", "amount": int((2500 + 1800 * ship_tier) * factor)}
    if kind == "aether":
        return {"kind": "aether", "amount": int((20 + 12 * ship_tier) * factor)}
    # materials — the deep hunt drops a spread, heavier at higher tiers
    drops = {}
    for _ in range(random.randint(3, 4 + ship_tier)):
        mat = random.choice(MATS)
        drops[mat] = drops.get(mat, 0) + random.randint(2, 3 + ship_tier)
    return {"kind": "materials", "drops": drops}


def _apply_reward(conn, reward: dict, half: bool = False):
    if reward["kind"] == "gold":
        amt = reward["amount"] // 2 if half else reward["amount"]
        conn.execute("UPDATE base SET gold = gold + ? WHERE id = 1", (amt,))
        return {"kind": "gold", "amount": amt}
    if reward["kind"] == "aether":
        amt = reward["amount"] // 2 if half else reward["amount"]
        conn.execute("UPDATE base SET aether = aether + ? WHERE id = 1", (amt,))
        return {"kind": "aether", "amount": amt}
    drops = reward["drops"]
    if half:
        drops = {k: max(1, v // 2) for k, v in drops.items()}
    row = conn.execute("SELECT materials FROM base WHERE id = 1").fetchone()
    current = json.loads(row["materials"]) if row and row["materials"] else {}
    for mat, qty in drops.items():
        current[mat] = current.get(mat, 0) + qty
    conn.execute("UPDATE base SET materials = ? WHERE id = 1", (json.dumps(current),))
    return {"kind": "materials", "drops": drops}


def expeditions_status() -> dict:
    with db() as conn:
        state = _state(conn)
        tier = _ship_tier(conn)
        ship = SHIP_TIERS.get(tier)
        row = conn.execute("SELECT ship_name FROM base WHERE id = 1").fetchone()
        ship_name = (row["ship_name"] if row else None) or (ship["name"] if ship else None)
        now = datetime.now(timezone.utc)

        active_lane = state.get("lane")
        lanes = []
        for key, cfg in LANES.items():
            lane = {
                "key": key, "name": cfg["name"], "hours": cfg["hours"],
                "desc": cfg["desc"], "tone": cfg["tone"], "reward": cfg["reward"],
                "min_tier": cfg["min_tier"],
            }
            if key == active_lane:
                returns_at = datetime.fromisoformat(state["returns_at"])
                remaining = int((returns_at - now).total_seconds())
                lane["state"] = "ready" if remaining <= 0 else "underway"
                lane["returns_in_seconds"] = max(0, remaining)
                lane["crew_names"] = state.get("crew_names", [])
                lane["crew_count"] = len(state.get("crew", []))
            elif tier < cfg["min_tier"]:
                lane["state"] = "locked"
                lane["req"] = f"TIER {'I' * cfg['min_tier']} HULL OR GREATER" if cfg["min_tier"] <= 3 else f"TIER {cfg['min_tier']} HULL"
            elif active_lane:
                lane["state"] = "no_ship"  # the hull is out on another lane
            elif tier == 0:
                lane["state"] = "locked"
                lane["req"] = "BUILD A HULL AT THE SKYDOCK"
            else:
                lane["state"] = "open"
            lanes.append(lane)

        return {
            "lanes": lanes,
            "ship": ({"tier": tier, "name": ship_name, "crew_capacity": ship["crew"]} if ship else None),
            "underway": active_lane,
        }


def dispatch(lane_key: str, hero_ids: list) -> dict:
    if lane_key not in LANES:
        raise HTTPException(status_code=400, detail="No such lane on the charts.")
    with db() as conn:
        state = _state(conn)
        if state.get("lane"):
            raise HTTPException(status_code=400, detail="The hull is already underway — recall it or wait for its return.")
        tier = _ship_tier(conn)
        if tier == 0:
            raise HTTPException(status_code=400, detail="No hull to dispatch. Build one at the Skydock.")
        cfg = LANES[lane_key]
        if tier < cfg["min_tier"]:
            raise HTTPException(status_code=400, detail="This lane needs a greater hull.")
        if not hero_ids:
            raise HTTPException(status_code=400, detail="A hull cannot fly uncrewed.")
        capacity = SHIP_TIERS[tier]["crew"]
        if len(hero_ids) > capacity:
            raise HTTPException(status_code=400, detail=f"The {SHIP_TIERS[tier]['name']} holds a crew of {capacity}.")
        placeholders = ",".join("?" * len(hero_ids))
        rows = conn.execute(
            f"SELECT id, name FROM heroes WHERE id IN ({placeholders}) AND is_alive = 1",
            hero_ids,
        ).fetchall()
        if len(rows) != len(set(hero_ids)):
            raise HTTPException(status_code=400, detail="Some of that crew cannot fly — dead or unknown.")

        now = datetime.now(timezone.utc)
        returns_at = now + timedelta(hours=cfg["hours"])
        _save(conn, {
            "lane": lane_key,
            "ship_tier": tier,
            "crew": [r["id"] for r in rows],
            "crew_names": [r["name"] for r in rows],
            "departed_at": now.isoformat(),
            "returns_at": returns_at.isoformat(),
        })
        return {"ok": True, "lane": lane_key, "returns_in_seconds": int(cfg["hours"] * 3600),
                "message": f"{cfg['name']} — the hull slips its moorings. Returns in {cfg['hours']} hours."}


def collect(lane_key: str) -> dict:
    with db() as conn:
        state = _state(conn)
        if state.get("lane") != lane_key:
            raise HTTPException(status_code=400, detail="No hull is out on that lane.")
        now = datetime.now(timezone.utc)
        returns_at = datetime.fromisoformat(state["returns_at"])
        if now < returns_at:
            raise HTTPException(status_code=400, detail="The hull is still out — recall it early for half spoils, or wait.")
        reward = _roll_reward(lane_key, state.get("ship_tier", 1), len(state.get("crew", [])))
        applied = _apply_reward(conn, reward)
        _save(conn, {})
        return {"ok": True, "lane": lane_key, "reward": applied,
                "message": f"{LANES[lane_key]['name']} — the hull returns heavy with spoils."}


def recall(lane_key: str) -> dict:
    with db() as conn:
        state = _state(conn)
        if state.get("lane") != lane_key:
            raise HTTPException(status_code=400, detail="No hull is out on that lane.")
        reward = _roll_reward(lane_key, state.get("ship_tier", 1), len(state.get("crew", [])))
        applied = _apply_reward(conn, reward, half=True)
        _save(conn, {})
        return {"ok": True, "lane": lane_key, "reward": applied,
                "message": f"{LANES[lane_key]['name']} — recalled early. Half spoils, but the hull is home."}
