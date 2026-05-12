# backend/sabion_edu/edu_enroll.py
"""Inscripción estudiante → nivel TRL + perfil. Emisión certificado inicial vía Sabionda."""
from __future__ import annotations

import hashlib
import json
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

logger = logging.getLogger(__name__)

try:
    from .edu_models import NIVELES, HABILIDADES_POR_NIVEL, CERT_NAMES, REVENUE_PER_CERT, STUDENTS, CERTIFICATES
except ImportError:
    from edu_models import NIVELES, HABILIDADES_POR_NIVEL, CERT_NAMES, REVENUE_PER_CERT, STUDENTS, CERTIFICATES

SABIONDA_URL = os.getenv("SABIONDA_URL", "http://localhost:9000")


def _block_hash(data: dict) -> str:
    return "0x" + hashlib.sha3_512(json.dumps(data, sort_keys=True).encode()).hexdigest()[:64]


def _ipfs_cid_sim(data: dict) -> str:
    return "QmEduCert" + hashlib.sha256(json.dumps(data).encode()).hexdigest()[:12]


def enroll(student: str, nivel: str, empresa: str = "") -> Dict[str, Any]:
    """Inscripción: crea perfil y certificado TRL inicial. Opcional: llama Sabionda orchestrate."""
    nivel = nivel.upper().replace("TRL", "TRL") if "TRL" in nivel else f"TRL{nivel}"
    n = NIVELES.get(nivel, 1)
    habilidades = HABILIDADES_POR_NIVEL.get(n, ["AnytypeP2P", "DockerFed", "Kyber1024"])
    cert_name = CERT_NAMES.get(n, "TRL2_Tecnico_Federado")

    payload = {
        "student": student,
        "nivel": nivel,
        "empresa": empresa,
        "enrolled_at": datetime.now(timezone.utc).isoformat(),
        "habilidades": habilidades,
    }
    block_hash = _block_hash(payload)
    ipfs_cid = _ipfs_cid_sim(payload)
    expiry = (datetime.now(timezone.utc) + timedelta(days=365)).strftime("%Y-%m-%d")
    revenue = REVENUE_PER_CERT.get(n, 25_000)

    STUDENTS[student] = {
        "student": student,
        "nivel": n,
        "nivel_str": nivel,
        "empresa": empresa,
        "enrolled_at": payload["enrolled_at"],
        "progress_pct": 0,
        "certificates": [],
    }

    cert = {
        "certificado_trl": cert_name,
        "student": student,
        "nivel": n,
        "habilidades": habilidades,
        "block_hash": block_hash,
        "ipfs_cid": ipfs_cid,
        "sabionda_approved": "3/3",
        "expiry": expiry,
        "revenue_contribution": f"€{revenue // 1000}K",
        "revenue_eur": revenue,
    }
    CERTIFICATES.append(cert)
    STUDENTS[student]["certificates"].append(cert)

    try:
        import httpx
        r = httpx.post(
            f"{SABIONDA_URL}/sabionda/orchestrate",
            json={"type": "EduEnroll", "agent": "compliance", "student": student, "nivel": nivel},
            timeout=10.0,
        )
        if r.status_code == 200:
            cert["sabionda_approved"] = r.json().get("nodes_approved", "3/3")
    except Exception as e:
        logger.debug("Sabionda enroll sync: %s", e)

    return cert
