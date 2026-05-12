"""Pytest wrapper for the cloud IoT smoke checks.

These tests run against a *mocked* MQTT broker and *mocked* API so they
pass in CI without any running Docker stack.

To run against a live Docker Compose stack use the script directly:
    ./scripts/cloud-iot-smoke.sh
"""
from __future__ import annotations

import importlib.util
import json
import sys
import threading
import time
from pathlib import Path
from typing import Any
from unittest import mock

import pytest

# Make scripts/cloud-iot-smoke.py importable as a module
_SMOKE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "cloud-iot-smoke.py"
_spec = importlib.util.spec_from_file_location("cloud_iot_smoke", _SMOKE_PATH)
_module = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
_spec.loader.exec_module(_module)  # type: ignore[union-attr]
smoke = _module


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _reset() -> None:
    smoke._results.clear()  # noqa: SLF001


# ---------------------------------------------------------------------------
# 1. api_health
# ---------------------------------------------------------------------------

class TestApiHealth:
    def test_pass_on_200(self) -> None:
        _reset()
        mock_resp = mock.Mock(status_code=200)
        with mock.patch.object(smoke.httpx, "Client") as mock_client_cls:
            mock_client_cls.return_value.__enter__.return_value.get.return_value = mock_resp
            assert smoke.check_api_health() is True
        assert smoke._results.get("api_health") == "PASS"

    def test_fail_on_500(self) -> None:
        _reset()
        mock_resp = mock.Mock(status_code=500)
        with mock.patch.object(smoke.httpx, "Client") as mock_client_cls:
            mock_client_cls.return_value.__enter__.return_value.get.return_value = mock_resp
            assert smoke.check_api_health() is False
        assert "FAIL" in smoke._results.get("api_health", "")

    def test_fail_on_connection_error(self) -> None:
        _reset()
        with mock.patch.object(smoke.httpx, "Client") as mock_client_cls:
            mock_client_cls.return_value.__enter__.return_value.get.side_effect = Exception("refused")
            assert smoke.check_api_health() is False
        assert "FAIL" in smoke._results.get("api_health", "")


# ---------------------------------------------------------------------------
# 2. telemetry_ingest_lookup
# ---------------------------------------------------------------------------

class TestTelemetryIngestLookup:
    def test_pass_on_200_with_valid_sensor(self) -> None:
        _reset()
        ok = mock.Mock(status_code=200)
        ok.json.return_value = {
            "sensor_id": smoke.SENSOR_ID,
            "traces": {"status": "queued"},
        }
        with mock.patch.object(smoke.httpx, "Client") as mock_client_cls:
            mock_client_cls.return_value.__enter__.return_value.get.return_value = ok
            assert smoke.check_telemetry_ingest_lookup() is True

    def test_pass_on_404_then_200(self) -> None:
        _reset()
        not_found = mock.Mock(status_code=404, text="Not Found")
        ok = mock.Mock(status_code=200)
        ok.json.return_value = {
            "sensor_id": smoke.SENSOR_ID,
            "traces": {"status": "disabled"},
        }
        with (
            mock.patch.object(smoke.httpx, "Client") as mock_client_cls,
            mock.patch.object(smoke, "TIMEOUT", 2),
        ):
            mock_client_cls.return_value.__enter__.return_value.get.side_effect = [
                not_found,
                ok,
            ]
            assert smoke.check_telemetry_ingest_lookup() is True

    def test_fail_on_500(self) -> None:
        _reset()
        err = mock.Mock(status_code=500, text="internal error")
        with mock.patch.object(smoke.httpx, "Client") as mock_client_cls:
            mock_client_cls.return_value.__enter__.return_value.get.return_value = err
            assert smoke.check_telemetry_ingest_lookup() is False


# ---------------------------------------------------------------------------
# 3. MQTT publish (mocked client)
# ---------------------------------------------------------------------------

class TestMqttPublish:
    def _patched_client(self, connect_rc: int = 0, publish_ok: bool = True) -> Any:
        mock_client = mock.MagicMock()

        def fake_connect(host: str, port: int, **_: Any) -> None:  # noqa: ARG001
            # simulate on_connect callback immediately
            threading.Timer(
                0.05,
                lambda: mock_client.on_connect(mock_client, None, None, connect_rc),
            ).start()

        def fake_publish(topic: str, payload: str, qos: int = 0) -> mock.Mock:  # noqa: ARG001
            msg = mock.Mock()
            msg.wait_for_publish = mock.Mock(return_value=None)
            if publish_ok:
                threading.Timer(
                    0.05,
                    lambda: mock_client.on_publish(mock_client, None, 1),
                ).start()
            return msg

        mock_client.connect.side_effect = fake_connect
        mock_client.publish.side_effect = fake_publish
        mock_client.on_connect = None
        mock_client.on_publish = None
        return mock_client

    def test_pass_on_successful_publish(self) -> None:
        _reset()
        with (
            mock.patch.object(smoke.mqtt, "Client", return_value=self._patched_client()),
            mock.patch.object(smoke, "TIMEOUT", 3),
        ):
            result = smoke.check_mqtt_publish()
        assert result is True
        assert smoke._results.get("mqtt_publish") == "PASS"

    def test_fail_on_connect_exception(self) -> None:
        _reset()
        mock_client = mock.MagicMock()
        mock_client.connect.side_effect = OSError("connection refused")
        with mock.patch.object(smoke.mqtt, "Client", return_value=mock_client):
            result = smoke.check_mqtt_publish()
        assert result is False
        assert "FAIL" in smoke._results.get("mqtt_publish", "")


# ---------------------------------------------------------------------------
# 4. Wireless Logic upstream (skipped when env var absent)
# ---------------------------------------------------------------------------

class TestWirelessLogicUpstream:
    def test_skip_when_no_host(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("SMOKE_WL_HOST", raising=False)
        result = smoke.check_wireless_logic_upstream()
        assert result is None

    def test_fail_when_host_set_but_broker_unreachable(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _reset()
        monkeypatch.setenv("SMOKE_WL_HOST", "mqtt.conexa.example.invalid")
        monkeypatch.setenv("SMOKE_WL_TOKEN", "test-token")
        mock_client = mock.MagicMock()
        mock_client.connect.side_effect = OSError("network unreachable")
        with mock.patch.object(smoke.mqtt, "Client", return_value=mock_client):
            result = smoke.check_wireless_logic_upstream()
        assert result is False
        assert "wireless_logic_upstream" in str(smoke._results)
