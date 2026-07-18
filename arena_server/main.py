"""
Arena server — a small, separate FastAPI app from the main game backend.
Hosts PvP challenges between players using client-submitted, already-fully-
resolved hero stat snapshots. Never touches any player's local save file;
this process owns nothing but arena.db (player accounts/tokens + match
history). See arena_server/database.py and combat.py for why.
"""
import os
import random
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
from models import (
    WORLD_SIZE, DEFAULT_SCOUT_RADIUS, MAX_SCOUT_RADIUS, MAX_DEFENSE_JSON_BYTES,
    RaidOptInRequest, SubmitDefenseRequest, ScoutRequest, RaidAttackRequest,
    ClaimPrisonerRequest, TOURNAMENT_FORMATS, TournamentRegisterRequest,
    BannerRequest,
)
from raids import resolve_siege, build_scout_report
import tournaments
import guilds
import chat

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
    with db() as conn:
        guilds.init_tables(conn)
        chat.init_tables(conn)


class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class AuthRegisterRequest(BaseModel):
    email: str
    username: str          # public display name / world identity
    password: str


class AuthLoginRequest(BaseModel):
    identifier: str        # email OR username
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


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _issue_token(conn, username: str) -> str:
    token = secrets.token_hex(32)
    conn.execute(
        "UPDATE arena_players SET token = ?, token_expiry = ? WHERE username = ?",
        (token, time.time() + TOKEN_LIFETIME_SECONDS, username),
    )
    return token


@app.get("/")
def root_status():
    """Human-friendly landing so browsing the arena URL doesn't look broken —
    the real API lives under /auth and /arena; the game client knows the way."""
    return {"service": "Tower of Eternity — World Server", "status": "ok",
            "hint": "This is the multiplayer API. Launch the game to play."}


@app.post("/auth/register")
def auth_register(req: AuthRegisterRequest):
    """Account creation for the startup login screen: email + display name +
    password. Issues a session token immediately (register == logged in)."""
    email = req.email.strip().lower()
    username = req.username.strip()
    if not EMAIL_RE.match(email):
        raise HTTPException(status_code=400, detail="Enter a valid email address")
    if not USERNAME_RE.match(username):
        raise HTTPException(status_code=400, detail="Display name must be 3-20 characters: letters, digits, underscore")
    if len(req.password) < 6 or len(req.password) > 128:
        raise HTTPException(status_code=400, detail="Password must be 6-128 characters")
    password_hash = bcrypt.hashpw(req.password.encode(), bcrypt.gensalt()).decode()
    with db() as conn:
        if conn.execute("SELECT 1 FROM arena_players WHERE username = ?", (username,)).fetchone():
            raise HTTPException(status_code=409, detail="Display name already taken")
        if conn.execute("SELECT 1 FROM arena_players WHERE email = ?", (email,)).fetchone():
            raise HTTPException(status_code=409, detail="An account with that email already exists")
        conn.execute(
            "INSERT INTO arena_players (username, email, password_hash) VALUES (?, ?, ?)",
            (username, email, password_hash),
        )
        token = _issue_token(conn, username)
    return {"token": token, "username": username, "email": email}


@app.post("/auth/login")
def auth_login(req: AuthLoginRequest):
    """Login by email or display name. Same throttle as the legacy endpoint."""
    ident = req.identifier.strip()
    key = ident.lower()
    entry = _login_failures.get(key)
    if entry and entry[1] > time.time():
        raise HTTPException(status_code=429, detail="Too many failed attempts — try again in a minute")
    with db() as conn:
        row = conn.execute(
            "SELECT username, email, password_hash FROM arena_players WHERE email = ? OR username = ?",
            (key, ident),
        ).fetchone()
        if not row or not bcrypt.checkpw(req.password.encode(), row["password_hash"].encode()):
            fails = (_login_failures.get(key) or [0, 0])[0] + 1
            lock_until = time.time() + LOGIN_LOCKOUT_SECONDS if fails >= LOGIN_MAX_FAILS else 0
            _login_failures[key] = [0 if lock_until else fails, lock_until]
            raise HTTPException(status_code=401, detail="Invalid credentials")
        _login_failures.pop(key, None)
        token = _issue_token(conn, row["username"])
    return {"token": token, "username": row["username"], "email": row["email"]}


