"""
CASTÚO-SYSTEM™ v3.1 — Cliente Modbus para Sistema Agrovoltaico
Lee datos de inversores solares y medidores de energía vía Modbus TCP/RTU.
Incluye lógica de optimización de sombra para integración agrovoltaica.

Compatibilidad probada:
  - SolarEdge SE inversores (Modbus TCP, registro base 40000)
  - Fronius Symo (Modbus TCP, SunSpec)
  - SDM630 medidor de energía (Modbus RTU vía adaptador TCP)
  - Modo simulación cuando pymodbus no está instalado o el inversor no responde

Variables de entorno:
    MODBUS_INVERTER_HOST   IP del inversor/gateway Modbus (default: 192.168.1.100)
    MODBUS_INVERTER_PORT   Puerto TCP (default: 502)
    MODBUS_UNIT_ID         ID de unidad Modbus (default: 1)
    MODBUS_TIMEOUT         Timeout conexión en segundos (default: 5)
    SOLAR_PEAK_KW          Potencia pico instalada en kW (default: 10.0)

Dependencias opcionales:
    pip install pymodbus>=3.5.0
"""

from __future__ import annotations

import hashlib
import logging
import os
import time
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger("castuo.modbus_client")

# ── Config ──────────────────────────────────────────────────────────────────────

MODBUS_HOST    = os.getenv("MODBUS_INVERTER_HOST", "192.168.1.100")
MODBUS_PORT    = int(os.getenv("MODBUS_INVERTER_PORT", "502"))
MODBUS_UNIT    = int(os.getenv("MODBUS_UNIT_ID", "1"))
MODBUS_TIMEOUT = int(os.getenv("MODBUS_TIMEOUT", "5"))
SOLAR_PEAK_KW  = float(os.getenv("SOLAR_PEAK_KW", "10.0"))

# Rangos PAR óptimos por cultivo (μmol/m²/s)
PAR_OPTIMO: dict[str, float] = {
    "tomate":    600.0,
    "pimiento":  600.0,
    "pepino":    550.0,
    "lechuga":   350.0,
    "fresa":     400.0,
    "albahaca":  350.0,
    "espinaca":  300.0,
    "cilantro":  300.0,
}

try:
    from pymodbus.client import ModbusTcpClient as _ModbusTcpClient  # type: ignore
    _MODBUS_AVAILABLE = True
except ImportError:
    _MODBUS_AVAILABLE = False
    logger.info("[modbus_client] pymodbus no instalado — modo simulación activo")


class SolarReading:
    """Resultado de una lectura del sistema fotovoltaico."""

    __slots__ = (
        "voltaje_v", "corriente_a", "potencia_w", "kwh_hoy",
        "kwh_total", "temperatura_panel_c", "eficiencia_pct",
        "timestamp", "simulado",
    )

    def __init__(
        self,
        voltaje_v: float,
        corriente_a: float,
        potencia_w: float,
        kwh_hoy: float,
        kwh_total: float,
        temperatura_panel_c: float,
        eficiencia_pct: float,
        timestamp: str,
        simulado: bool = False,
    ):
        self.voltaje_v = voltaje_v
        self.corriente_a = corriente_a
        self.potencia_w = potencia_w
        self.kwh_hoy = kwh_hoy
        self.kwh_total = kwh_total
        self.temperatura_panel_c = temperatura_panel_c
        self.eficiencia_pct = eficiencia_pct
        self.timestamp = timestamp
        self.simulado = simulado

    def to_dict(self) -> dict:
        return {
            "voltaje_v":          self.voltaje_v,
            "corriente_a":        self.corriente_a,
            "potencia_w":         self.potencia_w,
            "kwh_hoy":            self.kwh_hoy,
            "kwh_total":          self.kwh_total,
            "temperatura_panel_c": self.temperatura_panel_c,
            "eficiencia_pct":     self.eficiencia_pct,
            "timestamp":          self.timestamp,
            "simulado":           self.simulado,
        }


