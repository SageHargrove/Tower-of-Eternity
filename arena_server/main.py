"""
Arena server — a small, separate FastAPI app from the main game backend.
Hosts PvP challenges between players using client-submitted, already-fully-
resolved hero stat snapshots. Never touches any player's local save file;
this process owns nothing but arena.db (player accounts/tokens + match
history). See arena_server/database.py and combat.py for why.
"""
import os
import secrets
import time
import json

import bcrypt
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import db, init_db
from combat import resolve_arena_fight
from elo import update_elo

TOKEN_LIFETIME_SECONDS = 7 * 24 * 60 * 60  # 7 days

import re

USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,20}$")
MAX_TEAM_SIZE = 5
MAX_TEAM_JSON_BYTES = 64 * 1024   # a legit 5-hero snapshot is a few KB
MAX_MARKET_JSON_BYTES = 16 * 1024
MAX_GEM_COST = 1000               # limits the cross-account gem-inbox exploit blast radius
MAX_REPORTED_FLOOR = 1000

# Admin actions require ARENA_ADMIN_KEY in the server's environment — the
# old hardcoded "secret_admin_key_123" meant anyone reading the public repo
# could wipe every player's season.
ADMIN_KEY = os.environ.get("ARENA_ADMIN_KEY")

# Naive in-memory login throttle: 5 failures locks a username out for 60s.
# Resets on process restart — fine for the friends-scale v1 this serves.
_login_failures: dict[str, list] = {}  # username -> [fail_count, lock_until_ts]
LOGIN_MAX_FAILS = 5
LOGIN_LOCKOUT_SECONDS = 60

