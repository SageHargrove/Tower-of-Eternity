from fastapi import APIRouter
from database import db

router = APIRouter()

@router.get("/")
def list_runs():
    with db() as conn:
        rows = conn.execute("SELECT * FROM runs ORDER BY started_at DESC LIMIT 20").fetchall()
    return [dict(r) for r in rows]

@router.get("/log")
def get_event_log(run_id: int = None, limit: int = 50):
    with db() as conn:
        if run_id:
            rows = conn.execute(
                "SELECT * FROM event_log WHERE run_id = ? ORDER BY id DESC LIMIT ?",
                (run_id, limit)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM event_log ORDER BY id DESC LIMIT ?",
                (limit,)
            ).fetchall()
    return [dict(r) for r in rows]
