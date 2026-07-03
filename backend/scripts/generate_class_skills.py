import os
import sys
import json
import asyncio
from dotenv import load_dotenv

# Add backend to path so we can import services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

from services.class_service import ALL_CLASSES
from services.skills_service import WEAPON_ART_SKILLS
from google import genai
from google.genai import types
import re

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Existing kits in skills_service.py that we don't need to overwrite
EXISTING_KITS = {
    "Rookie", "Squire", "Thief", "Acolyte", "Apprentice", "Archer",
    # Advanced
    "Knight", "Assassin", "Cleric", "Sorcerer", "Ranger",
    # Master
    "Paladin", "Nightblade", "High Priest", "Archmage", "Sniper",
    # Specialized
    "Berserker", "Druid", "Necromancer", "Bard", "Monk"
}

def get_missing_classes():
    missing = []
    for cls in ALL_CLASSES:
        if cls not in EXISTING_KITS:
            missing.append(cls)
    return missing

prompt_template = """
You are an expert game designer for an RPG auto-battler.
I will give you a list of RPG character classes. For each class, design exactly 5 unique skills (a mix of passive and active).

The output MUST be a valid JSON array of objects, matching this exact structure:
[
  {{
    "class_name": "The Class Name",
    "skills": [
      {{
        "id": "skill_id_like_this",
        "name": "Skill Name",
        "type": "active", // or "passive"
        "desc": "Short, punchy description (max 12 words)",
        "cooldown": 3, // only if active
        "effect": {{"hlt_pct": 0.1}} // Some thematic effect dictionary
      }}
    ]
  }}
]

Valid effect keys (use 1-2 per skill):
- atk_pct (e.g. 1.5 for 150% damage)
- heal_pct (e.g. 0.2 for 20% max hp heal to lowest ally)
- self_heal_pct
- hlt_pct, str_pct, def_pct, int_pct, agi_pct, lck_pct (passives)
- cleanse_self (True)
- death_heal (True)
- regen_pct (e.g. 0.05 for 5% hp per turn)
- mana_cost (e.g. 20)
- crushing_blow (True - chance to deal massive damage)
- enrage (True)

Here are the classes to generate for:
{classes}
"""

async def generate_batch(classes_batch):
    prompt = prompt_template.format(classes=json.dumps(classes_batch))
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.7,
            ),
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"Error on batch: {e}")
        return []

async def main():
    missing = get_missing_classes()
    print(f"Found {len(missing)} missing classes to generate.")
    
    batch_size = 10
    batches = [missing[i:i + batch_size] for i in range(0, len(missing), batch_size)]
    
    all_results = []
    for i, batch in enumerate(batches):
        print(f"Processing batch {i+1}/{len(batches)}...")
        results = await generate_batch(batch)
        all_results.extend(results)
        await asyncio.sleep(2) # rate limit buffer
        
    out_file = os.path.join(os.path.dirname(__file__), "generated_skills.json")
    with open(out_file, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"Successfully generated {len(all_results)} class kits! Saved to {out_file}.")

if __name__ == "__main__":
    asyncio.run(main())
