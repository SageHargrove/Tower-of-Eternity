"""
Portrait Cache System
=====================
Pre-generates portraits in the background so hero pulls are instant.
Optimized prompts for NoobAI V-pred — anime character portraits, dark fantasy.
"""

import threading
import random
import os
import re
import time
from database import db

CACHE_TARGET = 20
MIN_PER_STAR = {
    1: 5,
    2: 4,
    3: 4,
    4: 3,
    5: 2,
    6: 1,
    7: 1,
}

# NoobAI V-pred responds best to:
# - explicit composition tags (upper body, portrait)
# - looking at viewer for character focus
# - specific lighting descriptors
# - dark fantasy flavor in clothing/mood, NOT environment
# Gender split ~50/50 per tier for variety

ARCHETYPE_PROMPTS = {
    1: [
        "1boy, upper body, looking at viewer, portrait, young male soldier, worn leather armor, dirt on face, tired eyes, short messy hair, dark fantasy, dim torchlight, detailed face, serious expression",
        "1girl, upper body, looking at viewer, portrait, young female scavenger, patched cloak, cautious expression, dark circles under eyes, dark fantasy, candlelight, detailed face, survival gear",
        "1boy, upper body, looking at viewer, portrait, peasant fighter, simple iron sword over shoulder, hollow cheeks, rough stubble, dark fantasy, shadow lighting, detailed face, worn expression",
        "1girl, upper body, looking at viewer, portrait, young female archer, simple bow, determined eyes, braided hair, minor cuts on face, dark fantasy, moonlight, detailed face",
        "1boy, upper body, looking at viewer, portrait, young male laborer turned warrior, calloused hands gripping sword, haunted expression, dark fantasy, firelight, detailed face, disheveled",
    ],
    2: [
        "1boy, upper body, looking at viewer, portrait, male mercenary, chainmail armor, battle scar across cheek, short dark hair, dark fantasy, campfire lighting, detailed face, weathered",
        "1girl, upper body, looking at viewer, portrait, female soldier, dented shield, tired but fierce eyes, ponytail, dark fantasy, fortress torchlight, detailed face, determined expression",
        "1boy, upper body, looking at viewer, portrait, male ranger, leather pauldrons, calm watchful eyes, hooded cloak, dark fantasy, forest moonlight, detailed face",
        "1girl, upper body, looking at viewer, portrait, female mage apprentice, simple robes, faint magical glow in eyes, dark fantasy, candlelight, detailed face, focused expression",
    ],
    3: [
        "1boy, upper body, looking at viewer, portrait, male seasoned warrior, half-plate armor, blood on gauntlet, strong jaw, dark fantasy, dramatic torchlight, detailed face, battle-hardened",
        "1girl, upper body, looking at viewer, portrait, female battle mage, dark robes with silver trim, glowing purple eyes, silver hair, dark fantasy, magical light, detailed face, intense",
        "1boy, upper body, looking at viewer, portrait, male veteran knight, ornate pauldrons, grey-streaked hair, commanding presence, dark fantasy, cathedral light, detailed face",
        "1girl, upper body, looking at viewer, portrait, female assassin, form-fitting dark armor, sharp calculating eyes, dark braid, dark fantasy, shadow lighting, detailed face, cold expression",
    ],
    4: [
        "1boy, upper body, looking at viewer, portrait, male elite knight, ornate black armor with gold trim, imposing presence, strong features, dark fantasy, dramatic side lighting, detailed face, noble bearing",
        "1girl, upper body, looking at viewer, portrait, female commander, silver armor, silver hair, commanding golden eyes, battle-worn cloak, dark fantasy, war camp lighting, detailed face, authoritative",
        "1boy, upper body, looking at viewer, portrait, male arcane warrior, runed armor, glowing blue tattoos on neck, dark fantasy, arcane light, detailed face, intense concentration",
        "1girl, upper body, looking at viewer, portrait, female warlord, spiked pauldrons, red war paint, fierce amber eyes, dark fantasy, firelight, detailed face, battle fury",
    ],
    5: [
        "1boy, upper body, looking at viewer, portrait, legendary male warrior, glowing eyes, ethereal aura, ancient ornate armor with glowing runes, white hair, dark fantasy, dramatic divine light, detailed face, transcendent expression",
        "1girl, upper body, looking at viewer, portrait, legendary female archmage, floating magical artifacts around her, violet glowing eyes, silver hair flowing, dark fantasy, magical storm light, detailed face, otherworldly beauty",
        "1boy, upper body, looking at viewer, portrait, legendary male champion, divine golden armor, scarred heroic face, golden eyes, dark fantasy, heavenly shaft of light, detailed face, resolute",
    ],
    6: [
        "1girl, upper body, looking at viewer, portrait, near-mythic female immortal, impossibly beautiful, pale skin, dark energy crackling around black armor, white hair, glowing void eyes, dark fantasy, dimensional light, detailed face, ancient and cold",
        "1boy, upper body, looking at viewer, portrait, ancient male immortal warrior, timeless ageless face, black and gold armor with impossible runes, silver eyes, dark fantasy, cosmic light, detailed face, serene and terrifying",
    ],
    7: [
        "1girl, upper body, looking at viewer, portrait, female demigod, reality warping around her, burning white eyes, divine dark armor, white hair flowing with cosmic energy, dark fantasy, transcendent cosmic light, detailed face, overwhelming presence",
        "1boy, upper body, looking at viewer, portrait, male living legend, godlike presence, burning golden eyes, ancient black armor with living runes, dark fantasy, impossible divine light, detailed face, absolute power",
    ],
}

