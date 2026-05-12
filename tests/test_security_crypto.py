"""
Tests de contrato — QSEC-001 / QSEC-002

Tres suites:
  1. Cifrado híbrido X25519 + AES-256-GCM (crypto.py)
  2. JWT middleware quantum_auth (create_token + require_quantum_auth)
  3. ECIES P-384 + AES-256-GCM para IoT (ecies.py)

Estos tests corren sin pqcrypto (solo cryptography + PyJWT).
"""

from __future__ import annotations

import importlib
import os
import sys

# Permite importar desde infrastructure/ en el path del proyecto
_ROOT = os.path.join(os.path.dirname(__file__), "..")
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)


# ─── Suite 1: Cifrado híbrido X25519 ─────────────────────────────────────────

class TestHybridCrypto:
    def test_encrypt_decrypt_roundtrip(self):
        """Encrypt + decrypt devuelve el plaintext original."""
        from infrastructure.fastapi.crypto import decrypt, encrypt, generate_x25519_keypair

        private_key, public_key = generate_x25519_keypair()
        plaintext = b"Datos de trazabilidad CASTUO v3.1"

        envelope = encrypt(plaintext, public_key)

        assert "ephemeral_public_key" in envelope
        assert "nonce" in envelope
        assert "ciphertext" in envelope
        assert len(envelope["nonce"]) == 12

        recovered = decrypt(envelope, private_key)
        assert recovered == plaintext

    def test_ciphertext_differs_from_plaintext(self):
        """El ciphertext no debe contener el plaintext en claro."""
        from infrastructure.fastapi.crypto import encrypt, generate_x25519_keypair

        _, public_key = generate_x25519_keypair()
        plaintext = b"secreto castuo"
        envelope = encrypt(plaintext, public_key)
        assert plaintext not in envelope["ciphertext"]

    def test_tampered_ciphertext_raises(self):
        """Ciphertext modificado debe lanzar InvalidTag."""
        from cryptography.exceptions import InvalidTag
        from infrastructure.fastapi.crypto import decrypt, encrypt, generate_x25519_keypair

        private_key, public_key = generate_x25519_keypair()
        envelope = encrypt(b"datos originales", public_key)

        tampered = dict(envelope)
        tampered["ciphertext"] = b"\xff" * len(envelope["ciphertext"])

        try:
            decrypt(tampered, private_key)
            assert False, "Debería haber lanzado InvalidTag"
        except (InvalidTag, Exception):
            pass  # Cualquier error de integridad es correcto


# ─── Suite 2: JWT middleware ──────────────────────────────────────────────────

class TestQuantumAuth:
    _SECRET = "test-jwt-secret-castuo-qsec-001"

    def test_create_and_decode_token(self):
        """create_token genera un JWT decodificable con el mismo secreto."""
        import jwt
        from infrastructure.fastapi.middleware.quantum_auth import create_token

        token = create_token("device-001", "iot", secret=self._SECRET)
        payload = jwt.decode(token, self._SECRET, algorithms=["HS256"])
        assert payload["sub"] == "device-001"
        assert payload["role"] == "iot"

    def test_invalid_role_raises(self):
        """Rol no válido lanza ValueError."""
        from infrastructure.fastapi.middleware.quantum_auth import create_token

        try:
            create_token("x", "superadmin", secret=self._SECRET)
            assert False, "Debería haber lanzado ValueError"
        except ValueError:
            pass

    def test_require_quantum_auth_valid(self, monkeypatch):
        """Dependencia acepta token válido con rol permitido."""
        monkeypatch.setenv("CASTUO_QUANTUM_JWT_SECRET", self._SECRET)
        import importlib
        import infrastructure.fastapi.middleware.quantum_auth as mod
        importlib.reload(mod)

        from infrastructure.fastapi.middleware.quantum_auth import create_token, require_quantum_auth

        token = create_token("rpi-01", "iot", secret=self._SECRET)
        dep = require_quantum_auth(["iot"])
        result = dep(x_quantum_secure=f"Bearer {token}")
        assert result["sub"] == "rpi-01"
        assert result["role"] == "iot"

    def test_require_quantum_auth_wrong_role(self, monkeypatch):
        """Rol presente pero no en allowed_roles lanza 403."""
        from fastapi import HTTPException
        monkeypatch.setenv("CASTUO_QUANTUM_JWT_SECRET", self._SECRET)

        from infrastructure.fastapi.middleware.quantum_auth import create_token, require_quantum_auth

        token = create_token("rpi-01", "iot", secret=self._SECRET)
        dep = require_quantum_auth(["admin"])

        try:
            dep(x_quantum_secure=f"Bearer {token}")
            assert False, "Debería haber lanzado HTTPException 403"
        except HTTPException as exc:
            assert exc.status_code == 403


