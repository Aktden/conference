"""
Подключение к базе данных и инициализация таблиц
"""

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

DB_PATH = Path("conference.db")


def get_connection() -> sqlite3.Connection:
    """Создать подключение к SQLite с возвратом строк как словарей"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


@contextmanager
def db():
    """Контекстный менеджер: открыть соединение, зафиксировать или откатить"""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Создать таблицы, если их ещё нет"""
    with db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS participants (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                lastName      TEXT    NOT NULL,
                firstName     TEXT    NOT NULL,
                organization  TEXT    NOT NULL DEFAULT '',
                email         TEXT    NOT NULL UNIQUE,
                role          TEXT    NOT NULL
                                  CHECK(role IN ('докладчик','слушатель','организатор')),
                badgePrinted  INTEGER NOT NULL DEFAULT 0,
                createdAt     TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M', 'now', 'localtime'))
            );

            CREATE TABLE IF NOT EXISTS sections (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                title       TEXT    NOT NULL,
                room        TEXT    NOT NULL DEFAULT '',
                startTime   TEXT    NOT NULL DEFAULT '',
                capacity    INTEGER NOT NULL CHECK(capacity >= 1),
                createdAt   TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M', 'now', 'localtime'))
            );

            CREATE TABLE IF NOT EXISTS attendance (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                participantId INTEGER NOT NULL
                                  REFERENCES participants(id) ON DELETE CASCADE,
                sectionId     INTEGER NOT NULL
                                  REFERENCES sections(id)     ON DELETE CASCADE,
                status        TEXT    NOT NULL DEFAULT 'зарегистрирован'
                                  CHECK(status IN ('зарегистрирован','присутствовал','отсутствовал')),
                registeredAt  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M', 'now', 'localtime')),
                updatedAt     TEXT,
                UNIQUE(participantId, sectionId)
            );
        """)


def row_to_dict(row: sqlite3.Row) -> dict:
    """Преобразовать строку SQLite в обычный словарь"""
    d = dict(row)
    if "badgePrinted" in d:
        d["badgePrinted"] = bool(d["badgePrinted"])
    return d


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")
