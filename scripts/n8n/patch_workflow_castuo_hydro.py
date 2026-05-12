#!/usr/bin/env python3
"""
Parchea un workflow n8n exportado (JSON) para alinear HTTP Request con la API
hydroponics-saas y notifications/slack de CASTÚO-SYSTEM.

Uso:
  python scripts/n8n/patch_workflow_castuo_hydro.py workflow.json -o workflow.patched.json

Variables de entorno en la instancia n8n (recomendado):
  CASTUO_BASE_URL   ej. http://api:8000 (misma red que compose.prod) o http://host.docker.internal:8000 (n8n solo)
  CASTUO_API_KEY    misma clave que HYDROPONICS_SAAS_API_KEYS en el backend
  CASTUO_ZONE_ID    ej. zone_cannabis_1
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
from typing import Any, Dict, Optional


def _nodes_by_name(workflow: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for n in workflow.get("nodes", []):
        name = n.get("name")
        if name:
            out[str(name)] = n
    return out


def _set_params(node: Dict[str, Any], params: Dict[str, Any]) -> None:
    node.setdefault("parameters", {}).update(params)


def _conn_add(
    connections: Dict[str, Any],
    from_name: str,
    to_name: Optional[str] = None,
    remove_to: Optional[str] = None,
) -> None:
    """Añade main[0] from_name -> to_name; con remove_to elimina ese destino antes (sin re-añadirlo)."""
    block = connections.setdefault(from_name, {}).setdefault("main", [[]])[0]
    if remove_to:
        block[:] = [l for l in block if l.get("node") != remove_to]
    if to_name and not any(l.get("node") == to_name for l in block):
        block.append({"node": to_name, "type": "main", "index": 0})


def patch(workflow: Dict[str, Any]) -> Dict[str, Any]:
    w = copy.deepcopy(workflow)
    by_name = _nodes_by_name(w)
    connections = w.setdefault("connections", {})

    api_key = "={{ $env.CASTUO_API_KEY || 'default_n8n_key_123' }}"
    url_sensor = (
        "={{ ($env.CASTUO_BASE_URL || 'http://backend:8000').replace(/\\/$/, '') + "
        "'/hydroponics-saas/sensor-readings' }}"
    )
    url_analysis = (
        "={{ ($env.CASTUO_BASE_URL || 'http://backend:8000').replace(/\\/$/, '') + "
        "'/hydroponics-saas/daily-analysis' }}"
    )
    url_crops = (
        "={{ ($env.CASTUO_BASE_URL || 'http://backend:8000').replace(/\\/$/, '') + "
        "'/hydroponics-saas/crops' }}"
    )
    url_slack = (
        "={{ ($env.CASTUO_BASE_URL || 'http://backend:8000').replace(/\\/$/, '') + '/notifications/slack' }}"
    )

    # --- HTTP: sensores (JSON body, tipos normalizados) ---
    if "Enviar Lecturas a CASTÚO" in by_name:
        _set_params(
            by_name["Enviar Lecturas a CASTÚO"],
            {
                "method": "POST",
                "url": url_sensor,
                "sendHeaders": True,
                "headerParameters": {
                    "parameters": [
                        {"name": "X-API-KEY", "value": api_key},
                        {"name": "Content-Type", "value": "application/json"},
                    ]
                },
                "sendBody": True,
                "specifyBody": "json",
                "jsonBody": (
                    "={{ {\n"
                    "  sensor_id: $json.sensor_id,\n"
                    "  sensor_type: ($json.sensor_type === 'temperatura' ? 'temperature' : "
                    "$json.sensor_type === 'humedad' ? 'humidity' : "
                    "$json.sensor_type === 'luz' ? 'light' : $json.sensor_type),\n"
                    "  value: Number($json.value),\n"
                    "  timestamp: $json.timestamp,\n"
                    "  location: $json.location || 'default',\n"
                    "  unit: $json.unit || ($json.sensor_type === 'ph' ? 'pH' : "
                    "$json.sensor_type === 'temperatura' ? '\\u00b0C' : "
                    "$json.sensor_type === 'humedad' ? '%' : "
                    "$json.sensor_type === 'ec' ? 'mS/cm' : 'lux'),\n"
                    "  zone_id: $json.zone_id || $env.CASTUO_ZONE_ID\n"
                    "} }}"
                ),
            },
        )

    # --- HTTP: análisis diario (campos API reales) ---
    if "Enviar Análisis a CASTÚO" in by_name:
        _set_params(
            by_name["Enviar Análisis a CASTÚO"],
            {
                "method": "POST",
                "url": url_analysis,
                "sendHeaders": True,
                "headerParameters": {
                    "parameters": [
                        {"name": "X-API-KEY", "value": api_key},
                        {"name": "Content-Type", "value": "application/json"},
                    ]
                },
                "sendBody": True,
                "specifyBody": "json",
                "jsonBody": (
                    "={{ {\n"
                    "  analysis_date: $json.fecha_analisis || $now.toISO(),\n"
                    "  zone_id: $env.CASTUO_ZONE_ID,\n"
                    "  overall_status: $json.estado_general,\n"
                    "  issues: $json.issues || [],\n"
                    "  recommendations: $json.recommendations || [],\n"
                    "  trends: $json.trends || [],\n"
                    "  priority: ({ Alta: 'high', Media: 'medium', Baja: 'low' })[$json.prioridad] || 'medium'\n"
                    "} }}"
                ),
            },
        )

    # --- HTTP: cultivo ---
    if "Registrar Cultivo en CASTÚO" in by_name:
        _set_params(
            by_name["Registrar Cultivo en CASTÚO"],
            {
                "method": "POST",
                "url": url_crops,
                "sendHeaders": True,
                "headerParameters": {
                    "parameters": [
                        {"name": "X-API-KEY", "value": api_key},
                        {"name": "Content-Type", "value": "application/json"},
                    ]
                },
                "sendBody": True,
                "specifyBody": "json",
                "jsonBody": (
                    "={{ {\n"
                    "  crop_id: $json.crop_id,\n"
                    "  zone_id: $json.zone_id || $env.CASTUO_ZONE_ID,\n"
                    "  plant_type: $json.tipo_planta,\n"
                    "  planting_date: $json.fecha_siembra,\n"
                    "  growth_stage: $json.etapa_crecimiento,\n"
                    "  quantity: Number($json.cantidad_plantas),\n"
                    "  status: 'active',\n"
                    "  metadata: { nombre_cultivo: $json.nombre_cultivo, tipo_cultivo: $json.tipo_cultivo, "
                    "variedad: $json.variedad, source: 'n8n' }\n"
                    "} }}"
                ),
            },
        )

    # --- HTTP: cosecha ---
    if "Registrar Cosecha en CASTÚO" in by_name:
        _set_params(
            by_name["Registrar Cosecha en CASTÚO"],
            {
                "method": "PUT",
                "url": (
                    "={{ ($env.CASTUO_BASE_URL || 'http://api:8000').replace(/\\/$/, '') + "
                    "'/hydroponics-saas/crops/' + $json.crop_id_final + '/harvest' }}"
                ),
                "sendHeaders": True,
                "headerParameters": {
                    "parameters": [
                        {"name": "X-API-KEY", "value": api_key},
                        {"name": "Content-Type", "value": "application/json"},
                    ]
                },
                "sendBody": True,
                "specifyBody": "json",
                "jsonBody": (
                    "={{ {\n"
                    "  harvest_date: ($json.fecha_cosecha && String($json.fecha_cosecha).length <= 10) "
                    "? ($json.fecha_cosecha + 'T12:00:00Z') : $json.fecha_cosecha,\n"
                    "  weight: Number($json.peso_total),\n"
                    "  quality: ({ Excelente: 'optimal', Buena: 'good', Regular: 'poor', Deficiente: 'poor' })"
                    "[$json.calidad] || 'good',\n"
                    "  notes: $json.observaciones || '',\n"
                    "  zone_id: $env.CASTUO_ZONE_ID\n"
                    "} }}"
                ),
            },
        )

    # --- HTTP: Slack vía CASTÚO ---
    if "Enviar Alerta Slack CASTÚO" in by_name:
        _set_params(
            by_name["Enviar Alerta Slack CASTÚO"],
            {
                "method": "POST",
                "url": url_slack,
                "sendHeaders": True,
                "headerParameters": {
                    "parameters": [
                        {"name": "Content-Type", "value": "application/json"},
                    ]
                },
                "sendBody": True,
                "specifyBody": "json",
                "jsonBody": "={{ { channel: '#hidroponia', message: $json.message } }}",
            },
        )
    if "Notificar Error a CASTÚO" in by_name:
        _set_params(
            by_name["Notificar Error a CASTÚO"],
            {
                "method": "POST",
                "url": url_slack,
                "sendHeaders": True,
                "headerParameters": {
                    "parameters": [
                        {"name": "Content-Type", "value": "application/json"},
                    ]
                },
                "sendBody": True,
                "specifyBody": "json",
                "jsonBody": (
                    "={{ { channel: '#system-errors', "
                    "message: 'API CASTUO: ' + ($json.error_message || 'error') } }}"
                ),
            },
        )

    # --- Preparar Análisis para BD: listas JSON para CASTÚO + fallback parser ---
    if "Preparar Análisis para BD" in by_name:
        _set_params(
            by_name["Preparar Análisis para BD"],
            {
                "assignments": {
                    "assignments": [
                        {
                            "id": "id-1",
                            "name": "fecha_analisis",
                            "value": "={{ $json.fecha_reporte }}",
                            "type": "string",
                        },
                        {
                            "id": "id-2",
                            "name": "estado_general",
                            "value": "={{ $json.estado_general }}",
                            "type": "string",
                        },
                        {
                            "id": "id-3",
                            "name": "issues",
                            "value": (
                                "={{ JSON.parse($json.problemas || '[]').map(p => "
                                "({ type: 'issue', message: String(p) }) ) }}"
                            ),
                            "type": "array",
                        },
                        {
                            "id": "id-4",
                            "name": "recommendations",
                            "value": "={{ JSON.parse($json.recomendaciones || '[]') }}",
                            "type": "array",
                        },
                        {
                            "id": "id-5",
                            "name": "trends",
                            "value": (
                                "={{ $json.tendencias ? "
                                "[{ type: 'trend', description: String($json.tendencias) }] : [] }}"
                            ),
                            "type": "array",
                        },
                        {
                            "id": "id-6",
                            "name": "prioridad",
                            "value": "={{ $json.prioridad }}",
                            "type": "string",
                        },
                    ]
                },
                "options": {},
            },
        )

    # --- Preparar Datos Cultivos: crop_id + zone_id ---
    if "Preparar Datos Cultivos" in by_name:
        assigns = by_name["Preparar Datos Cultivos"].setdefault("parameters", {}).setdefault(
            "assignments", {}
        ).setdefault("assignments", [])
        names = {a.get("name") for a in assigns}
        if "crop_id" not in names:
            assigns.append(
                {
                    "id": "id-cropid",
                    "name": "crop_id",
                    "value": (
                        "={{ 'crop_' + String($env.CASTUO_ZONE_ID || 'zone').replace(/[^a-zA-Z0-9]+/g, '_') + '_' + "
                        "String($json.tipo_planta || 'plant').toLowerCase().replace(/[^a-z0-9]+/g, '_') + '_' + "
                        "new Date($json.fecha_siembra).getTime() }}"
                    ),
                    "type": "string",
                }
            )
        if "zone_id" not in names:
            assigns.append(
                {
                    "id": "id-zone",
                    "name": "zone_id",
                    "value": "={{ $env.CASTUO_ZONE_ID }}",
                    "type": "string",
                }
            )

    # --- Preparar Datos Sensores: zone_id por defecto desde env ---
    if "Preparar Datos Sensores" in by_name:
        for a in (
            by_name["Preparar Datos Sensores"]
            .setdefault("parameters", {})
            .setdefault("assignments", {})
            .setdefault("assignments", [])
        ):
            if a.get("name") == "zone_id":
                a["value"] = "={{ $json.zone_id || $env.CASTUO_ZONE_ID || 'zone_default' }}"
                break

    # --- Mostrar crop_id en formulario cosecha: texto ayuda en flujo ---
    # El operador debe pegar el crop_id devuelto por CASTÚO o generado en Preparar Datos Cultivos.

    # --- Conexiones: CASTÚO recibe items de Set, no de Data Table ---
    if all(
        n in by_name for n in ("Preparar Datos Sensores", "Enviar Lecturas a CASTÚO", "Guardar Lecturas Sensores")
    ):
        _conn_add(connections, "Preparar Datos Sensores", "Enviar Lecturas a CASTÚO")
        _conn_add(
            connections,
            "Guardar Lecturas Sensores",
            remove_to="Enviar Lecturas a CASTÚO",
        )

    if all(
        n in by_name for n in ("Preparar Datos Cultivos", "Registrar Cultivo en CASTÚO", "Guardar Cultivos")
    ):
        _conn_add(connections, "Preparar Datos Cultivos", "Registrar Cultivo en CASTÚO")
        _conn_add(
            connections,
            "Guardar Cultivos",
            remove_to="Registrar Cultivo en CASTÚO",
        )

    if all(
        n in by_name for n in ("Preparar Datos Cosechas", "Registrar Cosecha en CASTÚO", "Guardar Cosechas")
    ):
        _conn_add(connections, "Preparar Datos Cosechas", "Registrar Cosecha en CASTÚO")
        _conn_add(
            connections,
            "Guardar Cosechas",
            remove_to="Registrar Cosecha en CASTÚO",
        )

    # --- Tool LangChain: URL base api + misma X-API-KEY que el resto ---
    if "Tool API CASTÚO" in by_name:
        tp = by_name["Tool API CASTÚO"].setdefault("parameters", {})
        tp["url"] = (
            "={{ $fromAI('endpoint', 'URL completa del endpoint CASTÚO', 'string', "
            "($env.CASTUO_BASE_URL || 'http://api:8000').replace(/\\/$/, '') + '/hydroponics-saas/sensor-readings') }}"
        )
        for h in tp.get("headerParameters", {}).get("parameters", []):
            if h.get("name") == "X-API-KEY":
                h["value"] = api_key
                break

    return w


def main() -> int:
    ap = argparse.ArgumentParser(description="Parchea workflow n8n para CASTÚO hydroponics-saas")
    ap.add_argument("input", help="JSON exportado desde n8n")
    ap.add_argument("-o", "--output", help="Ruta de salida (default: sobrescribe input)")
    args = ap.parse_args()
    path = args.input
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    fixed = patch(data)
    out = args.output or path
    with open(out, "w", encoding="utf-8") as f:
        json.dump(fixed, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"OK -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