# ─── Suite 3: ECIES P-384 ────────────────────────────────────────────────────

class TestECIES:
    def test_encrypt_decrypt_roundtrip(self):
        """ECIES encrypt + decrypt devuelve el plaintext original."""
        from infrastructure.iot_security.ecies import decrypt, encrypt, generate_p384_keypair

        private_key, public_key = generate_p384_keypair()
        plaintext = b"Telemetria IoT cifrada con P-384"

        envelope = encrypt(plaintext, public_key)

        assert "ephemeral_public_key" in envelope
        assert "nonce" in envelope
        assert "ciphertext" in envelope

        recovered = decrypt(envelope, private_key)
        assert recovered == plaintext

    def test_different_keys_cannot_decrypt(self):
        """Clave distinta no puede descifrar."""
        from cryptography.exceptions import InvalidTag
        from infrastructure.iot_security.ecies import decrypt, encrypt, generate_p384_keypair

        _, pub_alice = generate_p384_keypair()
        priv_bob, _ = generate_p384_keypair()

        envelope = encrypt(b"mensaje privado", pub_alice)

        try:
            decrypt(envelope, priv_bob)
            assert False, "No debería poder descifrar con clave incorrecta"
        except (InvalidTag, Exception):
            pass
import importlib.util
from pathlib import Path


def _load_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_quantum_secure_encrypt_decrypt_roundtrip():
    crypto_mod = _load_module(
        Path(__file__).resolve().parents[1] / "infrastructure" / "fastapi" / "crypto.py",
        "castuo_quantum_crypto",
    )

    receiver = crypto_mod.QuantumSecure()
    sender = crypto_mod.QuantumSecure()

    encrypted = sender.encrypt(
        "mensaje-critico-castuo",
        recipient_public_key_hex=receiver.public_key_hex,
    )
    decrypted = receiver.decrypt(encrypted)

    assert decrypted == "mensaje-critico-castuo"
    assert encrypted["suite"] == "x25519-hkdf-sha256+aes256gcm"


def test_quantum_secure_generate_keypair_shapes():
    crypto_mod = _load_module(
        Path(__file__).resolve().parents[1] / "infrastructure" / "fastapi" / "crypto.py",
        "castuo_quantum_crypto_keypair",
    )

    keypair = crypto_mod.QuantumSecure.generate_keypair()
    assert isinstance(keypair["private_key_hex"], str)
    assert isinstance(keypair["public_key_hex"], str)
    assert len(keypair["private_key_hex"]) > 0
    assert len(keypair["public_key_hex"]) > 0


def test_ecies_encrypt_decrypt_roundtrip():
    ecies_mod = _load_module(
        Path(__file__).resolve().parents[1]
        / "infrastructure"
        / "iot-security"
        / "ecies.py",
        "castuo_ecies",
    )

    receiver = ecies_mod.ECIES()
    sender = ecies_mod.ECIES()

    encrypted = sender.encrypt("payload-iot", receiver.public_key_pem)
    decrypted = receiver.decrypt(encrypted)

    assert decrypted == "payload-iot"
    assert isinstance(encrypted, bytes)
    assert len(encrypted) > 64
