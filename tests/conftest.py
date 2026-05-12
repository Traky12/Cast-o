"""
Configuración global de pytest para CASTÚO-SYSTEM™.
Deshabilita el rate limiter en tests para evitar fallos por volumen de peticiones.
"""
import os

# Desactivar rate limiting en tests (127.0.0.1 alcanzaría el límite rápidamente)
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")
