"""
Fix the SKILL_POOL format to match what the code expects:
- Original/Expected format: {"ClassName": {"common": [...], "uncommon": [...], ...}}
- Injected format (wrong): {"ClassName": [...]}

This script converts the incorrectly formatted SKILL_POOL back to the correct nested format.
"""
import json
import os
import re
import subprocess

backend_dir = os.path.dirname(os.path.abspath(__file__))
generated_file = os.path.join(backend_dir, "generated_skills.json")
service_file = os.path.join(os.path.dirname(backend_dir), "services", "skills_service.py")

print("Loading generated skills...")
with open(generated_file, "r", encoding="utf-8") as f:
    generated_data = json.load(f)

# These are the hand-tuned classes that should be preserved from git history
EXISTING_KITS = {
    "Rookie", "Squire", "Thief", "Acolyte", "Apprentice", "Archer",
    "Knight", "Assassin", "Cleric", "Sorcerer", "Ranger",
    "Paladin", "Nightblade", "High Priest", "Archmage", "Sniper",
    "Berserker", "Druid", "Necromancer", "Bard", "Monk"
}

print("\nExtracting existing hand-tuned skills from git history...")
try:
    # Get the original skills_service.py from git
    result = subprocess.run(
        ["git", "show", "HEAD:backend/services/skills_service.py"],
        cwd=os.path.dirname(os.path.dirname(backend_dir)),
        capture_output=True,
        text=True,
        timeout=10
    )
    original_content = result.stdout

    # Parse out the SKILL_POOL from the original
    # Find the SKILL_POOL = { line and extract until the closing }
    match = re.search(r'SKILL_POOL\s*=\s*\{(.*?)(\n\s*# [\w\s:=-]+)?(?=\n[A-Z_]+\s*=)', original_content, re.DOTALL)
    if match:
        skill_pool_content = match.group(1)

        # Try to extract the existing classes
        existing_entries = {}
        class_pattern = r'"([^"]+)"\s*:\s*\{((?:[^{}]|(?:\{[^}]*\}))*)\}'
        for class_match in re.finditer(class_pattern, skill_pool_content, re.DOTALL):
            class_name = class_match.group(1)
            if class_name in EXISTING_KITS:
                # Extract the full nested structure
                full_match_start = match.start(1) + class_match.start()
                # Find the next class or end of dict
                next_class_match = re.search(r'^\s*"[^"]+"\s*:', skill_pool_content[class_match.end():], re.MULTILINE)
                if next_class_match:
                    full_match_end = match.start(1) + class_match.end() + next_class_match.start()
                else:
                    full_match_end = match.start(1) + len(skill_pool_content)

                existing_entries[class_name] = original_content[full_match_start:full_match_end].rstrip(',').rstrip()

        print(f"Found {len(existing_entries)} existing class entries")
except Exception as e:
    print(f"Warning: Could not extract from git: {e}")
    print("Will continue with only generated skills")
    existing_entries = {}

print("\nConverting generated skills to nested format...")

def convert_to_nested_dict(skills_list):
    """Convert flat list of skills to nested dictionary by rarity"""
    result = {}
    for skill in skills_list:
        rarity = skill.get('rarity', 'common')
        if rarity not in result:
            result[rarity] = []
        # Don't include the rarity field in nested skills
        skill_copy = {k: v for k, v in skill.items() if k != 'rarity'}
        result[rarity].append(skill_copy)
    return result

# Generate the SKILL_POOL dictionary
skill_pool_dict = {}

# Add existing hand-tuned classes
for class_data in generated_data:
    class_name = class_data['class_name']
    if class_name in EXISTING_KITS:
        # These should come from git, but if not found, use generated
        if class_name not in existing_entries:
            skills_by_rarity = convert_to_nested_dict(class_data['skills'])
            skill_pool_dict[class_name] = skills_by_rarity
    else:
        # Generated classes - convert to nested format
        skills_by_rarity = convert_to_nested_dict(class_data['skills'])
        skill_pool_dict[class_name] = skills_by_rarity

# Generate Python code
def serialize_skill_pool(pool_dict):
    """Serialize skill pool to Python code with proper indentation"""
    lines = ["SKILL_POOL = {"]

    for class_name in sorted(pool_dict.keys()):
        nested = pool_dict[class_name]
        lines.append(f'    "{class_name}": {{')

        for rarity in ['common', 'uncommon', 'rare', 'epic', 'legendary']:
            if rarity in nested:
                skills = nested[rarity]
                skills_json = json.dumps(skills, indent=8)
                # Convert JSON booleans to Python booleans
                skills_json = re.sub(r':\s*true\b', ': True', skills_json)
                skills_json = re.sub(r':\s*false\b', ': False', skills_json)

                lines.append(f'        "{rarity}": {skills_json},')

        lines.append('    },')

    lines.append('}')
    return '\n'.join(lines)

new_skill_pool_code = serialize_skill_pool(skill_pool_dict)

# Read the original file and replace SKILL_POOL
print("\nReading services/skills_service.py...")
with open(service_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace SKILL_POOL
# Match from "SKILL_POOL = {" to the first line starting with a non-whitespace that's not "}" or a class definition
match = re.search(r'(SKILL_POOL = \{.*?\n\})', content, re.DOTALL)
if match:
    print(f"Found SKILL_POOL, replacing...")
    new_content = content[:match.start()] + new_skill_pool_code + content[match.end():]

    with open(service_file, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"Successfully fixed SKILL_POOL format!")
    print(f"Total classes in SKILL_POOL: {len(skill_pool_dict)}")
else:
    print("ERROR: Could not find SKILL_POOL definition")
    exit(1)
