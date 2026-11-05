"""Runtime settings resolved against the project root."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Settings:
    db_path: Path
    demo: bool = True
    production: bool = False
    secure_cookie: bool = False
    allowed_hosts: tuple[str, ...] = ("localhost", "127.0.0.1", "testserver")
    admin_password: str = ""
    session_hours: int = 8


def settings_from_env() -> Settings:
    load_dotenv(ROOT / ".env", override=False)
    path = Path(os.getenv("DATABASE_PATH", "data/conference.db"))
    production = os.getenv("APP_ENV", "demo") == "production"
    demo = os.getenv("DEMO_MODE", "true").lower() == "true"
    secure = os.getenv("COOKIE_SECURE", "false").lower() == "true"
    if production and (demo or not secure):
        raise RuntimeError("Production requires DEMO_MODE=false and COOKIE_SECURE=true")
    return Settings(
        db_path=path if path.is_absolute() else ROOT / path,
        demo=demo,
        production=production,
        secure_cookie=secure,
        allowed_hosts=tuple(os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")),
        admin_password=os.getenv("ADMIN_PASSWORD", ""),
    )
