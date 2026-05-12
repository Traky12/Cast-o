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
