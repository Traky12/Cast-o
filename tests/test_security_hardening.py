"""
Tests para validar mejoras de seguridad integral del sistema.

Cubre:
- Validación de secretos obligatorios
- Security headers HTTP
- Rate limiting
- CORS
- Token validation hardened
- Input sanitization
"""

import os
from typing import Any

import pytest
from fastapi import HTTPException, FastAPI
from fastapi.testclient import TestClient

from api.security.hardened import (
    SecretValidator,
    SecurityHeadersMiddleware,
    CORSConfig,
    RateLimitStore,
    SecurityAudit,
    TokenValidator,
    InputValidator,
)


class TestSecretValidator:
    """Pruebas para validación de secretos."""

    def test_missing_required_secrets_in_production_raises(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """En producción, faltan secretos obliga error."""
        monkeypatch.setenv("ENV", "production")
        monkeypatch.delenv("JWT_SECRET", raising=False)
        monkeypatch.delenv("DEVICE_JWT_SECRET", raising=False)

        with pytest.raises(RuntimeError, match="Secretos obligatorios"):
            SecretValidator.validate()

    def test_required_secrets_provided_in_production_success(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Con todos los secretos, validación exitosa."""
        monkeypatch.setenv("ENV", "production")
        monkeypatch.setenv("JWT_SECRET", "test-secret-key")
        monkeypatch.setenv("DEVICE_JWT_SECRET", "device-secret")

        result = SecretValidator.validate()
        assert result["status"] == "secure"
        assert result["missing_required"] == []

    def test_development_mode_allows_missing_secrets(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """En desarrollo, secretos no obligatorios."""
        monkeypatch.setenv("ENV", "development")
        monkeypatch.delenv("JWT_SECRET", raising=False)
        monkeypatch.delenv("DEVICE_JWT_SECRET", raising=False)

        result = SecretValidator.validate()
        assert result["environment"] == "development"
        assert result["status"] == "secure"


class TestSecurityHeaders:
    """Pruebas para security headers middleware."""

    def test_security_headers_middleware_adds_headers(self) -> None:
        """Valida que el middleware agrega headers de seguridad."""
        from fastapi import FastAPI
        from fastapi.responses import JSONResponse
        from fastapi.testclient import TestClient

        # Crear app mini para test
        app = FastAPI()

        @app.get("/test")
        async def test_endpoint() -> JSONResponse:
            return JSONResponse({"status": "ok"})

        # Agregar middleware manualmente
        app.add_middleware(SecurityHeadersMiddleware)

        client = TestClient(app)
        response = client.get("/test")

        # Validar headers (names are lowercase in response.headers dict)
        assert response.headers.get("x-content-type-options") == "nosniff"
        assert response.headers.get("x-frame-options") == "DENY"
        assert "nosniff" in response.headers.get("x-content-type-options", "")
        assert "geolocation" in response.headers.get("permissions-policy", "")

    def test_security_headers_middleware_all_required_headers(self) -> None:
        """Valida presencia de todos los headers requeridos."""
        from fastapi import FastAPI
        from fastapi.responses import PlainTextResponse
        from fastapi.testclient import TestClient

        app = FastAPI()

        @app.get("/health")
        async def health() -> PlainTextResponse:
            return PlainTextResponse("ok")

        app.add_middleware(SecurityHeadersMiddleware)
        client = TestClient(app)
        response = client.get("/health")

        # Validar headers requeridos (lowercase)
        assert response.headers.get("x-content-type-options") == "nosniff"
        assert response.headers.get("x-frame-options") == "DENY"
        assert response.headers.get("referrer-policy") is not None
        assert response.headers.get("permissions-policy") is not None


class TestRateLimiting:
    """Pruebas para rate limiting."""

    def test_rate_limit_store_allows_within_limit(self) -> None:
        """Requests dentro del límite son permitidos."""
        store = RateLimitStore(default_limit=5, window_seconds=60)

        for i in range(5):
            assert store.is_allowed(f"user_{i}") is True

    def test_rate_limit_store_rejects_beyond_limit(self) -> None:
        """Requests fuera del límite son rechazados."""
        store = RateLimitStore(default_limit=3, window_seconds=60)
        key = "test_user"

        # Los primeros 3 pasan
        for _ in range(3):
            assert store.is_allowed(key) is True

        # El 4to falla
        assert store.is_allowed(key) is False

    def test_rate_limit_remaining_calculation(self) -> None:
        """Calcula correctamente requests restantes."""
        store = RateLimitStore(default_limit=10, window_seconds=60)
        key = "test"

        # Primero: 10 disponibles
        assert store.get_remaining(key) == 10

        # Después de 3: 7 disponibles
        for _ in range(3):
            store.is_allowed(key)

        assert store.get_remaining(key) == 7


class TestCORSConfig:
    """Pruebas para configuración de CORS."""

    def test_cors_development_mode(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """En desarrollo, más origins permitidos."""
        monkeypatch.setenv("ENV", "development")

        origins = CORSConfig.get_allowed_origins()
        assert "http://localhost:3000" in origins
        assert len(origins) >= 2  # Al menos localhost

    def test_cors_production_mode_restricted(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """En producción, solo origins configurados explícitamente."""
        monkeypatch.setenv("ENV", "production")
        monkeypatch.setenv(
            "CORS_ALLOWED_ORIGINS",
            "https://example.com,https://app.example.com"
        )

        origins = CORSConfig.get_allowed_origins()
        assert "https://example.com" in origins
        assert "https://app.example.com" in origins
        assert "http://localhost:3000" not in origins


class TestSecurityAudit:
    """Pruebas para auditoría de seguridad."""

    def test_audit_log_event_structure(self, caplog: Any) -> None:
        """Valida estructura de log de auditoría."""
        with caplog.at_level("WARNING"):
            SecurityAudit.log_event(
                event_type="auth_failure",
                severity="high",
                user_id="user123",
                ip_address="192.168.1.1",
                details={"reason": "invalid_password"},
            )

        assert "SECURITY_AUDIT" in caplog.text
        assert "auth_failure" in caplog.text
        assert "user123" in caplog.text

    def test_audit_hash_sensitive_data(self) -> None:
        """Hash de datos sensibles es consisten pero no reversible."""
        password = "super-secret-password"
        hashed1 = SecurityAudit.hash_sensitive_data(password)
        hashed2 = SecurityAudit.hash_sensitive_data(password)

        # Mismo input → mismo hash
        assert hashed1 == hashed2

        # No es el original
        assert hashed1 != password
        assert len(hashed1) == 16  # SHA256 truncado


class TestTokenValidator:
    """Pruebas para validación de tokens."""

    def test_validate_token_age_fresh_token(self) -> None:
        """Token reciente es válido."""
        import time

        now = time.time()
        claims = {"iat": now, "sub": "test", "roles": ["user"]}

        assert TokenValidator.validate_token_age(claims) is True

    def test_validate_token_age_old_token(self) -> None:
        """Token viejo está expirado."""
        import time

        now = time.time()
        token_age_seconds = TokenValidator.MAX_TOKEN_AGE_SECONDS + 100

        old_iat = now - token_age_seconds
        claims = {"iat": old_iat, "sub": "test", "roles": ["user"]}

        assert TokenValidator.validate_token_age(claims) is False

    def test_validate_token_required_claims(self) -> None:
        """Token sin claims requeridos es inválido."""
        claims_missing_sub = {"iat": 1234567, "roles": ["user"]}
        claims_missing_roles = {"iat": 1234567, "sub": "test"}

        assert TokenValidator.validate_required_claims(claims_missing_sub) is False
        assert TokenValidator.validate_required_claims(claims_missing_roles) is False

    def test_validate_token_with_all_claims(self) -> None:
        """Token con todos los claims es válido."""
        claims = {"iat": 1234567, "sub": "test", "roles": ["user"]}
        assert TokenValidator.validate_required_claims(claims) is True


class TestInputValidator:
    """Pruebas para validación de entrada."""

    def test_sanitize_string_removes_null_bytes(self) -> None:
        """Remueve null bytes de strings."""
        dangerous = "hello\x00world"
        sanitized = InputValidator.sanitize_string(dangerous)
        assert "\x00" not in sanitized
        assert sanitized == "helloworld"

    def test_sanitize_string_removes_control_chars(self) -> None:
        """Remueve caracteres de control (excepto new lines)."""
        dangerous = "hello\x01\x02world"
        sanitized = InputValidator.sanitize_string(dangerous)
        assert "\x01" not in sanitized
        assert "\x02" not in sanitized

    def test_sanitize_string_preserves_newlines(self) -> None:
        """Preserva newlines y tabs lícitos."""
        text = "hello\nworld\ttest"
        sanitized = InputValidator.sanitize_string(text)
        assert "\n" in sanitized
        assert "\t" in sanitized

    def test_sanitize_string_truncates_long(self) -> None:
        """Trunca strings muy largos."""
        long_str = "a" * 2000
        sanitized = InputValidator.sanitize_string(long_str, max_length=100)
        assert len(sanitized) == 100

    def test_validate_email_valid(self) -> None:
        """Valida emails válidos."""
        assert InputValidator.validate_email("user@example.com") is True
        assert InputValidator.validate_email("test.user+tag@example.co.uk") is True

    def test_validate_email_invalid(self) -> None:
        """Rechaza emails inválidos."""
        assert InputValidator.validate_email("invalid") is False
        assert InputValidator.validate_email("@example.com") is False
        assert InputValidator.validate_email("user@") is False
        assert InputValidator.validate_email("") is False

    def test_validate_uuid_valid(self) -> None:
        """Valida UUIDs válidos."""
        valid_uuid = "550e8400-e29b-41d4-a716-446655440000"
        assert InputValidator.validate_uuid(valid_uuid) is True

    def test_validate_uuid_invalid(self) -> None:
        """Rechaza UUIDs inválidos."""
        assert InputValidator.validate_uuid("not-a-uuid") is False
        assert InputValidator.validate_uuid("550e8400") is False
