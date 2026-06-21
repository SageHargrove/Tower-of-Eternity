import re

# Read with error handling
with open('services/portrait_cache.py', 'rb') as f:
    raw = f.read()

# Try to decode
try:
    content = raw.decode('utf-8')
except UnicodeDecodeError:
    content = raw.decode('utf-8', errors='replace')

# Replace RACES_HIGH
old_races = """RACES_HIGH = [
    ("human", 40),
    ("elf, pointed ears, elegant exotic features", 20),
    ("beastfolk, animal ears, feral features, exotic aesthetics", 15),
    ("dark elf, dark skin, white hair, pointed ears, otherworldly beauty", 15),
    ("half-elf, slightly pointed ears", 10),
]"""

new_races = """RACES_HIGH = [
    ("human", 40),
    ("elf, pointed ears, elegant exotic features", 20),
    ("beastfolk, animal ears, feral features, exotic aesthetics", 15),
    ("dark elf, dark skin, white hair, pointed ears, otherworldly beauty", 15),
    ("half-elf, slightly pointed ears", 10),
    ("half-dragon, subtle scales on cheek, slit pupils, draconic features", 10),
    ("celestial-blooded, faint glowing halo, ethereal features", 5),
    ("tiefling, small demonic horns, unnatural skin tone", 5),
]"""

content = content.replace(old_races, new_races)

# Replace highly detailed face, masterpiece with detailed face, gritty realistic for 1-stars
content = content.replace("highly detailed face, masterpiece", "detailed face, gritty realistic")

with open('services/portrait_cache.py', 'wb') as f:
    f.write(content.encode('utf-8'))

print("Patch applied successfully.")
