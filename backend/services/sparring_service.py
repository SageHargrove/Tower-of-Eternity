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


# Traits that mark a hero as a gifted teacher (see traits_service).
TEACHER_TRAIT_IDS = {"mentors_heart"}


def teaching_multiplier(hero: dict) -> float:
    """How effective this hero is as a MENTOR. Some heroes just lean toward
    teaching: a natural leader (high Leadership aptitude), a patient,
    thorough worker (high Diligence), or one born with the Mentor's Heart
    trait. Scales the XP a mentorship transfers and the teach-a-skill chance.
    Ranges ~1.0 (unremarkable teacher) to ~2.5 (a legendary mentor)."""
    import json as _json
    mult = 1.0
    if (hero.get("apt_leadership") or 50) >= 75:
        mult += 0.3
    if (hero.get("apt_diligence") or 50) >= 75:
        mult += 0.2
    try:
        traits = _json.loads(hero.get("traits") or "[]")
        if any(t.get("id") in TEACHER_TRAIT_IDS for t in traits):
            mult += 0.7
    except Exception:
        pass
    return mult


def _build_bond(conn, hero_a_id: int, hero_b_id: int):
    """Training together builds the same bond fighting together does. Bond
    level is derived from floors_together + spar_sessions combined, so a
    pair who spar often grow a real combat bond (see bonds_service /
    get_team_bonds_multiplier). Returns the new integer bond level."""
    a, b = min(hero_a_id, hero_b_id), max(hero_a_id, hero_b_id)
    conn.execute("""
        INSERT INTO hero_bonds (hero_a_id, hero_b_id, bond_level, floors_together, spar_sessions)
        VALUES (?, ?, 0, 0, 1)
        ON CONFLICT(hero_a_id, hero_b_id) DO UPDATE SET spar_sessions = spar_sessions + 1
    """, (a, b))
    row = conn.execute(
        "SELECT floors_together, spar_sessions FROM hero_bonds WHERE hero_a_id = ? AND hero_b_id = ?",
        (a, b),
    ).fetchone()
    new_level = int((row["floors_together"] + row["spar_sessions"]) / 5)
    conn.execute(
        "UPDATE hero_bonds SET bond_level = ? WHERE hero_a_id = ? AND hero_b_id = ?",
        (new_level, a, b),
    )
    return new_level


def _record_mentorship(conn, mentor_id: int, student_id: int, xp_given: int):
    """Directional mentor->student relationship, for hero-card display and
    attachment flavor. Self-migrates its table so old saves gain it."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS mentorships (
            mentor_id INTEGER,
            student_id INTEGER,
            sessions INTEGER DEFAULT 0,
            xp_given INTEGER DEFAULT 0,
            PRIMARY KEY (mentor_id, student_id)
        )
    """)
    conn.execute("""
        INSERT INTO mentorships (mentor_id, student_id, sessions, xp_given)
        VALUES (?, ?, 1, ?)
        ON CONFLICT(mentor_id, student_id) DO UPDATE SET
            sessions = sessions + 1,
            xp_given = xp_given + ?
    """, (mentor_id, student_id, xp_given, xp_given))


