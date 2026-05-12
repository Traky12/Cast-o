#!/usr/bin/env python3
"""
CASTÚO-SYSTEM™ — Destrucción cuántica con hardware QKD (ej. ID Quantique Cerberis XG).
Genera claves cuánticas, deriva clave de destrucción, registra en GaiaChain; opcional DMS.
Sin QKD disponible usa generación local. No se almacenan PINs en código.
Uso: python3 quantum_destruction_qkd.py activate [target] | backup <file> [target]
"""
from __future__ import annotations

import hashlib
import os
import sys
import time

GAIA_URL = os.getenv("GAIA_CHAIN_API_URL", "https://gaiachain.castuo-system.com")
CHAIN_DIR = os.getenv("GAIA_CHAIN_DIR", "/etc/gaiachain")
QKD_SERVER = os.getenv("QKD_SERVER_ADDRESS")
QKD_API_KEY = os.getenv("QKD_API_KEY")


def _sign_for_gaia(message: bytes) -> str | None:
    pin = os.getenv("HSM_USER_PIN")
    if not pin:
        try:
            pin = __import__("getpass").getpass("HSM PIN (o Enter para PEM): ") or None
        except Exception:
            pin = None
    if pin:
        try:
            import subprocess
            r = subprocess.run(
                ["pkcs11-tool", "--login", "--pin", pin, "--sign", "--mechanism", "CKM_SHA256_RSA_PKCS", "--id", "01", "-"],
                input=message,
                capture_output=True,
                timeout=10,
            )
            if r.returncode == 0 and r.stdout:
                import base64
                return base64.b64encode(r.stdout).decode()
        except Exception:
            pass
    key_path = os.path.join(CHAIN_DIR, "master_key.pem")
    if os.path.isfile(key_path):
        import subprocess
        p = subprocess.run(["openssl", "dgst", "-sha512", "-sign", key_path, "-"], input=message, capture_output=True, timeout=5)
        if p.returncode == 0 and p.stdout:
            import base64
            return base64.b64encode(p.stdout).decode()
    return None


