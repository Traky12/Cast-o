"""Caché Redis opcional SNN: sin Redis en CI, comportamiento base; mocks con TTL simulado."""

import os
from typing import Optional, Tuple

import pytest

pytestmark = pytest.mark.trl6

os.environ.setdefault("CASTUO_ROBOTICS_LAB_BEARER_TOKEN", "test-bearer-secret")


class _FakeRedisTTL:
    """Reloj monotónico simulado para expiración tipo Redis setex (segundos)."""

    def __init__(self) -> None:
        self._t = 0.0
        self._kv: dict[str, Tuple[str, float]] = {}
        self.setex_calls = 0

    def advance(self, seconds: float) -> None:
        self._t += float(seconds)

    def get(self, key: str) -> Optional[str]:
        if key not in self._kv:
            return None
        val, exp = self._kv[key]
        if exp <= self._t:
            del self._kv[key]
            return None
        return val

    def setex(self, key: str, ttl: int, value: str) -> None:
        self.setex_calls += 1
        self._kv[key] = (value, self._t + float(ttl))


def test_snn_cache_hit_reproducible(monkeypatch):
    """Misma clave canónica de sensores → mismo riego_ml y sellado (hit de caché)."""
    monkeypatch.setenv("CASTUO_SNN_CACHE_REDIS_URL", "redis://unused:6379/0")
    fake = _FakeRedisTTL()

    monkeypatch.setattr(
        "backend.integrations.robotics.neuromorphic_edge.redis_client_snn_cache",
        lambda: fake,
    )
    from backend.integrations.robotics.neuromorphic_edge import hydro_infer_dict

    sensors = {"humedad": 41.0, "ph": 6.1, "ec": 1.7}
    a = hydro_infer_dict(sensors)
    b = hydro_infer_dict(sensors)
    assert a["inference"]["riego_ml"] == b["inference"]["riego_ml"]
    assert a["chain_seal"] == b["chain_seal"]
    assert fake.setex_calls == 1


def test_snn_cache_ttl_seconds_explicit_overrides_season(monkeypatch):
    monkeypatch.delenv("CASTUO_SNN_CACHE_TTL_SECONDS", raising=False)
    monkeypatch.setenv("CASTUO_SNN_CACHE_SEASON", "verano")
    from backend.integrations.robotics.neuromorphic_edge import snn_cache_ttl_seconds

    assert snn_cache_ttl_seconds() == 600
    monkeypatch.setenv("CASTUO_SNN_CACHE_TTL_SECONDS", "120")
    assert snn_cache_ttl_seconds() == 120


def test_snn_cache_ttl_seconds_season_invierno(monkeypatch):
    monkeypatch.delenv("CASTUO_SNN_CACHE_TTL_SECONDS", raising=False)
    monkeypatch.setenv("CASTUO_SNN_CACHE_SEASON", "invierno")
    from backend.integrations.robotics.neuromorphic_edge import snn_cache_ttl_seconds

    assert snn_cache_ttl_seconds() == 300


def test_snn_cache_ttl_expiry(monkeypatch):
    """Tras superar TTL, get devuelve None → nueva escritura setex (miss)."""
    monkeypatch.setenv("CASTUO_SNN_CACHE_REDIS_URL", "redis://unused:6379/0")
    monkeypatch.setenv("CASTUO_SNN_CACHE_TTL_SECONDS", "300")
    fake = _FakeRedisTTL()

    monkeypatch.setattr(
        "backend.integrations.robotics.neuromorphic_edge.redis_client_snn_cache",
        lambda: fake,
    )
    from backend.integrations.robotics.neuromorphic_edge import hydro_infer_dict

    sensors = {"humedad": 22.0, "ph": 6.5, "ec": 0.5}
    hydro_infer_dict(sensors)
    hydro_infer_dict(sensors)
    assert fake.setex_calls == 1
    fake.advance(301)
    hydro_infer_dict(sensors)
    assert fake.setex_calls == 2
