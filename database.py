import sqlite3
import os

DATABASE = "data/database.db"


def get_db():
    os.makedirs("data", exist_ok=True)

    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row

    return conn


def init_db():
    conn = get_db()

    conn.executescript("""
        CREATE TABLE IF NOT EXISTS persons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS observations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id INTEGER NOT NULL,
            weekday INTEGER NOT NULL,
            time_slot INTEGER NOT NULL,
            floor INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (person_id)
                REFERENCES persons(id)
                ON DELETE CASCADE,

            CHECK(weekday BETWEEN 0 AND 6),
            CHECK(time_slot BETWEEN 0 AND 3),
            CHECK(floor BETWEEN 1 AND 6)
        );

        CREATE TABLE IF NOT EXISTS time_slots (
            id INTEGER PRIMARY KEY,
            label TEXT NOT NULL,
            time TEXT NOT NULL
        );
    """)

    # Neljä oletusajankohtaa
    defaults = [
        (0, "Aamu", "08:00"),
        (1, "Päivä", "12:00"),
        (2, "Iltapäivä", "16:00"),
        (3, "Ilta", "20:00")
    ]

    conn.executemany("""
        INSERT OR IGNORE INTO time_slots
        (id, label, time)
        VALUES (?, ?, ?)
    """, defaults)

    conn.commit()
    conn.close()