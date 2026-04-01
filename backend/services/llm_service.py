import os
import json
import re
from google import genai
from google.genai import types
from pydantic import BaseModel

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Free tier text model
TEXT_MODEL = "gemini-3-flash-preview"
# Paid image model (~$0.02/image)
IMAGE_MODEL = "imagen-4.0-fast-generate-001"

RARITY_FLAVOR = {
    1: "a common peasant, laborer, or wanderer with humble origins",
    2: "a minor adventurer or soldier with some experience",
    3: "a seasoned fighter, skilled craftsman, or minor mage",
    4: "an elite warrior, veteran commander, or powerful spellcaster",
    5: "a legendary hero, archmage, or noble champion",
    6: "a near-mythic figure, ancient warrior, or transcendent being",
    7: "an impossibly rare entity — a demigod, an immortal, or a living legend",
}

class HeroProfile(BaseModel):
    name: str
    title: str
    backstory: str
    personality: str
    portrait_prompt: str


def generate_hero_profile(birth_star: int, aptitudes: dict) -> HeroProfile:
    apt_names = {
        "apt_combat": "combat prowess",
        "apt_tactical": "tactical genius",
        "apt_survival": "survival instinct",
        "apt_mental": "mental fortitude",
        "apt_leadership": "leadership presence",
    }
    top_apt = max(aptitudes, key=aptitudes.get)
    top_apt_label = apt_names.get(top_apt, "unknown gift")

    prompt = f"""You are generating a hero for a dark fantasy roguelike tower-climbing game.

Hero rarity: {birth_star}★ — {RARITY_FLAVOR[birth_star]}
This hero has a notable hidden gift in: {top_apt_label} (do NOT state this directly — hint at it through personality and backstory)

Generate a hero profile. Be creative, grounded, and avoid clichés.
The world is dark, morally complex, and dangerous. Heroes are people, not archetypes.

Respond ONLY with valid JSON and nothing else — no markdown, no backticks, no preamble:
{{
  "name": "Full name (culturally varied, not generic fantasy)",
  "title": "Short epithet or nickname (e.g. 'The Twice-Burned', 'Ash of the North')",
  "backstory": "2-3 sentences. Specific, evocative, no tropes.",
  "personality": "1-2 sentences. How they act under pressure.",
  "portrait_prompt": "A detailed image gen prompt for a portrait. Dark fantasy style, painterly. No text. Describe appearance, mood, lighting."
}}"""

    response = client.models.generate_content(
        model=TEXT_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(temperature=0.9, max_output_tokens=600),
    )

    raw = response.text.strip()
    raw = re.sub(r'^```json\s*', '', raw)
    raw = re.sub(r'\s*```$', '', raw)
    data = json.loads(raw)
    return HeroProfile(**data)


def generate_portrait(portrait_prompt: str, hero_name: str) -> str | None:
    try:
        response = client.models.generate_images(
            model=IMAGE_MODEL,
            prompt=portrait_prompt + " Portrait orientation. No text. Dark fantasy painting style.",
            config=types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio="1:1",
                output_mime_type="image/png",
            ),
        )
        image_data = response.generated_images[0].image.image_bytes
        safe_name = re.sub(r'[^a-z0-9]', '_', hero_name.lower())[:30]
        filename = f"static/portraits/{safe_name}_{abs(hash(hero_name))}.png"
        with open(filename, "wb") as f:
            f.write(image_data)
        return filename
    except Exception as e:
        print(f"Portrait generation failed: {e}")
        return None


def generate_combat_narration(combat_log: list, hero_names: list[str]) -> str:
    log_text = "\n".join([f"- {e}" for e in combat_log[-10:]])
    prompt = f"""You are narrating a battle in a dark fantasy roguelike game.
Heroes involved: {', '.join(hero_names)}

Combat events:
{log_text}

Write 2-4 sentences of vivid, grim narration. Focus on emotional weight, not just actions.
Be specific about names. Do not sugarcoat deaths or losses.
Respond with only the narration text, no preamble."""

    response = client.models.generate_content(
        model=TEXT_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(temperature=0.8, max_output_tokens=200),
    )
    return response.text.strip()


def generate_event_text(floor_number: int, event_type: str, context: str = "") -> dict:
    prompt = f"""You are generating a floor event for a dark fantasy roguelike.
Floor: {floor_number}, Event type: {event_type}
Context: {context or "Standard tower exploration."}

Respond ONLY with valid JSON and nothing else — no markdown, no backticks:
{{
  "title": "Short event name",
  "description": "2-3 sentence scene description. Grim, specific, atmospheric.",
  "choices": [
    {{"id": "a", "text": "Choice text", "hint": "Vague hint at consequence"}},
    {{"id": "b", "text": "Choice text", "hint": "Vague hint at consequence"}}
  ]
}}"""

    response = client.models.generate_content(
        model=TEXT_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(temperature=0.85, max_output_tokens=400),
    )
    raw = response.text.strip()
    raw = re.sub(r'^```json\s*', '', raw)
    raw = re.sub(r'\s*```$', '', raw)
    return json.loads(raw)
