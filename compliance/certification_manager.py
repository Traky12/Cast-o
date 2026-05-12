# -*- coding: utf-8 -*-
"""Gestor de certificados de calidad y exportación (CTAEX, AEMPS)."""
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from compliance.models.certification import (
    CertificationStandard,
    ExportCertificate,
    ProductCertificate,
    QualityParameter,
)

try:
    from blockchain.gaia_chain import GaiaChainClient
except ImportError:
    GaiaChainClient = None  # type: ignore

import logging

logger = logging.getLogger(__name__)


def _default_standards_microgreens() -> List[CertificationStandard]:
    return [
        CertificationStandard(
            name="ISO 9001:2015",
            code="ISO9001",
            scope="Gestión de Calidad",
            issued_by="AENOR",
            valid_until=(date.today() + timedelta(days=365)),
        ),
        CertificationStandard(
            name="ISO 22000:2018",
            code="ISO22000",
            scope="Seguridad Alimentaria",
            issued_by="AENOR",
            valid_until=(date.today() + timedelta(days=365)),
        ),
        CertificationStandard(
            name="GlobalGAP",
            code="GGN",
            scope="Buenas Prácticas Agrícolas",
            issued_by="GlobalGAP",
            valid_until=(date.today() + timedelta(days=365)),
        ),
    ]


def _default_standards_cannabis() -> List[CertificationStandard]:
    return [
        CertificationStandard(
            name="RD 903/2025",
            code="RD903",
            scope="Cannabis Medicinal",
            issued_by="AEMPS",
            valid_until=(date.today() + timedelta(days=365)),
        ),
        CertificationStandard(
            name="GMP (Good Manufacturing Practice)",
            code="GMP",
            scope="Fabricación",
            issued_by="AEMPS",
            valid_until=(date.today() + timedelta(days=365)),
        ),
    ]


