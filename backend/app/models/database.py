import os
import sqlite3
from pathlib import Path


def get_database_path() -> Path:
    configured = os.getenv("SAMPLE_DB_PATH")
    if configured:
        return Path(configured)
    return Path(__file__).resolve().parents[2] / "data" / "samples.sqlite3"


def get_connection() -> sqlite3.Connection:
    db_path = get_database_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS samples (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                tags TEXT NOT NULL,
                category TEXT NOT NULL,
                likes INTEGER NOT NULL,
                collects INTEGER NOT NULL,
                comments INTEGER NOT NULL,
                cover_text TEXT NOT NULL,
                publish_time TEXT,
                source_note TEXT NOT NULL,
                source_type TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS diagnosis_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                input_json TEXT NOT NULL,
                output_json TEXT NOT NULL,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                overall_score INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
