"""
Lore Journal
============
A growing, in-game journal — one page unlocks per 10-floor milestone
cleared (10, 20, 30...), revealing more of the Tower's mythology the
deeper the player climbs. Pages are generated once via the LLM and
frozen forever in lore_entries (see database.py), same caching shape as
floor_cache — a page's text must never change after being read.
"""

from services.llm_service import generate_lore_entry

MILESTONE_INTERVAL = 10


def get_unlocked_milestones(highest_floor: int) -> list[int]:
    """Every milestone the player has actually cleared, oldest first."""
    last = (highest_floor // MILESTONE_INTERVAL) * MILESTONE_INTERVAL
    if last < MILESTONE_INTERVAL:
        return []
    return list(range(MILESTONE_INTERVAL, last + 1, MILESTONE_INTERVAL))


def get_or_create_lore_entry(conn, milestone: int, previous_titles: list[str]) -> dict:
    row = conn.execute("SELECT milestone, title, text FROM lore_entries WHERE milestone = ?", (milestone,)).fetchone()
    if row:
        return dict(row)
    # Pull THIS save's own encounters since the prior milestone — what it
    # actually fought and chose — so the page reflects this run specifically
    # rather than being identical generic text for every save that reaches
    # floor `milestone`.
    encounters = get_floor_history_range(conn, milestone - MILESTONE_INTERVAL, milestone)
    title, text = generate_lore_entry(milestone, previous_titles, encounters)
    conn.execute(
        "INSERT INTO lore_entries (milestone, title, text) VALUES (?, ?, ?)",
        (milestone, title, text),
    )
    return {"milestone": milestone, "title": title, "text": text}


def record_floor_history(conn, floor_number: int, floor_type: str, summary: str):
    """One row per floor actually resolved — the raw material a milestone's
    lore page draws from. Called right alongside the existing
    floors_survived/kills updates, never on a mere preview or re-roll."""
    conn.execute(
        "INSERT INTO floor_history (floor_number, floor_type, summary) VALUES (?, ?, ?)",
        (floor_number, floor_type, summary),
    )


def get_floor_history_range(conn, start_floor: int, end_floor: int) -> list[str]:
    rows = conn.execute(
        "SELECT floor_number, floor_type, summary FROM floor_history WHERE floor_number > ? AND floor_number <= ? ORDER BY floor_number",
        (start_floor, end_floor),
    ).fetchall()
    return [f"Floor {r['floor_number']} ({r['floor_type']}): {r['summary']}" for r in rows]


def get_lore_journal(conn, highest_floor: int) -> list[dict]:
    """Every unlocked page, oldest first — generates any milestone that's
    been reached but never had its page rolled yet (e.g. a save that
    jumped floors via dev tools, or just the first time this is opened)."""
    entries = []
    titles_so_far = []
    for milestone in get_unlocked_milestones(highest_floor):
        entry = get_or_create_lore_entry(conn, milestone, titles_so_far)
        entries.append(entry)
        titles_so_far.append(entry["title"])
    return entries
