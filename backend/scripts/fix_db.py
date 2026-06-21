import os
from database import db

with db() as conn:
    rows = conn.execute('SELECT id, path FROM portrait_cache').fetchall()
    deleted = 0
    for r in rows:
        if not os.path.exists(r['path']):
            conn.execute('DELETE FROM portrait_cache WHERE id = ?', (r['id'],))
            deleted += 1
    print('Deleted', deleted, 'missing cache entries')
    
    heroes = conn.execute('SELECT id, portrait_path, birth_star FROM heroes WHERE portrait_path IS NOT NULL').fetchall()
    fixed_heroes = 0
    for h in heroes:
        p = h['portrait_path']
        if 'default_' not in p and not os.path.exists(p):
            star = h['birth_star']
            new_path = f"default_{star}star.png"
            conn.execute('UPDATE heroes SET portrait_path = ? WHERE id = ?', (new_path, h['id']))
            fixed_heroes += 1
    print('Fixed', fixed_heroes, 'heroes with missing portraits')
