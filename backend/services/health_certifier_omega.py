# -*- coding: utf-8 -*-
"""
HealthCertifierOmega — Sabionda Omega 2040.

La superioridad no está en la tecnología, sino en la integridad del tiempo.
El sistema no se conforma con un dato puntual: exige 24 horas de paz biótica
antes de emitir un Certificado de Salud Ancestral (VeChain).
No vendemos sensores; vendemos certezas biológicas inmutables.
"""
from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional

from ..models.hidroponia import HidroponiaSensor

logger = logging.getLogger(__name__)

# Rango de paz biótica: el aliento de la solución en equilibrio ancestral
PH_PAZ_MIN, PH_PAZ_MAX = 5.8, 6.2
HORAS_ESTABILIDAD_PARA_CERT = 24


class HealthCertifierOmega:
    """
    Certificador de salud biótica.
    Acumula horas de pH en rango de paz; al alcanzar 24h emite certificado (VeChain).
    """

    def __init__(self) -> None:
        self.stable_hours = 0
        self.last_valid_ph = 6.0

    async def check_and_mint_health_cert(
        self, sensor: HidroponiaSensor
    ) -> Optional[Dict[str, Any]]:
        """
        Si el sistema detecta paz biótica (pH 5.8–6.2) por 24h,
        mina un Certificado de Salud Ancestral en VeChain.
        Fuera de rango: se reinicia el ciclo de confianza.
        """
        if PH_PAZ_MIN <= sensor.ph <= PH_PAZ_MAX:
            self.stable_hours += 1
            self.last_valid_ph = sensor.ph
        else:
            self.stable_hours = 0  # Ruido detectado — reinicio del ciclo de confianza

        if self.stable_hours >= HORAS_ESTABILIDAD_PARA_CERT:
            cert_id = f"CERT-BIO-{int(time.time())}"
            logger.info("🌿 [SABIONDA_OMEGA] Emitiendo Certificado: %s", cert_id)
            # En producción: llamada a API VeChain Thor Mainnet
            return {
                "cert_id": cert_id,
                "msg": "Soberanía Biótica Certificada: 24h de estabilidad ancestral",
                "blockchain": "VeChain Thor Mainnet",
            }
        return None