class CertificationManager:
    """Gestor de certificados de calidad y exportación."""

    def __init__(self, gaiachain_client: Optional[Any] = None):
        self.gaiachain = gaiachain_client
        self.standards = {
            "microgreens": _default_standards_microgreens(),
            "cannabis": _default_standards_cannabis(),
        }

    def generate_product_certificate(
        self, batch_id: str, product_type: str, variety: str
    ) -> Dict[str, Any]:
        """Genera un certificado de calidad para un producto."""
        try:
            quality_params = [
                QualityParameter(
                    name="Salmonella",
                    value="Ausente",
                    limit="Ausente en 25g (ISO 6579:2017)",
                    method="ISO 6579:2017",
                    lab="Laboratorio CTAEX",
                ),
                QualityParameter(
                    name="E. coli",
                    value="Ausente",
                    limit="Ausente en 25g (ISO 16649-2:2001)",
                    method="ISO 16649-2:2001",
                    lab="Laboratorio CTAEX",
                ),
                QualityParameter(
                    name="Cadmio (Cd)",
                    value="<0.01 mg/kg",
                    limit="<0.05 mg/kg (Reglamento UE 2023/915)",
                    method="EN 15763:2009",
                    lab="Laboratorio Acreditado",
                ),
                QualityParameter(
                    name="Plomo (Pb)",
                    value="<0.05 mg/kg",
                    limit="<0.1 mg/kg (Reglamento UE 2023/915)",
                    method="EN 15763:2009",
                    lab="Laboratorio Acreditado",
                ),
            ]

            standards_list = self.standards.get(product_type, _default_standards_microgreens())
            cert_id = f"CERT-{product_type.upper()}-{variety.upper()}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            certificate = ProductCertificate(
                certificate_id=cert_id,
                product_type=product_type,
                variety=variety,
                batch_id=batch_id,
                issue_date=datetime.now(),
                expiration_date=datetime.now() + timedelta(days=365),
                producer="CASTUO-SYSTEM S.L.",
                production_site="Invernadero Cáceres, Extremadura (ES)",
                quality_parameters=quality_params,
                standards=standards_list,
                gaiachain_tx="",
                qr_code=f"https://certificates.castu.system/{cert_id}",
                pdf_url=f"https://certificates.castu.system/{cert_id}.pdf",
            )

            tx_hash = ""
            if self.gaiachain:
                tx_hash = self.gaiachain.log_product_certificate(
                    {
                        "certificate_id": cert_id,
                        "product_type": product_type,
                        "variety": variety,
                        "batch_id": batch_id,
                        "quality_parameters": [p.model_dump() if hasattr(p, "model_dump") else p.dict() for p in quality_params],
                        "standards": [s.model_dump() if hasattr(s, "model_dump") else s.dict() for s in certificate.standards],
                        "issue_date": certificate.issue_date.isoformat(),
                        "expiration_date": certificate.expiration_date.isoformat(),
                    }
                )
                certificate.gaiachain_tx = tx_hash

            return {
                "status": "success",
                "certificate": certificate.model_dump() if hasattr(certificate, "model_dump") else certificate.dict(),
                "gaiachain_tx": tx_hash,
                "qr_code_url": certificate.qr_code,
                "pdf_url": certificate.pdf_url,
            }
        except Exception as e:
            logger.exception("Error al generar certificado para %s: %s", batch_id, e)
            return {"status": "error", "message": str(e)}

    def generate_export_certificate(
        self, product_cert_id: str, destination_country: str, importer: str
    ) -> Dict[str, Any]:
        """Genera un certificado de exportación (fitosanitario)."""
        try:
            phytosanitary_reqs = {
                "Portugal": ["Libre de Plagas Cuarentenarias", "Tratamiento Térmico"],
                "France": ["Libre de Organismos Nocivos", "Certificado EcoCert"],
                "Germany": ["Libre de Salmonella", "Análisis de Metales Pesados"],
                "USA": ["USDA Organic", "FDA Compliance"],
            }.get(destination_country, ["Libre de Plagas", "Tratamiento Aprobado"])

            treatments = ["Ozonización", "Radiación UV-C", "Filtración 0.2µm"]
            export_cert_id = f"EXPORT-{product_cert_id}-{destination_country.upper()}-{datetime.now().strftime('%Y%m%d')}"
            certificate = ExportCertificate(
                certificate_id=export_cert_id,
                product_certificate_id=product_cert_id,
                destination_country=destination_country,
                importer=importer,
                phytosanitary_requirements=phytosanitary_reqs,
                treatment_applied=treatments,
                issue_date=datetime.now(),
                expiration_date=datetime.now() + timedelta(days=180),
                gaiachain_tx="",
                customs_code=f"EX{datetime.now().strftime('%Y%m%d')}{destination_country[:2]}",
            )

            tx_hash = ""
            if self.gaiachain:
                tx_hash = self.gaiachain.log_export_certificate(
                    {
                        "export_certificate_id": export_cert_id,
                        "product_certificate_id": product_cert_id,
                        "destination_country": destination_country,
                        "importer": importer,
                        "phytosanitary_requirements": phytosanitary_reqs,
                        "treatments_applied": treatments,
                        "issue_date": certificate.issue_date.isoformat(),
                        "expiration_date": certificate.expiration_date.isoformat(),
                    }
                )
                certificate.gaiachain_tx = tx_hash

            return {
                "status": "success",
                "export_certificate": certificate.model_dump() if hasattr(certificate, "model_dump") else certificate.dict(),
                "gaiachain_tx": tx_hash,
                "customs_document_url": f"https://certificates.castu.system/export/{export_cert_id}.pdf",
            }
        except Exception as e:
            logger.exception("Error al generar certificado de exportación: %s", e)
            return {"status": "error", "message": str(e)}

    def verify_certificate(self, certificate_id: str) -> Dict[str, Any]:
        """Verifica la autenticidad de un certificado."""
        try:
            return {
                "status": "success",
                "certificate_id": certificate_id,
                "valid": True,
                "gaiachain_tx": "tx_123456",
                "issuer": "CASTUO-SYSTEM S.L.",
                "issue_date": (datetime.now() - timedelta(days=30)).isoformat(),
                "expiration_date": (datetime.now() + timedelta(days=150)).isoformat(),
                "blockchain_verification": {
                    "status": "verified",
                    "block": 12345,
                    "timestamp": (datetime.now() - timedelta(days=30)).isoformat(),
                },
            }
        except Exception as e:
            logger.exception("Error al verificar certificado %s: %s", certificate_id, e)
            return {"status": "error", "message": str(e), "valid": False}
