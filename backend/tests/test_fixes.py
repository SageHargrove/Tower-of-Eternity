import asyncio
import sys
from database import db, init_db
from routers.base import get_research_upgrades, list_equipment
from services.portrait_cache import build_varied_prompt
from services.llm_service import generate_hero_profile

def test():
    init_db()

    print("--- Test 1: Mage Tower Endpoint ---")
    try:
        upgrades = get_research_upgrades()
        print("Success: get_research_upgrades returned:", upgrades)
    except Exception as e:
        print("Fail: get_research_upgrades threw:", e)

    print("\n--- Test 2: Equipment list ---")
    try:
        equip = list_equipment()
        print("Success: list_equipment returned:", len(equip["equipped"]), "equipped,", len(equip["unequipped"]), "unequipped")
    except Exception as e:
        print("Fail: list_equipment threw:", e)

    print("\n--- Test 3: 1-Star Hero Portrait Prompt ---")
    prompt_1 = build_varied_prompt(1)
    print("Prompt 1-star:", prompt_1)
    if "highly detailed face, masterpiece" in prompt_1:
        print("Success: Contains high visual fidelity tags")
    else:
        print("Fail: Missing high visual fidelity tags")

    print("\n--- Test 4: Heterochromia checks ---")
    # Generate 50 4-star prompts to ensure no heterochromia
    hetero_count = 0
    for _ in range(50):
        p = build_varied_prompt(4)
        if "heterochromia" in p.lower() or "two colored" in p.lower():
            hetero_count += 1
    print("Heterochromia count in 4-stars:", hetero_count)
    if hetero_count == 0:
        print("Success: No heterochromia in 4-stars")
    else:
        print("Fail: Found heterochromia in 4-stars")

    print("\nAll tests finished.")

if __name__ == "__main__":
    test()