def _teach_skill(conn, mentor: dict, student: dict, teach_mult: float = 1.0) -> str | None:
    """A mentor may pass down one of their OWN skills the student doesn't yet
    know — the "shape your roster's kit across generations" idea. Base 40%
    chance, scaled by the mentor's teaching gift. Returns the skill name."""
    import random
    if random.random() > min(0.9, 0.4 * teach_mult):
        return None
    mentor_skills = json.loads(mentor.get("skills") or "[]")
    student_skills = json.loads(student.get("skills") or "[]")
    known = {s.get("name") for s in student_skills}
    teachable = [s for s in mentor_skills if s.get("name") not in known]
    if not teachable:
        return None
    taught = dict(random.choice(teachable))
    taught["level"] = 1
    taught["xp"] = 0
    taught["max_xp"] = taught.get("max_xp", 100)
    student_skills.append(taught)
    conn.execute("UPDATE heroes SET skills = ? WHERE id = ?", (json.dumps(student_skills), student["id"]))
    return taught["name"]


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
        # Transfer scales with the mentor's level, the Training Grounds level,
        # AND the mentor's teaching gift (Leadership/Diligence aptitude or the
        # Mentor's Heart trait — a natural teacher gives far more).
        teach_mult = teaching_multiplier(mentor)
        transfer = int((50 + mentor["level"] * 6) * (1 + 0.1 * (tg_level - 1)) * teach_mult)
        conn.execute("UPDATE heroes SET xp = xp + ? WHERE id = ?", (transfer, student["id"]))
        # Aggregate mentor stats: how many sessions, and total XP given —
        # both feed the legacy gate (a great mentor is remembered).
        conn.execute(
            "UPDATE heroes SET mentored_count = COALESCE(mentored_count, 0) + 1, "
            "mentor_xp_given = COALESCE(mentor_xp_given, 0) + ? WHERE id = ?",
            (transfer, mentor["id"]),
        )
        # Directional per-pair mentorship record (drives hero-card "mentor"/
        # "students" display and attachment flavor).
        _record_mentorship(conn, mentor["id"], student["id"], transfer)

        student_reload = _hero(conn, student["id"])
        skill_name = _bump_skill(student_reload, guaranteed=True)
        if skill_name:
            conn.execute("UPDATE heroes SET skills = ? WHERE id = ?", (student_reload["skills"], student["id"]))

        old_level = student["level"]
        new_level = recalculate_hero_level(_hero(conn, student["id"]))
        if new_level != old_level:
            conn.execute("UPDATE heroes SET level = ? WHERE id = ?", (new_level, student["id"]))
            messages.extend(level_up_summary(old_level, new_level, student["name"]))

        # The mentor may pass down one of their own skills (kit lineage) —
        # a gifted teacher does so more readily.
        taught = _teach_skill(conn, mentor, _hero(conn, student["id"]), teach_mult)
        if taught:
            messages.append(f"{mentor['name']} taught {student['name']} the ways of {taught}!")

        result["mode"] = "mentorship"
        result["mentor"] = mentor["name"]
        result["student"] = student["name"]
        result["xp_transferred"] = transfer
        result["taught_skill"] = taught
        if teach_mult >= 1.5:
            messages.append(f"{mentor['name']} is a gifted teacher — the lesson runs deep.")
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

    # Time on the training floor together deepens their bond, win or lose.
    new_bond = _build_bond(conn, hero_a_id, hero_b_id)
    result["bond_level"] = new_bond
    messages.append(f"{a['name']} and {b['name']} grow closer — Bond Lv.{new_bond}.")

    conn.execute("UPDATE heroes SET last_spar_time = ? WHERE id IN (?, ?)", (now, hero_a_id, hero_b_id))
    return result


# ── Internal Sparring Tournament ─────────────────────────────────────

TOURNAMENT_COOLDOWN_SECONDS = 24 * 3600
TOURNAMENT_MIN_ENTRANTS = 3


def _spar_score(h: dict) -> float:
    """A hero's raw sparring strength — level-weighted, plus their physical
    stats, with a Luck-influenced random swing so upsets happen and the
    tournament stays worth watching."""
    import random
    base = h.get("level", 1) * 10
    base += (h.get("strength", 10) + h.get("agility", 10) + h.get("endurance", 5)
             + h.get("willpower", 6) + h.get("intelligence", 5))
    swing = random.uniform(0.75, 1.25) + (h.get("luck", 5) / 100.0)
    return base * swing


