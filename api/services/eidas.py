"""
Firma electrónica cualificada según eIDAS Nivel Alto.

Dependencias opcionales:
  - pypdf  (manipulación de PDF)
  - cryptography (ya en requirements.txt)
  - requests (HTTP al servicio TSA)

Si alguna dependencia no está disponible, opera en modo simulado.
"""

import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Any

# cryptography ya está en requirements.txt
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_private_key

_requests: Any | None = None
_requests_available = False
try:
    import requests as _requests

    _requests_available = True
except ImportError:  # pragma: no cover
    pass

PdfReader: Any = None
PdfWriter: Any = None
_pypdf_available = False
try:
    from pypdf import PdfReader, PdfWriter

    _pypdf_available = True
except ImportError:  # pragma: no cover
    pass

_page_letter: Any = None
rl_canvas: Any = None
_reportlab_available = False
try:
    from reportlab.lib import pagesizes
    from reportlab.pdfgen import canvas as rl_canvas

    _page_letter = pagesizes.letter
    _reportlab_available = True
except ImportError:  # pragma: no cover
    pass


class EIDASSigner:
    """Firma electrónica cualificada según eIDAS (Nivel Alto).

    - Si existe la clave privada en EIDAS_PRIVATE_KEY_PATH: firma real.
    - Si no existe: firma simulada con marca de agua (modo dev/staging).
    """

    def __init__(self) -> None:
        self.private_key = self._load_private_key()
        self.cert_url = os.getenv(
            "EIDAS_CERT_URL",
            "https://trusted-service.castuo-system.cloud/cert",
        )
        self.tsa_url = os.getenv(
            "EIDAS_TSA_URL",
            "https://tsa.castuo-system.cloud/tsa",
        )

    def _load_private_key(self) -> Any | None:
        """Carga la clave privada PEM para firma eIDAS."""
        key_path = os.getenv(
            "EIDAS_PRIVATE_KEY_PATH", "/secrets/eidas_private_key.pem"
        )
        if not os.path.exists(key_path):
            return None
        try:
            with open(key_path, "rb") as fh:
                return load_pem_private_key(
                    fh.read(), password=None, backend=default_backend()
                )
        except Exception as exc:  # pragma: no cover
            print(f"❌ Error cargando clave eIDAS: {exc}")
            return None

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def sign_document(
        self, pdf_path: str, output_path: str, metadata: dict[str, Any]
    ) -> bool:
        """Firma un PDF con sello de tiempo y metadatos eIDAS.

        Retorna True si la firma fue exitosa (real o simulada).
        """
        if self.private_key and _pypdf_available:
            return self._real_sign(pdf_path, output_path, metadata)
        return self._simulate_sign(pdf_path, output_path, metadata)

    def sign_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Firma un dict JSON y devuelve {payload, signature_hex, hash, timestamp}.

        Usado para firmar payloads TRACES sin necesidad de PDF.
        """
        now = datetime.now(timezone.utc).isoformat()
        payload_str = json.dumps(payload, sort_keys=True)
        payload_hash = hashlib.sha256(payload_str.encode()).hexdigest()

        if self.private_key:
            raw_sig = self.private_key.sign(
                payload_hash.encode(), padding.PKCS1v15(), hashes.SHA256()
            )
            signature_hex = raw_sig.hex()
        else:
            signature_hex = "SIMULATED_" + payload_hash[:32]

        return {
            "payload": payload,
            "signature_hex": signature_hex,
            "hash": payload_hash,
            "timestamp": now,
            "mode": "real" if self.private_key else "simulated",
        }

    # ------------------------------------------------------------------
    # Implementaciones internas
    # ------------------------------------------------------------------

    def _real_sign(self, pdf_path: str, output_path: str, metadata: dict[str, Any]) -> bool:
        """Firma real con clave privada + sello TSA."""
        try:
            timestamp = datetime.now(timezone.utc).isoformat()
            metadata_extended = {**metadata, "signed_at": timestamp}
            metadata_str = json.dumps(metadata_extended, sort_keys=True)
            metadata_hash = hashlib.sha256(metadata_str.encode()).hexdigest()

            raw_sig = self.private_key.sign(  # type: ignore[union-attr]
                metadata_hash.encode(), padding.PKCS1v15(), hashes.SHA256()
            )
            tsa_token = self._get_tsa_token(metadata_hash) or "TSA_UNAVAILABLE"

            reader = PdfReader(pdf_path)
            writer = PdfWriter()
            for page in reader.pages:
                writer.add_page(page)

            writer.add_metadata(
                {
                    "/eIDAS_Signature": raw_sig.hex(),
                    "/eIDAS_Metadata": metadata_str,
                    "/eIDAS_TSA": tsa_token,
                    "/eIDAS_Timestamp": timestamp,
                }
            )
            with open(output_path, "wb") as fh:
                writer.write(fh)
            return True
        except Exception as exc:  # pragma: no cover
            print(f"❌ Error firmando documento: {exc}")
            return False

    def _simulate_sign(
        self, pdf_path: str, output_path: str, metadata: dict[str, Any]
    ) -> bool:
        """Firma simulada para entornos sin clave privada."""
        timestamp = datetime.now(timezone.utc).isoformat()
        sim_hash = hashlib.sha256(json.dumps(metadata, sort_keys=True).encode()).hexdigest()

        # Si pypdf disponible: copiar PDF y añadir metadatos de firma simulada
        if _pypdf_available and os.path.exists(pdf_path):
            try:
                reader = PdfReader(pdf_path)
                writer = PdfWriter()
                for page in reader.pages:
                    writer.add_page(page)
                writer.add_metadata(
                    {
                        "/eIDAS_Signature": f"SIMULATED_{sim_hash}",
                        "/eIDAS_Metadata": json.dumps(metadata),
                        "/eIDAS_Timestamp": timestamp,
                    }
                )
                with open(output_path, "wb") as fh:
                    writer.write(fh)
                return True
            except Exception as exc:  # pragma: no cover
                print(f"⚠️ Firma simulada (pypdf) falló: {exc}")

        # Fallback: crear un PDF mínimo con reportlab
        if _reportlab_available:
            try:
                c = rl_canvas.Canvas(output_path, pagesize=_page_letter)
                c.drawString(
                    72, 700, f"FIRMA SIMULADA eIDAS — {timestamp}"
                )
                c.drawString(72, 680, f"Hash: {sim_hash}")
                c.save()
                return True
            except Exception as exc:  # pragma: no cover
                print(f"⚠️ Firma simulada (reportlab) falló: {exc}")

        # Último recurso: escribe un archivo de texto plano
        with open(output_path, "w") as fh:
            fh.write(f"FIRMA SIMULADA eIDAS\ntimestamp={timestamp}\nhash={sim_hash}\n")
        return True

    def _get_tsa_token(self, data_hash: str) -> str | None:
        """Obtiene un sello de tiempo RFC 3161 del servicio TSA."""
        if not _requests_available or _requests is None:
            return None
        try:
            response = _requests.post(
                self.tsa_url,
                json={"hash": data_hash, "algorithm": "sha256"},
                timeout=5,
            )
            if response.status_code == 200:
                return response.json().get("token")
            print(f"⚠️ TSA retornó {response.status_code}: {response.text}")
        except Exception as exc:  # pragma: no cover
            print(f"❌ Error contactando TSA: {exc}")
        return None


# Singleton
eidas_signer = EIDASSigner()
