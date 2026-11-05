import sqlite3
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace

import pytest
from fastapi.testclient import TestClient

from database import connection, init_db
from main import create_app
from tests.conftest import login


def test_clean_start_and_seed_once(client, cfg):
    assert client.get("/api/health").json()["status"] == "ok"
    with connection(cfg.db_path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM participants").fetchone()[0] == 12
    init_db(cfg)
    with connection(cfg.db_path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM participants").fetchone()[0] == 12


def test_restart_preserves_intentionally_empty_data(authorized, cfg):
    assert (
        authorized.post(
            "/api/import",
            json={"confirm": "REPLACE", "participants": [], "sections": [], "attendance": []},
        ).status_code
        == 200
    )
    init_db(cfg)
    assert authorized.get("/api/stats").json()["participants"] == 0


def test_authentication_cookie_and_logout(client):
    assert client.get("/api/participants").status_code == 401
    result = login(client)
    cookie = result.headers["set-cookie"].lower()
    assert "httponly" in cookie and "samesite=strict" in cookie
    assert client.get("/api/auth/me").json()["user"]["role"] == "admin"
    assert client.post("/api/auth/logout").status_code == 200
    assert client.get("/api/participants").status_code == 401


def test_login_rate_limit(client):
    for _ in range(5):
        assert (
            client.post(
                "/api/auth/login", json={"username": "admin", "password": "bad"}
            ).status_code
            == 401
        )
    assert (
        client.post("/api/auth/login", json={"username": "admin", "password": "bad"}).status_code
        == 429
    )


def test_login_origin_and_csrf(client, participant):
    assert (
        client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "DemoAdmin!2026"},
            headers={"Origin": "https://attacker.example"},
        ).status_code
        == 403
    )
    login(client)
    del client.headers["X-CSRF-Token"]
    assert client.post("/api/participants", json=participant).status_code == 403


@pytest.mark.parametrize(
    "path",
    ["/api/participants", "/api/participants/1", "/api/attendance", "/api/export", "/api/audit"],
)
def test_viewer_cannot_read_personal_records(client, path):
    login(client, "viewer")
    assert client.get(path).status_code == 403


def test_viewer_can_read_aggregate_stats(client):
    login(client, "viewer")
    assert client.get("/api/stats").status_code == 200
    assert client.get("/api/sections").status_code == 200


def test_operator_permissions(client, participant):
    login(client, "operator")
    result = client.post("/api/participants", json=participant)
    assert result.status_code == 201
    assert client.delete(f"/api/participants/{result.json()['id']}").status_code == 403
    assert client.post("/api/sections", json={"title": "S", "capacity": 20}).status_code == 403
    assert client.get("/api/export").status_code == 403
    assert (
        client.post(
            "/api/import",
            json={"confirm": "REPLACE", "participants": [], "sections": [], "attendance": []},
        ).status_code
        == 403
    )


def test_participant_crud_duplicate_and_search(authorized, participant):
    p = authorized.post("/api/participants", json=participant)
    assert p.status_code == 201
    pid = p.json()["id"]
    assert (
        authorized.post(
            "/api/participants", json={**participant, "email": "TEST@EXAMPLE.COM"}
        ).status_code
        == 409
    )
    assert len(authorized.get("/api/participants", params={"search": "ТЕСТОВ"}).json()) == 1
    assert authorized.get("/api/participants", params={"search": "' OR 1=1 --"}).json() == []
    assert (
        authorized.put(
            f"/api/participants/{pid}", json={**participant, "firstName": "Пётр"}
        ).json()["firstName"]
        == "Пётр"
    )
    assert authorized.delete(f"/api/participants/{pid}").status_code == 200
    assert authorized.get(f"/api/participants/{pid}").status_code == 404


@pytest.mark.parametrize(
    "field,value",
    [("email", "bad"), ("lastName", "   "), ("role", "admin"), ("firstName", "a" * 81)],
)
def test_invalid_participant_preserves_data(authorized, participant, field, value):
    before = authorized.get("/api/stats").json()
    response = authorized.post("/api/participants", json={**participant, field: value})
    assert response.status_code == 422
    assert authorized.get("/api/stats").json() == before
    assert "Traceback" not in response.text


@pytest.mark.parametrize(
    "time,capacity", [("25:30", 10), ("09:70", 10), ("9:30", 10), ("10:00", 0), ("10:00", 10001)]
)
def test_section_validation(authorized, time, capacity):
    assert (
        authorized.post(
            "/api/sections", json={"title": "Section", "startTime": time, "capacity": capacity}
        ).status_code
        == 422
    )


def test_capacity_duplicate_and_cascade(authorized):
    sec = authorized.post("/api/sections", json={"title": "Один участник", "capacity": 1}).json()
    sid = sec["id"]
    payload = {"participantId": 1, "sectionId": sid}
    assert authorized.post("/api/attendance", json=payload).status_code == 201
    assert authorized.post("/api/attendance", json=payload).status_code == 409
    assert (
        authorized.post("/api/attendance", json={**payload, "participantId": 2}).status_code == 409
    )
    assert (
        authorized.put(f"/api/attendance/1/{sid}", json={"attended": True}).json()["status"]
        == "присутствовал"
    )
    assert (
        authorized.put(f"/api/attendance/1/{sid}", json={"attended": False}).json()["status"]
        == "отсутствовал"
    )
    assert authorized.delete(f"/api/sections/{sid}").status_code == 200
    assert all(a["sectionId"] != sid for a in authorized.get("/api/attendance").json())


