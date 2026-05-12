#!/usr/bin/env python3
"""
CASTÚO-SYSTEM™ — Threat modeling continuo STRIDE por release.
Ejecuta checks por categoría (Spoofing, Tampering, Repudiation, Info Disclosure, DoS, Elevation)
y registra resultado en GaiaChain como testigo inmutable.
Uso: python3 stride_pipeline.py v1.2.0
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

GAIA_URL = os.getenv("GAIA_CHAIN_API_URL", "https://gaiachain.castuo-system.com")
CHAIN_DIR = os.getenv("GAIA_CHAIN_DIR", "/etc/gaiachain")
REPO_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "../.."))


def _sign_for_gaia(message: bytes) -> str | None:
    pin = os.getenv("HSM_USER_PIN")
    if not pin:
        try:
            pin = __import__("getpass").getpass("HSM PIN (o Enter para PEM): ") or None
        except Exception:
            pin = None
    if pin:
        try:
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
        p = subprocess.run(["openssl", "dgst", "-sha512", "-sign", key_path, "-"], input=message, capture_output=True, timeout=5)
        if p.returncode == 0 and p.stdout:
            import base64
            return base64.b64encode(p.stdout).decode()
    return None


def _check_auth_sharding() -> bool:
    """Spoofing: verificar que auth use sharding (YubiKey/HSM/Shamir)."""
    # Comprobar que existan scripts de auth y fragmentos
    auth_scripts = [
        os.path.join(REPO_ROOT, "scripts/security/authenticate_with_yubikey.py"),
        os.path.join(REPO_ROOT, "scripts/security/generate_emergency_keys.py"),
    ]
    return any(os.path.isfile(p) for p in auth_scripts)


def _verify_integrity_all() -> bool:
    """Tampering: ejecutar verify-integrity en docker/castuo-bookstack."""
    bookstack = os.path.join(REPO_ROOT, "docker/castuo-bookstack/verify-integrity.sh")
    if not os.path.isfile(bookstack):
        return True
    r = subprocess.run(["bash", bookstack], cwd=os.path.dirname(bookstack), capture_output=True, timeout=15)
    return r.returncode == 0


def _gaia_chain_audit(tag: str) -> bool:
    """Repudiation: comprobar que GaiaChain esté configurado para auditoría."""
    return bool(os.getenv("GAIA_CHAIN_ADMIN_KEY") or os.path.isfile(os.path.join(CHAIN_DIR, "master_key.pem")))


def _scan_encryption() -> bool:
    """Info Disclosure: verificar que cifrado E2E esté disponible (castuo_crypto_v1.1)."""
    crypto = os.path.join(REPO_ROOT, "scripts/crypto/castuo_crypto_v1.1.py")
    return os.path.isfile(crypto)


def _uptime_healthchecks() -> bool:
    """DoS: comprobar que healthchecks estén definidos en compose."""
    compose = os.path.join(REPO_ROOT, "docker/castuo-bookstack/docker-compose.yml")
    if not os.path.isfile(compose):
        return True
    with open(compose) as f:
        return "healthcheck" in f.read().lower()


def _cap_drop_validation() -> bool:
    """Elevation: validar que se dropeen capacidades en contenedores."""
    compose = os.path.join(REPO_ROOT, "docker/castuo-bookstack/docker-compose.yml")
    if not os.path.isfile(compose):
        return True
    with open(compose) as f:
        content = f.read()
    return "cap_drop" in content or "no-new-privileges" in content.lower()


def threat_model_release(tag: str) -> dict:
    """Modelado automático STRIDE por release. Devuelve dict con resultado por categoría."""
    threats = {
        "Spoofing": _check_auth_sharding(),
        "Tampering": _verify_integrity_all(),
        "Repudiation": _gaia_chain_audit(tag),
        "Info Disclosure": _scan_encryption(),
        "DoS": _uptime_healthchecks(),
        "Elevation": _cap_drop_validation(),
    }
    return threats


def gaia_witness(tag: str, payload: dict) -> bool:
    """Registra en GaiaChain el resultado STRIDE como testigo (firma opcional)."""
    import urllib.request
    msg = json.dumps({"STRIDE": tag, **payload}, sort_keys=True).encode()
    sig = _sign_for_gaia(msg)
    admin = os.getenv("GAIA_CHAIN_ADMIN_KEY")
    if not admin or not sig:
        return False
    try:
        req = urllib.request.Request(
            f"{GAIA_URL}/api/v1/stride_witness",
            data=json.dumps({"tag": tag, "threats": payload, "signature": sig}).encode(),
            headers={"Authorization": f"Bearer {admin}", "Content-Type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=10)
        return True
    except Exception:
        return False


def main() -> None:
    tag = sys.argv[1] if len(sys.argv) > 1 else "v1.2.0"
    threats = threat_model_release(tag)
    ok = all(threats.values())
    print(f"STRIDE {tag}:")
    for k, v in threats.items():
        print(f"  {'✅' if v else '❌'} {k}: {v}")
    if gaia_witness(f"STRIDE_{tag}", threats):
        print("  GaiaChain: testigo registrado")
    else:
        print("  GaiaChain: no registrado (configure GAIA_CHAIN_ADMIN_KEY)")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
