# -*- coding: utf-8 -*-
"""HarvestBot: cosecha robótica simulada con visión IA y trazabilidad GaiaChain."""
from __future__ import annotations

import json
import logging
import os
import subprocess
from datetime import datetime, timezone
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

_GAIACHAIN_CLI = os.getenv("GAIACHAIN_CLI", "/usr/local/bin/gaiachain")


class HarvestBot:
    """Simula cosecha autónoma (detección + brazo); en producción conectar cámara y brazo real."""

    def __init__(self) -> None:
        self.gaiachain_cli = _GAIACHAIN_CLI

    def get_harvest_data(self, lote_id: str, cultivo: str = "cannabis_medicinal") -> Dict[str, Any]:
        """
        Devuelve datos de cosecha para un lote (para certificados soberanos).
        Si se desea registrar en GaiaChain, llamar antes a harvest(cultivo, lote_id).
        """
        harvest_result = self.harvest(cultivo, lote_id)
        return {
            "lote_id": lote_id,
            "producto": f"Cannabis Medicinal ({cultivo})",
            "fecha_cosecha": datetime.now(timezone.utc).strftime("%d/%m/%Y"),
            "peso_neto": f"{harvest_result.get('peso_estimado_gr', 0)} g",
            "ubicacion": "Invernadero 3, Finca La Dehesa, Caceres",
            "responsable": "CASTUO-SYSTEM S.L.",
            "cliente": {"nombre": "Publico", "cif_nif": "N/A", "direccion": "N/A"},
            "yield_actual": 98.5,
            "gaiachain_tx": harvest_result.get("gaiachain_tx", ""),
        }

    def harvest(self, cultivo: str, lote_id: str) -> Dict[str, Any]:
        """
        Detecta plantas listas (stub) y simula cosecha; registra en GaiaChain.
        """
        plantas_listas = self._detectar_plantas_listas(cultivo)
        cosecha_data = self._realizar_cosecha(plantas_listas)
        tx_hash = self._registrar_en_gaiachain({
            "cultivo": cultivo,
            "lote_id": lote_id,
            "plantas_cosechadas": len(plantas_listas),
            "peso_estimado": cosecha_data.get("peso", 0),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        return {
            "status": "cosechado",
            "cultivo": cultivo,
            "lote_id": lote_id,
            "plantas_cosechadas": len(plantas_listas),
            "peso_estimado_gr": cosecha_data.get("peso", 0),
            "gaiachain_tx": tx_hash,
        }

    def _detectar_plantas_listas(self, cultivo: str) -> List[Dict[str, Any]]:
        """Stub: devuelve lista simulada. En producción usar YOLOv8/OpenCV."""
        return [
            {"confianza": 0.92, "coordenadas": (100, 100, 50, 80), "clase": cultivo},
            {"confianza": 0.88, "coordenadas": (200, 150, 48, 78), "clase": cultivo},
        ]

    def _realizar_cosecha(self, plantas: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Stub: peso simulado. En producción controlar brazo y balanza."""
        peso = len(plantas) * 25.0
        return {"plantas_cosechadas": len(plantas), "peso": peso}

    def _registrar_en_gaiachain(self, data: Dict[str, Any]) -> str:
        if not os.path.isfile(self.gaiachain_cli):
            return "gaiachain-no-cli"
        try:
            r = subprocess.run(
                [self.gaiachain_cli, "record", "--type", "harvest", "--data", json.dumps(data)],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return (r.stdout or "").strip() or "ok" if r.returncode == 0 else f"Error: {r.stderr}"
        except Exception as e:
            return f"Error: {e}"
