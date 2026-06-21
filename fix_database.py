import re

with open('backend/database.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = re.sub(r"INSERT INTO facilities \(base_id, type, level, slots_unlocked\)\s*SELECT 1, 'The Lobby', 1, 1\s*WHERE NOT EXISTS \(SELECT 1 FROM facilities WHERE type = 'The Lobby'\);", "", content)

content = re.sub(r"INSERT INTO facilities \(base_id, type, level, slots_unlocked\)\s*SELECT 1, 'The Market', 1, 1\s*WHERE NOT EXISTS \(SELECT 1 FROM facilities WHERE type = 'The Market'\);", "", content)

content = re.sub(r"INSERT INTO facilities \(base_id, type, level, slots_unlocked\)\s*SELECT 1, 'The Farm', 1, 1\s*WHERE NOT EXISTS \(SELECT 1 FROM facilities WHERE type = 'The Farm'\);", "", content)

with open('backend/database.py', 'w', encoding='utf-8') as f:
    f.write(content)
