#!/usr/bin/env python3
"""Prueba E2E de staging con checks de APIs, auth, Redis y Timescale.

Exit codes:
  0: todas las pruebas pasan
  1: al menos una prueba funcional falla
  2: error de conexión a dependencias críticas (Redis/Timescale/API)
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta, timezone

import jwt
import requests

try:
    import redis
except ImportError:
    redis = None

try:
    import psycopg2
except ImportError:
    psycopg2 = None


API_URL = os.getenv("API_URL", "http://api.castuo-system.cloud")
JWT_SECRET = os.getenv("JWT_SECRET", "dev-only-insecure-secret")
TENANT_ID = os.getenv("TENANT_ID", "test")

REDIS_URL = os.getenv("REDIS_URL", "")
TIMESCALE_DSN = os.getenv("TIMESCALE_DSN", "")


def mk_token() -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": "e2e-user",
        "tenant": TENANT_ID,
        "roles": ["admin_general"],
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=30)).timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def ok(msg: str) -> None:
    print(f"✅ {msg}")


def fail(msg: str) -> None:
    print(f"❌ {msg}")


def check_api_endpoints(token: str) -> bool:
    success = True

    for path in ("/health", "/metrics"):
        try:
            r = requests.get(f"{API_URL}{path}", timeout=10)
            if r.status_code == 200:
                ok(f"[API] {path} responde en estado 200")
            else:
                fail(f"[API] {path} devolvió {r.status_code}")
                success = False
        except Exception as exc:
            fail(f"[API] {path} error de conexión: {exc}")
            raise

    headers = {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": TENANT_ID,
    }
    for path in (
        "/api/v1/audit/verify",
        "/api/v1/embeddings/search",
    ):
        try:
            if path.endswith("/search"):
                r = requests.post(
                    f"{API_URL}{path}",
                    headers=headers,
                    json={"query": "agricultura", "limit": 3},
                    timeout=10,
                )
            else:
                r = requests.get(f"{API_URL}{path}", headers=headers, timeout=10)
            if r.status_code < 500:
                ok(f"[API] {path} respondió ({r.status_code})")
            else:
                fail(f"[API] {path} error servidor ({r.status_code})")
                success = False
        except Exception as exc:
            fail(f"[API] {path} error de conexión: {exc}")
            raise

    return success


def check_auth_mfa(token: str) -> bool:
    try:
        r = requests.get(
            f"{API_URL}/api/v1/auth/protected",
            headers={
                "Authorization": f"Bearer {token}",
                "X-MFA-Code": "000000",
            },
            timeout=10,
        )
        if r.status_code in (200, 403):
            ok(f"[Auth] protected validado (HTTP {r.status_code})")
            return True
        fail(f"[Auth] protected devolvió {r.status_code}")
        return False
    except Exception as exc:
        fail(f"[Auth] error de conexión: {exc}")
        raise


def check_redis() -> tuple[bool, bool]:
    if not REDIS_URL:
        print("⚠️ [Redis] REDIS_URL no configurado, check omitido")
        return True, False
    if redis is None:
        fail("[Redis] dependencia redis no instalada")
        return False, True
    try:
        client = redis.Redis.from_url(REDIS_URL)
        pong = client.ping()
        if pong:
            ok("[Redis] Conexión exitosa (PONG)")
            return True, False
        fail("[Redis] ping sin respuesta")
        return False, True
    except Exception as exc:
        fail(f"[Redis] error de conexión: {exc}")
        return False, True


def check_timescale() -> tuple[bool, bool]:
    if not TIMESCALE_DSN:
        print("⚠️ [Timescale] TIMESCALE_DSN no configurado, check omitido")
        return True, False
    if psycopg2 is None:
        fail("[Timescale] dependencia psycopg2 no instalada")
        return False, True
    try:
        conn = psycopg2.connect(TIMESCALE_DSN, connect_timeout=5)
        with conn.cursor() as cur:
            cur.execute("SELECT 1;")
            row = cur.fetchone()
        conn.close()
        if row and row[0] == 1:
            ok("[Timescale] Consulta SQL ejecutada")
            return True, False
        fail("[Timescale] consulta devolvió resultado inesperado")
        return False, True
    except Exception as exc:
        fail(f"[Timescale] error de conexión: {exc}")
        return False, True


def main() -> int:
    token = mk_token()
    functional_ok = True

    try:
        functional_ok = check_api_endpoints(token) and functional_ok
        functional_ok = check_auth_mfa(token) and functional_ok
    except Exception:
        return 2

    redis_ok, redis_conn_err = check_redis()
    timescale_ok, timescale_conn_err = check_timescale()
    functional_ok = functional_ok and redis_ok and timescale_ok

    if redis_conn_err or timescale_conn_err:
        print("---")
        print("RESULTADO: FAIL (error de conexión a Redis/Timescale)")
        return 2

    if not functional_ok:
        print("---")
        print("RESULTADO: FAIL (al menos una prueba funcional falló)")
        return 1

    print("---")
    print("RESULTADO: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
