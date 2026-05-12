# backend/security/tests/test_pq_crypto.py
import os
import sys
import tempfile

import pytest

# Usar directorio temporal para claves en tests
os.environ["CASTUO_KEY_DIR"] = tempfile.mkdtemp(prefix="castuo_keys_")

# Importar después de fijar env
_repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)
try:
    from backend.security.pq_crypto import PostQuantumCrypto
except ImportError:
    from pq_crypto import PostQuantumCrypto


@pytest.fixture
def crypto():
    return PostQuantumCrypto()


def test_kyber_encrypt_decrypt(crypto):
    message = "Mensaje secreto CASTÚO-SYSTEM™"
    encrypted = crypto.kyber_encrypt(message)
    decrypted = crypto.kyber_decrypt(encrypted)
    assert decrypted == message


def test_dilithium_sign_verify(crypto):
    message = "Documento oficial CASTÚO-SYSTEM™"
    signature = crypto.dilithium_sign(message)
    assert crypto.dilithium_verify(message, signature) is True
    assert crypto.dilithium_verify("Mensaje falsificado", signature) is False


def test_hybrid_encrypt_large(crypto):
    large_data = "A" * (1024 * 100)  # 100KB
    encrypted = crypto.hybrid_encrypt_large(large_data)
    decrypted = crypto.hybrid_decrypt_large(encrypted)
    assert decrypted == large_data
    assert encrypted.get("integrity_hash") == crypto.blake3_hash(large_data)


def test_file_encryption(crypto, tmp_path):
    test_file = tmp_path / "test.txt"
    encrypted_file = tmp_path / "test.encrypted.json"
    decrypted_file = tmp_path / "test_decrypted.txt"

    test_file.write_text("Datos sensibles CASTÚO-SYSTEM™", encoding="utf-8")

    result = crypto.encrypt_file(str(test_file), str(encrypted_file))
    assert result["status"] == "success"

    result2 = crypto.decrypt_file(str(encrypted_file), str(decrypted_file))
    assert result2["status"] == "success"
    assert decrypted_file.read_text(encoding="utf-8") == "Datos sensibles CASTÚO-SYSTEM™"


def test_blake3_hash(crypto):
    data = "Datos para hashing CASTÚO-SYSTEM™"
    h1 = crypto.blake3_hash(data)
    h2 = crypto.blake3_hash(data)
    assert h1 == h2
    assert len(h1) >= 64
