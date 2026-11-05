import secrets
import time

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from database import audit, get_db, token_digest
from models import Login
from security import current_user, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["Авторизация"])
DUMMY_HASH = hash_password("timing-only-not-a-user-password")


@router.post("/login")
def login(data: Login, request: Request, response: Response, conn=Depends(get_db)):
    origin = request.headers.get("Origin")
    if origin and origin != str(request.base_url).rstrip("/"):
        raise HTTPException(403, "Недопустимый источник запроса")
    now = time.time()
    client = request.client.host if request.client else "unknown"
    attempt = conn.execute(
        "SELECT count,until FROM login_attempts WHERE client=?", (client,)
    ).fetchone()
    if attempt and attempt["until"] > now and attempt["count"] >= 5:
        raise HTTPException(429, "Слишком много попыток. Повторите вход через 5 минут")
    user = conn.execute("SELECT * FROM users WHERE username=?", (data.username,)).fetchone()
    valid = verify_password(data.password, user["password_hash"] if user else DUMMY_HASH)
    if not user or not valid:
        count = attempt["count"] + 1 if attempt and attempt["until"] > now else 1
        conn.execute("DELETE FROM login_attempts WHERE until < ?", (now,))
        conn.execute(
            "INSERT OR REPLACE INTO login_attempts VALUES (?,?,?)", (client, count, now + 300)
        )
        conn.commit()
        raise HTTPException(401, "Неверный логин или пароль")
    conn.execute("DELETE FROM login_attempts WHERE client=?", (client,))
    conn.execute("DELETE FROM sessions WHERE expires < ?", (now,))
    conn.execute(
        "DELETE FROM sessions WHERE token_hash=?",
        (token_digest(request.cookies.get("conference_session", "")),),
    )
    token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    ttl = request.app.state.settings.session_hours * 3600
    conn.execute(
        "INSERT INTO sessions VALUES (?,?,?,?)", (token_digest(token), user["id"], csrf, now + ttl)
    )
    audit(conn, dict(user), "login", "session")
    response.set_cookie(
        "conference_session",
        token,
        max_age=ttl,
        httponly=True,
        secure=request.app.state.settings.secure_cookie,
        samesite="strict",
    )
    return {
        "user": {k: user[k] for k in ("id", "username", "display_name", "role")},
        "csrfToken": csrf,
    }


@router.get("/me")
def me(user=Depends(current_user)):
    return {"user": {k: v for k, v in user.items() if k != "csrf"}, "csrfToken": user["csrf"]}


@router.post("/logout")
def logout(request: Request, response: Response, user=Depends(current_user), conn=Depends(get_db)):
    conn.execute(
        "DELETE FROM sessions WHERE token_hash=?",
        (token_digest(request.cookies.get("conference_session", "")),),
    )
    audit(conn, user, "logout", "session")
    response.delete_cookie("conference_session", httponly=True, samesite="strict")
    return {"ok": True}
