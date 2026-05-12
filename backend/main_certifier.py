# -*- coding: utf-8 -*-
"""Flujo de certificación soberana: sensores, agentes, sellos eIDAS/AI Act/GDPR y certificado PDF+XML."""
from __future__ import annotations

import json
import logging
import os
import subprocess
from datetime import datetime, timezone
from typing import Any, Dict

from backend.agents_autonomous.cannabis_lab import CannabisLab
from backend.agents_autonomous.harvest_bot import HarvestBot
from backend.agents_autonomous.yield_master import analizar_yield
from backend.legal.ai_act_compliance import AIActCompliance
from backend.legal.certificate_generator import SovereignCertificateGenerator
from backend.legal.gdpr_compliance import GDPRCompliance
from backend.legal.gaiachain_seal import GaiaChainSeal
from backend.database.local_db import local_db

logger = logging.getLogger(__name__)

_GAIACHAIN_CLI = os.getenv("GAIACHAIN_CLI", os.getenv("GAIA_CHAIN_CLI", "/usr/local/bin/gaiachain"))


class MainCertifier:
    """Orquesta recolección de datos, sellos legales y generación del certificado soberano."""

    def __init__(self) -> None:
        self.harvest_bot = HarvestBot()
        self.cannabis_lab = CannabisLab()
        self.certificate_generator = SovereignCertificateGenerator()
        self.gaiachain_seal = GaiaChainSeal()
        self.ai_act = AIActCompliance()
        self.gdpr = GDPRCompliance()

    def ejecutar_certificacion_real(self, lote_id: str, cultivo: str = "cannabis_medicinal") -> Dict[str, Any]:
        """
        Ejecuta el flujo completo de certificación soberana para un lote.
        Returns:
            Dict con certificate_path, certificate_hash, gaiachain_tx, verification_url, etc.
        """
        logger.info("Iniciando certificacion soberana para lote: %s", lote_id)

        data_cosecha = self.harvest_bot.get_harvest_data(lote_id, cultivo)
        data_yield = analizar_yield({
            "lote_id": lote_id,
            "metric": "yield",
            "current_value": data_cosecha.get("yield_actual", 98.5),
        })
        data_lab = self.cannabis_lab.analyze_cannabinoids(lote_id, f"MUE-{lote_id[-3:] if len(lote_id) >= 3 else '001'}")

        eidas_seal = self.gaiachain_seal.generate_qualified_seal({
            "lote_id": lote_id,
            "producto": data_cosecha.get("producto", "Cannabis Medicinal"),
            "fecha": datetime.now(timezone.utc).isoformat(),
            "datos": {"cosecha": data_cosecha, "yield": data_yield, "lab": data_lab},
        })
        ai_act_result = self.ai_act.register_ai_decision({
            "decision_id": f"DEC-{lote_id}-{datetime.now(timezone.utc).strftime('%Y%m%d')}",
            "model": "Mistral-7B",
            "input_data": {
                "lote_id": lote_id,
                "metric": "yield",
                "current_value": data_cosecha.get("yield_actual", 98.5),
                "target_value": (data_yield.get("simulacion") or {}).get("escenario_1", {}).get("yield", 99.0),
            },
            "output": data_yield,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "risk_assessment": {"level": "low"},
            "human_oversight": {"reviewed_by": "Gemelo Digital", "approval": True},
        })
        cliente_data = data_cosecha.get("cliente") or {}
        gdpr_result = self.gdpr.pseudonymize_data(cliente_data) if cliente_data else {"gaiachain_tx": "gaiachain-no-cli", "gdpr_compliant": True}

        metadata = {
            "analisis_yield": {
                "yield_actual": data_yield.get("current_yield", data_cosecha.get("yield_actual", 98.5)),
                "yield_optimo": (data_yield.get("simulacion") or {}).get("escenario_1", {}).get("yield", 99.0),
                "recomendaciones": data_yield.get("recomendaciones", []),
                "metodo": "Agrovoltaica Cuantica + QKD",
                "gaiachain_tx": data_yield.get("gaiachain_tx", "N/A"),
            },
            "cannabinoides": data_lab.get("cannabinoids", {}),
            "trazabilidad": {
                "blockchain": "GaiaChain",
                "sensores_usados": ["humedad", "temperatura", "luz_par"],
                "gaiachain_tx": [
                    data_cosecha.get("gaiachain_tx", "N/A"),
                    data_lab.get("gaiachain_tx", "N/A"),
                ],
            },
            "normativas": ["eIDAS 2", "AI Act 2024", "GDPR", "RD 903/2025"],
        }

        legal_seals = {
            "eidas_seal": (eidas_seal.get("seal") or {}).get("hash", "eidas-pending"),
            "gaiachain_tx": [
                data_cosecha.get("gaiachain_tx"),
                data_lab.get("gaiachain_tx"),
                eidas_seal.get("gaiachain_tx"),
                ai_act_result.get("gaiachain_tx"),
                gdpr_result.get("gaiachain_tx"),
            ],
            "ai_act_tx": ai_act_result.get("gaiachain_tx"),
            "gdpr_compliant": gdpr_result.get("gdpr_compliant", True),
        }
        gaiachain_tx_first = (legal_seals["gaiachain_tx"] or [None])[0] or eidas_seal.get("gaiachain_tx") or "pending"
        legal_seals["gaiachain_tx"] = gaiachain_tx_first

        certificate_path, certificate_hash = self.certificate_generator.generate_sovereign_certificate(
            harvest_data=data_cosecha,
            legal_seals=legal_seals,
            metadata=metadata,
        )
        final_tx = self._register_final_certificate(
            lote_id=lote_id,
            certificate_path=certificate_path,
            certificate_hash=certificate_hash,
            legal_seals=legal_seals,
        )
        verification_url = f"https://gaiachain.castuo-system.com/verify/{final_tx}"

        return {
            "status": "success",
            "lote_id": lote_id,
            "certificate_path": certificate_path,
            "certificate_hash": certificate_hash,
            "gaiachain_tx": final_tx,
            "verification_url": verification_url,
            "qr_code_path": f"{self.certificate_generator.output_path}/QR_{lote_id}_{str(final_tx)[:8]}.png",
            "metadata": metadata,
            "legal_seals": legal_seals,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _register_final_certificate(
        self,
        lote_id: str,
        certificate_path: str,
        certificate_hash: str,
        legal_seals: Dict[str, Any],
    ) -> str:
        """Registra el certificado final en GaiaChain (tipo final_certificate)."""
        if not os.path.isfile(_GAIACHAIN_CLI):
            # Cuando GaiaChain está offline, generamos un tx local único para que la verificación
            # por QR (y el endpoint verify) funcione sin depender de la red.
            local_tx = f"local-fallback-final_certificate-{lote_id}-{certificate_hash[:10]}"
            try:
                local_db.update_certificate_tx(
                    lote_id=lote_id,
                    pdf_hash=certificate_hash,
                    gaiachain_tx=local_tx,
                    status="local_only",
                )
                local_db.log_operation(
                    "final_certificate",
                    {
                        "lote_id": lote_id,
                        "certificate_hash": certificate_hash,
                        "certificate_path": certificate_path,
                        "legal_seals": legal_seals,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "status": "CERTIFIED_SOVERIGN_ASSET",
                    },
                    gaiachain_tx=None,
                    error="gaiachain-cli-missing",
                )
                local_db.log_system_event(
                    "gaiachain_final_certificate_offline_fallback",
                    f"GaiaChain offline. Tx local generado: {local_tx}",
                    "warning",
                )
            except Exception as e:
                logger.warning("Final certificate offline fallback: %s", e)
            return local_tx
        data = {
            "lote_id": lote_id,
            "certificate_hash": certificate_hash,
            "certificate_path": certificate_path,
            "legal_seals": legal_seals,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "CERTIFIED_SOVERIGN_ASSET",
        }
        try:
            r = subprocess.run(
                [_GAIACHAIN_CLI, "record", "--type", "final_certificate", "--data", json.dumps(data)],
                capture_output=True,
                text=True,
                timeout=15,
            )
            return (r.stdout or "").strip() or "ok" if r.returncode == 0 else "gaiachain-error"
        except Exception as e:
            logger.warning("GaiaChain final_certificate: %s", e)
            return f"Error: {e}"

    def get_certificate_status(self, tx_hash: str) -> Dict[str, Any]:
        """Consulta el estado de un certificado en GaiaChain."""
        if not os.path.isfile(_GAIACHAIN_CLI):
            # Offline: devolvemos evidencia local si el tx coincide.
            try:
                cert = local_db.get_certificate_by_tx(tx_hash)
                if not cert:
                    return {"valid": False, "error": "gaiachain-no-cli"}
                certificate_data = cert.get("certificate_data", {}) or {}
                legal_seals = certificate_data.get("legal_seals", {})
                return {
                    "valid": True,
                    "data": {
                        # Estructura compatible con `/certificates/verify` (incluye `data.certificate_data.pdf_path`).
                        "lote_id": cert.get("lote_id"),
                        "certificate_hash": cert.get("pdf_hash"),
                        "pdf_hash": cert.get("pdf_hash"),
                        "xml_hash": cert.get("xml_hash"),
                        "gaiachain_tx": cert.get("gaiachain_tx"),
                        "status": cert.get("status"),
                        "timestamp": cert.get("timestamp"),
                        "legal_seals": legal_seals,
                        "certificate_data": certificate_data,
                    },
                }
            except Exception as e:
                return {"valid": False, "error": str(e)}
        try:
            r = subprocess.run(
                [_GAIACHAIN_CLI, "query", "--type", "final_certificate", "--tx", tx_hash],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if r.returncode != 0 or not (r.stdout or "").strip():
                return {"valid": False, "error": r.stderr or "not found"}
            return {"valid": True, "data": json.loads(r.stdout)}
        except Exception as e:
            return {"valid": False, "error": str(e)}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    certifier = MainCertifier()
    result = certifier.ejecutar_certificacion_real("CAN-2026-001")
    print("Lote certificado:", result["lote_id"])
    print("Certificado:", result["certificate_path"])
    print("Hash:", result["certificate_hash"])
    print("Verificacion:", result["verification_url"])