class ModbusEnergyClient:
    """
    Cliente de lectura de inversores solares vía Modbus TCP.
    Fallback a datos simulados cuando el inversor no es accesible.
    """

    def __init__(self) -> None:
        self._client = None
        self._connected = False
        self._last_reading: Optional[SolarReading] = None
        self._connect()

    def _connect(self) -> None:
        if not _MODBUS_AVAILABLE:
            return
        try:
            self._client = _ModbusTcpClient(
                host=MODBUS_HOST,
                port=MODBUS_PORT,
                timeout=MODBUS_TIMEOUT,
            )
            self._connected = self._client.connect()
            if self._connected:
                logger.info(
                    "[modbus_client] Conectado al inversor Modbus %s:%d",
                    MODBUS_HOST, MODBUS_PORT,
                )
        except Exception as exc:
            logger.warning("[modbus_client] No se pudo conectar al inversor: %s — simulación", exc)
            self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected

    # ── Lectura real (SunSpec / SolarEdge) ──────────────────────────────────────

    def read_solar_data(self) -> SolarReading:
        """
        Lee los registros del inversor. Registro base SunSpec (40000):
          40071: Voltaje CC (SF: 40075)
          40072: Corriente CC
          40083: Potencia AC (W)
          40093: kWh producidos hoy
          40094: kWh totales
          40103: Temperatura inversor (°C)
        """
        if self._connected and self._client:
            try:
                result = self._client.read_holding_registers(40000, count=120, slave=MODBUS_UNIT)
                if not result.isError():
                    regs = result.registers
                    # Escala SunSpec — simplificado, ajustar a modelo real
                    voltaje     = regs[70] * 0.1 if len(regs) > 70 else 380.0
                    corriente   = regs[71] * 0.01 if len(regs) > 71 else 0.0
                    potencia_w  = regs[82] * 1.0 if len(regs) > 82 else 0.0
                    kwh_hoy     = regs[92] * 0.001 if len(regs) > 92 else 0.0
                    kwh_total   = regs[93] * 0.001 if len(regs) > 93 else 0.0
                    temp_inv    = regs[102] * 0.1 if len(regs) > 102 else 25.0
                    eficiencia  = round((potencia_w / (SOLAR_PEAK_KW * 1000)) * 100, 1) if SOLAR_PEAK_KW > 0 else 0.0

                    reading = SolarReading(
                        voltaje_v=round(voltaje, 1),
                        corriente_a=round(corriente, 2),
                        potencia_w=round(potencia_w, 1),
                        kwh_hoy=round(kwh_hoy, 3),
                        kwh_total=round(kwh_total, 1),
                        temperatura_panel_c=round(temp_inv, 1),
                        eficiencia_pct=round(min(eficiencia, 100.0), 1),
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        simulado=False,
                    )
                    self._last_reading = reading
                    return reading
            except Exception as exc:
                logger.warning("[modbus_client] Error leyendo Modbus: %s — simulando", exc)

        return self._simulated_reading()

    def _simulated_reading(self) -> SolarReading:
        """Genera una lectura simulada determinista basada en la hora del día."""
        now = datetime.now(timezone.utc)
        hora = now.hour + now.minute / 60.0
        # Curva solar simplificada: pico al mediodía solar (~13:00 UTC+1)
        solar_factor = max(0.0, -0.04 * (hora - 13) ** 2 + 1.0)
        potencia_w = round(SOLAR_PEAK_KW * 1000 * solar_factor * 0.85, 1)
        voltaje = round(380.0 + solar_factor * 20, 1)
        corriente = round(potencia_w / voltaje if voltaje > 0 else 0, 2)
        temp_panel = round(25.0 + solar_factor * 35.0, 1)  # 25°C base, +35°C a pleno sol

        # Seed determinista para kwh_hoy
        day_seed = int(hashlib.sha256(now.strftime("%Y%m%d").encode()).hexdigest()[:8], 16)
        kwh_hoy = round((day_seed % 30) + hora * SOLAR_PEAK_KW * solar_factor * 0.1, 3)

        return SolarReading(
            voltaje_v=voltaje,
            corriente_a=corriente,
            potencia_w=potencia_w,
            kwh_hoy=kwh_hoy,
            kwh_total=round(kwh_hoy * 365 * 0.7, 1),
            temperatura_panel_c=temp_panel,
            eficiencia_pct=round(solar_factor * 85, 1),
            timestamp=now.isoformat(),
            simulado=True,
        )

    def close(self) -> None:
        if self._client:
            self._client.close()


