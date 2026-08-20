"""
Nodo 1: INVERNADERO — Lectura y validación IoT
Lee sensores, valida parámetros contra rangos óptimos por cultivo.
Sin escrituras externas → sin compensating action.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

try:
    from ..state import AgroState
    from ..tools import tool_validate_iot_readings, tool_log_elk
except ImportError:
    from state import AgroState
    from tools import tool_validate_iot_readings, tool_log_elk


async def invernadero_node(state: AgroState) -> AgroState:
    readings = state.get("sensor_readings", [])
    lote_id = state.get("lote_id", "unknown")

    cultivo = "tomate"  # En producción: leer del lote en PostgreSQL
    result = await tool_validate_iot_readings(readings, cultivo)

    alertas = result.get("alertas", [])
    status = result.get("status", "OPTIMO")

    await tool_log_elk(
        lote_id=lote_id,
        event_type="IOT_VALIDATED",
        node="invernadero",
        data={"readings_count": len(readings), "status": status, "alertas_count": len(alertas)},
    )

    return {
        **state,
        "validated_readings": readings,
        "readings_alertas": alertas,
        "invernadero_status": status,
        "current_node": "invernadero",
    }
