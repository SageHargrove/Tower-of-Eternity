import re

with open('src/index.css', 'r', encoding='utf-8') as f:
    content = f.read()

# Find all blocks starting with .hero-card
blocks = []
inside_hero_card = False
new_content = []

for line in content.split('\n'):
    if line.startswith('.hero-card'):
        inside_hero_card = True
    elif inside_hero_card and line.startswith('}'):
        inside_hero_card = False
        new_content.append(line)
        continue
    elif not line.startswith(' ') and not line.startswith('\t') and '{' in line and not line.startswith('.hero-card'):
        inside_hero_card = False
        
    if inside_hero_card:
        new_content.append(line.replace('rem', 'em'))
    else:
        new_content.append(line)

with open('src/index.css', 'w', encoding='utf-8') as f:
    f.write('\n'.join(new_content))
