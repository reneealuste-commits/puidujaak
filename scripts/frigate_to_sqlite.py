#!/usr/bin/env python3
"""
Minimal example: pull recent Frigate events into a local SQLite database.
Run on the same Raspberry Pi (or any machine that can reach Frigate).
"""

import sqlite3
import requests
from datetime import datetime

FRIGATE_URL = "http://127.0.0.1:5000"
DB_PATH = "events.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id TEXT PRIMARY KEY,
            camera TEXT,
            label TEXT,
            start_time REAL,
            end_time REAL,
            score REAL,
            created_at TEXT
        )
    """)
    conn.commit()
    return conn

def fetch_and_store():
    conn = init_db()
    c = conn.cursor()

    # Get last 50 events
    r = requests.get(f"{FRIGATE_URL}/api/events?limit=50", timeout=10)
    r.raise_for_status()
    events = r.json()

    for ev in events:
        c.execute("""
            INSERT OR IGNORE INTO events
            (id, camera, label, start_time, end_time, score, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            ev.get("id"),
            ev.get("camera"),
            ev.get("label"),
            ev.get("start_time"),
            ev.get("end_time"),
            ev.get("top_score"),
            datetime.utcnow().isoformat()
        ))

    conn.commit()
    conn.close()
    print(f"Stored {len(events)} events (duplicates ignored).")

if __name__ == "__main__":
    fetch_and_store()
