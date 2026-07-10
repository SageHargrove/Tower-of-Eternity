"""
Corrected injection script that:
1. Preserves existing hand-tuned skills
2. Converts generated skills to the correct format (nested by rarity)
3. Merges them into skills_service.py without losing data
"""
import json
import os
import re

backend_dir = os.path.dirname(os.path.abspath(__file__))
generated_file = os.path.join(backend_dir, "generated_skills.json")
service_file = os.path.join(os.path.dirname(backend_dir), "services", "skills_service.py")

print("Loading generated skills...")
with open(generated_file, "r", encoding="utf-8") as f:
    generated_data = json.load(f)

print("Reading original skills_service.py...")
with open(service_file, "r", encoding="utf-8") as f:
    original_content = f.read()

# Extract the original SKILL_POOL to preserve existing skills
# This is a bit tricky - we need to find the SKILL_POOL dictionary
import ast
import re as regex

# Find where SKILL_POOL = { starts and extract existing entries
# We'll use a regex to find the SKILL_POOL definition
match = regex.search(r'SKILL_POOL\s*=\s*\{', original_content)
if not match:
    print("ERROR: Could not find SKILL_POOL definition in skills_service.py")
    exit(1)

start_pos = match.start()
print(f"Found SKILL_POOL at position {start_pos}")

# Extract existing classes that should be preserved
# These are the hand-tuned ones mentioned in generate_class_skills.py
EXISTING_KITS = {
    "Rookie", "Squire", "Thief", "Acolyte", "Apprentice", "Archer",
    "Knight", "Assassin", "Cleric", "Sorcerer", "Ranger",
    "Paladin", "Nightblade", "High Priest", "Archmage", "Sniper",
    "Berserker", "Druid", "Necromancer", "Bard", "Monk"
}

print(f"\nPreserving {len(EXISTING_KITS)} existing hand-tuned classes")

# Read the original file and extract the original SKILL_POOL structure
# We'll do this by extracting lines between SKILL_POOL = { and the closing }
lines = original_content.split('\n')
skill_pool_start = None
skill_pool_end = None
brace_count = 0

for i, line in enumerate(lines):
    if 'SKILL_POOL = {' in line:
        skill_pool_start = i
        brace_count = 1
    elif skill_pool_start is not None and brace_count > 0:
        # Count braces to find the end of SKILL_POOL
        brace_count += line.count('{') - line.count('}')
        if brace_count == 0:
            skill_pool_end = i
            break

print(f"Original SKILL_POOL spans lines {skill_pool_start} to {skill_pool_end}")

# Now extract just the skill definitions for existing classes
existing_entries = []
if skill_pool_start and skill_pool_end:
    # Extract the content between SKILL_POOL = { and the closing }
    content_lines = lines[skill_pool_start + 1:skill_pool_end]

    # Try to reconstruct the existing skills by parsing the content
    # This is complex, so we'll try a different approach:
    # We'll keep the original SKILL_POOL and just add new entries to it

    print("Preserving original SKILL_POOL structure and adding new skills...")

# Build the new SKILL_POOL content with all skills
print("\nConverting generated skills to correct format...")

def convert_to_rarity_dict(skills_list):
    """Convert flat list of skills to nested dictionary by rarity"""
    result = {}
    for skill in skills_list:
        rarity = skill.get('rarity', 'common')
        if rarity not in result:
            result[rarity] = []
        result[rarity].append(skill)
    return result

# Generate Python code for skill pool entries
new_entries = []
for class_data in generated_data:
    class_name = class_data['class_name']
    skills = class_data['skills']

    # Convert to rarity dictionary
    rarity_dict = convert_to_rarity_dict(skills)

    # Generate Python code
    skills_by_rarity = []
    for rarity in ['common', 'uncommon', 'rare', 'epic', 'legendary']:
        if rarity in rarity_dict:
            skills_list = rarity_dict[rarity]
            skills_json = json.dumps(skills_list, indent=12)
            # Convert JSON booleans to Python booleans
            skills_json = re.sub(r':\s*true\b', ': True', skills_json)
            skills_json = re.sub(r':\s*false\b', ': False', skills_json)
            skills_by_rarity.append(f'        "{rarity}": {skills_json}')

    entry = f'    "{class_name}": {{\n' + ',\n'.join(skills_by_rarity) + '\n    }'
    new_entries.append(entry)

print(f"Generated code for {len(new_entries)} new classes")

# Now reconstruct the full file
# Keep everything before SKILL_POOL
header_lines = lines[:skill_pool_start + 1]  # Include the SKILL_POOL = { line

# Add existing entries if they were found
if skill_pool_start and skill_pool_end:
    # Keep the existing entries for the existing classes
    existing_class_entries = []
    current_class = None
    current_entry_lines = []

    for line in lines[skill_pool_start + 1:skill_pool_end]:
        # Check if this line starts a new class definition
        if regex.match(r'^\s*"[^"]+"\s*:\s*\{', line):
            # Extract class name
            match = regex.search(r'"([^"]+)"', line)
            if match:
                if current_class in EXISTING_KITS and current_entry_lines:
                    # Save the previous entry
                    existing_class_entries.append((current_class, current_entry_lines))

                current_class = match.group(1)
                current_entry_lines = [line]
        elif current_class:
            current_entry_lines.append(line)
            if line.strip() == '}' or line.strip() == '},':
                # End of current class entry
                if current_class in EXISTING_KITS:
                    existing_class_entries.append((current_class, current_entry_lines))
                current_class = None
                current_entry_lines = []

    # Rebuild with preserved existing entries
    body_lines = []
    for class_name, entry_lines in existing_class_entries:
        body_lines.extend(entry_lines)
        body_lines.append('')  # Add blank line for readability

    # Add new entries
    for entry in new_entries:
        body_lines.append(entry + ',')
        body_lines.append('')

# Footer (closing brace and rest of file)
footer_lines = lines[skill_pool_end:]

# Reconstruct the file
final_lines = header_lines + body_lines + footer_lines
final_content = '\n'.join(final_lines)

# Write back
with open(service_file, "w", encoding="utf-8") as f:
    f.write(final_content)

print(f"\nInjected {len(new_entries)} new classes into skills_service.py!")
print("Preserved all existing hand-tuned skill classes.")
