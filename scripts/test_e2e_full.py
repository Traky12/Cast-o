#!/usr/bin/env python3
"""
scripts/test_e2e_full.py — Prueba End-to-End del flujo completo:
  IoT → API → Blockchain → TRACES → Documentos

Uso:
    python3 scripts/test_e2e_full.py
    API_URL=https://api.castuo-system.cloud python3 scripts/test_e2e_full.py
"""

import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone

import jwt
import requests

# ─────────────────────────────────────────────────────────────
# Configuración
# ─────────────────────────────────────────────────────────────
API_URL = os.getenv("API_URL", "http://localhost:8000")
DEVICE_ID = f"TEST-DEVICE-E2E-{int(time.time()) % 10000}"
LOTE_ID = f"LOTE-E2E-{int(time.time())}"
JWT_SECRET = os.getenv("DEVICE_JWT_SECRET", "dev-only-insecure-secret")


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def _generate_device_jwt(device_id: str, secret: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": device_id,
        "iat": now,
        "exp": now + timedelta(minutes=60),
        "scope": "iot:telemetry",
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def _ok(label: str, data: dict | None = None) -> None:
    msg = f"  ✅ {label}"
    if data:
        print(msg, json.dumps(data, indent=4, ensure_ascii=False))
    else:
        print(msg)


def _fail(label: str, detail: str = "") -> None:
    print(f"  ❌ {label}", detail, file=sys.stderr)


# ─────────────────────────────────────────────────────────────
# Pasos del flujo E2E
# ─────────────────────────────────────────────────────────────

def step_health() -> bool:
    """Paso 0: Verificar que la API está activa."""
    try:
        r = requests.get(f"{API_URL}/health", timeout=10)
        r.raise_for_status()
        data = r.json()
        _ok("API health OK", data)
        return True
    except Exception as exc:
        _fail("API no responde", str(exc))
        return False


def step_iot_telemetry(jwt_token: str) -> bool:
    """Paso 1: Enviar datos de telemetría IoT."""
    payload = {
        "sensor_id": DEVICE_ID,
        "readings": {
            "humedad": 65.5,
            "temperatura": 22.3,
            "co2_ppm": 420,
        },
        "source": "e2e-test",
    }
    headers = {"Authorization": f"Bearer {jwt_token}"}
    try:
        r = requests.post(
            f"{API_URL}/api/v1/iot/telemetry",
            json=payload,
            headers=headers,
            timeout=10,
        )
        data = r.json()
        if r.status_code in (200, 202):
            _ok(f"IoT telemetry aceptada (HTTP {r.status_code})")
            return True
        _fail(f"IoT telemetry falló (HTTP {r.status_code})", str(data))
        return False
    except Exception as exc:
        _fail("IoT telemetry — excepción", str(exc))
        return False


def step_iot_latest() -> bool:
    """Paso 2: Recuperar última telemetría del sensor."""
    try:
        r = requests.get(
            f"{API_URL}/api/v1/iot/telemetry/{DEVICE_ID}/latest",
            timeout=10,
        )
        if r.status_code == 200:
            _ok("IoT latest OK", r.json())
            return True
        _fail(f"IoT latest falló (HTTP {r.status_code})", r.text)
        return False
    except Exception as exc:
        _fail("IoT latest — excepción", str(exc))
        return False


def step_traces_submit() -> bool:
    """Paso 3: Enviar lote a TRACES/Hyperledger con firma eIDAS."""
    payload = {
        "lote_id": LOTE_ID,
        "metadata": {
            "product_id": "AGRO-PROD-001",
            "quantity_kg": 250,
            "thc": 0.18,
            "cbd": 12.1,
            "fecha_cosecha": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "ubicacion": "Dehesa de Cáceres, parcela 42",
        },
    }
    try:
        r = requests.post(
            f"{API_URL}/api/v1/traces/submit",
            json=payload,
            timeout=15,
        )
        data = r.json()
        if r.status_code == 200:
            _ok("TRACES submit OK")
            traces_status = data.get("traces", {}).get("status", "unknown")
            print(f"     traces.status = {traces_status}")
            return True
        _fail(f"TRACES submit falló (HTTP {r.status_code})", str(data))
        return False
    except Exception as exc:
        _fail("TRACES submit — excepción", str(exc))
        return False


def step_gdpr_delete() -> bool:
    """Paso 4 (opcional): Verificar endpoint GDPR."""
    test_user = f"e2e-test-user-{int(time.time())}"
    try:
        r = requests.delete(
            f"{API_URL}/api/v1/admin/gdpr/users/{test_user}",
            timeout=10,
        )
        data = r.json()
        if r.status_code == 200:
            _ok(f"GDPR delete OK (user={test_user})")
            return True
        _fail(f"GDPR delete falló (HTTP {r.status_code})", str(data))
        return False
    except Exception as exc:
        _fail("GDPR delete — excepción", str(exc))
        return False


def step_prometheus_metrics() -> bool:
    """Paso 5: Comprobar que /metrics responde."""
    try:
        r = requests.get(f"{API_URL}/metrics", timeout=10)
        if r.status_code == 200 and ("castuo" in r.text or "uptime" in r.text):
            _ok("Prometheus /metrics OK")
            return True
        _fail(f"Prometheus metrics falló (HTTP {r.status_code})")
        return False
    except Exception as exc:
        _fail("Prometheus metrics — excepción", str(exc))
        return False


# ─────────────────────────────────────────────────────────────
# Runner
# ─────────────────────────────────────────────────────────────

def run_e2e_test() -> bool:
    print(f"\n{'='*55}")
    print(f"  🧪 CASTÚO-SYSTEM™ — Prueba E2E")
    print(f"  API: {API_URL}")
    print(f"  Device: {DEVICE_ID}")
    print(f"  Lote:   {LOTE_ID}")
    print(f"{'='*55}\n")

    results: dict[str, bool] = {}

    # Paso 0 — Health
    print("Paso 0: Health check")
    results["health"] = step_health()
    if not results["health"]:
        print("\n⛔ API no disponible. Abortando.")
        return False

    # Paso 1 — JWT + IoT
    print("\nPaso 1: Generar JWT y enviar telemetría IoT")
    token = _generate_device_jwt(DEVICE_ID, JWT_SECRET)
    print(f"  🔑 JWT generado para {DEVICE_ID}")
    results["iot_telemetry"] = step_iot_telemetry(token)

    # Paso 2 — Latest
    print("\nPaso 2: Recuperar última telemetría")
    results["iot_latest"] = step_iot_latest()

    # Paso 3 — TRACES
    print("\nPaso 3: Enviar a TRACES/Hyperledger (firma eIDAS)")
    results["traces_submit"] = step_traces_submit()

    # Paso 4 — GDPR
    print("\nPaso 4: Endpoint GDPR (derecho al olvido)")
    results["gdpr_delete"] = step_gdpr_delete()

    # Paso 5 — Metrics
    print("\nPaso 5: Prometheus /metrics")
    results["prometheus"] = step_prometheus_metrics()

    # Resumen
    passed = sum(results.values())
    total = len(results)
    print(f"\n{'='*55}")
    for step, ok in results.items():
        icon = "✅" if ok else "❌"
        print(f"  {icon} {step}")
    print(f"{'='*55}")
    print(f"  Resultado: {passed}/{total} pasos OK")
    print(f"{'='*55}\n")

    return passed == total


if __name__ == "__main__":
    success = run_e2e_test()
    sys.exit(0 if success else 1)
