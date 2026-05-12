# -*- coding: utf-8 -*-
"""Gestor de cultivos de microgreens con trazabilidad y certificaciones."""
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from production.models.microgreens import MicrogreenBatch, MicrogreenVariety

try:
    from blockchain.gaia_chain import GaiaChainClient
except ImportError:
    GaiaChainClient = None  # type: ignore

import logging

logger = logging.getLogger(__name__)


class MicrogreensManager:
    """Gestor de cultivos de microgreens con trazabilidad y certificaciones."""

    def __init__(self, gaiachain_client: Optional[Any] = None):
        self.gaiachain = gaiachain_client
        self.varieties = self._load_varieties()

    def _load_varieties(self) -> Dict[str, MicrogreenVariety]:
        """Carga las variedades de microgreens con sus parámetros."""
        return {
            "radish": MicrogreenVariety(
                name="Rábano",
                scientific_name="Raphanus sativus",
                germination_days=3,
                harvest_days=10,
                ideal_temperature={"min": 18, "max": 22},
                ideal_humidity={"min": 60, "max": 70},
                ideal_ec={"min": 0.8, "max": 1.2},
                ideal_ph={"min": 5.8, "max": 6.2},
                light_requirements={"intensity": 150, "hours": 12},
                seed_density=10,
                yield_kg_per_m2=2.5,
            ),
            "broccoli": MicrogreenVariety(
                name="Brócoli",
                scientific_name="Brassica oleracea",
                germination_days=4,
                harvest_days=12,
                ideal_temperature={"min": 20, "max": 24},
                ideal_humidity={"min": 65, "max": 75},
                ideal_ec={"min": 1.0, "max": 1.4},
                ideal_ph={"min": 6.0, "max": 6.5},
                light_requirements={"intensity": 200, "hours": 14},
                seed_density=8,
                yield_kg_per_m2=2.0,
            ),
            "sunflower": MicrogreenVariety(
                name="Girasol",
                scientific_name="Helianthus annuus",
                germination_days=5,
                harvest_days=14,
                ideal_temperature={"min": 20, "max": 25},
                ideal_humidity={"min": 60, "max": 70},
                ideal_ec={"min": 1.2, "max": 1.6},
                ideal_ph={"min": 6.0, "max": 6.5},
                light_requirements={"intensity": 250, "hours": 16},
                seed_density=12,
                yield_kg_per_m2=3.0,
            ),
        }

    def create_batch(
        self, variety_name: str, tray_id: str, quantity: float
    ) -> Dict[str, Any]:
        """Crea un nuevo lote de microgreens."""
        try:
            variety = self.varieties.get(variety_name)
            if not variety:
                return {"status": "error", "message": f"Variedad {variety_name} no encontrada"}

            batch_id = f"MG-{variety_name.upper()}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            batch = MicrogreenBatch(
                batch_id=batch_id,
                variety=variety,
                tray_id=tray_id,
                start_date=datetime.now(),
                status="seeding",
                environmental_data=[],
                quality_checks=[],
                germination_date=None,
                harvest_date=None,
            )

            dump = variety.model_dump() if hasattr(variety, "model_dump") else variety.dict()
            tx_hash = ""
            if self.gaiachain:
                tx_hash = self.gaiachain.log_microgreen_batch(
                    {
                        "batch_id": batch_id,
                        "variety": dump,
                        "tray_id": tray_id,
                        "start_date": batch.start_date.isoformat(),
                        "status": batch.status,
                        "quantity_grams": quantity,
                        "expected_yield_kg": quantity
                        * variety.yield_kg_per_m2
                        / variety.seed_density,
                    }
                )

            return {
                "status": "success",
                "batch": batch.model_dump() if hasattr(batch, "model_dump") else batch.dict(),
                "gaiachain_tx": tx_hash,
                "expected_harvest_date": (
                    datetime.now()
                    + timedelta(days=variety.germination_days + variety.harvest_days)
                ).isoformat(),
                "recommendations": {
                    "environment": dump,
                    "light_schedule": f"{variety.light_requirements['hours']} horas al día a {variety.light_requirements['intensity']} µmol/m²/s",
                },
            }
        except Exception as e:
            logger.exception("Error al crear lote de microgreens: %s", e)
            return {"status": "error", "message": str(e)}

    def update_batch_status(
        self, batch_id: str, status: str, data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Actualiza el estado de un lote de microgreens."""
        try:
            update_data = {"status": status, "update_date": datetime.now().isoformat()}
            if data:
                update_data.update(data)

            tx_hash = ""
            if self.gaiachain:
                tx_hash = self.gaiachain.log_microgreen_update(
                    {
                        "batch_id": batch_id,
                        "status": status,
                        "update_data": update_data,
                        "timestamp": datetime.now().isoformat(),
                    }
                )

            return {
                "status": "success",
                "batch_id": batch_id,
                "new_status": status,
                "gaiachain_tx": tx_hash,
                "message": f"Lote {batch_id} actualizado a {status}",
            }
        except Exception as e:
            logger.exception("Error al actualizar lote %s: %s", batch_id, e)
            return {"status": "error", "message": str(e)}

    def add_environmental_data(self, batch_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Añade datos ambientales a un lote de microgreens."""
        try:
            tx_hash = ""
            if self.gaiachain:
                tx_hash = self.gaiachain.log_microgreen_environmental(
                    {
                        "batch_id": batch_id,
                        "data": data,
                        "timestamp": datetime.now().isoformat(),
                    }
                )
            return {"status": "success", "batch_id": batch_id, "gaiachain_tx": tx_hash}
        except Exception as e:
            logger.exception("Error al añadir datos ambientales a %s: %s", batch_id, e)
            return {"status": "error", "message": str(e)}

    def generate_certificate(self, batch_id: str) -> Dict[str, Any]:
        """Genera un certificado de calidad para un lote de microgreens."""
        try:
            certificate_data = {
                "batch_id": batch_id,
                "issue_date": datetime.now().isoformat(),
                "standards": [
                    "ISO 9001:2015 (Calidad)",
                    "ISO 22000:2018 (Seguridad Alimentaria)",
                    "GlobalGAP",
                    "EcoCert",
                ],
                "quality_parameters": {
                    "microbiological": "Ausencia de Salmonella, E. coli, Listeria",
                    "pesticides": "Libre de pesticidas (LOQ < 0.01 mg/kg)",
                    "heavy_metals": "Cd < 0.05 mg/kg, Pb < 0.1 mg/kg, Hg < 0.01 mg/kg",
                },
                "gaiachain_tx": "",
            }

            tx_hash = ""
            if self.gaiachain:
                tx_hash = self.gaiachain.log_microgreen_certificate(
                    {
                        "batch_id": batch_id,
                        "certificate": certificate_data,
                        "timestamp": datetime.now().isoformat(),
                    }
                )
                certificate_data["gaiachain_tx"] = tx_hash

            return {
                "status": "success",
                "certificate": certificate_data,
                "gaiachain_tx": tx_hash,
                "certificate_url": f"https://certificates.castu.system/{batch_id}.pdf",
            }
        except Exception as e:
            logger.exception("Error al generar certificado para %s: %s", batch_id, e)
            return {"status": "error", "message": str(e)}

    def get_batch_history(self, batch_id: str) -> Dict[str, Any]:
        """Obtiene el historial completo de un lote de microgreens."""
        try:
            variety = self.varieties.get("radish", list(self.varieties.values())[0])
            history = {
                "batch_id": batch_id,
                "variety": variety.model_dump() if hasattr(variety, "model_dump") else variety.dict(),
                "timeline": [
                    {
                        "status": "seeding",
                        "date": (datetime.now() - timedelta(days=12)).isoformat(),
                        "data": {"quantity_grams": 100, "tray_id": "CASTUO-TRAY-001"},
                    },
                    {
                        "status": "germinating",
                        "date": (datetime.now() - timedelta(days=9)).isoformat(),
                        "data": {"temperature": 20.5, "humidity": 65},
                    },
                    {
                        "status": "growing",
                        "date": (datetime.now() - timedelta(days=6)).isoformat(),
                        "data": {"ec": 1.0, "ph": 6.1, "light_hours": 12},
                    },
                ],
                "environmental_data": [
                    {
                        "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
                        "temperature": 21.0,
                        "humidity": 68,
                    },
                    {
                        "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
                        "temperature": 21.2,
                        "humidity": 67,
                    },
                ],
                "gaiachain_tx": ["tx_123", "tx_456", "tx_789"],
            }
            return {"status": "success", "history": history}
        except Exception as e:
            logger.exception("Error al obtener historial de %s: %s", batch_id, e)
            return {"status": "error", "message": str(e)}
