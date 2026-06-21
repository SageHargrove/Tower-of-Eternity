with open('backend/services/portrait_cache.py', 'r', encoding='utf-8') as f:
    c = f.read()

c = c.replace('def _random_traits(birth_star: int = 1) -> dict:', 'def _random_traits(birth_star: int = 1, gender: str = "unknown") -> dict:')
c = c.replace('traits = _random_traits(gender)', 'traits = _random_traits(1, gender)')
c = c.replace('def build_varied_prompt(birth_star: int = 1) -> tuple:', 'def build_varied_prompt(birth_star: int = 1, gender: str = "unknown") -> tuple:')
c = c.replace('traits = _random_traits(birth_star)', 'traits = _random_traits(birth_star, gender)')

with open('backend/services/portrait_cache.py', 'w', encoding='utf-8') as f:
    f.write(c)
