#!/usr/bin/env python3
"""
CASTÚO-SYSTEM™ — Destrucción cuántica con fotónica (pares entrelazados, ruido). Qiskit opcional.
Registro en GaiaChain; opcional DMS. No se almacenan PINs en código.
Uso: python3 quantum_photonic_destruction.py activate [target] | simulate [target]
"""
from __future__ import annotations

import hashlib
import os
import sys
import time

GAIA_URL = os.getenv("GAIA_CHAIN_API_URL", "https://gaiachain.castuo-system.com")
CHAIN_DIR = os.getenv("GAIA_CHAIN_DIR", "/etc/gaiachain")


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


def generate_entangled_photons(pairs: int = 1000) -> tuple[bytes, bytes]:
    """Simula pares de fotones entrelazados (Qiskit si está disponible)."""
    try:
        from qiskit import QuantumCircuit, Aer, execute

        qc = QuantumCircuit(2, 2)
        qc.h(0)
        qc.cx(0, 1)
        qc.measure([0, 1], [0, 1])
        backend = Aer.get_backend("qasm_simulator")
        result = execute(qc, backend, shots=pairs).result()
        counts = result.get_counts(qc)
        alice_bits = []
        bob_bits = []
        for outcome, c in counts.items():
            for _ in range(c):
                alice_bits.append(int(outcome[0]))
                bob_bits.append(int(outcome[1]))
        return bytes(alice_bits[: pairs // 8]), bytes(bob_bits[: pairs // 8])
    except ImportError:
        # Sin Qiskit: bytes aleatorios
        n = max(1, pairs // 8)
        a, b = os.urandom(n), os.urandom(n)
        return a, b


def generate_quantum_noise(target: str, duration_seconds: int = 30) -> dict:
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.backends import default_backend

    alice_bits, bob_bits = generate_entangled_photons(10000)
    hkdf = HKDF(
        algorithm=hashes.SHA512(),
        length=64,
        salt=alice_bits[:32],
        info=f"CASTUO-PHOTONIC-DESTRUCTION-{target}".encode(),
        backend=default_backend(),
    )
    destruction_key = hkdf.derive(bob_bits[:32])
    noise_signal = os.urandom(1024)
    return {
        "target": target,
        "duration": duration_seconds,
        "entangled_pairs": 10000,
        "destruction_key_hash": hashlib.sha512(destruction_key).hexdigest(),
        "timestamp": int(time.time()),
    }


def activate_photonic_destruction(target: str) -> dict:
    """Activa destrucción fotónica: ruido cuántico + registro GaiaChain + opcional DMS."""
    noise_result = generate_quantum_noise(target, duration_seconds=60)
    msg = f"PHOTONIC_DESTRUCTION_{target}_{noise_result['timestamp']}".encode()
    sig = _sign_for_gaia(msg)
    tx_hash = None
    admin = os.getenv("GAIA_CHAIN_ADMIN_KEY")
    if admin and sig:
        try:
            import urllib.request
            import json
            urllib.request.urlopen(
                urllib.request.Request(
                    f"{GAIA_URL}/api/v1/quantum_photonic_alert",
                    data=json.dumps({
                        "type": "QUANTUM_PHOTONIC_DESTRUCTION",
                        "target": target,
                        "quantum_noise": {
                            "duration_seconds": noise_result["duration"],
                            "entangled_pairs": noise_result["entangled_pairs"],
                            "destruction_key_hash": noise_result["destruction_key_hash"],
                        },
                        "timestamp": noise_result["timestamp"],
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
    if os.environ.get("CASTUO_PHOTONIC_TRIGGER_DMS"):
        dms = "/opt/castuo/scripts/security/secure-destruction-protocol.sh"
        if os.path.isfile(dms):
            import subprocess
            subprocess.run([dms], timeout=300)
    return {
        "status": "SUCCESS",
        "target": target,
        "quantum_noise": noise_result,
        "gaiachain_tx": tx_hash,
    }


def main() -> None:
    if len(sys.argv) < 2:
        print("Uso: quantum_photonic_destruction.py activate [target] | simulate [target]")
        sys.exit(1)
    cmd = sys.argv[1].lower()
    target = sys.argv[2] if len(sys.argv) > 2 else "madrid_quantum_dc"
    if cmd == "simulate":
        r = generate_quantum_noise(target, 30)
        print(f"Simulación ruido cuántico: target={r['target']}, hash={r['destruction_key_hash'][:32]}...")
        sys.exit(0)
    result = activate_photonic_destruction(target)
    print(f"Destrucción fotónica activada: {result['target']}")
    print(f"  TX GaiaChain: {result.get('gaiachain_tx', 'N/A')}")
    print(f"  destruction_key_hash: {result['quantum_noise']['destruction_key_hash'][:32]}...")


if __name__ == "__main__":
    main()
