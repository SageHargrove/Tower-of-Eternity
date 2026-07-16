import json
import random
from datetime import datetime
from database import db
from services.llm_service import _generate_with_fallback, generate_with_claude, _clean_json


def _time_of_day_bucket(hour: int) -> tuple[str, str]:
    """(bucket name, prompt instruction) for the current LOCAL hour — this
    is a desktop app, server and player are the same machine, so
    datetime.now() (no UTC conversion) already IS the player's real local
    time. Chat previously had zero time-of-day awareness at all; this is
    what actually lets heroes reference morning/lunch/late-night rather
    than the timestamp on the message just being incidentally correct."""
    if 5 <= hour < 11:
        return "morning", "It's morning at camp. A few are still waking up; some are already up and about."
    if 11 <= hour < 14:
        return "midday", "It's around midday — lunch is likely on someone's mind, or already happening."
    if 14 <= hour < 18:
        return "afternoon", "It's mid-afternoon. A normal, unremarkable stretch of the day."
    if 18 <= hour < 22:
        return "evening", "It's evening. The day's winding down; this is a relaxed, unwind-after-the-climb mood."
    if 22 <= hour < 24 or 0 <= hour < 2:
        return "night", "It's late at night. Most are asleep or heading there; whoever's still up is talking quietly so as not to wake the others."
    return "late_night", "It's the dead of night (very late/very early). Almost everyone is asleep — only a genuine night owl would still be up talking."


def is_night_owl(hero_id: int) -> bool:
    """Deterministic per-hero trait (no schema change) — roughly 3 in 10
    heroes are night owls, so 'late_night' chatter has someone plausible to
    pull from instead of waking a random morning person."""
    return (hero_id * 2654435761) % 100 < 30


def _generate_chat_text(prompt: str, max_tokens: int, temperature: float) -> str:
    """Hero chatter prefers Claude/Haiku for voice (see llm_service's
    CLAUDE_CHAT_MODEL comment) — falls back to Gemini if no Anthropic key
    is configured yet, or if the Claude call itself fails, so this doesn't
    just break for anyone who hasn't added ANTHROPIC_API_KEY."""
    try:
        return generate_with_claude(prompt, max_tokens=max_tokens, temperature=temperature)
    except Exception as e:
        print(f"[Chat] Claude unavailable ({e}), falling back to Gemini")
        return _generate_with_fallback(prompt, max_tokens=max_tokens, temperature=temperature)


def _tower_era(highest_floor: int) -> tuple[str, str]:
    """Buckets the save's overall progress into a fixed set of narrative eras —
    chatter should read as confused strangers early on, gradually settling into
    a lived-in understanding of the Tower as floors are cleared."""
    if highest_floor < 3:
        return "Awakening", (
            "This is VERY early on. Nobody understands the Tower or how they got "
            "here. The mood should be confusion, fear, and disorientation - lean "
            "into 'What is going on?' energy. They are strangers piecing together "
            "the absolute basics, not yet a found-family."
        )
    elif highest_floor < 15:
        return "Piecing It Together", (
            "The group has working theories about the Tower by now, though nothing "
            "is fully settled - expect debate, half-confident claims, and the "
            "occasional correction between heroes. Camaraderie is forming but "
            "confusion hasn't fully given way to confidence yet."
        )
    else:
        return "The Way Things Are", (
            "By now there's a settled, lived-in understanding of the Tower among "
            "the group - dark routine, inside jokes about Tower life, no more "
            "'what is this place' confusion. Long-timers talk like veterans."
        )


def _tenure_tag(hero_created_at: str, all_created_ats: list[str]) -> str:
    """'veteran' / 'newcomer' / '' (settled) based on this hero's percentile
    rank among currently-alive heroes' created_at — relative to the current
    roster, not a fixed date, so it stays meaningful no matter when a save is
    loaded. A hero pulled early is a 'veteran' of this world even in a
    late-game save where the Tower Era itself has long since settled."""
    if not hero_created_at or len(all_created_ats) < 3:
        return ""
    sorted_dates = sorted(all_created_ats)
    idx = sorted_dates.index(hero_created_at)
    pct = idx / max(1, len(sorted_dates) - 1)
    if pct <= 0.3:
        return "veteran"
    elif pct >= 0.7:
        return "newcomer"
    return ""


