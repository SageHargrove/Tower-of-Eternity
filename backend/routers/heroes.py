from fastapi import APIRouter, HTTPException
from database import db
from pydantic import BaseModel

router = APIRouter()

def row_to_hero(row) -> dict:
    return dict(row)

@router.get("/")
def list_heroes(alive_only: bool = False):
    with db() as conn:
        query = "SELECT * FROM heroes"
        if alive_only:
            query += " WHERE is_alive = 1"
        query += " ORDER BY birth_star DESC, created_at DESC"
        rows = conn.execute(query).fetchall()
    return [row_to_hero(r) for r in rows]

@router.get("/{hero_id}")
def get_hero(hero_id: int):
    with db() as conn:
        row = conn.execute("SELECT * FROM heroes WHERE id = ?", (hero_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Hero not found")
    return row_to_hero(row)

@router.delete("/{hero_id}")
def dismiss_hero(hero_id: int):
    """Dismiss (remove) a hero from roster. Not the same as death."""
    with db() as conn:
        conn.execute("DELETE FROM heroes WHERE id = ?", (hero_id,))
    return {"ok": True}

class TeamUpdate(BaseModel):
    hero_ids: list[int]

@router.post("/team/set")
def set_team(data: TeamUpdate):
    if len(data.hero_ids) > 5:
        raise HTTPException(status_code=400, detail="Max 5 heroes per team")
    with db() as conn:
        # Clear team
        conn.execute("UPDATE heroes SET is_on_team = 0")
        # Set new team
        for hid in data.hero_ids:
            conn.execute("UPDATE heroes SET is_on_team = 1 WHERE id = ? AND is_alive = 1", (hid,))
    return {"ok": True, "team": data.hero_ids}

@router.get("/team/current")
def get_team():
    with db() as conn:
        rows = conn.execute(
            "SELECT * FROM heroes WHERE is_on_team = 1 AND is_alive = 1"
        ).fetchall()
    return [row_to_hero(r) for r in rows]
