"""
Local-backend side of Arena support. This endpoint runs the exact same
hero stat-resolution pipeline (level/class/equipment/relics/bonds/base-floor
LP/passives) that a normal Tower floor fight uses, then hands the result
back to the client as a JSON snapshot — the client then ships that snapshot
to the separately-hosted arena_server via POST /arena/submit_team there.
This local backend never talks to the arena_server directly; it has no
knowledge of it at all, just like before Arena existed.
"""
from fastapi import APIRouter, HTTPException
from database import db
from services.combat_service import resolve_hero_stats

router = APIRouter()


@router.get("/team/{team_id}/snapshot")
def get_team_snapshot(team_id: int):
    with db() as conn:
        rows = conn.execute(
            "SELECT * FROM heroes WHERE is_on_team = ? AND is_alive = 1 ORDER BY team_position ASC, id ASC",
            (team_id,),
        ).fetchall()
    if not rows:
        raise HTTPException(status_code=400, detail="That team has no living heroes assigned")
    heroes = [dict(r) for r in rows]
    processed = resolve_hero_stats(heroes)
    return {"team": processed}


class ArenaResultRequest(BaseModel):
    win: bool
    new_elo: int

@router.post("/result")
def record_arena_result(req: ArenaResultRequest):
    """
    Called by the frontend after a match on the arena_server finishes,
    so the local save file can track wins/losses for achievements.
    """
    with db() as conn:
        if req.win:
            conn.execute("UPDATE base SET arena_wins = arena_wins + 1, arena_elo = ? WHERE id = 1", (req.new_elo,))
        else:
            conn.execute("UPDATE base SET arena_losses = arena_losses + 1, arena_elo = ? WHERE id = 1", (req.new_elo,))
    return {"ok": True}


from pydantic import BaseModel
import json

class ApplyTrainingRequest(BaseModel):
    student_id: int
    gem_cost: int
    teacher_stats: dict
    teacher_skills: list

@router.post("/apply_training")
def apply_training(req: ApplyTrainingRequest):
    """
    Called by the frontend after hiring a teacher from the Arena Server market.
    Deducts the gems locally, and grants stat/skill XP to the student based on
    the teacher's strength.
    """
    with db() as conn:
        base = conn.execute("SELECT gems FROM base WHERE id = 1").fetchone()
        if base["gems"] < req.gem_cost:
            raise HTTPException(status_code=400, detail=f"Not enough gems. Need {req.gem_cost}.")
            
        student = conn.execute("SELECT * FROM heroes WHERE id = ? AND is_alive = 1", (req.student_id,)).fetchone()
        if not student:
            raise HTTPException(status_code=404, detail="Student hero not found.")
            
        student = dict(student)

        # Deduct gems
        conn.execute("UPDATE base SET gems = gems - ? WHERE id = 1", (req.gem_cost,))

        # Stat growth: for each core stat where the teacher clearly outclasses
        # the student, the student gains a point (health gains two). Uses the
        # REAL stat columns — the old code referenced attack/speed columns that
        # don't exist on heroes, so hiring a teacher used to crash outright.
        # teacher_stats keys come from the Arena snapshot / listing payload;
        # tolerate a legacy listing that still sends attack/speed by mapping
        # them onto strength/agility.
        ts = dict(req.teacher_stats)
        ts.setdefault("strength", ts.get("attack", 0))
        ts.setdefault("agility", ts.get("speed", 0))
        ts.setdefault("endurance", ts.get("defense", 0))

        stat_cols = {
            "max_health": 2, "strength": 1, "intelligence": 1,
            "agility": 1, "endurance": 1, "willpower": 1,
        }
        stat_gains = {}
        for col, amount in stat_cols.items():
            if ts.get(col, 0) > (student.get(col) or 0):
                stat_gains[col] = amount

        # Skill XP — a shared skill with the teacher gets a big boost.
        skills = json.loads(student["skills"]) if student["skills"] else []
        teacher_skill_ids = {s.get("id") for s in req.teacher_skills}
        skill_log = []
        for s in skills:
            if s.get("id") in teacher_skill_ids:
                s["xp"] = s.get("xp", 0) + 100
                skill_log.append(f"{s['name']} XP +100")
                if s["xp"] >= s.get("max_xp", 100):
                    s["level"] = s.get("level", 1) + 1
                    s["xp"] -= s.get("max_xp", 100)
                    s["max_xp"] = int(s.get("max_xp", 100) * 1.5)
                    skill_log.append(f"{s['name']} leveled up to {s['level']}!")

        xp_gain = 500

        # Build the UPDATE from whichever stats actually gained, so we never
        # reference a column that isn't there.
        set_parts = ["xp = xp + ?"]
        params = [xp_gain]
        for col, amount in stat_gains.items():
            set_parts.append(f"{col} = {col} + ?")
            params.append(amount)
            if col == "max_health":
                set_parts.append("health = health + ?")
                params.append(amount)
            if col == "endurance":
                # defense is a legacy mirror of endurance (see database.py).
                set_parts.append("defense = defense + ?")
                params.append(amount)
        set_parts.append("skills = ?")
        params.append(json.dumps(skills))
        params.append(req.student_id)
        conn.execute(f"UPDATE heroes SET {', '.join(set_parts)} WHERE id = ?", params)

        # Recalculate level in case the XP pushed a threshold.
        from services.level_service import recalculate_hero_level
        fresh = conn.execute("SELECT * FROM heroes WHERE id = ?", (req.student_id,)).fetchone()
        if fresh:
            new_level = recalculate_hero_level(dict(fresh))
            if new_level != fresh["level"]:
                conn.execute("UPDATE heroes SET level = ? WHERE id = ?", (new_level, req.student_id))

    return {
        "ok": True,
        "xp": xp_gain,
        "stats": stat_gains,
        "skills": skill_log
    }