def test_parallel_capacity(authorized):
    sid = authorized.post("/api/sections", json={"title": "Race", "capacity": 1}).json()["id"]

    def register(pid):
        return authorized.post(
            "/api/attendance", json={"participantId": pid, "sectionId": sid}
        ).status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(register, [1, 2])) == [201, 409]


def test_capacity_cannot_shrink_below_registrations(authorized):
    sid = authorized.post("/api/sections", json={"title": "Capacity", "capacity": 2}).json()["id"]
    for pid in [1, 2]:
        assert (
            authorized.post(
                "/api/attendance", json={"participantId": pid, "sectionId": sid}
            ).status_code
            == 201
        )
    assert (
        authorized.put(
            f"/api/sections/{sid}", json={"title": "Capacity", "capacity": 1}
        ).status_code
        == 409
    )
    assert authorized.delete(f"/api/attendance/1/{sid}").status_code == 200
    assert (
        authorized.put(
            f"/api/sections/{sid}", json={"title": "Capacity", "capacity": 1}
        ).status_code
        == 200
    )


def test_badges(authorized):
    assert authorized.post("/api/badges/1/print").status_code == 200
    assert authorized.post("/api/badges/99999/print").status_code == 404
    assert authorized.post("/api/badges/print-all").status_code == 200
    assert all(p["badgePrinted"] for p in authorized.get("/api/participants").json())
    assert (
        authorized.put("/api/participants/1", json={"badgePrinted": False}).json()["badgePrinted"]
        is False
    )


def test_export_import_roundtrip(authorized):
    data = authorized.get("/api/export").json()
    assert "users" not in data and "sessions" not in data
    assert authorized.post("/api/import", json={**data, "confirm": "REPLACE"}).status_code == 200
    after = authorized.get("/api/export").json()
    for name in ["participants", "sections", "attendance"]:
        assert after[name] == data[name]


@pytest.mark.parametrize(
    "invalid", ["foreign_id", "duplicate_email", "capacity", "confirm", "duplicate_attendance"]
)
def test_import_validation_is_atomic(authorized, invalid):
    data = authorized.get("/api/export").json()
    before = authorized.get("/api/stats").json()
    data["confirm"] = "REPLACE"
    if invalid == "foreign_id":
        data["attendance"][0]["participantId"] = 999999
    if invalid == "duplicate_email":
        data["participants"][1]["email"] = data["participants"][0]["email"]
    if invalid == "capacity":
        data["sections"][0]["capacity"] = 1
    if invalid == "confirm":
        data["confirm"] = "WRONG"
    if invalid == "duplicate_attendance":
        data["attendance"].append(data["attendance"][0])
    assert authorized.post("/api/import", json=data).status_code == 422
    assert authorized.get("/api/stats").json() == before


def test_csv_formula_and_encoding(authorized, participant):
    assert (
        authorized.post(
            "/api/participants", json={**participant, "organization": "=1+1"}
        ).status_code
        == 201
    )
    result = authorized.get("/api/export/csv")
    assert result.content.startswith(b"\xef\xbb\xbf")
    assert "'=1+1" in result.text


def test_headers_and_hosts(client):
    result = client.get("/")
    assert result.status_code == 200
    assert result.headers["x-frame-options"] == "DENY"
    assert "default-src 'self'" in result.headers["content-security-policy"]
    assert "access-control-allow-origin" not in result.headers
    assert client.get("/", headers={"host": "evil.example"}).status_code == 400
    assert client.get("/assets/app.js").status_code == 200
    assert client.get("/participants.html", follow_redirects=False).status_code == 307


def test_production_rejects_demo_db(client, cfg):
    with pytest.raises(RuntimeError, match="demo database"):
        init_db(
            replace(
                cfg,
                demo=False,
                production=True,
                secure_cookie=True,
                admin_password="LongPrivatePass!123",
            )
        )


def test_production_requires_password_and_disables_docs(tmp_path):
    from config import Settings

    cfg = Settings(db_path=tmp_path / "prod.db", demo=False, production=True, secure_cookie=True)
    with pytest.raises(RuntimeError, match="ADMIN_PASSWORD"):
        init_db(cfg)
    cfg = replace(cfg, admin_password="LongPrivatePass!123")
    with TestClient(create_app(cfg)) as client:
        assert client.get("/docs").status_code == 404
        result = client.post(
            "/api/auth/login", json={"username": "admin", "password": "LongPrivatePass!123"}
        )
        assert "Secure" in result.headers["set-cookie"]


def test_expired_session(client, cfg):
    login(client)
    with connection(cfg.db_path) as conn:
        conn.execute("UPDATE sessions SET expires=0")
    assert client.get("/api/participants").status_code == 401


def test_legacy_database_compatible(tmp_path):
    from config import Settings

    path = tmp_path / "legacy.db"
    with sqlite3.connect(path) as conn:
        conn.execute(
            "CREATE TABLE participants(id INTEGER PRIMARY KEY,lastName TEXT,firstName TEXT,organization TEXT,email TEXT UNIQUE,role TEXT,badgePrinted INTEGER DEFAULT 0,createdAt TEXT DEFAULT '')"
        )
        conn.execute(
            "INSERT INTO participants(lastName,firstName,organization,email,role) VALUES ('Legacy','User','','LEGACY@example.com','слушатель')"
        )
    with TestClient(create_app(Settings(db_path=path))) as client:
        login(client)
        assert client.get("/api/stats").json()["participants"] == 1
        assert (
            client.post(
                "/api/participants",
                json={"lastName": "Test", "firstName": "User", "email": "legacy@example.com"},
            ).status_code
            == 409
        )
