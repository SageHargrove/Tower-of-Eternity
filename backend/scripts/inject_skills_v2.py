"""
Injects backend/scripts/generated_skills.json (Haiku-authored, validated
30-skill kits — see generate_class_skills.py) into skills_service.py's
SKILL_POOL. Writes the format the code actually reads:
    SKILL_POOL["ClassName"] = {"common": [...], "uncommon": [...], ...}
not a flat list — the earlier version of this script wrote flat lists,
which required a separate repair pass to become usable.

Safe to re-run: it replaces the ENTIRE SKILL_POOL literal with one entry
per class in generated_skills.json (this is a full regeneration pass —
every one of the game's 148 classes gets a complete 30-skill kit here, so
there's no legacy content to preserve/merge around).
"""
import json
import os
import re

backend_dir = os.path.dirname(os.path.abspath(__file__))
generated_file = os.path.join(backend_dir, "generated_skills.json")
service_file = os.path.join(os.path.dirname(backend_dir), "services", "skills_service.py")

RARITY_ORDER = ["common", "uncommon", "rare", "epic", "legendary"]


def to_pool_dict(skills: list[dict]) -> dict:
    pool = {r: [] for r in RARITY_ORDER}
    for s in skills:
        entry = dict(s)
        entry.pop("rarity", None)  # rarity is the dict KEY, not a field on the skill
        pool[s["rarity"]].append(entry)
    return pool


def py_literal(pool: dict) -> str:
    """json.dumps gives valid Python for everything except true/false/null."""
    text = json.dumps(pool, indent=8)
    text = re.sub(r':\s*true\b', ': True', text)
    text = re.sub(r':\s*false\b', ': False', text)
    text = re.sub(r':\s*null\b', ': None', text)
    return text


def main():
    with open(generated_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    with open(service_file, "r", encoding="utf-8") as f:
        src = f.read()

    # Replace the whole `SKILL_POOL = { ... }` top-level literal (matched by
    # bracket depth, not regex greediness, so nested braces in skill effects
    # don't truncate the match early).
    start = src.index("SKILL_POOL = {")
    brace_start = src.index("{", start)
    depth = 0
    i = brace_start
    for i in range(brace_start, len(src)):
        if src[i] == "{":
            depth += 1
        elif src[i] == "}":
            depth -= 1
            if depth == 0:
                break
    end = i + 1  # position just past the matching closing brace

    entries = []
    for class_data in data:
        cname = class_data["class_name"]
        pool = to_pool_dict(class_data["skills"])
        entries.append(f'    "{cname}": {py_literal(pool)}')

    new_block = "SKILL_POOL = {\n" + ",\n".join(entries) + "\n}"
    new_src = src[:start] + new_block + src[end:]

    with open(service_file, "w", encoding="utf-8") as f:
        f.write(new_src)

    print(f"Injected {len(data)} classes into skills_service.py (full SKILL_POOL replacement).")


if __name__ == "__main__":
    main()