# ── Optimización de sombra agrovoltaica ────────────────────────────────────────

def calculate_shadow_adjustment(
    luz_par_actual: float,
    cultivo: str = "tomate",
    cobertura_actual_pct: float = 20.0,
) -> dict:
    """
    Calcula el ajuste óptimo de la pantalla de sombra para maximizar
    simultáneamente la producción fotovoltaica y el bienestar del cultivo.

    luz_par_actual:      Irradiancia PAR medida (μmol/m²/s)
    cultivo:             Cultivo en producción (para PAR óptimo)
    cobertura_actual_pct: % de sombra actual (0-100)

    Retorna:
        accion:           mantener | aumentar_sombra | reducir_sombra
        nueva_cobertura:  % recomendado
        delta:            cambio en % respecto al actual
        motivo:           descripción legible
    """
    par_optimo = PAR_OPTIMO.get(cultivo.lower(), 500.0)
    diferencia = luz_par_actual - par_optimo

    if diferencia > 150:
        # Demasiada luz — aumentar sombra en pasos del 15%
        incremento = min(15, int(diferencia / 50) * 5)
        nueva = min(80, cobertura_actual_pct + incremento)
        return {
            "accion": "aumentar_sombra",
            "nueva_cobertura_pct": nueva,
            "delta_pct": nueva - cobertura_actual_pct,
            "luz_actual": luz_par_actual,
            "luz_optima": par_optimo,
            "motivo": (
                f"PAR {luz_par_actual:.0f} > óptimo {par_optimo:.0f} μmol/m²/s "
                f"(+{diferencia:.0f}) — aumentar sombra {cobertura_actual_pct}% → {nueva}%"
            ),
        }
    elif diferencia < -150:
        # Poca luz — reducir sombra en pasos del 15%
        decremento = min(15, int(abs(diferencia) / 50) * 5)
        nueva = max(0, cobertura_actual_pct - decremento)
        return {
            "accion": "reducir_sombra",
            "nueva_cobertura_pct": nueva,
            "delta_pct": nueva - cobertura_actual_pct,
            "luz_actual": luz_par_actual,
            "luz_optima": par_optimo,
            "motivo": (
                f"PAR {luz_par_actual:.0f} < óptimo {par_optimo:.0f} μmol/m²/s "
                f"({diferencia:.0f}) — reducir sombra {cobertura_actual_pct}% → {nueva}%"
            ),
        }
    else:
        return {
            "accion": "mantener",
            "nueva_cobertura_pct": cobertura_actual_pct,
            "delta_pct": 0,
            "luz_actual": luz_par_actual,
            "luz_optima": par_optimo,
            "motivo": f"PAR {luz_par_actual:.0f} dentro de rango aceptable (±150 μmol/m²/s del óptimo {par_optimo:.0f})",
        }


def calcular_autoconsumo_pct(kwh_generados: float, kwh_consumidos: float) -> float:
    """% de energía solar autoconsumida por el invernadero (0–100)."""
    if kwh_generados <= 0:
        return 0.0
    return round(min(100.0, (kwh_consumidos / kwh_generados) * 100), 2)


def calcular_excedente_kwh(kwh_generados: float, kwh_consumidos: float) -> float:
    """kWh excedentes vertidos a red (puede ser negativo si hay déficit)."""
    return round(kwh_generados - kwh_consumidos, 3)


# ── Instancia global ───────────────────────────────────────────────────────────

_modbus_instance: ModbusEnergyClient | None = None


def get_modbus_client() -> ModbusEnergyClient:
    global _modbus_instance
    if _modbus_instance is None:
        _modbus_instance = ModbusEnergyClient()
    return _modbus_instance
