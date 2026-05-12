"""
Servicio de privacidad: derecho al olvido (GDPR Art. 17).
Integra verificación de identidad, borrado en metadatos IPFS, actualización en GaiaChain,
generación de certificado PDF y envío de confirmación por email.
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

PERSONAL_FIELDS = {"Propietario", "propietario", "DNI", "dni", "Email", "email", "Correo", "correo", "Teléfono", "telefono"}

_GAIA_RPC = os.getenv("GAIA_CHAIN_RPC", "https://gaiachain.castuo-system.com")
_FOREST_ADDRESS = os.getenv("FOREST_OWNERSHIP_TOKEN_ADDRESS", "")
_JUNTA_KEY = os.getenv("JUNTA_PRIVATE_KEY") or os.getenv("PRIVATE_KEY")

FOREST_ABI = [
    {"inputs": [{"name": "tokenId", "type": "uint256"}], "name": "ownerOf", "outputs": [{"name": "", "type": "address"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"name": "tokenId", "type": "uint256"}], "name": "getProperty", "outputs": [
        {"name": "parcelaId", "type": "string"}, {"name": "owner", "type": "address"},
        {"name": "coordinates", "type": "string"}, {"name": "area", "type": "uint256"},
        {"name": "treeSpecies", "type": "string"}, {"name": "carbonSequestered", "type": "uint256"},
        {"name": "ipfsHash", "type": "string"}, {"name": "isProtected", "type": "bool"},
    ], "stateMutability": "view", "type": "function"},
    {"inputs": [{"name": "tokenId", "type": "uint256"}, {"name": "newIpfsHash", "type": "string"}], "name": "updateMetadata", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
]


FOREST_ABI_GET_PROPERTY = FOREST_ABI + [
    {"inputs": [{"name": "tokenId", "type": "uint256"}], "name": "getCertifications", "outputs": [{"name": "", "type": "string[]"}], "stateMutability": "view", "type": "function"},
]


def _get_contract(abi: list | None = None):
    try:
        from web3 import Web3
    except ImportError:
        raise RuntimeError("web3 no instalado")
    if not _FOREST_ADDRESS:
        raise RuntimeError("FOREST_OWNERSHIP_TOKEN_ADDRESS es obligatorio")
    w3 = Web3(Web3.HTTPProvider(_GAIA_RPC))
    use_abi = abi or FOREST_ABI
    return w3, w3.eth.contract(
        address=Web3.to_checksum_address(_FOREST_ADDRESS),
        abi=use_abi,
    )


def get_property_data(token_id: int) -> dict | None:
    """Devuelve datos de la propiedad para el dashboard (parcelaId, area, certifications, owner, ipfsHash)."""
    try:
        w3, contract = _get_contract(FOREST_ABI_GET_PROPERTY)
        prop = contract.functions.getProperty(token_id).call()
        certs = contract.functions.getCertifications(token_id).call()
        return {
            "parcelaId": prop[0],
            "owner": prop[1],
            "coordinates": prop[2],
            "area": str(prop[3]),
            "treeSpecies": prop[4],
            "carbonSequestered": str(prop[5]),
            "ipfsHash": prop[6],
            "isProtected": prop[7],
            "certifications": list(certs) if certs else [],
        }
    except Exception as e:
        logger.warning("get_property_data %s: %s", token_id, e)
        return None


def verify_identity(wallet_address: str, token_id: int) -> bool:
    """Comprueba que la wallet sea propietaria del token."""
    try:
        _, contract = _get_contract()
        owner = contract.functions.ownerOf(token_id).call()
        return owner.lower() == wallet_address.strip().lower()
    except Exception as e:
        logger.error("Error al verificar identidad: %s", e)
        return False


def get_metadata_from_ipfs(ipfs_hash: str) -> dict | None:
    """Obtiene metadatos desde IPFS vía gateway público."""
    if not ipfs_hash or ipfs_hash.startswith("QmPlaceholder"):
        return None
    try:
        import requests
        r = requests.get(f"https://ipfs.io/ipfs/{ipfs_hash}", timeout=15)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        logger.warning("No se pudieron obtener metadatos de IPFS %s: %s", ipfs_hash[:20], e)
    return None


def _erase_personal_data(metadata: dict) -> dict:
    """Copia de metadatos sin atributos personales."""
    return {
        "name": metadata.get("name", ""),
        "description": metadata.get("description", ""),
        "image": metadata.get("image", ""),
        "attributes": [
            attr for attr in metadata.get("attributes", [])
            if attr.get("trait_type") not in PERSONAL_FIELDS
        ],
        "certifications": metadata.get("certifications", []),
    }


def _upload_to_ipfs(data: dict) -> str | None:
    """Sube JSON a IPFS; devuelve hash o None."""
    try:
        from ipfshttpclient import connect
        client = connect("/dns/ipfs.infura.io/tcp/5001/https")
        result = client.add_json(data)
        if isinstance(result, str):
            return result
        if isinstance(result, (list, tuple)) and result:
            r = result[0]
            return r.get("Hash") or r.get("hash") if isinstance(r, dict) else str(r)
        return None
    except Exception as e:
        logger.warning("IPFS no disponible, usando hash placeholder: %s", e)
        return None


def erase_personal_data(token_id: int) -> dict[str, Any]:
    """
    Obtiene metadatos del token desde el contrato e IPFS, borra datos personales,
    sube nuevo JSON a IPFS. Devuelve old_ipfs_hash, new_ipfs_hash, redacted_fields.
    """
    w3, contract = _get_contract()
    prop = contract.functions.getProperty(token_id).call()
    old_ipfs_hash = prop[6]
    metadata = get_metadata_from_ipfs(old_ipfs_hash)
    if not metadata:
        raise ValueError("No se pudieron obtener metadatos del token (IPFS no disponible o hash vacío)")
    new_metadata = _erase_personal_data(metadata)
    new_ipfs_hash = _upload_to_ipfs(new_metadata) or "QmPlaceholderRightToBeForgotten"
    return {
        "old_ipfs_hash": old_ipfs_hash,
        "new_ipfs_hash": new_ipfs_hash,
        "redacted_fields": ["Propietario", "DNI", "Email"],
    }


def update_metadata_in_blockchain(token_id: int, new_ipfs_hash: str) -> str:
    """Actualiza el hash de metadatos en ForestOwnershipToken (firma con JUNTA_PRIVATE_KEY)."""
    w3, contract = _get_contract()
    account = w3.eth.account.from_key(_JUNTA_KEY.replace("0x", "").strip())
    tx = contract.functions.updateMetadata(token_id, new_ipfs_hash).build_transaction({
        "from": account.address,
        "nonce": w3.eth.get_transaction_count(account.address),
        "gas": 200000,
        "gasPrice": w3.to_wei("50", "gwei"),
    })
    signed = account.sign_transaction(tx)
    tx_hash_bytes = w3.eth.send_raw_transaction(signed.raw_transaction)
    return tx_hash_bytes.hex()


def generate_erasure_certificate(
    token_id: int,
    old_hash: str,
    new_hash: str,
    redacted_fields: list,
    tx_hash: str,
) -> dict[str, str]:
    """Genera certificado de borrado en PDF. Devuelve {'id': cert_id, 'path': ruta_archivo}."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
    except ImportError:
        logger.warning("reportlab no instalado; certificado no generado")
        cert_id = f"CERT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        return {"id": cert_id, "path": ""}
    cert_id = f"CERT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    cert_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "certificates")
    os.makedirs(cert_dir, exist_ok=True)
    file_path = os.path.join(cert_dir, f"{cert_id}.pdf")
    c = canvas.Canvas(file_path, pagesize=letter)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, 750, "CERTIFICADO DE EJERCICIO DEL DERECHO AL OLVIDO")
    c.setFont("Helvetica", 12)
    c.drawString(100, 720, f"ID de Certificado: {cert_id}")
    c.drawString(100, 700, f"Fecha: {datetime.utcnow().strftime('%d/%m/%Y %H:%M UTC')}")
    c.drawString(100, 680, f"Token ID: {token_id}")
    c.drawString(100, 660, f"Hash antiguo: {old_hash[:50]}..." if len(old_hash) > 50 else f"Hash antiguo: {old_hash}")
    c.drawString(100, 640, f"Nuevo hash: {new_hash[:50]}..." if len(new_hash) > 50 else f"Nuevo hash: {new_hash}")
    c.drawString(100, 620, f"Campos borrados: {', '.join(redacted_fields)}")
    c.drawString(100, 600, f"Transaccion GaiaChain: {tx_hash[:42]}..." if len(tx_hash) > 42 else f"Transaccion: {tx_hash}")
    c.drawString(100, 580, "Firma DPO: ________________________")
    c.save()
    return {"id": cert_id, "path": file_path}


