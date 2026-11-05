"""Transactional SQLite storage; compatible with the original UP02 schema."""

import hashlib
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from fastapi import Request

SCHEMA = """
CREATE TABLE IF NOT EXISTS participants (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 lastName TEXT NOT NULL, firstName TEXT NOT NULL, organization TEXT NOT NULL DEFAULT '',
 email TEXT NOT NULL COLLATE NOCASE UNIQUE,
 role TEXT NOT NULL CHECK(role IN ('докладчик','слушатель','организатор')),
 badgePrinted INTEGER NOT NULL DEFAULT 0 CHECK(badgePrinted IN (0,1)),
 createdAt TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS sections (
 id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, room TEXT NOT NULL DEFAULT '',
 startTime TEXT NOT NULL DEFAULT '', capacity INTEGER NOT NULL CHECK(capacity >= 1),
 createdAt TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS attendance (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 participantId INTEGER NOT NULL REFERENCES participants(id) ON DELETE CASCADE,
 sectionId INTEGER NOT NULL REFERENCES sections(id) ON DELETE CASCADE,
 status TEXT NOT NULL DEFAULT 'зарегистрирован'
 CHECK(status IN ('зарегистрирован','присутствовал','отсутствовал')),
 registeredAt TEXT NOT NULL DEFAULT (datetime('now')), updatedAt TEXT,
 UNIQUE(participantId, sectionId)
);
CREATE INDEX IF NOT EXISTS ix_attendance_section ON attendance(sectionId);
CREATE TABLE IF NOT EXISTS users (
 id INTEGER PRIMARY KEY, username TEXT NOT NULL UNIQUE, display_name TEXT NOT NULL,
 password_hash TEXT NOT NULL, role TEXT NOT NULL CHECK(role IN ('admin','operator','viewer'))
);
CREATE TABLE IF NOT EXISTS sessions (
 token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 csrf TEXT NOT NULL, expires REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS login_attempts (
 client TEXT PRIMARY KEY, count INTEGER NOT NULL, until REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS audit (
 id INTEGER PRIMARY KEY, actor TEXT NOT NULL, action TEXT NOT NULL, entity TEXT NOT NULL,
 entity_id INTEGER, created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS app_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
PRAGMA user_version = 1;
"""


def connect(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path, timeout=15, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=15000")
    conn.create_function(
        "CASEFOLD", 1, lambda value: str(value or "").casefold(), deterministic=True
    )
    return conn


@contextmanager
def connection(path: Path):
    conn = connect(path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_db(request: Request):
    with connection(request.app.state.settings.db_path) as conn:
        yield conn


def record(row):
    result = dict(row)
    if "badgePrinted" in result:
        result["badgePrinted"] = bool(result["badgePrinted"])
    return result


def audit(conn, user, action, entity, entity_id=None):
    conn.execute(
        "INSERT INTO audit(actor,action,entity,entity_id) VALUES (?,?,?,?)",
        (user["username"], action, entity, entity_id),
    )


def init_db(settings):
    from security import hash_password

    settings.db_path.parent.mkdir(parents=True, exist_ok=True)
    with connection(settings.db_path) as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.executescript(SCHEMA)
        mode = conn.execute("SELECT value FROM app_meta WHERE key='mode'").fetchone()
        if settings.production and mode and mode["value"] == "demo":
            raise RuntimeError("Do not use a demo database in production; use a new DATABASE_PATH")
        if not mode:
            conn.execute(
                "INSERT INTO app_meta VALUES ('mode',?)", ("demo" if settings.demo else "private",)
            )
        if not conn.execute("SELECT 1 FROM users LIMIT 1").fetchone():
            if settings.demo:
                accounts = [
                    ("admin", "Администратор", "DemoAdmin!2026", "admin"),
                    ("operator", "Оператор регистрации", "DemoOperator!2026", "operator"),
                    ("viewer", "Наблюдатель", "DemoViewer!2026", "viewer"),
                ]
            else:
                if len(settings.admin_password) < 14 or settings.admin_password.startswith("Demo"):
                    raise RuntimeError("Set a unique ADMIN_PASSWORD of at least 14 characters")
                accounts = [("admin", "Администратор", settings.admin_password, "admin")]
            for login, name, password, role in accounts:
                conn.execute(
                    "INSERT INTO users(username,display_name,password_hash,role) VALUES (?,?,?,?)",
                    (login, name, hash_password(password), role),
                )
        if (
            settings.demo
            and not conn.execute("SELECT 1 FROM app_meta WHERE key='seeded'").fetchone()
        ):
            if (
                not conn.execute("SELECT 1 FROM participants LIMIT 1").fetchone()
                and not conn.execute("SELECT 1 FROM sections LIMIT 1").fetchone()
            ):
                seed_demo(conn)
            conn.execute("INSERT INTO app_meta VALUES ('seeded','1')")


def seed_demo(conn):
    people = [
        ("Морозова", "Анна", "ДВФУ", "докладчик"),
        ("Соколов", "Михаил", "ИТ Академия", "докладчик"),
        ("Волкова", "Мария", "Технопарк", "слушатель"),
        ("Лебедев", "Артём", "ДВФУ", "организатор"),
        ("Новикова", "Алиса", "Цифровая среда", "слушатель"),
        ("Орлов", "Даниил", "ИТ Академия", "докладчик"),
        ("Козлова", "София", "Технопарк", "слушатель"),
        ("Попов", "Илья", "ДВФУ", "слушатель"),
        ("Смирнова", "Вера", "Цифровая среда", "организатор"),
        ("Иванов", "Максим", "ДВФУ", "слушатель"),
        ("Петрова", "Полина", "ИТ Академия", "слушатель"),
        ("Зайцев", "Никита", "Технопарк", "докладчик"),
    ]
    ids = []
    for i, (last, first, org, role) in enumerate(people, 1):
        ids.append(
            conn.execute(
                "INSERT INTO participants(lastName,firstName,organization,email,role,badgePrinted) VALUES (?,?,?,?,?,?)",
                (last, first, org, f"demo{i}@example.com", role, int(i <= 8)),
            ).lastrowid
        )
    sids = []
    for title, room, time, capacity in [
        ("Разработка и архитектура", "Аудитория 301", "10:00", 24),
        ("Данные и искусственный интеллект", "Аудитория 204", "11:30", 18),
        ("Кибербезопасность", "Аудитория 105", "13:00", 16),
        ("Дизайн цифровых продуктов", "Коворкинг", "14:30", 20),
    ]:
        sids.append(
            conn.execute(
                "INSERT INTO sections(title,room,startTime,capacity) VALUES (?,?,?,?)",
                (title, room, time, capacity),
            ).lastrowid
        )
    for i, pid in enumerate(ids):
        for offset in range(2 if i < 6 else 1):
            conn.execute(
                "INSERT INTO attendance(participantId,sectionId,status) VALUES (?,?,?)",
                (pid, sids[(i + offset) % 4], "присутствовал" if i < 7 else "зарегистрирован"),
            )


def token_digest(value):
    return hashlib.sha256(value.encode()).hexdigest()
