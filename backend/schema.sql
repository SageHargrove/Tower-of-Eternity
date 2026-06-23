CREATE TABLE heroes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            title TEXT,
            backstory TEXT,
            personality TEXT,
            portrait_path TEXT,

            -- Rarity
            birth_star INTEGER DEFAULT 1,
            ascension_star INTEGER DEFAULT 0,

            -- Class
            hero_class TEXT DEFAULT 'Classless',
            hidden_class TEXT,
            can_pilot INTEGER DEFAULT 0,

            -- Level
            level INTEGER DEFAULT 1,

            -- Base stats
            health INTEGER DEFAULT 100,
            max_health INTEGER DEFAULT 100,
            strength INTEGER DEFAULT 10,
            intelligence INTEGER DEFAULT 5,
            agility INTEGER DEFAULT 10,

            -- Hidden aptitudes (0-100 each)
            apt_combat INTEGER DEFAULT 50,
            apt_tactical INTEGER DEFAULT 50,
            apt_survival INTEGER DEFAULT 50,
            apt_mental INTEGER DEFAULT 50,
            apt_leadership INTEGER DEFAULT 50,
            apt_diligence INTEGER DEFAULT 50,
            aptitudes_revealed INTEGER DEFAULT 0,

            -- Mental State & Achievements
            condition TEXT DEFAULT 'Normal',
            condition_until TEXT,
            near_wipes_survived INTEGER DEFAULT 0,
            unique_floors_cleared INTEGER DEFAULT 0,

            -- Morale
            morale INTEGER DEFAULT 100,
            stress INTEGER DEFAULT 0,
            trauma INTEGER DEFAULT 0,
            morale_state TEXT DEFAULT 'steady',

            -- Status
            is_alive INTEGER DEFAULT 1,
            is_on_team INTEGER DEFAULT 0,
            floor_joined INTEGER DEFAULT 0,
            team_position INTEGER DEFAULT 0,
            ego_type TEXT,

            -- Progression
            kills INTEGER DEFAULT 0,
            floors_survived INTEGER DEFAULT 0,
            missions_completed INTEGER DEFAULT 0,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            current_star INTEGER,
            synthesized INTEGER DEFAULT 0,
            skills TEXT DEFAULT '[]',
            synergy_group TEXT,
            gender TEXT,
            fatigue INTEGER DEFAULT 0,
            base_floor INTEGER DEFAULT 0,
            traits TEXT DEFAULT '[]'
        )

CREATE TABLE runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            status TEXT DEFAULT 'active',
            current_floor INTEGER DEFAULT 0,
            highest_floor INTEGER DEFAULT 0,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ended_at TIMESTAMP
        )

CREATE TABLE run_heroes (
            run_id INTEGER REFERENCES runs(id),
            hero_id INTEGER REFERENCES heroes(id),
            PRIMARY KEY (run_id, hero_id)
        )

CREATE TABLE floors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER REFERENCES runs(id),
            floor_number INTEGER NOT NULL,
            floor_type TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            outcome TEXT,
            narrative TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )

CREATE TABLE base (
            id INTEGER PRIMARY KEY DEFAULT 1,
            name TEXT DEFAULT 'The Hollow Spire',
            level INTEGER DEFAULT 1,
            gold INTEGER DEFAULT 10000,
            supplies INTEGER DEFAULT 0,
            materials TEXT DEFAULT '{}',
            highest_floor INTEGER DEFAULT 0,
            unlocked_features TEXT DEFAULT '[]',
            research_points INTEGER DEFAULT 0,
            global_buffs TEXT DEFAULT '{}',
            pity_counter INTEGER DEFAULT 0,
            spark_points INTEGER DEFAULT 0,
            last_training_tick TIMESTAMP,
            last_fatigue_tick TIMESTAMP
        , last_research_tick TIMESTAMP)

CREATE TABLE event_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER,
            floor_number INTEGER,
            event_type TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )

CREATE TABLE portrait_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            birth_star INTEGER NOT NULL,
            path TEXT NOT NULL,
            used INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        , gender TEXT, class_name TEXT)

CREATE TABLE facilities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            base_id INTEGER DEFAULT 1,
            type TEXT NOT NULL,
            level INTEGER DEFAULT 1,
            slots_unlocked INTEGER DEFAULT 1
        )

CREATE TABLE facility_assignments (
            facility_id INTEGER REFERENCES facilities(id),
            hero_id INTEGER REFERENCES heroes(id),
            role TEXT,
            target_hero_id INTEGER,
            target_skill_id TEXT,
            UNIQUE(hero_id)
        )

CREATE TABLE hero_chat_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location TEXT DEFAULT 'The Square',
            message TEXT NOT NULL,
            participants TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )

CREATE TABLE equipment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            rarity TEXT NOT NULL,
            level INTEGER DEFAULT 1,
            base_str INTEGER DEFAULT 0,
            base_int INTEGER DEFAULT 0,
            base_hlt INTEGER DEFAULT 0,
            base_agi INTEGER DEFAULT 0,
            str_pct REAL DEFAULT 0.0,
            int_pct REAL DEFAULT 0.0,
            hlt_pct REAL DEFAULT 0.0,
            agi_pct REAL DEFAULT 0.0,
            crit_chance REAL DEFAULT 0.0,
            dodge_chance REAL DEFAULT 0.0,
            armor_pen REAL DEFAULT 0.0,
            is_equipped_to INTEGER REFERENCES heroes(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )

CREATE TABLE legacies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hero_id INTEGER,
            hero_name TEXT,
            hero_star INTEGER,
            title TEXT,
            flavor_text TEXT,
            bonus_json TEXT,
            score INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )

CREATE TABLE inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL,
            item_type TEXT NOT NULL,
            quantity INTEGER DEFAULT 0,
            description TEXT
        )