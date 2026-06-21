import os, glob
from database import db
with db() as conn:
    conn.execute('DELETE FROM portrait_cache')
    conn.execute('UPDATE heroes SET portrait_path = "static/portraits/default_male.png" WHERE portrait_path NOT LIKE "%default_%"')
print('DB cleared.')
for f in glob.glob('static/portraits/cached/*.png'):
    try: os.remove(f)
    except: pass
for f in glob.glob('static/portraits/main/*.png'):
    try: os.remove(f)
    except: pass
print('Files deleted.')