def generate_hero_chat(preferred_location: str | None = None) -> dict:
    """
    Selects heroes (preferably on a team or sharing synergy) and generates a chat log
    based on their personality, the current state of the base, and recent chats.
    preferred_location pins the scene (the /chat/generate endpoint passes one);
    otherwise a random unlocked location is rolled.
    """
    with db() as conn:
        heroes = conn.execute("SELECT id, name, personality, hero_class, level, ego_type, is_on_team, synergy_group, created_at FROM heroes WHERE is_alive = 1").fetchall()
        base_row = conn.execute("SELECT gold, highest_floor FROM base WHERE id = 1").fetchone()
        facilities = conn.execute("SELECT type FROM facilities").fetchall()
        recent_chats = conn.execute("SELECT message FROM hero_chat_logs ORDER BY created_at DESC LIMIT 2").fetchall()
        
    if not heroes:
        return {"status": "error", "message": "No alive heroes to chat."}
        
    gold = base_row["gold"] if base_row else 0
    highest_floor = base_row["highest_floor"] if base_row else 0
    unlocked_locations = ["The Lobby", "The Vault"] + [f["type"] for f in facilities]
    
    # Pick location
    if preferred_location and preferred_location in unlocked_locations:
        location = preferred_location
    else:
        location = random.choice(unlocked_locations)
    
    assigned_heroes = []
    with db() as conn:
        if location not in ["The Lobby", "The Vault"]:
            fac_row = conn.execute("SELECT id FROM facilities WHERE type = ?", (location,)).fetchone()
            if fac_row:
                assigned = conn.execute("SELECT h.id, h.name, h.personality, h.hero_class, h.level, h.ego_type, h.is_on_team, h.synergy_group, h.created_at FROM heroes h JOIN facility_assignments fa ON h.id = fa.hero_id WHERE fa.facility_id = ? AND h.is_alive = 1", (fac_row["id"],)).fetchall()
                if assigned:
                    assigned_heroes = [dict(r) for r in assigned]

    heroes_dict_list = [dict(h) for h in heroes]

    time_bucket, time_instruction = _time_of_day_bucket(datetime.now().hour)

    # Late at night, narrow the whole pool down to actual night owls before
    # any selection logic runs (groups included) — falls back to everyone
    # if this save happens to have no night owls alive, rather than going
    # silent for the rest of the night.
    if time_bucket == "late_night":
        night_owls = [h for h in heroes_dict_list if is_night_owl(h["id"])]
        if night_owls:
            heroes_dict_list = night_owls
            assigned_heroes = [h for h in assigned_heroes if is_night_owl(h["id"])]

    # Grouping logic: Try to pick heroes on the same team, or sharing synergy.
    grouped_heroes = {}
    for h in heroes_dict_list:
        if h["is_on_team"]:
            grouped_heroes.setdefault(f"Team {h['is_on_team']}", []).append(h)
        if h["synergy_group"]:
            grouped_heroes.setdefault(f"Synergy {h['synergy_group']}", []).append(h)

    valid_groups = [g for g in grouped_heroes.values() if len(g) >= 2]

    num_chatters = min(random.randint(2, 3), len(heroes_dict_list))
    chatters = []

    if assigned_heroes:
        # Prioritize assigned heroes. Add a random wanderer if possible
        num_assigned = min(len(assigned_heroes), num_chatters)
        chatters = random.sample(assigned_heroes, num_assigned)
        if len(chatters) < num_chatters:
            wanderer_pool = [h for h in heroes_dict_list if h["id"] not in [c["id"] for c in chatters]]
            if wanderer_pool:
                chatters.append(random.choice(wanderer_pool))
    elif valid_groups and random.random() < 0.7:
        group = random.choice(valid_groups)
        chatters = random.sample(group, min(num_chatters, len(group)))
    else:
        chatters = random.sample(heroes_dict_list, num_chatters)
    
    era_name, era_instruction = _tower_era(highest_floor)
    all_created_ats = [h["created_at"] for h in heroes_dict_list]

    chatter_profiles = []
    for h in chatters:
        ego = f" (Ego: {h['ego_type']})" if h["ego_type"] else ""
        tenure = _tenure_tag(h["created_at"], all_created_ats)
        tenure_note = ""
        if tenure == "veteran":
            tenure_note = " [Has been in the Tower since early on - understands the basics, may explain things to others.]"
        elif tenure == "newcomer":
            tenure_note = " [Arrived recently - still getting their bearings, may ask questions others take for granted.]"
        chatter_profiles.append(f"- {h['name']}: Lvl {h['level']} {h['hero_class']}{ego}. Personality: {h['personality']}{tenure_note}")

    has_restaurant = any(f["type"] == "Dining Hall" for f in facilities)
    has_chef = any(h["hero_class"] == "Chef" for h in heroes_dict_list)

    food_activity = "complaining about eating bland potatoes/rations"
    if has_restaurant and has_chef:
        food_activity = "praising the food or discussing the Chef's cooking"
    elif has_restaurant:
        food_activity = "complaining about the food being bland, but admitting it's better than rations"

    activities = [
        "playing a card game", "cleaning their weapons", food_activity, 
        "complaining about the smell", "bragging about a recent kill", 
        "nervously discussing the Tower", "enjoying a rare moment of peace",
        "arguing over a trivial matter", "sharing a rumor they heard"
    ]
    activity = random.choice(activities)
    
    recent_topics_prompt = ""
    if recent_chats:
        recent_topics_prompt = "CRITICAL INSTRUCTION: Do NOT repeat the general tropes or topics from these recent conversations (e.g. if they talked about silence/storms, DO NOT mention it):\n"
        for idx, rc in enumerate(recent_chats):
            try:
                msgs = json.loads(rc["message"])
                summary = " ".join([m["message"] for m in msgs])
                recent_topics_prompt += f"Recent Chat {idx+1}: {summary[:200]}...\n"
            except:
                pass
                
    prompt = f"""
You are writing a short, in-character chat log for a group of heroes hanging out in the base camp.
The current location they are at is: {location}.
They are currently {activity}.

Tower Era: {era_name}
{era_instruction}

Time of Day: {time_bucket}
{time_instruction}

Base State Context:
- Current Base Gold: {gold}
- Highest Tower Floor Cleared: {highest_floor}
- CRITICAL LORE: The heroes are climbing UP a massive Tower. Their goal is the TOP, not the "center" or "end of a labyrinth".
- CRITICAL LORE: The heroes are physically standing together in {location}, face to face. NEVER write lines implying radio, comms, static, signals, transmissions, or any kind of remote/long-distance communication — they are not separated and never hear from each other indirectly.

{recent_topics_prompt}

The heroes participating are:
{chr(10).join(chatter_profiles)}

Write a short, engaging 3-5 line conversation between them. Keep it realistic to their personalities and the current context. Make it feel alive and lived-in.
DO NOT use cliché tropes like "the silence is loud" or "quiet before the storm". Be highly creative.

Return ONLY a valid JSON array of message objects. Do not wrap in markdown tags like ```json.
Format:
[
  {{"speaker": "Hero Name", "message": "Their dialogue here"}},
  ...
]
"""
    try:
        response = _generate_chat_text(prompt, max_tokens=300, temperature=0.9)
        chat_data = json.loads(_clean_json(response))

        # The LLM's speaker field is untrusted: coerce every line to a real
        # participant (exact name, then first-name match) and drop lines it
        # attributed to characters we never gave it — invented speakers were
        # reaching the drawer as portrait-less ghosts.
        if isinstance(chat_data, list):
            by_full = {h["name"]: h["name"] for h in chatters}
            by_first = {h["name"].split()[0].lower(): h["name"] for h in chatters}
            cleaned = []
            for m in chat_data:
                spk = str(m.get("speaker", "")).strip()
                real = by_full.get(spk) or by_first.get(spk.split()[0].lower() if spk else "")
                if real and m.get("message"):
                    cleaned.append({"speaker": real, "message": m["message"]})
            chat_data = cleaned

        if isinstance(chat_data, list) and len(chat_data) > 0:
            with db() as conn:
                participants_str = ", ".join([h["name"] for h in chatters])
                conn.execute(
                    "INSERT INTO hero_chat_logs (location, message, participants) VALUES (?, ?, ?)",
                    (location, json.dumps(chat_data), participants_str)
                )
                
                # Delete older logs keeping only the 5 most recent
                conn.execute("""
                    DELETE FROM hero_chat_logs 
                    WHERE id NOT IN (
                        SELECT id FROM hero_chat_logs 
                        ORDER BY created_at DESC 
                        LIMIT 5
                    )
                """)
            return {"status": "success", "chat": chat_data, "participants": participants_str, "location": location}
    except Exception as e:
        print(f"[Chat] Failed to generate chat: {e}")
        return {"status": "error", "message": str(e)}