app = FastAPI(title="Tower of Eternity — Arena Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup():
    init_db()


class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class SubmitTeamRequest(BaseModel):
    team: list[dict]


class ChallengeRequest(BaseModel):
    opponent: str


class UpdateFloorRequest(BaseModel):
    highest_floor: int


def _require_player(authorization: str | None) -> str:
    """Validates the Bearer token from the Authorization header, returns
    the owning username. Raises 401 on anything wrong."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.removeprefix("Bearer ").strip()
    with db() as conn:
        row = conn.execute(
            "SELECT username, token_expiry FROM arena_players WHERE token = ?", (token,)
        ).fetchone()
    if not row:
        raise HTTPException(status_code=401, detail="Invalid token")
    if row["token_expiry"] is None or row["token_expiry"] < time.time():
        raise HTTPException(status_code=401, detail="Token expired, please log in again")
    return row["username"]


@app.post("/arena/register")
def register(req: RegisterRequest):
    username = req.username.strip()
    if not username or not req.password:
        raise HTTPException(status_code=400, detail="Username and password are required")
    if not USERNAME_RE.match(username):
        raise HTTPException(status_code=400, detail="Username must be 3-20 characters: letters, digits, underscore")
    if len(req.password) < 6 or len(req.password) > 128:
        raise HTTPException(status_code=400, detail="Password must be 6-128 characters")
    password_hash = bcrypt.hashpw(req.password.encode(), bcrypt.gensalt()).decode()
    with db() as conn:
        existing = conn.execute(
            "SELECT username FROM arena_players WHERE username = ?", (username,)
        ).fetchone()
        if existing:
            raise HTTPException(status_code=409, detail="Username already taken")
        conn.execute(
            "INSERT INTO arena_players (username, password_hash) VALUES (?, ?)",
            (username, password_hash),
        )
    return {"status": "registered", "username": username}


@app.post("/arena/login")
def login(req: LoginRequest):
    uname = req.username.strip()

    # Throttle brute-force attempts per username.
    entry = _login_failures.get(uname)
    if entry and entry[1] > time.time():
        raise HTTPException(status_code=429, detail="Too many failed attempts — try again in a minute")

    with db() as conn:
        row = conn.execute(
            "SELECT username, password_hash FROM arena_players WHERE username = ?",
            (uname,),
        ).fetchone()
        if not row or not bcrypt.checkpw(req.password.encode(), row["password_hash"].encode()):
            fails = (_login_failures.get(uname) or [0, 0])[0] + 1
            lock_until = time.time() + LOGIN_LOCKOUT_SECONDS if fails >= LOGIN_MAX_FAILS else 0
            _login_failures[uname] = [0 if lock_until else fails, lock_until]
            raise HTTPException(status_code=401, detail="Invalid username or password")
        _login_failures.pop(uname, None)
        token = secrets.token_hex(32)
        expiry = time.time() + TOKEN_LIFETIME_SECONDS
        conn.execute(
            "UPDATE arena_players SET token = ?, token_expiry = ? WHERE username = ?",
            (token, expiry, row["username"]),
        )
    return {"token": token, "username": row["username"]}


@app.post("/arena/submit_team")
def submit_team(req: SubmitTeamRequest, authorization: str | None = Header(default=None)):
    """Stores the caller's current best team snapshot — the team an
    opponent's challenge will be resolved against. The client computes this
    snapshot exactly as it already does for a normal Tower floor; the
    server does no stat recomputation (see the known-risk note in combat.py
    / the arena plan: a modified client could inflate stats — accepted
    for a friends-scale v1)."""
    if not req.team:
        raise HTTPException(status_code=400, detail="Team cannot be empty")
    if len(req.team) > MAX_TEAM_SIZE:
        raise HTTPException(status_code=400, detail=f"Teams are at most {MAX_TEAM_SIZE} heroes")
    if not all(isinstance(h, dict) for h in req.team):
        raise HTTPException(status_code=400, detail="Malformed team payload")
    payload = json.dumps(req.team)
    if len(payload.encode()) > MAX_TEAM_JSON_BYTES:
        raise HTTPException(status_code=400, detail="Team payload too large")
    username = _require_player(authorization)
    with db() as conn:
        conn.execute(
            "UPDATE arena_players SET team_json = ? WHERE username = ?",
            (payload, username),
        )
    return {"status": "team submitted", "team_size": len(req.team)}


@app.post("/arena/challenge")
def challenge(req: ChallengeRequest, authorization: str | None = Header(default=None)):
    username = _require_player(authorization)
    opponent = req.opponent.strip()
    if opponent == username:
        raise HTTPException(status_code=400, detail="You can't challenge yourself")

    with db() as conn:
        me = conn.execute(
            "SELECT team_json FROM arena_players WHERE username = ?", (username,)
        ).fetchone()
        them = conn.execute(
            "SELECT team_json FROM arena_players WHERE username = ?", (opponent,)
        ).fetchone()
    if not them:
        raise HTTPException(status_code=404, detail=f"No such player: {opponent}")
    if not me or not me["team_json"]:
        raise HTTPException(status_code=400, detail="Submit your team before challenging (POST /arena/submit_team)")
    if not them["team_json"]:
        raise HTTPException(status_code=400, detail=f"{opponent} hasn't submitted a team yet")

    team_a = json.loads(me["team_json"])
    team_b = json.loads(them["team_json"])
    result = resolve_arena_fight(team_a, team_b)

    winner_username = username if result["winner"] == "heroes" else opponent
    loser_username = opponent if winner_username == username else username

    with db() as conn:
        elo_row_w = conn.execute("SELECT elo FROM arena_players WHERE username = ?", (winner_username,)).fetchone()
        elo_row_l = conn.execute("SELECT elo FROM arena_players WHERE username = ?", (loser_username,)).fetchone()
        new_winner_elo, new_loser_elo = update_elo(elo_row_w["elo"] or 1000, elo_row_l["elo"] or 1000)

        conn.execute(
            "UPDATE arena_players SET wins = wins + 1, elo = ? WHERE username = ?", (new_winner_elo, winner_username)
        )
        conn.execute(
            "UPDATE arena_players SET losses = losses + 1, elo = ? WHERE username = ?", (new_loser_elo, loser_username)
        )
        conn.execute(
            "INSERT INTO arena_matches (player1, player2, winner, log_json, timestamp) VALUES (?, ?, ?, ?, ?)",
            (username, opponent, winner_username, json.dumps(result.get("log", [])), time.time()),
        )

    return {
        "winner": winner_username,
        "loser": loser_username,
        "log": result.get("log", []),
        "turns": result.get("turns", []),
        "elo_change": {winner_username: new_winner_elo, loser_username: new_loser_elo},
    }


@app.post("/arena/matchmake")
def matchmake(authorization: str | None = Header(default=None)):
    username = _require_player(authorization)
    with db() as conn:
        me = conn.execute("SELECT wins, losses, elo, team_json FROM arena_players WHERE username = ?", (username,)).fetchone()
        if not me or not me["team_json"]:
            raise HTTPException(status_code=400, detail="Submit your team before matchmaking")

        my_elo = me["elo"] or 1000

        # Find opponent with the closest ELO rating — a true skill-based pairing
        # now that ELO exists, rather than the old raw net-wins proxy.
        opponent_row = conn.execute(
            """SELECT username, team_json, ABS(COALESCE(elo, 1000) - ?) as diff
               FROM arena_players
               WHERE username != ? AND team_json IS NOT NULL
               ORDER BY diff ASC
               LIMIT 1""",
            (my_elo, username)
        ).fetchone()

    if not opponent_row:
        raise HTTPException(status_code=404, detail="No suitable opponents found. Wait for others to join!")

    # We found an opponent. Proceed to run a challenge exactly like /arena/challenge
    opponent = opponent_row["username"]
    team_a = json.loads(me["team_json"])
    team_b = json.loads(opponent_row["team_json"])
    result = resolve_arena_fight(team_a, team_b)

    winner_username = username if result["winner"] == "heroes" else opponent
    loser_username = opponent if winner_username == username else username

    with db() as conn:
        elo_row_w = conn.execute("SELECT elo FROM arena_players WHERE username = ?", (winner_username,)).fetchone()
        elo_row_l = conn.execute("SELECT elo FROM arena_players WHERE username = ?", (loser_username,)).fetchone()
        new_winner_elo, new_loser_elo = update_elo(elo_row_w["elo"] or 1000, elo_row_l["elo"] or 1000)

        conn.execute("UPDATE arena_players SET wins = wins + 1, elo = ? WHERE username = ?", (new_winner_elo, winner_username))
        conn.execute("UPDATE arena_players SET losses = losses + 1, elo = ? WHERE username = ?", (new_loser_elo, loser_username))
        conn.execute(
            "INSERT INTO arena_matches (player1, player2, winner, log_json, timestamp) VALUES (?, ?, ?, ?, ?)",
            (username, opponent, winner_username, json.dumps(result.get("log", [])), time.time()),
        )

    return {
        "opponent": opponent,
        "winner": winner_username,
        "loser": loser_username,
        "log": result.get("log", []),
        "turns": result.get("turns", []),
        "elo_change": {winner_username: new_winner_elo, loser_username: new_loser_elo},
    }


@app.post("/arena/update_floor")
def update_floor(req: UpdateFloorRequest, authorization: str | None = Header(default=None)):
    username = _require_player(authorization)
    # Client-authoritative by design (the server can't verify a local climb),
    # but at least clamp to the game's actual floor range so the PvE
    # leaderboard can't display a 9-digit floor.
    if req.highest_floor < 1 or req.highest_floor > MAX_REPORTED_FLOOR:
        raise HTTPException(status_code=400, detail=f"Floor must be 1-{MAX_REPORTED_FLOOR}")
    with db() as conn:
        # Only update if it's strictly greater (so we don't accidentally revert)
        conn.execute(
            "UPDATE arena_players SET highest_floor = ? WHERE username = ? AND highest_floor < ?",
            (req.highest_floor, username, req.highest_floor)
        )
    return {"status": "floor updated", "highest_floor": req.highest_floor}


@app.get("/arena/leaderboard")
def leaderboard(limit: int = 20):
    with db() as conn:
        pvp_rows = conn.execute(
            "SELECT username, wins, losses, elo FROM arena_players "
            "ORDER BY COALESCE(elo, 1000) DESC LIMIT ?",
            (limit,),
        ).fetchall()
        pve_rows = conn.execute(
            "SELECT username, highest_floor FROM arena_players "
            "ORDER BY highest_floor DESC LIMIT ?",
            (limit,),
        ).fetchall()

    return {
        "leaderboard": [
            {"username": r["username"], "wins": r["wins"], "losses": r["losses"], "elo": r["elo"] or 1000}
            for r in pvp_rows
        ],
        "pve_leaderboard": [
            {"username": r["username"], "highest_floor": r["highest_floor"]}
            for r in pve_rows
        ]
    }


@app.get("/arena/health")
def health():
    return {"status": "ok"}


# ─── Seasons & Rewards ────────────────────────────────────────────

class ResetSeasonRequest(BaseModel):
    admin_key: str

@app.post("/arena/admin/reset_season")
def reset_season(req: ResetSeasonRequest):
    # Requires ARENA_ADMIN_KEY in the environment — disabled entirely when
    # unset. compare_digest avoids leaking the key length via timing.
    if not ADMIN_KEY:
        raise HTTPException(status_code=503, detail="Admin actions are not configured on this server")
    if not secrets.compare_digest(req.admin_key, ADMIN_KEY):
        raise HTTPException(status_code=403, detail="Forbidden")
        
    now = time.time()
    with db() as conn:
        # Rank by wins for PvP rewards
        pvp_rows = conn.execute("SELECT username, wins, losses FROM arena_players ORDER BY wins DESC, losses ASC LIMIT 100").fetchall()
        for i, row in enumerate(pvp_rows):
            rank = i + 1
            gems = 0
            if rank == 1:
                gems = 1500
            elif rank <= 3:
                gems = 1000
            elif rank <= 10:
                gems = 500
            elif rank <= 50:
                gems = 200
            else:
                gems = 50
                
            conn.execute(
                "INSERT INTO arena_season_rewards (username, season_end_date, reward_type, amount) VALUES (?, ?, ?, ?)",
                (row["username"], now, "gems", gems)
            )
            
        # Reset PvP scores
        conn.execute("UPDATE arena_players SET wins = 0, losses = 0")
        
    return {"status": "season_reset", "awarded_pvp_ranks": len(pvp_rows)}

@app.get("/arena/my_rewards")
def my_rewards(authorization: str | None = Header(default=None)):
    username = _require_player(authorization)
    with db() as conn:
        rows = conn.execute(
            "SELECT id, reward_type, amount, season_end_date FROM arena_season_rewards WHERE username = ? AND claimed = 0",
            (username,)
        ).fetchall()
        
    return {"rewards": [dict(r) for r in rows]}

class ClaimRewardRequest(BaseModel):
    reward_id: int

@app.post("/arena/claim_reward")
def claim_reward(req: ClaimRewardRequest, authorization: str | None = Header(default=None)):
    username = _require_player(authorization)
    with db() as conn:
        row = conn.execute(
            "SELECT id, reward_type, amount FROM arena_season_rewards WHERE id = ? AND username = ? AND claimed = 0",
            (req.reward_id, username)
        ).fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Reward not found or already claimed.")
            
        conn.execute("UPDATE arena_season_rewards SET claimed = 1 WHERE id = ?", (req.reward_id,))
        
    return {"status": "claimed", "reward_type": row["reward_type"], "amount": row["amount"]}


# ─── Training Market ──────────────────────────────────────────────

class ListTeacherRequest(BaseModel):
    hero_name: str
    hero_class: str
    hero_stats: dict
    hero_skills: list
    gem_cost: int

@app.post("/arena/market/list")
def list_teacher(req: ListTeacherRequest, authorization: str | None = Header(default=None)):
    username = _require_player(authorization)
    if req.gem_cost < 0 or req.gem_cost > MAX_GEM_COST:
        raise HTTPException(status_code=400, detail=f"Gem cost must be 0-{MAX_GEM_COST}.")
    if len(req.hero_name) > 40 or len(req.hero_class) > 40:
        raise HTTPException(status_code=400, detail="Hero name/class too long.")
    if len(json.dumps(req.hero_stats).encode()) > MAX_MARKET_JSON_BYTES or len(json.dumps(req.hero_skills).encode()) > MAX_MARKET_JSON_BYTES:
        raise HTTPException(status_code=400, detail="Listing payload too large.")
        
    with db() as conn:
        # Check how many they have listed to prevent spam
        count = conn.execute("SELECT COUNT(*) as c FROM training_market WHERE username = ?", (username,)).fetchone()["c"]
        if count >= 3:
            raise HTTPException(status_code=400, detail="You can only list up to 3 teachers at a time.")
            
        conn.execute(
            """INSERT INTO training_market 
               (username, hero_name, hero_class, hero_stats_json, hero_skills_json, gem_cost, listed_at) 
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (username, req.hero_name, req.hero_class, json.dumps(req.hero_stats), json.dumps(req.hero_skills), req.gem_cost, time.time())
        )
    return {"status": "listed"}

