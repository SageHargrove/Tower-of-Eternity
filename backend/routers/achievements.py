from fastapi import APIRouter, HTTPException
from database import db
from services.achievement_service import get_achievements_with_progress, claim_achievement
from pydantic import BaseModel

router = APIRouter()


@router.get("/")
def list_achievements():
    with db() as conn:
        return {"achievements": get_achievements_with_progress(conn)}


class ClaimRequest(BaseModel):
    achievement_id: str


@router.post("/claim")
def claim(req: ClaimRequest):
    with db() as conn:
        result = claim_achievement(conn, req.achievement_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


# ─── Daily & Weekly Rites (the DAILIES / WEEKLIES tabs) ──────────────

@router.get("/rites")
def get_rites():
    from services.quests_service import rites
    return rites()


class RiteClaimRequest(BaseModel):
    quest_id: str


@router.post("/rites/claim")
def claim_rite(req: RiteClaimRequest):
    from services.quests_service import claim as claim_quest
    try:
        return claim_quest(req.quest_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