# ─── The Hearth: a word to the company ──────────────────────────────
#
# The player can send one of three words down to the company from the
# Hearth drawer. Each nudges the whole living roster's mood a little and
# gets an in-character reaction back (LLM when available, canned when not).

HEARTH_WORD_COOLDOWN_SECS = 300

HEARTH_TONES = {
    "rally": {
        "instruction": "The commander just sent word to RALLY — a rousing call to push higher up the Tower. Heroes react in character: fired up, wry, or grumbling but game.",
        "sql": "UPDATE heroes SET morale = MIN(100, morale + 3) WHERE is_alive = 1",
        "fallback": ["To the stairs, then. Again.", "You heard the word. Sharpen up.", "Fine. But I'm finishing my drink first."],
    },
    "reassure": {
        "instruction": "The commander just sent a REASSURING word — steady, warm, telling the company they're doing well and are looked after. Heroes react in character: touched, deflecting, or quietly grateful.",
        "sql": "UPDATE heroes SET stress = MAX(0, stress - 4) WHERE is_alive = 1",
        "fallback": ["...That helps more than I'd admit.", "Tell the commander we're fine. Mostly.", "See? Someone up there remembers us."],
    },
    "rest": {
        "instruction": "The commander just sent word to LET THEM REST — no climbing today, take it easy. Heroes react in character: relieved, suspicious of the kindness, or already asleep.",
        "sql": "UPDATE heroes SET stress = MAX(0, stress - 2), fatigue = MAX(0, COALESCE(fatigue, 0) - 3) WHERE is_alive = 1",
        "fallback": ["Don't have to tell me twice.", "A whole day? What's the catch?", "Wake me when the Tower's gone."],
    },
}