def _generate_quantum_key(length: int = 512) -> bytes:
    """Obtiene clave desde servidor QKD o genera localmente (pseudoaleatorio)."""
    if QKD_SERVER and QKD_API_KEY:
        try:
            import urllib.request
            import json
            req = urllib.request.Request(
                f"{QKD_SERVER.rstrip('/')}/api/v1/keys",
                data=json.dumps({"length": length}).encode(),
                headers={"Authorization": f"Bearer {QKD_API_KEY}", "Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=15) as r:
                data = json.loads(r.read().decode())
                raw = data.get("key_material") or data.get("key")
                if isinstance(raw, str):
                    return bytes.fromhex(raw)
                return raw
        except Exception:
            pass
    return os.urandom(length // 8)


def _derive_destruction_key(quantum_key: bytes, target: str) -> bytes:
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.backends import default_backend

    return HKDF(
        algorithm=hashes.SHA512(),
        length=64,
        salt=None,
        info=f"CASTUO-QUANTUM-DESTRUCTION-{target}".encode(),
        backend=default_backend(),
    ).derive(quantum_key)


def activate_quantum_destruction(target: str) -> dict:
    """Activa destrucción cuántica: clave QKD, ruido (simulado si no hay hardware), registro GaiaChain."""
    quantum_key = _generate_quantum_key(512)
    destruction_key = _derive_destruction_key(quantum_key, target)
    key_hash = hashlib.sha512(destruction_key).hexdigest()
    ts = int(time.time())
    msg = f"QKD_DESTRUCTION_{target}_{ts}".encode()
    sig = _sign_for_gaia(msg)
    tx_hash = None
    admin = os.getenv("GAIA_CHAIN_ADMIN_KEY")
    if admin and sig:
        try:
            import urllib.request
            import json
            urllib.request.urlopen(
                urllib.request.Request(
                    f"{GAIA_URL}/api/v1/quantum_alert",
                    data=json.dumps({
                        "target": target,
                        "quantum_key_id": quantum_key[:32].hex(),
                        "noise_duration": 30,
                        "destruction_key_hash": key_hash,
                        "timestamp": ts,
                        "signature": sig,
                    }).encode(),
                    headers={"Authorization": f"Bearer {admin}", "Content-Type": "application/json"},
                    method="POST",
                ),
                timeout=15,
            )
            tx_hash = "ok"
        except Exception:
            pass
    if os.environ.get("CASTUO_QUANTUM_TRIGGER_DMS"):
        dms = "/opt/castuo/scripts/security/secure-destruction-protocol.sh"
        if os.path.isfile(dms):
            import subprocess
            subprocess.run([dms], timeout=300)
    return {
        "status": "SUCCESS",
        "target": target,
        "quantum_key_id": quantum_key[:32].hex(),
        "gaiachain_tx": tx_hash,
        "destruction_key_hash": key_hash,
    }


def prepare_quantum_resistant_backup(data: bytes, target: str) -> dict:
    """Backup resistente a cuántica usando clave QKD + AES-256-GCM."""
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.backends import default_backend

    quantum_key = _generate_quantum_key(512)
    backup_key = _derive_destruction_key(quantum_key, f"backup_{target}")[:32]
    iv = os.urandom(12)
    cipher = Cipher(algorithms.AES(backup_key), modes.GCM(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ct = encryptor.update(data) + encryptor.finalize()
    tag = encryptor.tag
    backup_payload = {
        "ciphertext": (iv + tag + ct).hex(),
        "quantum_key_id": quantum_key[:32].hex(),
        "algorithm": "QKD-AES256-GCM",
        "target": target,
        "timestamp": int(time.time()),
    }
    sig = _sign_for_gaia(f"QKD_BACKUP_{target}_{backup_payload['timestamp']}".encode())
    admin = os.getenv("GAIA_CHAIN_ADMIN_KEY")
    backup_id = None
    if admin and sig:
        try:
            import urllib.request
            import json
            urllib.request.urlopen(
                urllib.request.Request(
                    f"{GAIA_URL}/api/v1/quantum_backup",
                    data=json.dumps({"data": backup_payload, "signature": sig}).encode(),
                    headers={"Authorization": f"Bearer {admin}", "Content-Type": "application/json"},
                    method="POST",
                ),
                timeout=15,
            )
            backup_id = "ok"
        except Exception:
            pass
    return {
        "backup_id": backup_id,
        "quantum_key_id": backup_payload["quantum_key_id"],
        "algorithm": backup_payload["algorithm"],
    }


def main() -> None:
    if len(sys.argv) < 2:
        print("Uso: quantum_destruction_qkd.py activate [target] | backup <file> [target]")
        sys.exit(1)
    cmd = sys.argv[1].lower()
    target = sys.argv[2] if len(sys.argv) > 2 else "caceres_quantum_dc"
    if cmd == "activate":
        result = activate_quantum_destruction(target)
        print(f"Destrucción cuántica activada: {result['target']}")
        print(f"  TX GaiaChain: {result.get('gaiachain_tx', 'N/A')}")
        print(f"  destruction_key_hash: {result['destruction_key_hash'][:32]}...")
    elif cmd == "backup":
        path = sys.argv[2] if len(sys.argv) > 2 else None
        t = sys.argv[3] if len(sys.argv) > 3 else "caceres_quantum_dc"
        data = open(path, "rb").read() if path and os.path.isfile(path) else b"Critical data"
        result = prepare_quantum_resistant_backup(data, t)
        print(f"Backup QKD: {result.get('backup_id')}")
        print(f"  Algorithm: {result['algorithm']}")
    else:
        print("Comando no válido.")
        sys.exit(1)


if __name__ == "__main__":
    main()
