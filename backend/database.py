import sqlite3
import json
from contextlib import contextmanager

DB_PATH = "game.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

@contextmanager
def db():
    conn = get_conn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    with db() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS heroes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            title TEXT,
            backstory TEXT,
            personality TEXT,
            portrait_path TEXT,

            -- Rarity
            birth_star INTEGER DEFAULT 1,        -- 1-7, from gacha
            ascension_star INTEGER DEFAULT 0,    -- 0-7, earned

            -- Base stats (scaled by birth_star + aptitudes)
            hp INTEGER DEFAULT 100,
            max_hp INTEGER DEFAULT 100,
            attack INTEGER DEFAULT 10,
            defense INTEGER DEFAULT 5,
            speed INTEGER DEFAULT 10,

            -- Hidden aptitudes (0-100 each, revealed through play)
            apt_combat INTEGER DEFAULT 50,
            apt_tactical INTEGER DEFAULT 50,
            apt_survival INTEGER DEFAULT 50,
            apt_mental INTEGER DEFAULT 50,
            apt_leadership INTEGER DEFAULT 50,
            aptitudes_revealed INTEGER DEFAULT 0, -- bitmask

            -- Morale / psychology
            morale INTEGER DEFAULT 100,          -- 0-100
            stress INTEGER DEFAULT 0,            -- 0-100
            trauma INTEGER DEFAULT 0,            -- 0-100
            morale_state TEXT DEFAULT 'steady',  -- steady/shaken/fearful/broken

            -- Status
            is_alive INTEGER DEFAULT 1,
            is_on_team INTEGER DEFAULT 0,
            floor_joined INTEGER DEFAULT 0,      -- which floor run they joined on

            -- Progression
            kills INTEGER DEFAULT 0,
            floors_survived INTEGER DEFAULT 0,
            missions_completed INTEGER DEFAULT 0,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            status TEXT DEFAULT 'active',        -- active/completed/failed
            current_floor INTEGER DEFAULT 0,
            highest_floor INTEGER DEFAULT 0,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ended_at TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS run_heroes (
            run_id INTEGER REFERENCES runs(id),
            hero_id INTEGER REFERENCES heroes(id),
            PRIMARY KEY (run_id, hero_id)
        );

        CREATE TABLE IF NOT EXISTS floors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER REFERENCES runs(id),
            floor_number INTEGER NOT NULL,
            floor_type TEXT NOT NULL,            -- combat/event/resource/boss/miniboss
            status TEXT DEFAULT 'pending',       -- pending/completed/failed
            outcome TEXT,                        -- JSON summary
            narrative TEXT,                      -- LLM-generated flavor
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS base (
            id INTEGER PRIMARY KEY DEFAULT 1,
            name TEXT DEFAULT 'The Hollow Spire',
            level INTEGER DEFAULT 1,
            gold INTEGER DEFAULT 10000,
            materials TEXT DEFAULT '{}',         -- JSON
            unlocked_features TEXT DEFAULT '[]'  -- JSON list
        );

        CREATE TABLE IF NOT EXISTS event_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER,
            floor_number INTEGER,
            event_type TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Seed base if not exists
        INSERT OR IGNORE INTO base (id) VALUES (1);
        """)
    print("Database initialized.")
