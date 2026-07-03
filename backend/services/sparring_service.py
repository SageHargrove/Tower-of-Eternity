"""
Sparring Service — Training Grounds active training.

Two modes, both run against heroes ASSIGNED to the Training Grounds:

  peer       — two heroes of similar level spar. Both gain moderate XP and
               each has a high chance to level up a random skill.
  mentorship — a high-level hero drills a lower-level one. The mentor gains
               NO xp (they've nothing to learn here) but transfers a large
               chunk of xp to the student, plus a guaranteed skill level for
               the student. The mentor's mentored_count ticks up (fuels the
               legacy qualification gate — see legacy_service).

Both are on a cooldown so the Training Grounds isn't a free infinite XP
faucet — it's a deliberate, paced investment.
"""
import json
import time

from services.level_service import recalculate_hero_level, level_up_summary

SPAR_COOLDOWN_SECONDS = 300  # 5 min, shared per hero pair via last_spar_time
PEER_LEVEL_WINDOW = 5        # "similar level" = within this many levels
MENTOR_LEVEL_GAP = 8         # mentor must be at least this far above student


def _hero(conn, hero_id):
    row = conn.execute("SELECT * FROM heroes WHERE id = ? AND is_alive = 1", (hero_id,)).fetchone()
    return dict(row) if row else None


def _assigned_to_training(conn, hero_id) -> bool:
    row = conn.execute("""
        SELECT 1 FROM facility_assignments fa
        JOIN facilities f ON fa.facility_id = f.id
        WHERE fa.hero_id = ? AND f.type = 'Training Grounds' AND f.base_id = 1
    """, (hero_id,)).fetchone()
    return row is not None


def _training_level(conn) -> int:
    row = conn.execute("SELECT level FROM facilities WHERE type = 'Training Grounds' AND base_id = 1").fetchone()
    return row["level"] if row else 0


def _bump_skill(hero_dict: dict, guaranteed: bool, chance: float = 0.6) -> str | None:
    """Level up one random skill on the hero (in-place on the dict's skills
    JSON). Returns the skill name if one leveled, else None. Caller persists."""
    import random
    skills = json.loads(hero_dict.get("skills") or "[]")
    if not skills:
        return None
    if not guaranteed and random.random() > chance:
        return None
    target = random.choice(skills)
    target["level"] = target.get("level", 1) + 1
    target["xp"] = 0
    target["max_xp"] = int(target.get("max_xp", 100) * 1.5)
    hero_dict["skills"] = json.dumps(skills)
    return target["name"]


def spar(conn, hero_a_id: int, hero_b_id: int) -> dict:
    """Resolve a sparring session between two assigned heroes. Auto-detects
    peer vs mentorship from the level gap."""
    import random
    if hero_a_id == hero_b_id:
        raise ValueError("A hero can't spar with themselves.")

    a = _hero(conn, hero_a_id)
    b = _hero(conn, hero_b_id)
    if not a or not b:
        raise ValueError("Both sparring partners must be living heroes.")
    if not _assigned_to_training(conn, hero_a_id) or not _assigned_to_training(conn, hero_b_id):
        raise ValueError("Both heroes must be assigned to the Training Grounds to spar.")

    now = time.time()
    for h in (a, b):
        last = h.get("last_spar_time") or 0
        if now - last < SPAR_COOLDOWN_SECONDS:
            rem = int(SPAR_COOLDOWN_SECONDS - (now - last))
            raise ValueError(f"{h['name']} is still catching their breath — {rem}s until they can spar again.")

    tg_level = max(1, _training_level(conn))
    gap = abs(a["level"] - b["level"])
    messages = []
    result = {"mode": None, "messages": messages}

    if gap >= MENTOR_LEVEL_GAP:
        # ── Mentorship ──
        mentor, student = (a, b) if a["level"] > b["level"] else (b, a)
        # Transfer scales with the mentor's level and the Training Grounds
        # level — a big chunk, since the mentor "spends" a session teaching.
        transfer = int((50 + mentor["level"] * 6) * (1 + 0.1 * (tg_level - 1)))
        conn.execute("UPDATE heroes SET xp = xp + ? WHERE id = ?", (transfer, student["id"]))
        conn.execute("UPDATE heroes SET mentored_count = COALESCE(mentored_count, 0) + 1 WHERE id = ?", (mentor["id"],))

        student_reload = _hero(conn, student["id"])
        skill_name = _bump_skill(student_reload, guaranteed=True)
        if skill_name:
            conn.execute("UPDATE heroes SET skills = ? WHERE id = ?", (student_reload["skills"], student["id"]))

        old_level = student["level"]
        new_level = recalculate_hero_level(_hero(conn, student["id"]))
        if new_level != old_level:
            conn.execute("UPDATE heroes SET level = ? WHERE id = ?", (new_level, student["id"]))
            messages.extend(level_up_summary(old_level, new_level, student["name"]))

        result["mode"] = "mentorship"
        result["mentor"] = mentor["name"]
        result["student"] = student["name"]
        result["xp_transferred"] = transfer
        messages.insert(0, f"{mentor['name']} drilled {student['name']} hard — {transfer} XP transferred."
                          + (f" {student['name']}'s {skill_name} sharpened." if skill_name else ""))
    else:
        # ── Peer sparring ──
        if gap > PEER_LEVEL_WINDOW:
            raise ValueError(
                f"{a['name']} and {b['name']} are too far apart to spar as equals "
                f"(gap {gap}) — but far enough for Mentorship (needs a {MENTOR_LEVEL_GAP}+ gap)."
                if gap < MENTOR_LEVEL_GAP else "Level gap mismatch."
            )
        each_xp = int((30 + max(a["level"], b["level"]) * 4) * (1 + 0.1 * (tg_level - 1)))
        for h in (a, b):
            conn.execute("UPDATE heroes SET xp = xp + ? WHERE id = ?", (each_xp, h["id"]))
            reload = _hero(conn, h["id"])
            skill_name = _bump_skill(reload, guaranteed=False, chance=0.75)
            if skill_name:
                conn.execute("UPDATE heroes SET skills = ? WHERE id = ?", (reload["skills"], h["id"]))
                messages.append(f"{h['name']}'s {skill_name} improved.")
            old_level = h["level"]
            new_level = recalculate_hero_level(_hero(conn, h["id"]))
            if new_level != old_level:
                conn.execute("UPDATE heroes SET level = ? WHERE id = ?", (new_level, h["id"]))
                messages.extend(level_up_summary(old_level, new_level, h["name"]))

        result["mode"] = "peer"
        result["each_xp"] = each_xp
        messages.insert(0, f"{a['name']} and {b['name']} sparred to a standstill — {each_xp} XP each.")

    conn.execute("UPDATE heroes SET last_spar_time = ? WHERE id IN (?, ?)", (now, hero_a_id, hero_b_id))
    return result
