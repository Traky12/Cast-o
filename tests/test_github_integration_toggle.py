"""Pruebas de feature flag para desacoplar integración GitHub del API principal."""
from __future__ import annotations

import importlib
import sys
from types import ModuleType

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.routing import Route


def _reload_main_module() -> ModuleType:
    """Recarga api.main para reevaluar flags de entorno de carga de routers."""
    sys.modules.pop("api.main", None)
    return importlib.import_module("api.main")


def _has_github_webhook_route(app: FastAPI) -> bool:
    return any(
        route.path == "/api/v1/github/webhook"
        for route in app.routes
        if isinstance(route, Route)
    )


def test_github_router_not_loaded_when_flag_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ENABLE_GITHUB_INTEGRATION", "false")
    monkeypatch.delenv("REQUIRE_GITHUB_HARDENING", raising=False)

    main_module = _reload_main_module()

    assert _has_github_webhook_route(main_module.app) is False
    assert main_module.ENABLE_GITHUB_INTEGRATION is False
    assert main_module.REQUIRE_GITHUB_HARDENING is False


@pytest.mark.certification
def test_github_toggle_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    """Alias operativo para reportes de certificación OFF."""
    monkeypatch.setenv("ENABLE_GITHUB_INTEGRATION", "false")
    monkeypatch.delenv("REQUIRE_GITHUB_HARDENING", raising=False)

    main_module = _reload_main_module()
    client = TestClient(main_module.app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert _has_github_webhook_route(main_module.app) is False


def test_github_defaults_to_disabled_when_env_vars_are_absent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("ENABLE_GITHUB_INTEGRATION", raising=False)
    monkeypatch.delenv("REQUIRE_GITHUB_HARDENING", raising=False)

    main_module = _reload_main_module()

    assert _has_github_webhook_route(main_module.app) is False
    assert main_module.ENABLE_GITHUB_INTEGRATION is False
    assert main_module.REQUIRE_GITHUB_HARDENING is False


def test_github_router_loaded_when_flag_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ENABLE_GITHUB_INTEGRATION", "true")
    monkeypatch.setenv("REQUIRE_GITHUB_HARDENING", "true")

    main_module = _reload_main_module()

    assert _has_github_webhook_route(main_module.app) is True
    assert main_module.ENABLE_GITHUB_INTEGRATION is True
    assert main_module.REQUIRE_GITHUB_HARDENING is True


@pytest.mark.certification
def test_github_toggle_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    """Alias operativo para reportes de certificación ON."""
    monkeypatch.setenv("ENABLE_GITHUB_INTEGRATION", "true")
    monkeypatch.setenv("REQUIRE_GITHUB_HARDENING", "true")

    main_module = _reload_main_module()
    client = TestClient(main_module.app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert _has_github_webhook_route(main_module.app) is True


@pytest.mark.parametrize(
    ("github_enabled", "expected_github_route"),
    [("false", False), ("true", True)],
)
def test_smoke_health_starts_with_and_without_github(
    monkeypatch: pytest.MonkeyPatch,
    github_enabled: str,
    expected_github_route: bool,
) -> None:
    monkeypatch.setenv("ENABLE_GITHUB_INTEGRATION", github_enabled)
    monkeypatch.delenv("REQUIRE_GITHUB_HARDENING", raising=False)

    main_module = _reload_main_module()
    client = TestClient(main_module.app)
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["version"] == "3.1.1"
    assert _has_github_webhook_route(main_module.app) is expected_github_route
