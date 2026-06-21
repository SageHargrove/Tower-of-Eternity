with open('src/components/HeroCard.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace 'rem' with 'em' to allow scaling
content = content.replace("rem'", "em'")
content = content.replace('rem"', 'em"')

# Inject font-size scaling on the main container based on showFull
content = content.replace(
    'className={`hero-card ${selected ? \'selected\' : \'\'} ${dead ? \'dead\' : \'\'}`}',
    'className={`hero-card ${selected ? \'selected\' : \'\'} ${dead ? \'dead\' : \'\'}`} style={{ fontSize: showFull ? "1.4em" : "1em" }}'
)

with open('src/components/HeroCard.jsx', 'w', encoding='utf-8') as f:
    f.write(content)
