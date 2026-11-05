"""Server-side session authentication, CSRF protection and role checks."""

import hashlib
import hmac
import secrets
import time

from fastapi import Depends, HTTPException, Request

from database import get_db, token_digest


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    derived = hashlib.scrypt(password.encode(), salt=salt.encode(), n=16384, r=8, p=1)
    return f"scrypt${salt}${derived.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    _, salt, expected = encoded.split("$")
    result = hashlib.scrypt(password.encode(), salt=salt.encode(), n=16384, r=8, p=1)
    return hmac.compare_digest(result.hex(), expected)


def current_user(request: Request, conn=Depends(get_db)):
    token = request.cookies.get("conference_session", "")
    row = conn.execute(
        "SELECT u.id,u.username,u.display_name,u.role,s.csrf FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token_hash=? AND s.expires>?",
        (token_digest(token), time.time()),
    ).fetchone()
    if not row:
        raise HTTPException(401, "Войдите в систему")
    if request.method not in ("GET", "HEAD", "OPTIONS"):
        if not hmac.compare_digest(request.headers.get("X-CSRF-Token", ""), row["csrf"]):
            raise HTTPException(403, "Сессия формы устарела. Обновите страницу")
    return dict(row)


def require(*roles):
    def dependency(user=Depends(current_user)):
        if user["role"] not in roles:
            raise HTTPException(403, "Недостаточно прав для этого действия")
        return user

    return dependency


staff = require("admin", "operator")
admin = require("admin")
