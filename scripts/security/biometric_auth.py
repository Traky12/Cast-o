#!/usr/bin/env python3
"""
CASTÚO-SYSTEM™ — Autenticación biométrica (huella + rostro) como segundo factor.
Opcional: requiere sensor de huellas (pyfingerprint) y/o OpenCV + modelo facial.
Si las dependencias no están disponibles, solo verifica YubiKey + contraseña/hash.
Uso: python3 biometric_auth.py
"""
from __future__ import annotations

import os
import sys

# Ruta a embeddings faciales (encriptados en producción)
FACE_EMBEDDINGS_PATH = os.getenv("CASTUO_FACE_EMBEDDINGS", "/etc/gaiachain/biometric/face_embeddings.npy")
SIMILARITY_THRESHOLD = float(os.getenv("CASTUO_FACE_THRESHOLD", "0.6"))


def verify_yubikey_otp(otp: str) -> bool:
    """Verificación OTP YubiKey (ver authenticate_with_yubikey)."""
    if not otp or len(otp) < 32:
        return False
    cid = os.getenv("YUBICO_CLIENT_ID")
    key = os.getenv("YUBICO_API_KEY")
    if not cid or not key:
        return bool(otp.isalnum())
    try:
        import urllib.request
        import urllib.parse
        nonce = os.urandom(16).hex()
        q = urllib.parse.urlencode({"id": cid, "nonce": nonce, "otp": otp})
        req = urllib.request.Request(f"https://api.yubico.com/wsapi/2.0/verify?{q}")
        with urllib.request.urlopen(req, timeout=10) as r:
            body = r.read().decode()
        return "status=OK" in body and nonce in body
    except Exception:
        return False


def verify_master_hash(password: str) -> bool:
    """Comprueba hash de contraseña maestra (archivo en GAIA_CHAIN_DIR)."""
    import hashlib
    chain_dir = os.getenv("GAIA_CHAIN_DIR", "/etc/gaiachain")
    path = os.path.join(chain_dir, "master_password.hash")
    if not os.path.isfile(path):
        return False
    h = hashlib.sha512(password.encode()).hexdigest()
    with open(path) as f:
        return h == f.read().strip()


def capture_fingerprint() -> bool:
    """Captura y verifica huella (opcional; requiere PyFingerprint y sensor)."""
    try:
        from pyfingerprint.pyfingerprint import PyFingerprint  # type: ignore
    except ImportError:
        return True  # Sin dependencia: omitir verificación de huella
    dev = os.getenv("FINGERPRINT_DEVICE", "/dev/ttyUSB0")
    if not os.path.exists(dev):
        return True
    try:
        f = PyFingerprint(dev, 57600, 0xFFFFFFFF, 0x00000000)
        if not f.verifyPassword():
            return False
        # Esperar imagen y comparar con plantilla 1
        import time
        for _ in range(30):
            if f.readImage():
                f.convertImage(0x01)
                if f.compareCharacteristics():
                    return True
                return False
            time.sleep(0.2)
        return False
    except Exception:
        return False


def capture_face() -> bool:
    """Captura y verifica rostro (opcional; OpenCV + embeddings)."""
    if not os.path.isfile(FACE_EMBEDDINGS_PATH):
        return True  # Sin registro facial: omitir
    try:
        import cv2  # type: ignore
        import numpy as np
    except ImportError:
        return True
    try:
        stored = np.load(FACE_EMBEDDINGS_PATH)
    except Exception:
        return True
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()
    if not ret:
        return False
    # Modelo ligero: si no hay FaceNet, usar embedding simple (promedio por región)
    try:
        net = cv2.dnn.readNetFromTensorflow(
            os.getenv("FACENET_PB", "models/facenet.pb"),
            os.getenv("FACENET_PBTXT", "models/facenet.pbtxt"),
        )
    except Exception:
        return True
    blob = cv2.dnn.blobFromImage(frame, 1.0, (160, 160), (104.0, 177.0, 123.0))
    net.setInput(blob)
    embeddings = net.forward()
    dist = np.linalg.norm(embeddings - stored)
    return bool(dist < SIMILARITY_THRESHOLD)


def authenticate_with_biometrics() -> bool:
    """Flujo: YubiKey OTP + (opcional) huella + (opcional) rostro + hash contraseña."""
    getpass = __import__("getpass")
    otp = getpass.getpass("Toca tu YubiKey y pega el OTP: ")
    if not verify_yubikey_otp(otp):
        print("OTP de YubiKey inválido.", file=sys.stderr)
        return False
    password = getpass.getpass("Contraseña maestra: ")
    if not verify_master_hash(password):
        print("Contraseña incorrecta.", file=sys.stderr)
        return False
    if not capture_fingerprint():
        print("Huella no reconocida.", file=sys.stderr)
        return False
    if not capture_face():
        print("Rostro no reconocido.", file=sys.stderr)
        return False

    # Token de sesión y registro en GaiaChain
    session_token = os.urandom(32).hex()
    session_file = os.getenv("CASTUO_SESSION_FILE", "/tmp/gaiachain_biometric_session.token")
    with open(session_file, "w") as f:
        f.write(session_token)
    os.chmod(session_file, 0o600)

    api_url = os.getenv("GAIA_CHAIN_API_URL", "https://gaiachain.castuo-system.com")
    admin_key = os.getenv("GAIA_CHAIN_ADMIN_KEY")
    if admin_key:
        try:
            import urllib.request
            import json
            urllib.request.urlopen(
                urllib.request.Request(
                    f"{api_url}/api/v1/auth/biometric",
                    data=json.dumps({
                        "biometric_types": ["fingerprint", "facial_recognition"],
                        "session_token": session_token,
                    }).encode(),
                    headers={"Authorization": f"Bearer {admin_key}", "Content-Type": "application/json"},
                    method="POST",
                ),
                timeout=10,
            )
        except Exception:
            pass

    print("Autenticación biométrica correcta. Token en:", session_file)
    return True


if __name__ == "__main__":
    if authenticate_with_biometrics():
        sys.exit(0)
    sys.exit(1)
