from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routers.education import router as education_router


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(education_router)
    return TestClient(app)


def test_validate_education_content_accepts_accessible_content() -> None:
    client = _client()
    response = client.post(
        "/api/v1/education/validate",
        json={
            "text": "Esta leccion promueve igualdad, medio ambiente y cooperacion en un huerto escolar.",
            "audience": "5-12",
            "topic": "huertos escolares",
            "images": [{"url": "/img.png", "alt": "Ninos regando plantas"}],
            "activities": [
                {
                    "type": "juego",
                    "accessibility": {"screen_reader_text": "Lee las instrucciones"},
                }
            ],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["issues"] == []
    assert data["audit"]["ready_for_gaiachain"] is True


def test_validate_education_content_rejects_banned_words_and_missing_alt() -> None:
    client = _client()
    response = client.post(
        "/api/v1/education/validate",
        json={
            "text": "Esta leccion incluye discriminacion y no menciona medio ambiente.",
            "audience": "5-12",
            "images": [{"url": "/img.png"}],
            "activities": [],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert any("prohibido" in issue.lower() for issue in data["issues"])
    assert any("alternativa" in issue.lower() for issue in data["issues"])


def test_example_content_endpoint_returns_seed_payload() -> None:
    client = _client()
    response = client.get("/api/v1/education/example-content")
    assert response.status_code == 200
    data = response.json()
    assert data["audience"] == "5-12"
    assert data["images"][0]["alt"]


def test_metrics_tracking_endpoints_return_ok() -> None:
    client = _client()
    lesson = client.post(
        "/api/v1/education/lesson-view",
        json={"age_group": "13-16", "topic": "sostenibilidad"},
    )
    users = client.post(
        "/api/v1/education/active-users",
        json={"region": "eu-west", "count": 12},
    )
    assert lesson.status_code == 200
    assert users.status_code == 200
    assert lesson.json()["tracked"] is True
    assert users.json()["tracked"] is True


def test_publish_rejects_discriminatory_content() -> None:
    client = _client()
    response = client.post(
        "/api/v1/education/publish",
        json={
            "text": "Este material excluye a ninas y migrantes del taller.",
            "topic": "huerto escolar",
            "audience": "13-16",
            "images": [],
            "activities": [],
        },
    )
    assert response.status_code == 400
