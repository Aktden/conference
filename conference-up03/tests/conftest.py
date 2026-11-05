from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from config import Settings
from main import create_app


@pytest.fixture
def cfg(tmp_path):
    return Settings(db_path=Path(tmp_path) / "app.db")


@pytest.fixture
def client(cfg):
    with TestClient(create_app(cfg)) as client:
        yield client


def login(client, role="admin"):
    password = {
        "admin": "DemoAdmin!2026",
        "operator": "DemoOperator!2026",
        "viewer": "DemoViewer!2026",
    }[role]
    result = client.post("/api/auth/login", json={"username": role, "password": password})
    assert result.status_code == 200
    client.headers["X-CSRF-Token"] = result.json()["csrfToken"]
    return result


@pytest.fixture
def authorized(client):
    login(client)
    return client


@pytest.fixture
def participant():
    return {
        "lastName": "Тестов",
        "firstName": "Иван",
        "organization": "Тест",
        "email": "test@example.com",
        "role": "слушатель",
    }