@app.get("/arena/market")
def get_training_market(authorization: str | None = Header(default=None)):
    _require_player(authorization)
    with db() as conn:
        rows = conn.execute("SELECT * FROM training_market ORDER BY listed_at DESC LIMIT 50").fetchall()
        
    return {"listings": [
        {
            "id": r["id"],
            "username": r["username"],
            "hero_name": r["hero_name"],
            "hero_class": r["hero_class"],
            "hero_stats": json.loads(r["hero_stats_json"]),
            "hero_skills": json.loads(r["hero_skills_json"]),
            "gem_cost": r["gem_cost"]
        } for r in rows
    ]}

class HireTeacherRequest(BaseModel):
    listing_id: int

@app.post("/arena/market/hire")
def hire_teacher(req: HireTeacherRequest, authorization: str | None = Header(default=None)):
    username = _require_player(authorization)
    with db() as conn:
        listing = conn.execute("SELECT * FROM training_market WHERE id = ?", (req.listing_id,)).fetchone()
        if not listing:
            raise HTTPException(status_code=404, detail="Listing not found.")
            
        if listing["username"] == username:
            raise HTTPException(status_code=400, detail="You cannot hire your own teacher.")
            
        # Payout the lister! We use the season rewards table as a generic inbox for now.
        if listing["gem_cost"] > 0:
            conn.execute(
                "INSERT INTO arena_season_rewards (username, season_end_date, reward_type, amount) VALUES (?, ?, ?, ?)",
                (listing["username"], time.time(), "gems", listing["gem_cost"])
            )
            
    return {
        "status": "hired", 
        "teacher": {
            "hero_name": listing["hero_name"],
            "hero_class": listing["hero_class"],
            "hero_stats": json.loads(listing["hero_stats_json"]),
            "hero_skills": json.loads(listing["hero_skills_json"]),
            "gem_cost": listing["gem_cost"]
        }
    }
