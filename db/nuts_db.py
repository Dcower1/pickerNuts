from __future__ import annotations

from pathlib import Path
import sqlite3


DB_PATH = Path(__file__).resolve().parents[1] / "nuts_system.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize_schema() -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.executescript(
        """
        CREATE TABLE IF NOT EXISTS classifications (
            classification_id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            total_nuts INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS classification_details (
            detail_id INTEGER PRIMARY KEY AUTOINCREMENT,
            classification_id INTEGER NOT NULL,
            grade TEXT NOT NULL,
            color TEXT,
            shape TEXT,
            size REAL,
            FOREIGN KEY(classification_id) REFERENCES classifications(classification_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS metrics_history (
            history_id INTEGER PRIMARY KEY AUTOINCREMENT,
            classification_id INTEGER NOT NULL,
            supplier_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            total_nuts INTEGER NOT NULL,
            count_A INTEGER NOT NULL DEFAULT 0,
            count_B INTEGER NOT NULL DEFAULT 0,
            count_C INTEGER NOT NULL DEFAULT 0,
            count_D INTEGER NOT NULL DEFAULT 0,
            avg_size REAL,
            color_distribution TEXT,
            FOREIGN KEY(classification_id) REFERENCES classifications(classification_id) ON DELETE CASCADE
        );
        """
    )
    conn.commit()
    conn.close()


initialize_schema()