def init_cache_table():
    with db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS portrait_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                birth_star INTEGER NOT NULL,
                path TEXT NOT NULL,
                used INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

def get_cache_counts() -> dict:
    with db() as conn:
        rows = conn.execute("""
            SELECT birth_star, COUNT(*) as cnt
            FROM portrait_cache
            WHERE used = 0
            GROUP BY birth_star
        """).fetchall()
    return {r["birth_star"]: r["cnt"] for r in rows}

def claim_cached_portrait(birth_star: int) -> str | None:
    with db() as conn:
        row = conn.execute("""
            SELECT id, path FROM portrait_cache
            WHERE birth_star = ? AND used = 0
            ORDER BY created_at ASC
            LIMIT 1
        """, (birth_star,)).fetchone()
        if not row:
            return None
        conn.execute("UPDATE portrait_cache SET used = 1 WHERE id = ?", (row["id"],))
        return row["path"]

def add_to_cache(birth_star: int, path: str):
    with db() as conn:
        conn.execute(
            "INSERT INTO portrait_cache (birth_star, path) VALUES (?,?)",
            (birth_star, path)
        )

def update_hero_portrait(hero_id: int, path: str):
    with db() as conn:
        conn.execute(
            "UPDATE heroes SET portrait_path = ? WHERE id = ?",
            (path, hero_id)
        )

def _generate_one_cached(birth_star: int):
    try:
        from services.comfy_service import generate_portrait_comfy
        prompt = random.choice(ARCHETYPE_PROMPTS.get(birth_star, ARCHETYPE_PROMPTS[1]))
        filename = f"static/portraits/cached_{birth_star}star_{int(time.time())}_{random.randint(1000,9999)}.png"
        success = generate_portrait_comfy(prompt, filename)
        if success:
            add_to_cache(birth_star, filename)
            print(f"[Cache] Generated {birth_star}★ portrait → {filename}")
        else:
            print(f"[Cache] Generation failed for {birth_star}★")
    except Exception as e:
        print(f"[Cache] Error generating {birth_star}★: {e}")

def _generate_custom_portrait(hero_id: int, portrait_prompt: str, hero_name: str):
    """Generate hero-specific portrait using Gemini's portrait_prompt, swap it in."""
    try:
        from services.comfy_service import generate_portrait_comfy
        safe_name = re.sub(r'[^a-z0-9]', '_', hero_name.lower())[:30]
        filename = f"static/portraits/custom_{safe_name}_{int(time.time())}.png"

        # Wrap Gemini's prompt with NoobAI quality tags
        full_prompt = (
            "1person, upper body, looking at viewer, portrait, "
            "detailed face, dark fantasy, "
            + portrait_prompt
        )
        success = generate_portrait_comfy(full_prompt, filename)
        if success:
            update_hero_portrait(hero_id, filename)
            print(f"[Cache] Custom portrait ready for hero {hero_id}")
    except Exception as e:
        print(f"[Cache] Custom portrait failed for hero {hero_id}: {e}")

def fill_cache_background():
    print("[Cache] Background portrait worker started.")
    while True:
        try:
            counts = get_cache_counts()
            for star, minimum in MIN_PER_STAR.items():
                current = counts.get(star, 0)
                needed = minimum - current
                for _ in range(needed):
                    _generate_one_cached(star)
                    time.sleep(0.5)
        except Exception as e:
            print(f"[Cache] Worker error: {e}")
        time.sleep(30)

def queue_custom_portrait(hero_id: int, portrait_prompt: str, hero_name: str):
    t = threading.Thread(
        target=_generate_custom_portrait,
        args=(hero_id, portrait_prompt, hero_name),
        daemon=True
    )
    t.start()

def start_cache_worker():
    init_cache_table()
    t = threading.Thread(target=fill_cache_background, daemon=True)
    t.start()