from fastapi import APIRouter
from database import db

router = APIRouter()

@router.get("/")
def get_base():
    with db() as conn:
        row = conn.execute("SELECT * FROM base WHERE id = 1").fetchone()
    return dict(row)

@router.post("/rest")
def rest_heroes():
    """Rest all alive heroes at base. Called after returning from tower."""
    from services.morale_service import rest_at_base_recovery
    with db() as conn:
        heroes = conn.execute("SELECT * FROM heroes WHERE is_alive = 1").fetchall()
        for hero in heroes:
            recovery = rest_at_base_recovery(dict(hero))
            conn.execute("""
                UPDATE heroes SET morale = ?, stress = ?, trauma = ?, morale_state = ?
                WHERE id = ?
            """, (recovery["morale"], recovery["stress"], recovery["trauma"],
                  recovery["morale_state"], hero["id"]))
    return {"ok": True, "rested": len(heroes)}