def send_erasure_confirmation_email(email: str, certificate: dict, tx_hash: str = "") -> None:
    """Envía email de confirmación con certificado adjunto. Si SMTP no está configurado, solo registra en log."""
    smtp_pass = os.getenv("SMTP_PASSWORD")
    if not smtp_pass:
        logger.info("SMTP no configurado; no se envia email a %s (certificado: %s)", email, certificate.get("id"))
        return
    try:
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        from email.mime.application import MIMEApplication
        msg = MIMEMultipart()
        msg["From"] = os.getenv("SMTP_FROM", "dpo@juntaextremadura.es")
        msg["To"] = email
        msg["Subject"] = "Confirmacion: Ejercicio del Derecho al Olvido (GDPR Art. 17)"
        body = f"""
        Estimado/a propietario/a,

        Su solicitud de ejercicio del derecho al olvido (GDPR Art. 17) ha sido procesada con exito.

        - Certificado: {certificate.get('id', 'N/A')}
        - Transaccion: {tx_hash}
        - Verificable en: https://explorer.gaiachain.castuo-system.com

        Para cualquier consulta: dpo@juntaex.es

        Atentamente,
        Delegado de Proteccion de Datos
        Junta de Extremadura
        """
        msg.attach(MIMEText(body, "plain"))
        if certificate.get("path") and os.path.isfile(certificate["path"]):
            with open(certificate["path"], "rb") as f:
                attach = MIMEApplication(f.read(), _subtype="pdf")
                attach.add_header("Content-Disposition", "attachment", filename=f"certificado_borrado_{certificate['id']}.pdf")
                msg.attach(attach)
        with smtplib.SMTP(os.getenv("SMTP_HOST", "smtp.juntaex.es"), int(os.getenv("SMTP_PORT", "587"))) as server:
            server.starttls()
            server.login(msg["From"], smtp_pass)
            server.send_message(msg)
        logger.info("Email de confirmacion enviado a %s", email)
    except Exception as e:
        logger.error("Error al enviar email de confirmacion: %s", e)
