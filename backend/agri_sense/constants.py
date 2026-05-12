"""Constantes fail-safe y umbrales del bucle de control AGRI-SENSE."""

import os

FAIL_SAFE_NPK_VALVE_CLOSED_ON_OZONE_FAULT = True
"""Si el sensor de Ozono falla (confidence bajo o timeout), cerrar válvula NPK de inmediato."""

GEOTHERMAL_SETPOINT_DEVIATION_C = 0.5
"""Desviación T_suelo respecto al setpoint que dispara recálculo del COP híbrido."""

MIN_SAMPLES_BEFORE_ACTUATION_NPK = 3
"""Mínimo de muestras filtradas (EWMA/Kalman) antes de permitir actuación sobre N/K."""

OZONE_PH_SYNC_MAX_PH_FOR_INJECTION = 7.2
"""Por encima de este pH no inyectar O3 para evitar oxidación de nitrato/potasio."""

CONDUCTIVITY_OPTIMAL_RO_MS_CM_LOW = 0.8
CONDUCTIVITY_OPTIMAL_RO_MS_CM_HIGH = 1.8
"""Banda de CE óptima para permeabilidad de membranas RO; ajustar bomba si fuera."""

CONFIDENCE_ACTION_THRESHOLD = 0.85
CONFIDENCE_OZONE_FAULT_THRESHOLD = 0.7

HSM_PUBLIC_KEY_PEM = os.getenv("CASTUO_HSM_PUBLIC_PEM", "")
"""Clave pública HSM inyectada en runtime (ZIP industrial); nunca en Git."""

HSM_SLOT = os.getenv("HSM_SLOT", "")
"""Slot PKCS#11 / HSM; valor real solo en entorno de despliegue."""

CASTUO_MEASURED_BOOT = os.getenv("CASTUO_MEASURED_BOOT", "0").lower() in ("1", "true", "yes")
"""Si True, minado BioCoin exige TrustOrchestrator.trusted_environment."""
