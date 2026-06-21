import sqlite3
c = sqlite3.connect('database.db')
print(c.execute("SELECT sql FROM sqlite_master WHERE name='inventory'").fetchone())
