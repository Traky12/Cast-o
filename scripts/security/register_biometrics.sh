#!/bin/bash
# CASTÚO-SYSTEM™ — Registro de biometría (huella + rostro) para MFA. Solo el administrador autorizado.
# Requiere: sensor de huellas (opcional), cámara y/o modelo FaceNet (opcional).
# Uso: sudo ./scripts/security/register_biometrics.sh

set -e
CHAIN_DIR="${GAIA_CHAIN_DIR:-/etc/gaiachain}"
BIO_DIR="$CHAIN_DIR/biometric"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mkdir -p "$BIO_DIR"
chmod 700 "$BIO_DIR"

# 1. Huella: si existe PyFingerprint y dispositivo
if command -v python3 >/dev/null 2>&1; then
  python3 -c "
import sys
try:
    from pyfingerprint.pyfingerprint import PyFingerprint
    f = PyFingerprint('/dev/ttyUSB0', 57600, 0xFFFFFFFF, 0x00000000)
    if f.verifyPassword():
        print('Coloca el dedo para registrar huella...')
        import time
        for _ in range(50):
            if f.readImage():
                f.convertImage(0x01)
                f.storeTemplate(1)
                print('Huella registrada en el sensor.')
                break
            time.sleep(0.2)
        else:
            print('Timeout. No se detectó huella.')
            sys.exit(1)
    else:
        sys.exit(1)
except ImportError:
    print('PyFingerprint no instalado. Omitiendo registro de huella.')
except Exception as e:
    print('Error en sensor de huellas:', e)
    sys.exit(1)
" 2>/dev/null || true
fi

# 2. Rostro: OpenCV + FaceNet (opcional)
if command -v python3 >/dev/null 2>&1; then
  python3 -c "
import os
import sys
try:
    import cv2
    import numpy as np
    path_pb = os.getenv('FACENET_PB', 'models/facenet.pb')
    path_pbtxt = os.getenv('FACENET_PBTXT', 'models/facenet.pbtxt')
    if os.path.isfile(path_pb) and os.path.isfile(path_pbtxt):
        net = cv2.dnn.readNetFromTensorflow(path_pb, path_pbtxt)
        cap = cv2.VideoCapture(0)
        ret, frame = cap.read()
        cap.release()
        if ret:
            blob = cv2.dnn.blobFromImage(frame, 1.0, (160, 160), (104.0, 177.0, 123.0))
            net.setInput(blob)
            emb = net.forward()
            out = '$BIO_DIR/face_embeddings.npy'
            np.save(out, emb)
            os.chmod(out, 0o600)
            print('Rostro registrado en', out)
    else:
        print('Modelo FaceNet no encontrado. Omitiendo registro facial.')
except ImportError:
    print('OpenCV no instalado. Omitiendo registro facial.')
except Exception as e:
    print('Error al registrar rostro:', e)
" 2>/dev/null || true
fi

# 3. Registrar en GaiaChain (firma con clave local; no almacenar contraseña en script)
if [ -n "$GAIA_CHAIN_ADMIN_KEY" ] && [ -f "$CHAIN_DIR/master_key.pem" ]; then
  SIG=$(echo -n "BIO_REGISTER_$(date +%s)" | openssl dgst -sha512 -sign "$CHAIN_DIR/master_key.pem" 2>/dev/null | base64 -w0) || true
  if [ -n "$SIG" ]; then
    curl -sf -X POST "${GAIA_CHAIN_API_URL:-https://gaiachain.castuo-system.com}/api/v1/biometric/register" \
      -H "Authorization: Bearer $GAIA_CHAIN_ADMIN_KEY" \
      -H "Content-Type: application/json" \
      -d "{\"biometric_types\":[\"fingerprint\",\"facial_recognition\"],\"hsm_signature\":\"$SIG\"}" >/dev/null || true
  fi
fi

echo "Registro de biometría completado."
echo "  Huella: en sensor local (si está disponible)."
echo "  Rostro: en $BIO_DIR/face_embeddings.npy (si OpenCV y FaceNet están disponibles)."
echo "  Solo el administrador autorizado puede registrar o acceder a estos datos."