def run_tournament(conn) -> dict:
    """A round-robin sparring tournament among every hero assigned to the
    Training Grounds. Pure motivation/reward event: the whole roster of
    entrants gets a morale lift (competition is good for them), the champion
    gets a big XP + morale + permanent stat prize, runners-up get a smaller
    cut. Once per day."""
    from services.morale_service import get_morale_state

    tg = conn.execute("SELECT id, level FROM facilities WHERE type = 'Training Grounds' AND base_id = 1").fetchone()
    if not tg:
        raise ValueError("Build the Training Grounds first.")

    entrants = [dict(r) for r in conn.execute("""
        SELECT h.* FROM facility_assignments fa
        JOIN heroes h ON fa.hero_id = h.id
        WHERE fa.facility_id = ? AND h.is_alive = 1
    """, (tg["id"],)).fetchall()]
    if len(entrants) < TOURNAMENT_MIN_ENTRANTS:
        raise ValueError(f"A tournament needs at least {TOURNAMENT_MIN_ENTRANTS} heroes assigned to the Training Grounds.")

    now = time.time()
    base = conn.execute("SELECT last_tournament_time FROM base WHERE id = 1").fetchone()
    last = (base["last_tournament_time"] or 0) if base else 0
    if now - last < TOURNAMENT_COOLDOWN_SECONDS:
        rem = int(TOURNAMENT_COOLDOWN_SECONDS - (now - last))
        raise ValueError(f"The next tournament can be held in {rem // 3600}h {(rem % 3600) // 60}m.")

    # Round robin: everyone spars everyone once, best score wins each match.
    wins = {h["id"]: 0 for h in entrants}
    for i in range(len(entrants)):
        for j in range(i + 1, len(entrants)):
            a, b = entrants[i], entrants[j]
            winner = a if _spar_score(a) >= _spar_score(b) else b
            wins[winner["id"]] += 1

    standings = sorted(entrants, key=lambda h: wins[h["id"]], reverse=True)
    champion = standings[0]
    tg_level = max(1, tg["level"])

    log = [f"🏆 The Training Grounds tournament begins — {len(entrants)} fighters enter!"]
    prizes = []

    # Everyone who competed gets a morale lift (win or lose — the thrill of it).
    for h in entrants:
        conn.execute(
            "UPDATE heroes SET morale = ?, morale_state = ?, xp = xp + ? WHERE id = ?",
            (min(100, h["morale"] + 8), get_morale_state(min(100, h["morale"] + 8)),
             40 * tg_level, h["id"]),
        )

    # Champion: big XP, big morale, and one permanent stat point.
    import random
    champ_stat = random.choice(["strength", "agility", "endurance", "willpower", "intelligence"])
    champ_xp = 200 * tg_level
    conn.execute(
        f"UPDATE heroes SET xp = xp + ?, morale = ?, morale_state = ?, {champ_stat} = {champ_stat} + 1 WHERE id = ?",
        (champ_xp, min(100, champion["morale"] + 20), get_morale_state(min(100, champion["morale"] + 20)), champion["id"]),
    )
    log.append(f"🥇 {champion['name']} is crowned Champion — {wins[champion['id']]} wins! (+{champ_xp} XP, +1 {champ_stat.title()}, morale soars)")
    prizes.append({"hero": champion["name"], "prize": f"+{champ_xp} XP, +1 {champ_stat.title()}"})

    if len(standings) > 1:
        runner = standings[1]
        r_xp = 100 * tg_level
        conn.execute("UPDATE heroes SET xp = xp + ? WHERE id = ?", (r_xp, runner["id"]))
        log.append(f"🥈 {runner['name']} takes second ({wins[runner['id']]} wins, +{r_xp} XP).")
        prizes.append({"hero": runner["name"], "prize": f"+{r_xp} XP"})

    # Level recalcs for everyone who might have crossed a threshold.
    for h in entrants:
        fresh = conn.execute("SELECT * FROM heroes WHERE id = ?", (h["id"],)).fetchone()
        if fresh:
            new_level = recalculate_hero_level(dict(fresh))
            if new_level != fresh["level"]:
                conn.execute("UPDATE heroes SET level = ? WHERE id = ?", (new_level, h["id"]))

    conn.execute("UPDATE base SET last_tournament_time = ? WHERE id = 1", (now,))
    return {
        "champion": champion["name"],
        "standings": [{"name": h["name"], "wins": wins[h["id"]]} for h in standings],
        "prizes": prizes,
        "log": log,
    }


def tournament_status(conn) -> dict:
    tg = conn.execute("SELECT id FROM facilities WHERE type = 'Training Grounds' AND base_id = 1").fetchone()
    if not tg:
        return {"ready": False, "entrants": 0, "cooldown_remaining": 0}
    entrants = conn.execute("""
        SELECT COUNT(*) AS c FROM facility_assignments fa
        JOIN heroes h ON fa.hero_id = h.id
        WHERE fa.facility_id = ? AND h.is_alive = 1
    """, (tg["id"],)).fetchone()["c"]
    base = conn.execute("SELECT last_tournament_time FROM base WHERE id = 1").fetchone()
    last = (base["last_tournament_time"] or 0) if base else 0
    remaining = max(0, int(TOURNAMENT_COOLDOWN_SECONDS - (time.time() - last)))
    return {
        "entrants": entrants,
        "min_entrants": TOURNAMENT_MIN_ENTRANTS,
        "cooldown_remaining": remaining,
        "ready": entrants >= TOURNAMENT_MIN_ENTRANTS and remaining == 0,
    }
