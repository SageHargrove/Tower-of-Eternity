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
    
    # Load already generated so we can resume
    generated_classes = set()
    out_file = os.path.join(os.path.dirname(__file__), "generated_skills.json")
    if os.path.exists(out_file):
        try:
            with open(out_file, "r") as f:
                data = json.load(f)
                for c in data:
                    generated_classes.add(c["class_name"])
        except Exception:
            pass

    for cls in ALL_CLASSES:
        if cls not in EXISTING_KITS and cls not in generated_classes:
            missing.append(cls)
    return missing

prompt_template = """
You are an expert game designer for a deep RPG auto-battler. Design skills
that are MECHANICALLY INSANE and build-defining — not just flat stat buffs.
The combat engine now supports a rich, composable effect system; USE IT.

For each class, design exactly 30 unique skills distributed EXACTLY as follows: 
10 Common, 8 Uncommon, 6 Rare, 4 Epic, and 2 Legendary. 
CRITICAL RULES:
1. Every single rarity tier MUST contain at least 1 "active" skill and at least 1 "passive" skill. For example, the 2 Legendaries must be exactly 1 Active and 1 Passive.
2. Overall across the 30 skills, there should be fewer actives and more passives (e.g. ~10 actives, ~20 passives).
3. Passives can be incredibly strong, game-changing conditional effects at higher rarities.
Commons should be basic attacks or simple passives. 
Legendary actives MUST be mechanically insane, fight-winning ultimates (massive AoE executes, team-wide revives). 
Fights are auto-battled front-to-back; positioning and status effects matter.

Output MUST be a valid JSON array, this exact structure:
[
  {{
    "class_name": "The Class Name",
    "skills": [
      {{
        "id": "snake_case_id",
        "name": "Skill Name",
        "type": "active",              // "active" or "passive"
        "rarity": "legendary",         // "common", "uncommon", "rare", "epic", or "legendary"
        "desc": "Punchy description (max 14 words)",
        "effect": {{ ... }}            // see schemas below
      }}
    ]
  }}
]

═══ ACTIVE SKILL SCHEMA (the powerful one — prefer this for actives) ═══
"effect": {{
  "mana_cost": 30,                     // 15-60; bigger effects cost more
  "cooldown": 3,                       // 1-5 rounds
  "target": "<mode>",                  // WHO it hits (see targets below)
  "target_count": 2,                   // only for random_enemies / random_allies
  "actions": [ <action>, ... ],        // WHAT happens to the target(s)
  "self_actions": [ <action>, ... ]    // optional: effects on the caster
}}

TARGET modes:
  Enemies: one_enemy, all_enemies, random_enemies, lowest_hp_enemy,
           highest_hp_enemy, strongest_enemy, weakest_enemy,
           frontline_enemies, backline_enemies, enemy_column
  Allies:  self, all_allies, lowest_hp_ally, random_allies, wounded_allies,
           dead_ally (for revive)

ACTION kinds (compose 1-3 per skill for combos):
  {{"kind":"damage","power":2.5,"stat":"auto"|"strength"|"intelligence",
     "ignore_def":0.5,          // 0-1, fraction of defense ignored (armor pen)
     "true_damage":true,        // ignores ALL mitigation (use sparingly)
     "crit_bonus":0.3,          // added crit chance for this hit
     "guaranteed_crit":true,
     "execute_threshold":0.3,"execute_bonus":0.5,  // bonus dmg vs low-hp
     "lifesteal":0.3,           // heal caster for % of damage dealt
     "chain":2,"chain_falloff":0.6}}   // bounce to N more foes at falling power
  {{"kind":"execute","threshold":0.25}}            // instakill below 25% HP
  {{"kind":"heal","pct":0.3}} OR {{"kind":"heal","heal_power":1.5,"stat":"intelligence"}}
  {{"kind":"status","status":"<status>","duration":2,"magnitude":0.4}}
  {{"kind":"buff","stat":"strength","pct":0.5,"duration":2}}   // timed, reverts
  {{"kind":"debuff","stat":"agility","pct":0.4,"duration":2}}
  {{"kind":"shield","status":"shield","duration":2,"magnitude":0.2}} // absorb 20% max HP
  {{"kind":"cleanse","count":2}}     // remove debuffs from targets (allies)
  {{"kind":"dispel","count":1}}      // strip buffs from targets (enemies)
  {{"kind":"restore_mana","amount":30}} / {{"kind":"drain_mana","amount":25}}
  {{"kind":"revive","pct":0.4}}      // target must be dead_ally

STATUS types for {{"kind":"status"}}:
  stun / freeze (skip their turn), blind (60% miss chance),
  silence (can't cast skills), disarm, taunting (forces enemies to hit them),
  bleed / poison / burn (damage-over-time; poison magnitude = dmg per tick),
  evasion (magnitude = added dodge chance, e.g. 0.5), invuln (immune to damage),
  regen (magnitude = % max HP healed per turn), dmg_shield (magnitude = % dmg reduced)

═══ PASSIVE SKILL SCHEMA ═══
Flat modifiers: {{"str_pct":0.15}}, {{"int_pct":0.15}}, {{"agi_pct":0.15}},
  {{"hlt_pct":0.15}}, {{"all_pct":0.1}}, {{"crit_pct":0.1}}, {{"dodge_pct":0.1}},
  {{"armor_pen":0.2}}, {{"regen_pct":0.05}}, {{"dmg_reduction_pct":0.15}},
  {{"physical_resist_pct":0.2}}, {{"magic_resist_pct":0.2}}, {{"fear_immune":true}},
  {{"death_save":1}}

CONDITIONAL TRIGGERS (the exciting passives) — reactive effects:
"effect": {{"triggers": [
  {{"event":"<event>","chance":0.5,"name":"Trigger Name",
    "target":"<mode or omit for the unit that caused it>",
    "actions":[ <action>, ... ]}}
]}}
  events: on_hit_taken (counter-attack), on_dodge, on_kill,
          on_ally_death, on_low_hp
  Example — a thorns/riposte passive:
    {{"triggers":[{{"event":"on_hit_taken","chance":0.4,"name":"Riposte",
      "actions":[{{"kind":"damage","power":1.0,"stat":"strength"}}]}}]}}

DESIGN GUIDANCE:
- Make skills feel like the class fantasy: an Assassin executes and bleeds; a
  Cleric shields, cleanses, and revives; a Warden taunts and gains regen; a
  Sniper hits backline_enemies with armor pen; a Time Mage silences + debuffs.
- Combine actions: damage + apply a debuff, or damage + self-buff.
- Balance: power 1.5-3.0 for single-target, 0.8-1.5 for all_enemies.
  execute thresholds 0.2-0.35. Strong effects → higher mana_cost/cooldown.
- Use conditional triggers liberally on passives — they make builds sing.

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
    
    # We must drop the batch size to 1 because asking for 30 skills per class 
    # will quickly blow past the 8192 output token limit of the LLM if we batch them.
    batch_size = 1
    batches = [missing[i:i + batch_size] for i in range(0, len(missing), batch_size)]
    
    all_results = []
    for i, batch in enumerate(batches):
        print(f"Processing batch {i+1}/{len(batches)}...")
        results = await generate_batch(batch)
        all_results.extend(results)
        await asyncio.sleep(2) # rate limit buffer
        
    out_file = os.path.join(os.path.dirname(__file__), "generated_skills.json")
    
    # Load existing to append
    if os.path.exists(out_file):
        with open(out_file, "r") as f:
            existing_data = json.load(f)
            all_results = existing_data + all_results

    with open(out_file, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"Successfully generated {len(all_results)} class kits! Saved to {out_file}.")

if __name__ == "__main__":
    asyncio.run(main())
