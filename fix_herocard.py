import re

with open('frontend/src/components/HeroCard.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Scale up the base font sizes inside HeroCard when showFull is true
# We can just change all relative font sizes '0.8rem' -> '1.1rem', '1.2rem' -> '1.6rem', '0.7em' -> '1em'
# But a better way is to wrap the expanded view in a container with a larger base font-size
# In HeroCard.jsx, it returns `<div className={...} style={{ ... }}>`
# I'll just change the font size on the root div if showFull is true.

content = content.replace(
    """<div className={`hero-card ${selected ? 'selected' : ''}`} onClick={onClick} style={{ opacity: dead ? 0.6 : 1, position: 'relative' }}>""",
    """<div className={`hero-card ${selected ? 'selected' : ''}`} onClick={onClick} style={{ opacity: dead ? 0.6 : 1, position: 'relative', fontSize: showFull ? '1.25rem' : '1rem' }}>"""
)

# And make the image larger when showFull is true
content = content.replace(
    """<img src={`http://127.0.0.1:8000/static/portraits/${hero.portrait_path}?t=${hero.id}`}""",
    """<img src={`http://127.0.0.1:8000/static/portraits/${hero.portrait_path}?t=${hero.id}`} style={{ height: showFull ? '600px' : '350px' }}"""
)
# Wait, the img tag already has styles. Let's find it.
