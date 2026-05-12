# -*- coding: utf-8 -*-
"""
Prueba de la interfaz master SABIONDA: visión general, versiones, producción, misiones, informes.
Ejecutar desde la raíz: python scripts/test_sabionda_master.py
"""
from __future__ import print_function

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import json
from interfaces.sabionda_master_interface import SabiondaMasterInterface


def test_sabionda_master():
    sabionda = SabiondaMasterInterface()

    # 1. Visión general
    print("Obteniendo vision general del sistema...")
    overview = sabionda.get_system_overview()
    print(json.dumps({
        "perfiles_activos": overview["profiles"]["active_sessions"],
        "versiones": overview["profiles"]["available_versions"],
        "drones_fabricados": overview["production"]["drones_manufactured"],
        "misiones_europeas": overview["european_network"]["total_missions"],
        "tasa_exito": str(overview["european_network"]["success_rate"]) + "%",
    }, indent=2))

    # 2. Versiones
    print("\nGestionando versiones...")
    versions = sabionda.manage_versions("list")
    print("Versiones disponibles (%d):" % len(versions["versions"]))
    for v in versions["versions"][:3]:
        print("  -", v["version_id"], "(%s)" % v.get("type", ""))

    new_version = sabionda.manage_versions(
        action="create",
        version_id="FARMER_ADVANCED",
        config={
            "base_version": "FARMER",
            "tone": "extremeno_technical",
            "allowed_modules": ["iot", "alerts", "basic_analytics", "production_read"],
            "restrictions": {"blockchain_write": False, "security_admin": False, "ai_autonomy": 40},
            "max_tokens": 48000,
            "response_style": "detailed_simple",
            "custom_templates": {
                "crop_alert": "ALERTA AVANZADA {farmer_name} - Lote: {batch_id}\n{details}\n{recommendations}",
            },
        },
    )
    print("Nueva version creada:", new_version["status"])

    # 3. Producción
    print("\nMonitoreando produccion local...")
    production_data = sabionda.monitor_production()
    print(json.dumps({
        "drones_fabricados": production_data["production_stats"].get("total_drones_manufactured", 0),
        "impacto_economico": "EUR " + str(production_data["local_impact"]["economic_impact_eur"]),
        "empleos_creados": production_data["local_impact"]["jobs_created"],
        "co2_ahorrado": str(production_data["local_impact"]["co2_saved_kg"]) + " kg",
    }, indent=2))

    # 4. Orden de fabricación
    print("\nCreando orden de fabricacion (10 PrecisionSprayer X1)...")
    order_result = sabionda.create_drone_manufacturing_order(
        product_id="CASTUO-DRONE-SPRAYER-001",
        quantity=10,
    )
    print(json.dumps({
        "orden_creada": order_result["order"]["order_id"],
        "productos": order_result["order"]["quantity"],
        "impacto_local": {
            "empleos": order_result["local_impact"]["jobs_created"],
            "economico": "EUR " + str(order_result["local_impact"]["economic_impact"]),
            "co2": str(order_result["local_impact"]["co2_saved"]) + " kg",
        },
    }, indent=2))

    # 5. Misión europea
    print("\nGestionando mision europea (Espana -> Portugal)...")
    mission_proposal = sabionda.manage_european_missions(
        action="propose",
        params={
            "origin_operator_id": "ES-CASTUO-001",
            "destination_country": "Portugal",
            "purpose": "Fumigacion vinedos bioestimulantes",
            "payload": {
                "required_drone_type": "PrecisionSprayer X1",
                "payload_capacity_kg": 10,
                "required_certifications": ["ISO 9001", "EcoCert"],
                "area_ha": 50,
            },
            "start_location": {"lat": 39.4769, "lon": -6.3706},
            "end_location": {"lat": 37.0222, "lon": -7.9289},
        },
    )
    print(json.dumps({
        "mision_propuesta": mission_proposal.get("mission_id"),
        "operador_destino": mission_proposal.get("destination_operator"),
        "distancia_km": mission_proposal.get("route_summary", {}).get("distance_km"),
    }, indent=2))

    # 6. Informe estratégico
    print("\nGenerando informe estrategico (produccion)...")
    report = sabionda.generate_strategic_report(focus_area="production")
    print(json.dumps({
        "titulo": report.get("title"),
        "destacados": report.get("highlights"),
        "recomendaciones": (report.get("recommendations") or [])[:2],
    }, indent=2))

    # 7. Acción estratégica
    print("\nEjecutando accion estrategica (expansion a Francia)...")
    expansion = sabionda.execute_strategic_action(
        action_type="expand_market",
        params={
            "country": "France",
            "expected_revenue": 2000000,
            "initial_investment": 500000,
            "target_products": ["CASTUO-DRONE-MULTISPECTRAL-001", "CASTUO-DRONE-SPRAYER-001"],
        },
    )
    print(json.dumps({
        "accion": expansion.get("action"),
        "pais_objetivo": expansion.get("target_country"),
        "impacto_estimado": expansion.get("estimated_impact"),
        "proximos_pasos": expansion.get("next_steps", []),
    }, indent=2))

    print("\nOK: Pruebas de Sabionda Master completadas.")


if __name__ == "__main__":
    test_sabionda_master()
