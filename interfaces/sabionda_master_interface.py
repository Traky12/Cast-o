# -*- coding: utf-8 -*-
"""
Interfaz principal para SABIONDA_MASTER_LANDUM_PROFESIONAL_CASTUO.
Gestión de versiones, producción local, misiones europeas, seguridad y decisiones estratégicas.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import sys
from pathlib import Path

_root = Path(__file__).resolve().parents[1]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from blockchain.gaia_chain import GaiaChainClient
from core.profile_engine import ProfileManager, ProfileType
from core.audit_system import AuditSystem
from profiles.sabionda_version_manager import SabiondaVersionManager
from messaging.european_drone_network import EuropeanDroneNetwork
from messaging.european_drone_coordinator import EuropeanDroneCoordinator
from production.local_production_system import LocalProductionSystem
from production.drone_traceability import DroneTraceabilitySystem


class SabiondaMasterInterface:
    """
    Interfaz principal para SABIONDA_MASTER_LANDUM_PROFESIONAL_CASTUO.
    Gestión de versiones, producción local, misiones europeas, seguridad y decisiones estratégicas.
    """

    def __init__(self, gaiachain_client: Optional[GaiaChainClient] = None) -> None:
        self.gaiachain = gaiachain_client or GaiaChainClient()
        self.profile_manager = ProfileManager(gaiachain_client=self.gaiachain)
        self.version_manager = SabiondaVersionManager(self.profile_manager)
        self.audit_system = AuditSystem(gaiachain_client=self.gaiachain)
        self.drone_network = EuropeanDroneNetwork(gaiachain_client=self.gaiachain)
        self.drone_coordinator = EuropeanDroneCoordinator(self.drone_network, self.gaiachain)
        self.production_system = LocalProductionSystem(gaiachain_client=self.gaiachain)
        self.traceability = DroneTraceabilitySystem(gaiachain_client=self.gaiachain)

    def get_system_overview(self) -> Dict[str, Any]:
        """Visión general del sistema."""
        trace_stats = self.traceability.get_production_stats()
        network_stats = self.drone_coordinator.get_network_stats()
        countries_involved = set()
        for m in self.drone_coordinator.active_missions.values():
            countries_involved.add(m.origin_country)
            countries_involved.add(m.destination_country)
        recent_alerts = self.audit_system.get_security_alerts(days=1)
        return {
            "timestamp": datetime.now().isoformat(),
            "profiles": {
                "active_sessions": len(self.profile_manager.active_sessions),
                "available_versions": len(self.version_manager.list_versions()),
                "custom_versions": len(self.version_manager.custom_versions),
            },
            "production": {
                "drones_manufactured": trace_stats.get("total_drones_manufactured", 0),
                "local_content_avg": trace_stats.get("local_content_avg", 0),
                "co2_saved_kg": trace_stats.get("co2_saved_kg", 0),
            },
            "european_network": {
                "total_missions": network_stats.get("total_missions", 0),
                "success_rate": network_stats.get("success_rate", 0),
                "countries_involved": len(countries_involved),
            },
            "security": {
                "active_alerts": len(recent_alerts),
                "auth_attempts": len(self.profile_manager.active_sessions),
            },
        }

    def manage_versions(
        self,
        action: str,
        version_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Gestiona versiones de perfiles (list, create, update, delete, get)."""
        if action == "list":
            return {"versions": self.version_manager.list_versions()}
        if action == "create":
            if not version_id or not config:
                return {"status": "error", "message": "Faltan parámetros"}
            base = config.get("base_version")
            if not base:
                return {"status": "error", "message": "Falta base_version en config"}
            success = self.version_manager.create_version(version_id, base, config)
            return {"status": "success" if success else "error"}
        if action == "update":
            if not version_id or not config:
                return {"status": "error", "message": "Faltan parámetros"}
            success = self.version_manager.update_version(version_id, config)
            return {"status": "success" if success else "error"}
        if action == "delete":
            if not version_id:
                return {"status": "error", "message": "Falta version_id"}
            success = self.version_manager.delete_version(version_id)
            return {"status": "success" if success else "error"}
        if action == "get":
            if not version_id:
                return {"status": "error", "message": "Falta version_id"}
            version = self.version_manager.get_version(version_id)
            return {"status": "success", "version": version} if version else {"status": "error"}
        return {"status": "error", "message": f"Acción no soportada: {action}"}

    def monitor_production(self, time_range: str = "7d") -> Dict[str, Any]:
        """Monitorea el sistema de producción local."""
        prod_stats = self.production_system.get_production_stats()
        trace_stats = self.traceability.get_production_stats()
        production_stats = {
            **prod_stats,
            "total_drones_manufactured": trace_stats.get("total_drones_manufactured", 0),
            "products_manufactured": trace_stats.get("products_manufactured", {}),
            "local_content_avg": trace_stats.get("local_content_avg", 0),
            "co2_saved_kg": trace_stats.get("co2_saved_kg", 0),
        }
        return {
            "production_stats": production_stats,
            "recent_manufacturing": trace_stats.get("recent_manufacturing", []),
            "inventory_levels": self.production_system.inventory,
            "local_impact": {
                "jobs_created": prod_stats.get("jobs_created", 0),
                "economic_impact_eur": prod_stats.get("economic_impact", 0),
                "co2_saved_kg": trace_stats.get("co2_saved_kg", 0),
            },
        }

    def manage_european_missions(
        self,
        action: str,
        mission_id: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Gestiona misiones transfronterizas (list, propose, accept, start, complete, get)."""
        params = params or {}
        if action == "list":
            return {
                "missions": self.drone_coordinator.get_network_stats(),
                "active_missions": len(self.drone_coordinator.active_missions),
            }
        if action == "propose":
            return self.drone_coordinator.propose_mission(
                origin_operator_id=params["origin_operator_id"],
                destination_country=params["destination_country"],
                purpose=params["purpose"],
                payload=params.get("payload", {}),
                start_location=params["start_location"],
                end_location=params["end_location"],
            )
        if action == "accept":
            if not mission_id or "destination_operator_id" not in params:
                return {"status": "error", "message": "Faltan parámetros"}
            return self.drone_coordinator.accept_mission(
                mission_id, params["destination_operator_id"], params.get("terms", {})
            )
        if action == "start":
            if not mission_id or "operator_id" not in params:
                return {"status": "error", "message": "Faltan parámetros"}
            return self.drone_coordinator.start_mission(mission_id, params["operator_id"])
        if action == "complete":
            if not mission_id or "operator_id" not in params or "telemetry_data" not in params:
                return {"status": "error", "message": "Faltan parámetros"}
            return self.drone_coordinator.complete_mission(
                mission_id, params["operator_id"], params["telemetry_data"]
            )
        if action == "get":
            if not mission_id:
                return {"status": "error", "message": "Falta mission_id"}
            return self.drone_coordinator.get_mission_status(mission_id)
        return {"status": "error", "message": f"Acción no soportada: {action}"}

    def security_dashboard(self) -> Dict[str, Any]:
        """Resumen del estado de seguridad del sistema."""
        sessions = []
        for session_id, session in self.profile_manager.active_sessions.items():
            profile = session.get("profile")
            profile_name = profile.profile_type.name if profile and hasattr(profile, "profile_type") else "unknown"
            sessions.append({
                "session_id": session_id,
                "user_id": session.get("user_id", ""),
                "profile": profile_name,
                "start_time": session.get("created_at", ""),
                "last_activity": session.get("last_activity", ""),
            })
        auth_count = 0
        cutoff = datetime.now() - timedelta(days=1)
        for log in getattr(self.audit_system, "local_logs", []):
            ts = log.get("timestamp", "")
            if not ts:
                continue
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "")[:19])
            except (ValueError, TypeError):
                continue
            if dt > cutoff and log.get("action", "").lower() in ("login", "authenticate", "auth"):
                auth_count += 1
        return {
            "active_sessions": sessions,
            "recent_alerts": self.audit_system.get_security_alerts(days=1),
            "auth_attempts_last_24h": auth_count,
            "blockchain_status": {
                "last_block": self.gaiachain.get_last_block(),
                "pending_transactions": self.gaiachain.get_pending_transactions(),
                "consensus_health": "healthy",
            },
        }

    def create_drone_manufacturing_order(self, product_id: str, quantity: int) -> Dict[str, Any]:
        """Crea una orden de fabricación de drones."""
        return self.production_system.create_production_order(product_id, quantity)

    def track_drone(self, drone_id: str) -> Dict[str, Any]:
        """Rastrear un dron desde fabricación hasta uso actual."""
        record = self.traceability.verify_drone(drone_id)
        if record.get("status") != "authentic":
            return {"status": "error", "message": f"Dron {drone_id} no encontrado o inválido"}
        missions = [
            m for m in self.drone_coordinator.active_missions.values()
            if m.payload.get("drone_id") == drone_id
        ]
        mission_list = []
        for m in missions:
            mission_list.append({
                "mission_id": m.mission_id,
                "purpose": m.purpose,
                "status": m.status,
                "start_time": m.start_time,
                "end_time": getattr(m, "actual_end_time", None) or m.end_time,
                "operator_id": m.origin_operator,
            })
        current_loc = None
        if missions and missions[-1].telemetry_data:
            route = missions[-1].telemetry_data.get("route", [])
            if route:
                current_loc = route[-1]
        manufacturing_records = self.traceability.get_manufacturing_records()
        return {
            "status": "success",
            "drone_info": {
                "drone_id": drone_id,
                "product_name": record.get("product_name"),
                "manufacturing_date": record.get("manufacturing_date"),
                "local_content": record.get("local_content"),
                "compliance": record.get("compliance"),
            },
            "manufacturing_details": manufacturing_records.get(drone_id),
            "mission_history": mission_list,
            "current_location": current_loc,
            "certificate": record.get("certificate"),
        }

    def generate_strategic_report(self, focus_area: str = "production") -> Dict[str, Any]:
        """Genera un informe estratégico (production, european_network, security, financial)."""
        if focus_area == "production":
            production_data = self.monitor_production()
            stats = production_data["production_stats"]
            products = stats.get("products_manufactured", {})
            low_production = [pid for pid, count in products.items() if count < 50]
            recommendations = [f"Aumentar producción de {pid} en un 20% (demanda alta en Europa)" for pid in low_production[:3]]
            return {
                "title": "Informe Estratégico: Producción Local (Extremadura)",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "highlights": {
                    "drones_manufactured": stats.get("total_drones_manufactured", 0),
                    "local_content": f"{stats.get('local_content_avg', 0) * 100:.1f}%",
                    "economic_impact": f"€{stats.get('economic_impact', 0):,.0f}",
                    "co2_saved": f"{stats.get('co2_saved_kg', 0):,.0f} kg",
                },
                "recommendations": recommendations or ["Mantener niveles actuales de producción."],
                "detailed_data": production_data,
            }
        if focus_area == "european_network":
            network_data = self.drone_coordinator.get_network_stats()
            return {
                "title": "Informe Estratégico: Red Europea de Drones",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "highlights": {
                    "total_missions": network_data.get("total_missions", 0),
                    "success_rate": f"{network_data.get('success_rate', 0):.1f}%",
                    "countries_involved": network_data.get("total_operators_involved", 0),
                    "total_distance": f"{network_data.get('total_distance_km', 0):,.0f} km",
                },
                "recommendations": [
                    "Establecer acuerdos preferenciales con operadores en Francia (alta demanda).",
                    "Optimizar rutas entre España y Portugal para reducir costes.",
                    "Invertir en drones con mayor autonomía para misiones >200km.",
                ],
                "detailed_data": network_data,
            }
        if focus_area == "security":
            security_data = self.security_dashboard()
            return {
                "title": "Informe Estratégico: Seguridad del Sistema",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "highlights": {
                    "active_sessions": len(security_data.get("active_sessions", [])),
                    "recent_alerts": len(security_data.get("recent_alerts", [])),
                    "auth_attempts": security_data.get("auth_attempts_last_24h", 0),
                    "blockchain_status": security_data.get("blockchain_status", {}).get("consensus_health", "unknown"),
                },
                "recommendations": [
                    "Revisar sesiones activas con más de 8 horas de duración.",
                    "Actualizar certificados de seguridad en 30 días.",
                    "Auditar acceso a módulos críticos (blockchain, security).",
                ],
                "detailed_data": security_data,
            }
        if focus_area == "financial":
            revenue = {
                "drone_sales": 12_000_000,
                "saas_subscriptions": 8_736_000,
                "certifications": 2_000_000,
                "carbon_credits": 300_000,
                "training": 1_000_000,
                "licensing": 3_000_000,
                "exports": 5_000_000,
            }
            costs = {"production": 7_000_000, "rnd": 3_000_000, "operations": 2_000_000, "marketing": 1_000_000}
            total_rev = sum(revenue.values())
            total_cost = sum(costs.values())
            return {
                "title": "Informe Estratégico: Desempeño Financiero (2026)",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "highlights": {
                    "total_revenue": f"€{total_rev:,}",
                    "total_costs": f"€{total_cost:,}",
                    "gross_profit": f"€{total_rev - total_cost:,}",
                    "profit_margin": f"{(total_rev - total_cost) / total_rev * 100:.1f}%",
                },
                "recommendations": [
                    "Invertir en automatización para reducir costes operativos.",
                    "Explorar nuevos mercados en América Latina (potencial €5M/año).",
                    "Optimizar cadena de suministro para reducir costes de producción.",
                ],
                "detailed_data": {
                    "revenue_by_stream": revenue,
                    "costs_by_area": costs,
                },
            }
        return {"status": "error", "message": f"Área de enfoque no soportada: {focus_area}"}

    def execute_strategic_action(self, action_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta una acción estratégica (create_version, launch_product, expand_market, etc.)."""
        if action_type == "create_version":
            return self.manage_versions(
                "create",
                version_id=params.get("version_id"),
                config=params.get("config"),
            )
        if action_type == "launch_product":
            return self.production_system.optimize_production_plan(
                params.get("product_id", ""),
                params.get("quantity", 1),
                params.get("months", 6),
            )
        if action_type == "expand_market":
            return {
                "status": "success",
                "action": "market_expansion_initiated",
                "target_country": params.get("country", ""),
                "estimated_impact": f"€{params.get('expected_revenue', 1_000_000):,} en 12 meses",
                "next_steps": [
                    f"Establecer alianza con operador local en {params.get('country', '')}",
                    "Adaptar productos a normativas locales",
                    "Lanzar campaña de marketing",
                ],
            }
        if action_type == "security_audit":
            return {
                "status": "success",
                "action": "security_audit_initiated",
                "scope": params.get("scope", "full_system"),
                "estimated_duration": "7 días",
                "audit_id": f"AUDIT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            }
        if action_type == "production_optimization":
            return self.production_system.optimize_production_plan(
                params.get("product_id", ""),
                params.get("quantity", 1),
                params.get("months", 6),
            )
        return {"status": "error", "message": f"Acción no soportada: {action_type}"}


if __name__ == "__main__":
    sabionda_master = SabiondaMasterInterface()
    print("System overview:")
    overview = sabionda_master.get_system_overview()
    print(json.dumps({
        "perfiles_activos": overview["profiles"]["active_sessions"],
        "versiones": overview["profiles"]["available_versions"],
        "drones_fabricados": overview["production"]["drones_manufactured"],
        "misiones_europeas": overview["european_network"]["total_missions"],
    }, indent=2, ensure_ascii=False))
    versions = sabionda_master.manage_versions("list")
    print("Versiones:", len(versions.get("versions", [])))
    prod = sabionda_master.monitor_production()
    print("Produccion local_content_avg:", prod["production_stats"].get("local_content_avg"))
    report = sabionda_master.generate_strategic_report("production")
    print("Report title:", report.get("title"))