def hearth_word(tone: str) -> dict:
    if tone not in HEARTH_TONES:
        return {"status": "error", "message": "Unknown word."}
    spec = HEARTH_TONES[tone]

    with db() as conn:
        try:
            conn.execute("ALTER TABLE base ADD COLUMN last_hearth_word TIMESTAMP")
        except Exception:
            pass
        base = conn.execute("SELECT last_hearth_word FROM base WHERE id = 1").fetchone()
        last = dict(base).get("last_hearth_word") if base else None
        if last:
            try:
                elapsed = (datetime.utcnow() - datetime.strptime(last, "%Y-%m-%d %H:%M:%S")).total_seconds()
                if elapsed < HEARTH_WORD_COOLDOWN_SECS:
                    return {"status": "cooldown", "remaining": int(HEARTH_WORD_COOLDOWN_SECS - elapsed)}
            except ValueError:
                pass

        heroes = conn.execute(
            "SELECT id, name, personality, hero_class, level FROM heroes WHERE is_alive = 1"
        ).fetchall()
        if not heroes:
            return {"status": "error", "message": "No one is left to hear it."}

        conn.execute(spec["sql"])
        conn.execute("UPDATE base SET last_hearth_word = CURRENT_TIMESTAMP WHERE id = 1")

    speakers = random.sample([dict(h) for h in heroes], min(3, len(heroes)))
    profiles = "\n".join(f"- {h['name']}: Lvl {h['level']} {h['hero_class']}. Personality: {h['personality']}" for h in speakers)
    prompt = f"""
You are writing hero reactions in a dark-fantasy tower-climbing game.
{spec['instruction']}

The heroes reacting are:
{profiles}

Write ONE short reaction line per hero (a single sentence each, in their own voice).
Return ONLY a valid JSON array, no markdown fences:
[{{"speaker": "Hero Name", "message": "Their line"}}, ...]
"""
    chat_data = None
    try:
        response = _generate_chat_text(prompt, max_tokens=200, temperature=0.9)
        parsed = json.loads(_clean_json(response))
        if isinstance(parsed, list) and parsed:
            # Same speaker-coercion as generate_hero_chat: only the heroes
            # we actually sampled may speak.
            by_full = {h["name"]: h["name"] for h in speakers}
            by_first = {h["name"].split()[0].lower(): h["name"] for h in speakers}
            cleaned = []
            for m in parsed:
                spk = str(m.get("speaker", "")).strip()
                real = by_full.get(spk) or by_first.get(spk.split()[0].lower() if spk else "")
                if real and m.get("message"):
                    cleaned.append({"speaker": real, "message": m["message"]})
            if cleaned:
                chat_data = cleaned
    except Exception as e:
        print(f"[Hearth] LLM reaction failed, using fallback: {e}")
    if not chat_data:
        lines = random.sample(spec["fallback"], min(len(speakers), len(spec["fallback"])))
        chat_data = [{"speaker": h["name"], "message": line} for h, line in zip(speakers, lines)]

    with db() as conn:
        conn.execute(
            "INSERT INTO hero_chat_logs (location, message, participants) VALUES (?, ?, ?)",
            ("The Hearth", json.dumps(chat_data), ", ".join(h["name"] for h in speakers)),
        )
        conn.execute("""
            DELETE FROM hero_chat_logs
            WHERE id NOT IN (SELECT id FROM hero_chat_logs ORDER BY created_at DESC LIMIT 5)
        """)
    return {"status": "success", "chat": chat_data, "cooldown": HEARTH_WORD_COOLDOWN_SECS}


import time
import threading

def _should_skip_tick() -> bool:
    """Late at night, most of the roster is asleep — chatter every 5
    minutes regardless of hour read as the whole camp being permanently
    awake. Skips most ticks during that window instead of slowing the
    interval itself, so a tick that DOES fire still has the normal 5-minute
    freshness when someone happens to check in."""
    bucket, _ = _time_of_day_bucket(datetime.now().hour)
    if bucket == "late_night":
        return random.random() < 0.75
    if bucket == "night":
        return random.random() < 0.35
    return False


def chat_worker_loop():
    # Generates immediately on startup instead of only after the first
    # 300s sleep — a short play session never saw any chat at all before
    # this, since the loop used to sleep before ever calling
    # generate_hero_chat() even once. Still every 5 minutes after that.
    try:
        if not _should_skip_tick():
            generate_hero_chat()
    except Exception as e:
        print(f'[Chat Worker] Error: {e}')
    while True:
        try:
            time.sleep(300)  # Generate new chat every 5 mins to save API quota
            if not _should_skip_tick():
                generate_hero_chat()
        except Exception as e:
            print(f'[Chat Worker] Error: {e}')

def start_chat_worker():
    t = threading.Thread(target=chat_worker_loop, daemon=True)
    t.start()
