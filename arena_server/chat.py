"""The Herald's Wire — server-side chat.

Channels (design: Chat - Illuminated / "The Herald's Wire"):
  world    — every climber; slowmode 5s per sender.
  trade    — offers/adverts; slowmode 300s; messages fade after 24h.
  guild    — the sender's lodge only (resolved server-side); no slowmode.
  whisper  — person-to-person threads; no slowmode.

Messages are plain text (no markup), capped at 300 chars. Fetches are
since-id polls — the client keeps the last seen id per channel and asks
for anything newer. Whisper reads are tracked per (me, other) pair so the
rail can badge unread threads.
"""
import time

from fastapi import HTTPException

SLOWMODE = {"world": 5, "trade": 300}
TRADE_TTL = 86400          # adverts fade after one day
MAX_LEN = 300
FETCH_LIMIT = 50


def init_tables(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel TEXT NOT NULL,          -- 'world' | 'trade' | 'guild:{id}' | 'whisper'
            sender TEXT NOT NULL,
            recipient TEXT,                 -- whispers only
            text TEXT NOT NULL,
            created_at REAL NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_chat_channel ON chat_messages (channel, id);
        CREATE INDEX IF NOT EXISTS idx_chat_whisper ON chat_messages (recipient, sender, id);

        CREATE TABLE IF NOT EXISTS chat_reads (
            username TEXT NOT NULL,
            thread TEXT NOT NULL,           -- the other party's username
            last_read_id INTEGER DEFAULT 0,
            PRIMARY KEY (username, thread)
        );
    """)


def _guild_channel(conn, username: str) -> str:
    row = conn.execute("SELECT guild_id FROM guild_members WHERE username = ?", (username,)).fetchone()
    if not row:
        raise HTTPException(status_code=400, detail="You bear no guild crest — join a lodge first.")
    return f"guild:{row['guild_id']}"


def _floor_of(conn, username: str) -> int:
    row = conn.execute("SELECT highest_floor FROM arena_players WHERE username = ?", (username,)).fetchone()
    return (row["highest_floor"] or 0) if row else 0


def _cooldown_remaining(conn, username: str, channel: str) -> int:
    wait = SLOWMODE.get(channel, 0)
    if not wait:
        return 0
    row = conn.execute(
        "SELECT MAX(created_at) AS at FROM chat_messages WHERE channel = ? AND sender = ?",
        (channel, username)).fetchone()
    if not row or not row["at"]:
        return 0
    return max(0, int(wait - (time.time() - row["at"])))


def send(conn, username: str, channel: str, text: str, to: str | None = None) -> dict:
    text = (text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="The wire carries no empty words.")
    if len(text) > MAX_LEN:
        raise HTTPException(status_code=400, detail=f"Keep it under {MAX_LEN} characters — the wire is shared.")

    channel = (channel or "").strip().lower()
    recipient = None
    if channel == "guild":
        channel = _guild_channel(conn, username)
    elif channel == "whisper":
        recipient = (to or "").strip()
        if not recipient or recipient == username:
            raise HTTPException(status_code=400, detail="Whisper a name that isn't your own.")
        if not conn.execute("SELECT 1 FROM arena_players WHERE username = ?", (recipient,)).fetchone():
            raise HTTPException(status_code=404, detail=f"No climber named {recipient}.")
    elif channel not in ("world", "trade"):
        raise HTTPException(status_code=400, detail="No such channel on the wire.")

    remaining = _cooldown_remaining(conn, username, channel)
    if remaining > 0:
        raise HTTPException(status_code=429, detail=f"Slowmode — the wire cools for {remaining}s.")

    cur = conn.execute(
        "INSERT INTO chat_messages (channel, sender, recipient, text, created_at) VALUES (?,?,?,?,?)",
        (channel, username, recipient, text, time.time()))
    # Your own words are always read.
    if recipient:
        conn.execute(
            "INSERT INTO chat_reads (username, thread, last_read_id) VALUES (?,?,?) "
            "ON CONFLICT(username, thread) DO UPDATE SET last_read_id = ?",
            (username, recipient, cur.lastrowid, cur.lastrowid))
    return {"ok": True, "id": cur.lastrowid, "cooldown": SLOWMODE.get(channel.split(":")[0], 0)}


def _rows_to_messages(conn, rows) -> list[dict]:
    floors: dict[str, int] = {}
    out = []
    for r in rows:
        if r["sender"] not in floors:
            floors[r["sender"]] = _floor_of(conn, r["sender"])
        out.append({
            "id": r["id"], "sender": r["sender"], "text": r["text"],
            "at": r["created_at"], "floor": floors[r["sender"]],
        })
    return out


def fetch(conn, username: str, channel: str, since: int = 0) -> dict:
    channel = (channel or "").strip().lower()
    if channel == "guild":
        channel = _guild_channel(conn, username)
    elif channel not in ("world", "trade"):
        raise HTTPException(status_code=400, detail="No such channel on the wire.")

    params = [channel, since]
    ttl_clause = ""
    if channel == "trade":
        ttl_clause = " AND created_at > ?"
        params.append(time.time() - TRADE_TTL)
    rows = conn.execute(
        f"SELECT * FROM chat_messages WHERE channel = ? AND id > ?{ttl_clause} ORDER BY id DESC LIMIT ?",
        (*params, FETCH_LIMIT)).fetchall()
    rows = list(reversed(rows))
    listeners = None
    if channel == "world":
        listeners = conn.execute("SELECT COUNT(*) AS n FROM arena_players").fetchone()["n"]
    return {
        "channel": channel, "messages": _rows_to_messages(conn, rows),
        "cooldown_remaining": _cooldown_remaining(conn, username, channel),
        "slowmode": SLOWMODE.get(channel.split(":")[0], 0),
        "listeners": listeners,
    }


def whisper_threads(conn, username: str) -> dict:
    rows = conn.execute("""
        SELECT m.*,
               CASE WHEN m.sender = ? THEN m.recipient ELSE m.sender END AS other
        FROM chat_messages m
        WHERE m.channel = 'whisper' AND (m.sender = ? OR m.recipient = ?)
        ORDER BY m.id DESC
    """, (username, username, username)).fetchall()
    reads = {r["thread"]: r["last_read_id"] for r in conn.execute(
        "SELECT thread, last_read_id FROM chat_reads WHERE username = ?", (username,)).fetchall()}
    threads: dict[str, dict] = {}
    for r in rows:
        other = r["other"]
        t = threads.setdefault(other, {"with": other, "last_text": r["text"], "last_at": r["created_at"], "unread": 0})
        if r["recipient"] == username and r["id"] > reads.get(other, 0):
            t["unread"] += 1
    return {"threads": sorted(threads.values(), key=lambda t: -t["last_at"])}


def whisper_thread(conn, username: str, other: str, since: int = 0) -> dict:
    rows = conn.execute("""
        SELECT * FROM chat_messages
        WHERE channel = 'whisper' AND id > ?
          AND ((sender = ? AND recipient = ?) OR (sender = ? AND recipient = ?))
        ORDER BY id DESC LIMIT ?
    """, (since, username, other, other, username, FETCH_LIMIT)).fetchall()
    rows = list(reversed(rows))
    if rows:
        conn.execute(
            "INSERT INTO chat_reads (username, thread, last_read_id) VALUES (?,?,?) "
            "ON CONFLICT(username, thread) DO UPDATE SET last_read_id = MAX(last_read_id, ?)",
            (username, other, rows[-1]["id"], rows[-1]["id"]))
    return {"with": other, "messages": _rows_to_messages(conn, rows)}
