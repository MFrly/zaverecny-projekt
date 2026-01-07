# database.py
import sqlite3
import json
from pathlib import Path

DB_PATH = Path("data") / "save.db"


def _connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _connect() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS players (
            name TEXT PRIMARY KEY,
            key_parts TEXT NOT NULL DEFAULT '[]',
            has_master_key INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """)
        conn.commit()


def save_player(name: str, key_parts: set[int], has_master_key: bool):
    # uložíme set jako JSON list (stabilně seřazený)
    key_parts_json = json.dumps(sorted(list(key_parts)))

    with _connect() as conn:
        conn.execute("""
        INSERT INTO players (name, key_parts, has_master_key, updated_at)
        VALUES (?, ?, ?, datetime('now'))
        ON CONFLICT(name) DO UPDATE SET
            key_parts=excluded.key_parts,
            has_master_key=excluded.has_master_key,
            updated_at=datetime('now')
        """, (name, key_parts_json, 1 if has_master_key else 0))
        conn.commit()


def load_player(name: str):
    with _connect() as conn:
        row = conn.execute("SELECT name, key_parts, has_master_key FROM players WHERE name=?",
                           (name,)).fetchone()

    if not row:
        return None

    try:
        parts_list = json.loads(row["key_parts"])
        key_parts = set(int(x) for x in parts_list)
    except Exception:
        key_parts = set()

    return {
        "name": row["name"],
        "key_parts": key_parts,
        "has_master_key": bool(row["has_master_key"]),
    }
