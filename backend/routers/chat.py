from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Optional
from database import db
from pydantic import BaseModel
import json

router = APIRouter()

class ChatGenerateRequest(BaseModel):
    location: str = "The Lobby"

@router.get("/")
def get_chat_logs(limit: int = 5):
    with db() as conn:
        rows = conn.execute(
            "SELECT id, location, message, participants, created_at FROM hero_chat_logs ORDER BY created_at DESC LIMIT ?", 
            (limit,)
        ).fetchall()
        
    # Only living heroes get a voice: logs outlive renames and dismissals
    # (speakers are stored as plain text), so lines from heroes who no
    # longer exist must be dropped at read time, never shown.
    with db() as conn:
        alive = {h["name"] for h in conn.execute("SELECT name FROM heroes WHERE is_alive = 1").fetchall()}

    logs = []
    for r in rows:
        try:
            msg_data = json.loads(r["message"])
        except:
            msg_data = []
        msg_data = [m for m in msg_data if m.get("speaker") in alive]
        if not msg_data:
            continue
        logs.append({
            "id": r["id"],
            "location": r["location"],
            "participants": r["participants"],
            "messages": msg_data,
            "created_at": r["created_at"]
        })
    return logs

@router.get("/hearth")
def get_hearth():
    """The Hearth drawer feed: recent CONVERSATIONS as threaded exchanges,
    newest first — NOT one detached line per hero (which read as everyone
    muttering independently, per Liam). Each conversation keeps its lines in
    spoken order so the back-and-forth is legible; every line is joined with
    its speaker's portrait + mood. Dead/renamed/phantom speakers are dropped
    per line, and a conversation with nothing left to show is skipped."""
    with db() as conn:
        rows = conn.execute(
            "SELECT id, location, participants, message, created_at FROM hero_chat_logs ORDER BY created_at DESC LIMIT 6"
        ).fetchall()
        heroes = conn.execute(
            "SELECT id, name, portrait_path, stress, morale FROM heroes WHERE is_alive = 1"
        ).fetchall()
        base = conn.execute("SELECT last_hearth_word FROM base WHERE id = 1").fetchone() if _has_hearth_col(conn) else None

    by_name = {h["name"]: dict(h) for h in heroes}
    conversations = []
    for r in rows:
        try:
            msgs = json.loads(r["message"])
        except Exception:
            continue
        thread = []
        for m in msgs:
            speaker = m.get("speaker", "")
            # Ghost guard: only living heroes may speak.
            if not speaker or speaker not in by_name or not m.get("message"):
                continue
            hero = by_name[speaker]
            stress = hero.get("stress") or 0
            morale = hero.get("morale")
            thread.append({
                "speaker": speaker,
                "message": m.get("message", ""),
                "hero_id": hero.get("id"),
                "portrait_path": hero.get("portrait_path"),
                "mood": "shaken" if (stress >= 60 or (morale is not None and morale < 40)) else "steady",
            })
        if thread:
            conversations.append({
                "location": r["location"],
                "created_at": r["created_at"],
                "lines": thread,
            })

    cooldown_remaining = 0
    if base and base["last_hearth_word"]:
        from datetime import datetime
        from services.chat_service import HEARTH_WORD_COOLDOWN_SECS
        try:
            elapsed = (datetime.utcnow() - datetime.strptime(base["last_hearth_word"], "%Y-%m-%d %H:%M:%S")).total_seconds()
            cooldown_remaining = max(0, int(HEARTH_WORD_COOLDOWN_SECS - elapsed))
        except ValueError:
            pass
    return {"conversations": conversations, "cooldown_remaining": cooldown_remaining,
            "newest_at": rows[0]["created_at"] if rows else None}


def _has_hearth_col(conn) -> bool:
    cols = [c["name"] for c in conn.execute("PRAGMA table_info(base)").fetchall()]
    return "last_hearth_word" in cols


class HearthWordRequest(BaseModel):
    tone: str

@router.post("/word")
def send_hearth_word(req: HearthWordRequest):
    from services.chat_service import hearth_word
    res = hearth_word(req.tone)
    if res.get("status") == "error":
        raise HTTPException(status_code=400, detail=res.get("message"))
    if res.get("status") == "cooldown":
        raise HTTPException(status_code=429, detail=f"The company needs a moment — try again in {res['remaining']}s.")
    return res


@router.post("/generate")
def generate_chat(req: ChatGenerateRequest, background_tasks: BackgroundTasks):
    from services.chat_service import generate_hero_chat
    # We could run this in background or synchronously
    res = generate_hero_chat(req.location)
    if res.get("status") == "error":
        raise HTTPException(status_code=500, detail=res.get("message"))
    return {"status": "success", "chat": res}
