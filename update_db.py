import re
schema = open('backend/schema.sql').read()

# Add the INSERT OR IGNORE INTO base to the schema
schema += "\n\nINSERT OR IGNORE INTO base (id) VALUES (1);\nINSERT OR IGNORE INTO facilities (base_id, type, level, slots_unlocked) VALUES (1, 'The Square', 1, 1);\n"

# Update base table defaults for gold and supplies
schema = schema.replace("gold INTEGER DEFAULT 10000", "gold INTEGER DEFAULT 1000")
if "supplies INTEGER" not in schema:
    schema = schema.replace("materials TEXT", "supplies INTEGER DEFAULT 500,\n            materials TEXT")

db_code = open('backend/database.py').read()
db_code = re.sub(r'conn\.executescript\(\"\"\"[\s\S]*?\"\"\"\)', 'conn.executescript(\"\"\"\\n' + schema + '\\n        \"\"\")', db_code)
open('backend/database.py', 'w').write(db_code)
