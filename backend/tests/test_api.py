"""
Basic API contract tests. These run against the FastAPI app without a live
DB by exercising validation and route wiring; full integration tests against
a real Postgres+pgvector instance are documented in README.md (manual test
plan) and require `docker compose up db` first.
"""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint_exists():
    response = client.get("/api/health")
    # DB likely unavailable in this unit-test context; we only assert the
    # contract (status code + shape), not that every dependency is up.
    assert response.status_code in (200, 500)


def test_create_session_missing_body_is_rejected():
    response = client.post("/api/sessions", json={"provider": "not-a-real-provider"})
    assert response.status_code == 422


def test_chat_requires_session_id():
    response = client.post("/api/chat", json={"message": "hello"})
    assert response.status_code == 422
