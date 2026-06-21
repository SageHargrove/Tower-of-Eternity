import json
import random
from database import db
from services.llm_service import _generate_with_fallback, _clean_json

def generate_hero_chat(location: str = "The Square") -> dict:
    """
    Selects a few random alive heroes and uses the LLM to generate a chat log 
    between them based on their personality, traits, and current location.
    """
    with db() as conn:
        heroes = conn.execute("SELECT id, name, personality, hero_class, level, ego_type FROM heroes WHERE is_alive = 1").fetchall()
        
    if not heroes:
        return {"status": "error", "message": "No alive heroes to chat."}
        
    # Pick 2-3 heroes to chat
    num_chatters = min(random.randint(2, 3), len(heroes))
    chatters = random.sample(heroes, num_chatters)
    
    chatter_profiles = []
    for h in chatters:
        ego = f" (Ego: {h['ego_type']})" if h["ego_type"] else ""
        chatter_profiles.append(f"- {h['name']}: Lvl {h['level']} {h['hero_class']}{ego}. Personality: {h['personality']}")
        
    prompt = f"""
You are writing a short, in-character chat log for a group of heroes hanging out in the base camp.
The current location they are at is: {location}.

The heroes participating are:
{chr(10).join(chatter_profiles)}

Write a short, engaging 3-5 line conversation between them. Keep it realistic to their personalities. They might discuss recent battles, the location they are in, or bicker based on their egos.

Return ONLY a valid JSON array of message objects. Do not wrap in markdown tags like ```json.
Format:
[
  {{"speaker": "Hero Name", "message": "Their dialogue here"}},
  ...
]
"""
    try:
        response = _generate_with_fallback(prompt, max_tokens=300)
        chat_data = json.loads(_clean_json(response))
        
        # Save to DB
        if isinstance(chat_data, list) and len(chat_data) > 0:
            with db() as conn:
                participants_str = ", ".join([h["name"] for h in chatters])
                # Save as a single block for the UI to parse
                conn.execute(
                    "INSERT INTO hero_chat_logs (location, message, participants) VALUES (?, ?, ?)",
                    (location, json.dumps(chat_data), participants_str)
                )
            return {"status": "success", "chat": chat_data, "participants": participants_str, "location": location}
    except Exception as e:
        print(f"[Chat] Failed to generate chat: {e}")
        return {"status": "error", "message": str(e)}

import time
import threading

def chat_worker_loop():
    while True:
        try:
            time.sleep(300)  # Generate new chat every 5 mins to save API quota
            generate_hero_chat()
        except Exception as e:
            print(f'[Chat Worker] Error: {e}')

def start_chat_worker():
    t = threading.Thread(target=chat_worker_loop, daemon=True)
    t.start()
