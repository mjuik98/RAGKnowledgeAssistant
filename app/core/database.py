from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable

from app.core.config import get_settings


SCHEMA_PATH = Path(__file__).resolve().parent.parent / "db" / "schema.sql"


def get_connection() -> sqlite3.Connection:
    settings = get_settings()
    conn = sqlite3.connect(settings.db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db() -> None:
    with get_connection() as conn:
        schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
        conn.executescript(schema_sql)
        conn.commit()


def execute(query: str, params: tuple | dict = ()) -> None:
    with get_connection() as conn:
        conn.execute(query, params)
        conn.commit()


def executemany(query: str, params: Iterable[tuple]) -> None:
    with get_connection() as conn:
        conn.executemany(query, params)
        conn.commit()


def fetchall(query: str, params: tuple | dict = ()) -> list[sqlite3.Row]:
    with get_connection() as conn:
        cur = conn.execute(query, params)
        return cur.fetchall()


def fetchone(query: str, params: tuple | dict = ()) -> sqlite3.Row | None:
    with get_connection() as conn:
        cur = conn.execute(query, params)
        return cur.fetchone()