@app.get("/auth/me")
def auth_me(authorization: str | None = Header(default=None)):
    """Session check for the startup screen: valid token -> identity."""
    username = _require_player(authorization)
    with db() as conn:
        row = conn.execute(
            "SELECT username, email, wins, losses, highest_floor FROM arena_players WHERE username = ?",
            (username,),
        ).fetchone()
    return dict(row)


@app.post("/auth/discord")
def auth_discord():
    """OAuth scaffold, same deal as Google: becomes live when
    DISCORD_CLIENT_ID is configured (system-browser OAuth -> code exchange ->
    upsert account by Discord email, issue session token)."""
    if not os.environ.get("DISCORD_CLIENT_ID"):
        raise HTTPException(status_code=501, detail="Discord sign-in is not configured on this server yet")
    raise HTTPException(status_code=501, detail="Discord sign-in verification not implemented yet")


@app.post("/auth/google")
def auth_google():
    """OAuth scaffold: becomes live when GOOGLE_CLIENT_ID is configured on
    the server (verify the posted id_token against Google's certs, upsert an
    account keyed by email, issue a session token). Deliberately 501 until
    then so the client can show the button as 'coming soon'."""
    if not os.environ.get("GOOGLE_CLIENT_ID"):
        raise HTTPException(status_code=501, detail="Google sign-in is not configured on this server yet")
    raise HTTPException(status_code=501, detail="Google sign-in verification not implemented yet")


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
        old_w, old_l = elo_row_w["elo"] or 1000, elo_row_l["elo"] or 1000
        new_winner_elo, new_loser_elo = update_elo(old_w, old_l)

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
        guilds.war_score(conn, winner_username, guilds.WAR_BOUT_SCORE)

    return {
        "winner": winner_username,
        "loser": loser_username,
        "log": result.get("log", []),
        "turns": result.get("turns", []),
        "elo_change": {winner_username: new_winner_elo, loser_username: new_loser_elo},
        # actual deltas — the old elo_change carried the NEW rating, which the
        # client displayed as "+1012"; keep both for stale clients.
        "elo_delta": {winner_username: new_winner_elo - old_w, loser_username: new_loser_elo - old_l},
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
        old_w, old_l = elo_row_w["elo"] or 1000, elo_row_l["elo"] or 1000
        new_winner_elo, new_loser_elo = update_elo(old_w, old_l)

        conn.execute("UPDATE arena_players SET wins = wins + 1, elo = ? WHERE username = ?", (new_winner_elo, winner_username))
        conn.execute("UPDATE arena_players SET losses = losses + 1, elo = ? WHERE username = ?", (new_loser_elo, loser_username))
        conn.execute(
            "INSERT INTO arena_matches (player1, player2, winner, log_json, timestamp) VALUES (?, ?, ?, ?, ?)",
            (username, opponent, winner_username, json.dumps(result.get("log", [])), time.time()),
        )
        guilds.war_score(conn, winner_username, guilds.WAR_BOUT_SCORE)

    return {
        "opponent": opponent,
        "winner": winner_username,
        "loser": loser_username,
        "log": result.get("log", []),
        "turns": result.get("turns", []),
        "elo_change": {winner_username: new_winner_elo, loser_username: new_loser_elo},
        "elo_delta": {winner_username: new_winner_elo - old_w, loser_username: new_loser_elo - old_l},
    }


@app.get("/arena/my_matches")
def my_matches(limit: int = 10, authorization: str | None = Header(default=None)):
    """The caller's recent bouts, newest first — feeds the RECENT BOUTS
    ledger so it survives a reload."""
    limit = max(1, min(25, limit))
    username = _require_player(authorization)
    with db() as conn:
        rows = conn.execute(
            "SELECT player1, player2, winner, timestamp FROM arena_matches "
            "WHERE player1 = ? OR player2 = ? ORDER BY id DESC LIMIT ?",
            (username, username, limit)).fetchall()
    return {"matches": [
        {"opponent": r["player2"] if r["player1"] == username else r["player1"],
         "won": r["winner"] == username, "winner": r["winner"], "at": r["timestamp"]}
        for r in rows
    ]}


@app.post("/arena/update_floor")
def update_floor(req: UpdateFloorRequest, authorization: str | None = Header(default=None)):
    username = _require_player(authorization)
    # Client-authoritative by design (the server can't verify a local climb),
    # but at least clamp to the game's actual floor range so the PvE
    # leaderboard can't display a 9-digit floor.
    if req.highest_floor < 1 or req.highest_floor > MAX_REPORTED_FLOOR:
        raise HTTPException(status_code=400, detail=f"Floor must be 1-{MAX_REPORTED_FLOOR}")
    with db() as conn:
        old = conn.execute("SELECT highest_floor FROM arena_players WHERE username = ?", (username,)).fetchone()
        old_floor = (old["highest_floor"] or 0) if old else 0
        # Only update if it's strictly greater (so we don't accidentally revert)
        conn.execute(
            "UPDATE arena_players SET highest_floor = ? WHERE username = ? AND highest_floor < ?",
            (req.highest_floor, username, req.highest_floor)
        )
        # Floors gained during a Lodge War bank war score for the guild.
        if req.highest_floor > old_floor:
            guilds.war_score(conn, username, (req.highest_floor - old_floor) * guilds.WAR_FLOOR_SCORE)
    return {"status": "floor updated", "highest_floor": req.highest_floor}


# ─── Guilds v1 (guilds.py; design: docs/guild-social-design.md) ─────

class FoundGuildRequest(BaseModel):
    name: str
    motto: str = ""
    banner: dict = {}

class GuildApplyRequest(BaseModel):
    guild_id: int
    message: str = ""

class GuildDecideRequest(BaseModel):
    app_id: int
    accept: bool

class GuildBuyRequest(BaseModel):
    item_id: str


@app.get("/guild/mine")
def guild_mine(authorization: str | None = Header(default=None)):
    username = _require_player(authorization)
    with db() as conn:
        return guilds.my_guild(conn, username)

@app.get("/guild/registry")
def guild_registry(authorization: str | None = Header(default=None)):
    _require_player(authorization)
    with db() as conn:
        return guilds.registry(conn)

@app.post("/guild/found")
def guild_found(req: FoundGuildRequest, authorization: str | None = Header(default=None)):
    username = _require_player(authorization)
    with db() as conn:
        return guilds.found_guild(conn, username, req.name, req.motto, req.banner)

@app.post("/guild/apply")
def guild_apply(req: GuildApplyRequest, authorization: str | None = Header(default=None)):
    username = _require_player(authorization)
    with db() as conn:
        return guilds.apply_to_guild(conn, username, req.guild_id, req.message)

@app.post("/guild/applications/decide")
def guild_decide(req: GuildDecideRequest, authorization: str | None = Header(default=None)):
    username = _require_player(authorization)
    with db() as conn:
        return guilds.decide_application(conn, username, req.app_id, req.accept)

@app.post("/guild/leave")
def guild_leave(authorization: str | None = Header(default=None)):
    username = _require_player(authorization)
    with db() as conn:
        return guilds.leave_guild(conn, username)

@app.post("/guild/checkin")
def guild_checkin(authorization: str | None = Header(default=None)):
    username = _require_player(authorization)
    with db() as conn:
        return guilds.checkin(conn, username)

@app.post("/guild/boss/strike")
def guild_boss_strike(authorization: str | None = Header(default=None)):
    username = _require_player(authorization)
    with db() as conn:
        return guilds.strike_boss(conn, username)

@app.get("/guild/shop")
def guild_shop(authorization: str | None = Header(default=None)):
    username = _require_player(authorization)
    with db() as conn:
        return guilds.shop(conn, username)

@app.post("/guild/shop/buy")
def guild_shop_buy(req: GuildBuyRequest, authorization: str | None = Header(default=None)):
    username = _require_player(authorization)
    with db() as conn:
        return guilds.shop_buy(conn, username, req.item_id)


@app.get("/guild/perks")
def guild_perks(authorization: str | None = Header(default=None)):
    username = _require_player(authorization)
    with db() as conn:
        return guilds.perks(conn, username)


class PerkBuyRequest(BaseModel):
    perk_id: str


@app.post("/guild/perks/buy")
def guild_perk_buy(req: PerkBuyRequest, authorization: str | None = Header(default=None)):
    username = _require_player(authorization)
    with db() as conn:
        return guilds.perk_buy(conn, username, req.perk_id)


@app.get("/guild/war")
def guild_war(authorization: str | None = Header(default=None)):
    username = _require_player(authorization)
    with db() as conn:
        return guilds.war_status(conn, username)


# ─── The Herald's Wire (chat) ────────────────────────────────────────

class ChatSendRequest(BaseModel):
    channel: str
    text: str
    to: str | None = None


@app.post("/chat/send")
def chat_send(req: ChatSendRequest, authorization: str | None = Header(default=None)):
    username = _require_player(authorization)
    with db() as conn:
        return chat.send(conn, username, req.channel, req.text, req.to)


@app.get("/chat/fetch")
def chat_fetch(channel: str, since: int = 0, authorization: str | None = Header(default=None)):
    username = _require_player(authorization)
    with db() as conn:
        return chat.fetch(conn, username, channel, since)


@app.get("/chat/whispers")
def chat_whispers(authorization: str | None = Header(default=None)):
    username = _require_player(authorization)
    with db() as conn:
        return chat.whisper_threads(conn, username)


@app.get("/chat/whisper/{other}")
def chat_whisper(other: str, since: int = 0, authorization: str | None = Header(default=None)):
    username = _require_player(authorization)
    with db() as conn:
        return chat.whisper_thread(conn, username, other, since)


# ─── Social: allies ──────────────────────────────────────────────────

class AllyRequest(BaseModel):
    username: str

class AllyDecideRequest(BaseModel):
    username: str
    accept: bool


@app.get("/social/allies")
def social_allies(authorization: str | None = Header(default=None)):
    username = _require_player(authorization)
    with db() as conn:
        return guilds.ally_list(conn, username)

@app.post("/social/invite")
def social_invite(req: AllyRequest, authorization: str | None = Header(default=None)):
    username = _require_player(authorization)
    with db() as conn:
        return guilds.ally_invite(conn, username, req.username)

@app.post("/social/decide")
def social_decide(req: AllyDecideRequest, authorization: str | None = Header(default=None)):
    username = _require_player(authorization)
    with db() as conn:
        return guilds.ally_decide(conn, username, req.username, req.accept)

@app.post("/social/remove")
def social_remove(req: AllyRequest, authorization: str | None = Header(default=None)):
    username = _require_player(authorization)
    with db() as conn:
        return guilds.ally_remove(conn, username, req.username)


MAX_BANNER_JSON_BYTES = 400 * 1024  # paint layer can be a canvas data-URL


@app.post("/arena/banner")
def set_banner(req: BannerRequest, authorization: str | None = Header(default=None)):
    """Carry the player's Banner Studio standard so opponents see it on
    leaderboards and the raid map (the PvP mind-games use case)."""
    username = _require_player(authorization)
    payload = json.dumps(req.banner)
    if len(payload.encode()) > MAX_BANNER_JSON_BYTES:
        raise HTTPException(status_code=400, detail="Banner payload too large")
    with db() as conn:
        conn.execute("UPDATE arena_players SET banner_json = ? WHERE username = ?", (payload, username))
    return {"ok": True}


def _banner_of(row) -> dict | None:
    try:
        return json.loads(row["banner_json"]) if row["banner_json"] else None
    except (json.JSONDecodeError, TypeError):
        return None


@app.get("/arena/leaderboard")
def leaderboard(limit: int = 20):
    with db() as conn:
        pvp_rows = conn.execute(
            "SELECT username, wins, losses, elo, banner_json FROM arena_players "
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
            {"username": r["username"], "wins": r["wins"], "losses": r["losses"], "elo": r["elo"] or 1000,
             "banner": _banner_of(r)}
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


# ─── Raids (PvP Base Sieges) ──────────────────────────────────────
# Opt-in ecosystem: raiders get a spot on the world map, the ability to
# launch sieges, and a target painted on their own base. Same
# client-snapshot trust model as /arena/submit_team (see that docstring) —
# the defender's base_defense/team and the attacker's team are both
# computed by each player's own local backend and shipped here.

RAID_STEAL_PCT = 0.20            # % of the defender's reported unspent gold / farm ingredients
RAID_SHIELD_SECONDS = 2 * 3600   # a freshly-raided base can't be hit again immediately
MAX_RAID_TEAM_SIZE = MAX_TEAM_SIZE


def _get_player(conn, username: str):
    return conn.execute("SELECT * FROM arena_players WHERE username = ?", (username,)).fetchone()


def _push_raid_event(conn, username: str, event_type: str, payload: dict):
    conn.execute(
        "INSERT INTO raid_events (username, event_type, payload_json, created_at) VALUES (?, ?, ?, ?)",
        (username, event_type, json.dumps(payload), time.time()),
    )


@app.post("/arena/raid/opt_in")
def raid_opt_in(req: RaidOptInRequest, authorization: str | None = Header(default=None)):
    """Toggle raid participation. Opting in places the base at a random free
    cell on the world grid — you can now launch raids, and be raided."""
    username = _require_player(authorization)
    with db() as conn:
        me = _get_player(conn, username)
        if req.enable:
            x, y = me["coord_x"], me["coord_y"]
            if x is None or y is None:
                taken = {(r["coord_x"], r["coord_y"]) for r in conn.execute(
                    "SELECT coord_x, coord_y FROM arena_players WHERE coord_x IS NOT NULL"
                ).fetchall()}
                for _ in range(2000):
                    x, y = random.randrange(WORLD_SIZE), random.randrange(WORLD_SIZE)
                    if (x, y) not in taken:
                        break
                conn.execute(
                    "UPDATE arena_players SET is_raider = 1, coord_x = ?, coord_y = ? WHERE username = ?",
                    (x, y, username),
                )
            else:
                conn.execute("UPDATE arena_players SET is_raider = 1 WHERE username = ?", (username,))
            return {"status": "opted_in", "coordinates": {"x": x, "y": y}}
        else:
            # Opting out delists you as a target AND revokes your raid rights;
            # coordinates are kept so re-opting-in returns you to your plot.
            conn.execute("UPDATE arena_players SET is_raider = 0 WHERE username = ?", (username,))
            return {"status": "opted_out"}


@app.post("/arena/raid/submit_defense")
def submit_defense(req: SubmitDefenseRequest, authorization: str | None = Header(default=None)):
    """Store the caller's defense snapshot: base_defense breakdown (wall/
    garrison/ship/beasts), the hypothetical strongest defending team (top 5),
    docked ship tier, and the lootable resources a successful raider can
    steal from. Built by the caller's local backend (GET /raid/defense_snapshot)."""
    username = _require_player(authorization)
    if not req.defenders:
        raise HTTPException(status_code=400, detail="Defense needs at least one defending hero")
    if len(req.defenders) > MAX_RAID_TEAM_SIZE:
        raise HTTPException(status_code=400, detail=f"At most {MAX_RAID_TEAM_SIZE} defenders")
    if not all(isinstance(h, dict) for h in req.defenders) or not isinstance(req.base_defense, dict):
        raise HTTPException(status_code=400, detail="Malformed defense payload")
    payload = json.dumps({
        "defenders": req.defenders,
        "base_defense": req.base_defense,
        "ship_tier": max(0, min(5, int(req.ship_tier or 0))),
        "lootable": {
            "gold": max(0, int(req.lootable.get("gold", 0) or 0)),
            "ingredients": max(0, int(req.lootable.get("ingredients", 0) or 0)),
        },
        "counter_intel": {
            "total": max(0.0, float(req.counter_intel.get("total", 0) or 0)),
            "breakdown": req.counter_intel.get("breakdown", {}),
        },
    })
    if len(payload.encode()) > MAX_DEFENSE_JSON_BYTES:
        raise HTTPException(status_code=400, detail="Defense payload too large")
    with db() as conn:
        conn.execute(
            "UPDATE arena_players SET defense_json = ?, defense_updated_at = ? WHERE username = ?",
            (payload, time.time(), username),
        )
    return {"status": "defense submitted", "defenders": len(req.defenders)}


@app.get("/arena/raid/map")
def raid_map(radius: int = DEFAULT_SCOUT_RADIUS, authorization: str | None = Header(default=None)):
    """Nearby opted-in bases within a coordinate radius (Chebyshev box) of
    the caller's own base. Defense details stay hidden until scouted."""
    username = _require_player(authorization)
    radius = max(1, min(MAX_SCOUT_RADIUS, radius))
    now = time.time()
    with db() as conn:
        me = _get_player(conn, username)
        if not me["is_raider"] or me["coord_x"] is None:
            raise HTTPException(status_code=400, detail="Opt in to raiding first (POST /arena/raid/opt_in)")
        rows = conn.execute(
            """SELECT username, coord_x, coord_y, elo, highest_floor, defense_json, last_raided_at, banner_json
               FROM arena_players
               WHERE is_raider = 1 AND username != ?
                 AND coord_x BETWEEN ? AND ? AND coord_y BETWEEN ? AND ?""",
            (username, me["coord_x"] - radius, me["coord_x"] + radius,
             me["coord_y"] - radius, me["coord_y"] + radius),
        ).fetchall()
    return {
        "my_coordinates": {"x": me["coord_x"], "y": me["coord_y"]},
        "world_size": WORLD_SIZE,
        "radius": radius,
        "bases": [
            {
                "username": r["username"],
                "x": r["coord_x"], "y": r["coord_y"],
                "distance": max(abs(r["coord_x"] - me["coord_x"]), abs(r["coord_y"] - me["coord_y"])),
                "elo": r["elo"] or 1000,
                "highest_floor": r["highest_floor"],
                "has_defense": bool(r["defense_json"]),
                "banner": _banner_of(r),
                "shielded": bool(r["last_raided_at"] and now - r["last_raided_at"] < RAID_SHIELD_SECONDS),
            }
            for r in rows
        ],
    }


@app.post("/arena/raid/scout")
def raid_scout(req: ScoutRequest, authorization: str | None = Header(default=None)):
    """Scout a target before committing to a siege. Not a flat info-dump:
    the caller's recon rating (scout_power, from their local backend's
    /raid/pay_scout — best Scout-line hero + Mage Tower scrying + battleship
    aerial recon) is graded against the target's counter-intel (patrols,
    wards, counter-spies), and the resulting intel tier (0-4) decides how
    much of the defense report is revealed — from a vague impression through
    a full dossier (see raids.build_scout_report). The Gold/Aether fee is
    charged by the scout's own local backend before this call — same
    client-side economy split as the Training Market's gem cost."""
    username = _require_player(authorization)
    target = req.target.strip()
    if target == username:
        raise HTTPException(status_code=400, detail="That's your own base")
    with db() as conn:
        them = _get_player(conn, target)
    if not them or not them["is_raider"]:
        raise HTTPException(status_code=404, detail=f"No raidable base for: {target}")
    if not them["defense_json"]:
        raise HTTPException(status_code=400, detail=f"{target} hasn't submitted a defense yet")
    defense = json.loads(them["defense_json"])
    # Fuzz-seed on (scout, target, defense version): re-scouting the same
    # defense repeats the same wrong numbers — the noise can't be averaged
    # away — but a resubmitted defense rolls fresh fuzz.
    seed = f"{username}:{target}:{them['defense_updated_at']}"
    report = build_scout_report(defense, req.scout_power, seed)
    report["target"] = target
    return report


@app.post("/arena/raid/attack")
def raid_attack(req: RaidAttackRequest, authorization: str | None = Header(default=None)):
    """Launch the siege. Resolved server-side as a real combat sim with both
    sides' stats shifted by their Base/Ship advantages (see raids.py). The
    victor — invader or defender who repelled them — earns the right to take
    one prisoner from the losing side (POST /arena/raid/claim_prisoner)."""
    username = _require_player(authorization)
    target = req.target.strip()
    if target == username:
        raise HTTPException(status_code=400, detail="You can't raid your own base")
    if not req.team or len(req.team) > MAX_RAID_TEAM_SIZE or not all(isinstance(h, dict) for h in req.team):
        raise HTTPException(status_code=400, detail=f"Attack team must be 1-{MAX_RAID_TEAM_SIZE} hero dicts")
    if len(json.dumps(req.team).encode()) > MAX_TEAM_JSON_BYTES:
        raise HTTPException(status_code=400, detail="Team payload too large")

    now = time.time()
    with db() as conn:
        me = _get_player(conn, username)
        them = _get_player(conn, target)
        if not me["is_raider"]:
            raise HTTPException(status_code=400, detail="Opt in to raiding first (POST /arena/raid/opt_in)")
        if not them or not them["is_raider"]:
            raise HTTPException(status_code=404, detail=f"No raidable base for: {target}")
        if not them["defense_json"]:
            raise HTTPException(status_code=400, detail=f"{target} hasn't submitted a defense yet")
        if them["last_raided_at"] and now - them["last_raided_at"] < RAID_SHIELD_SECONDS:
            mins = int((RAID_SHIELD_SECONDS - (now - them["last_raided_at"])) / 60)
            raise HTTPException(status_code=429, detail=f"{target}'s base is still recovering from the last raid ({mins}m shield left)")

    defense = json.loads(them["defense_json"])
    result = resolve_siege(
        attacker_team=req.team,
        attacker_ship_tier=max(0, min(5, int(req.ship_tier or 0))),
        defender_team=defense["defenders"],
        base_defense=defense.get("base_defense", {}),
        defender_ship_tier=defense.get("ship_tier", 0),
    )

    attacker_won = result["winner"] == "heroes"
    winner, loser = (username, target) if attacker_won else (target, username)
    losing_team = defense["defenders"] if attacker_won else req.team

    spoils = {"gold": 0, "ingredients": 0}
    if attacker_won:
        lootable = defense.get("lootable", {})
        spoils["gold"] = int((lootable.get("gold", 0) or 0) * RAID_STEAL_PCT)
        spoils["ingredients"] = int((lootable.get("ingredients", 0) or 0) * RAID_STEAL_PCT)

    # Survivors of the losing side (they're captured candidates, not corpses:
    # siege knockouts aren't permanent deaths). If the whole losing side was
    # wiped in the sim, every member is a candidate — knocked out and at the
    # victor's mercy is the fiction either way.
    candidates = [
        {
            "id": h.get("id"), "name": h.get("name"), "hero_class": h.get("hero_class"),
            "level": h.get("level", 1), "affinity": h.get("affinity", 50),
            "snapshot": h,
        }
        for h in losing_team
    ]

    with db() as conn:
        cur = conn.execute(
            """INSERT INTO raids (attacker, defender, winner, spoils_json, capture_candidates_json, log_json, timestamp)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (username, target, winner, json.dumps(spoils), json.dumps(candidates),
             json.dumps(result.get("log", [])), now),
        )
        raid_id = cur.lastrowid
        conn.execute("UPDATE arena_players SET last_raided_at = ? WHERE username = ?", (now, target))
        if attacker_won:
            conn.execute("UPDATE arena_players SET raid_wins = raid_wins + 1 WHERE username = ?", (username,))
            conn.execute("UPDATE arena_players SET defense_losses = defense_losses + 1 WHERE username = ?", (target,))
        else:
            conn.execute("UPDATE arena_players SET raid_losses = raid_losses + 1 WHERE username = ?", (username,))
            conn.execute("UPDATE arena_players SET defense_wins = defense_wins + 1 WHERE username = ?", (target,))
        # The defender wasn't online for this — their inbox tells their client
        # what to apply locally (resource losses; capture comes separately).
        _push_raid_event(conn, target, "raided", {
            "raid_id": raid_id,
            "attacker": username,
            "defended_successfully": not attacker_won,
            "gold_lost": spoils["gold"],
            "ingredients_lost": spoils["ingredients"],
        })

    return {
        "raid_id": raid_id,
        "winner": winner,
        "loser": loser,
        "attacker_won": attacker_won,
        "spoils": spoils,
        "capture_candidates": [
            {k: c[k] for k in ("id", "name", "hero_class", "level", "affinity")}
            for c in candidates
        ] if winner == username else [],
        "siege": result.get("siege"),
        "log": result.get("log", []),
        "turns": result.get("turns", []),
    }


@app.post("/arena/raid/claim_prisoner")
def claim_prisoner(req: ClaimPrisonerRequest, authorization: str | None = Header(default=None)):
    """The raid's victor picks ONE surviving hero from the losing side to
    take prisoner. Returns the full hero snapshot for local integration —
    the captive keeps their original loyalty, so a high-affinity hero enters
    the Rebellious Phase on arrival (see backend /raid/integrate_prisoner)."""
    username = _require_player(authorization)
    with db() as conn:
        raid = conn.execute("SELECT * FROM raids WHERE id = ?", (req.raid_id,)).fetchone()
        if not raid:
            raise HTTPException(status_code=404, detail="Raid not found")
        if raid["winner"] != username:
            raise HTTPException(status_code=403, detail="Only the raid's victor may take prisoners")
        if raid["prisoner_claimed"]:
            raise HTTPException(status_code=409, detail="A prisoner was already taken from this raid")
        candidates = json.loads(raid["capture_candidates_json"] or "[]")
        chosen = next((c for c in candidates if c.get("id") == req.hero_id), None)
        if not chosen:
            raise HTTPException(status_code=404, detail="That hero isn't among the raid's capture candidates")
        loser = raid["defender"] if raid["winner"] == raid["attacker"] else raid["attacker"]
        conn.execute(
            "UPDATE raids SET prisoner_claimed = 1, prisoner_json = ? WHERE id = ?",
            (json.dumps(chosen), req.raid_id),
        )
        _push_raid_event(conn, loser, "hero_captured", {
            "raid_id": req.raid_id,
            "captor": username,
            "hero_id": chosen.get("id"),
            "hero_name": chosen.get("name"),
        })
    return {"status": "captured", "prisoner": chosen["snapshot"], "original_master": loser}


@app.get("/arena/raid/events")
def raid_events(authorization: str | None = Header(default=None)):
    """Unseen raid outcomes for the caller (their base was raided / a hero
    of theirs was captured). Marks them seen — the client applies each one
    to the local save (see backend /raid/apply_raid_event)."""
    username = _require_player(authorization)
    with db() as conn:
        rows = conn.execute(
            "SELECT id, event_type, payload_json, created_at FROM raid_events WHERE username = ? AND seen = 0 ORDER BY id ASC",
            (username,),
        ).fetchall()
        if rows:
            conn.execute("UPDATE raid_events SET seen = 1 WHERE username = ? AND seen = 0", (username,))
    return {"events": [
        {"id": r["id"], "type": r["event_type"], "payload": json.loads(r["payload_json"]), "at": r["created_at"]}
        for r in rows
    ]}


# ─── Server-Wide Tournaments ──────────────────────────────────────

@app.get("/arena/tournaments")
def tournaments_status(authorization: str | None = Header(default=None)):
    """Current week's tournament state: phase (registration Mon-Wed, battles
    Thu-Sat, payouts Sunday), per-format entry counts, the caller's own
    registrations, and standings once a bracket has resolved."""
    username = _require_player(authorization)
    with db() as conn:
        return tournaments.get_status(conn, username)


@app.post("/arena/tournament/register")
def tournament_register(req: TournamentRegisterRequest, authorization: str | None = Header(default=None)):
    """Submit a specific team to one of the week's brackets during the
    Registration Phase (Monday-Wednesday). Team size must match the format:
    1v1 Duels, 2v2 Pairs, 4v4 Warbands, or 5-hero Battle Royale."""
    username = _require_player(authorization)
    if req.format not in TOURNAMENT_FORMATS:
        raise HTTPException(status_code=400, detail=f"Unknown format. One of: {', '.join(TOURNAMENT_FORMATS)}")
    required = TOURNAMENT_FORMATS[req.format]
    if len(req.team) != required or not all(isinstance(h, dict) for h in req.team):
        raise HTTPException(status_code=400, detail=f"The {req.format} bracket takes exactly {required} hero(es)")
    if len(json.dumps(req.team).encode()) > MAX_TEAM_JSON_BYTES:
        raise HTTPException(status_code=400, detail="Team payload too large")
    with db() as conn:
        return tournaments.register(conn, username, req.format, req.team)


@app.get("/arena/tournament/standings")
def tournament_standings(format: str, week: str | None = None, authorization: str | None = Header(default=None)):
    """Bracket standings. During Thu-Sat this lazily runs the bracket's
    auto-battler rounds the first time anyone asks; on Sunday it also
    triggers payouts (top of the leaderboard gets Summon Tickets and an
    exclusive Cosmetic in their reward inbox)."""
    _require_player(authorization)
    if format not in TOURNAMENT_FORMATS:
        raise HTTPException(status_code=400, detail=f"Unknown format. One of: {', '.join(TOURNAMENT_FORMATS)}")
    with db() as conn:
        return tournaments.get_standings(conn, format, week)


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
