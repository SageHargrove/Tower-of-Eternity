"""
Pydantic request/response models for the arena server's Raid (PvP base
siege) and Tournament systems, plus the raid-profile shape stored on
arena_players (is_raider + coord_x/coord_y + defense_json).

Same trust model as the rest of the arena server (see main.py's
submit_team): every stat here is a client-submitted snapshot the player's
own local backend computed — the server validates shape/size, never
recomputes. Accepted for the friends-scale v1 this serves.
"""
from pydantic import BaseModel, Field

# World map is a fixed square grid; opted-in players get a random free cell.
WORLD_SIZE = 64                 # coordinates run 0..WORLD_SIZE-1 on both axes
DEFAULT_SCOUT_RADIUS = 10       # /arena/raid/map default search box (Chebyshev)
MAX_SCOUT_RADIUS = 20

MAX_DEFENSE_JSON_BYTES = 96 * 1024   # 5 defenders + ratings is a few KB


class RaidOptInRequest(BaseModel):
    enable: bool


class SubmitDefenseRequest(BaseModel):
    """The defender-side snapshot a raid resolves against, computed by the
    submitter's own local backend (GET /raid/defense_snapshot there):
      - defenders: up to 5 fully-resolved hero dicts (the hypothetical
        strongest defending team)
      - base_defense: ship_service.get_base_defense() breakdown
        {wall, garrison, ship, beasts, total}
      - ship_tier: docked battleship tier (0 = none)
      - lootable: what a successful attacker can steal % of
    """
    defenders: list[dict]
    base_defense: dict
    ship_tier: int = 0
    lootable: dict = Field(default_factory=dict)  # {"gold": int, "ingredients": int}
    # Anti-scout rating (Wall/Bastion patrols, Mage Tower wards, counter-spy
    # heroes) — computed by the submitter's local backend alongside the rest.
    counter_intel: dict = Field(default_factory=dict)  # {"total": float, "breakdown": {...}}


class BannerRequest(BaseModel):
    # The local Banner Studio's banner_json (cloth/cut/frame_tier/sigil/
    # emblem/paint). Paint can be a canvas data-URL, so the size cap lives
    # at the endpoint rather than in the schema.
    banner: dict = Field(default_factory=dict)


class ScoutRequest(BaseModel):
    target: str
    # The scout's recon rating (best Scout-line hero + Mage Tower scrying +
    # battleship aerial recon), from the local backend's /raid/pay_scout.
    # Graded against the target's counter_intel to set the intel tier (0-4).
    scout_power: float = 0.0


class RaidAttackRequest(BaseModel):
    """Attacker brings their own already-resolved team snapshot (same shape
    submit_team uses) plus their battleship tier — attack power = team
    combat stats + battleship firepower."""
    target: str
    team: list[dict]
    ship_tier: int = 0


class ClaimPrisonerRequest(BaseModel):
    raid_id: int
    hero_id: int   # id within the losing side's capture-candidate snapshot


# ─── Tournaments ──────────────────────────────────────────────────

# Format → required team size. Battle Royale entries bring a full team and
# fight a multi-team free-for-all; the others are fixed-size brackets.
TOURNAMENT_FORMATS = {
    "duel": 1,       # 1v1 Duels
    "pairs": 2,      # 2v2 Pairs
    "warband": 4,    # 4v4 Warbands
    "royale": 5,     # Battle Royale free-for-all
}


class TournamentRegisterRequest(BaseModel):
    format: str
    team: list[dict]
