import sys
import os
import time

from database import db
from services.comfy_service import generate_portrait_comfy

def test_evolution(hero_id: int, new_star_level: int, denoise: float):
    print(f"Testing evolution for hero {hero_id} to {new_star_level} star with denoise {denoise}...")
    
    with db() as conn:
        hero = conn.execute("SELECT name, hero_class, gender, portrait_path FROM heroes WHERE id = ?", (hero_id,)).fetchone()
        if not hero:
            print("Hero not found.")
            return
            
    old_path = hero["portrait_path"]
    if not old_path or not os.path.exists(old_path):
        print(f"Original portrait not found at {old_path}.")
        return
            
    name = hero["name"]
    hero_class = hero["hero_class"]
    gender = hero["gender"] or "unknown"
    gender_norm = gender if gender and gender != "unknown" else "1person"
    
    if new_star_level == 2:
        tier_prompt = "(slightly better gear:1.1), battle-tested, leather armor upgrades"
        denoise_val = 0.43 if denoise is None else denoise
    elif new_star_level == 3:
        tier_prompt = "(seasoned veteran:1.15), (heavy armor:1.15), (subtle magical glow:1.15), intricate details"
        denoise_val = 0.45 if denoise is None else denoise
    elif new_star_level == 4:
        tier_prompt = "(elite champion:1.2), (ornate heavy armor:1.2), (glowing magical aura:1.2), intense rim lighting"
        denoise_val = 0.48 if denoise is None else denoise
    elif new_star_level == 5:
        tier_prompt = "(legendary hero:1.2), (majestic epic godlike armor:1.25), (blazing magical aura bursting:1.2), (floating glowing particles:1.2), transcendent lighting"
        denoise_val = 0.51 if denoise is None else denoise
    elif new_star_level == 6:
        tier_prompt = "(transcendent dark fantasy champion:1.25), (impossible cosmic armor:1.25), (intense blinding aura:1.25), (reality warping:1.2), wide open glowing eyes, god-tier power"
        denoise_val = 0.53 if denoise is None else denoise
    else:
        tier_prompt = "(god-tier dark fantasy champion:1.3), (blinding cosmic energy bursting:1.3), (huge glowing energy wings:1.3), transcendent reality-breaking power, wide open glowing eyes, (highest tier glowing artifact armor:1.3)"
        denoise_val = 0.55 if denoise is None else denoise

    prompt = f"centered face, upper body, {gender_norm} {hero_class}, exact same face, wide open eyes, looking at viewer, {tier_prompt}, intricate details, masterpiece, best quality"
    
    safe_name = name.replace(" ", "_").lower()
    custom_dir = f"static/portraits/test"
    os.makedirs(custom_dir, exist_ok=True)
    
    filename = f"{custom_dir}/test_{safe_name}_evo_{new_star_level}star_{denoise_val}_{int(time.time())}.png"
    
    success = generate_portrait_comfy(prompt, filename, init_image_path=old_path, denoise=denoise_val)
    
    if success:
        print(f"Success! Saved test portrait to backend/{filename}")
    else:
        print("Failed to generate portrait.")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python test_evo.py <hero_id> <new_star_level> [denoise]")
        sys.exit(1)
        
    hero_id = int(sys.argv[1])
    star = int(sys.argv[2])
    denoise = float(sys.argv[3]) if len(sys.argv) > 3 else None
    
    test_evolution(hero_id, star, denoise)
