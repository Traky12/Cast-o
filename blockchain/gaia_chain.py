# -*- coding: utf-8 -*-
"""
GaiaChain — Blockchain de trazabilidad CASTUO (UE/España).
Cumplimiento: trazabilidad inmutable, auditoría, integración con RD 903/2025 y AEMPS.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
import hashlib
import logging
import os

try:
    import requests
except ImportError:
    requests = None  # type: ignore

logger = logging.getLogger(__name__)


class GaiaChainClient:
    """Cliente stub para GaiaChain (trazabilidad cáñamo industrial, materiales, energía)."""

    def __init__(self, rpc_url: Optional[str] = None):
        self.rpc_url = rpc_url or ""
        self._tx_log: List[Dict] = []

    def _tx_id(self, prefix: str, *parts: Any) -> str:
        data = f"gaia-{prefix}-" + "-".join(str(p) for p in parts) + datetime.now().isoformat()
        return hashlib.sha256(data.encode()).hexdigest()[:32]

    def log_action(self, action: Dict[str, Any]) -> str:
        """Registra una acción (refrigeración, optimización luz, etc.) en GaiaChain."""
        tx = self._tx_id("action", action.get("greenhouse_id", ""), action.get("action", ""))
        self._tx_log.append({"type": "action", "tx": tx, "data": action})
        logger.info("GaiaChain action: %s", tx)
        return tx

    def register_harvest(self, yield_data: Dict[str, Any]) -> str:
        """Registra cosecha (invernadero, torre, kg, energía, CO₂ ahorrado)."""
        tx = self._tx_id("harvest", yield_data.get("greenhouse_id"), yield_data.get("tower_id"))
        self._tx_log.append({"type": "harvest", "tx": tx, "data": yield_data})
        return tx

    def register_processing(self, processing_data: Dict[str, Any]) -> str:
        """Registra procesamiento (biomasa → fibra, CBD, semillas, residuos)."""
        tx = self._tx_id("processing", processing_data.get("greenhouse_id"), processing_data.get("input_kg"))
        self._tx_log.append({"type": "processing", "tx": tx, "data": processing_data})
        return tx

    def register_waste_processing(self, waste_data: Dict[str, Any]) -> str:
        """Registra procesamiento de residuos (biogás/compost)."""
        tx = self._tx_id("waste", waste_data.get("input_waste_kg"))
        self._tx_log.append({"type": "waste", "tx": tx, "data": waste_data})
        return tx

    def register_sale(self, sale_data: Dict[str, Any]) -> str:
        """Registra venta de producto (tipo, kg, comprador)."""
        tx = self._tx_id("sale", sale_data.get("product_type"), sale_data.get("buyer_id"))
        self._tx_log.append({"type": "sale", "tx": tx, "data": sale_data})
        return tx

    def log_sensor_data(self, data: Dict[str, Any]) -> str:
        """Registra datos de sensores (invernadero, timestamp, sensores, energía)."""
        tx = self._tx_id("sensor", data.get("greenhouse_id"))
        self._tx_log.append({"type": "sensor", "tx": tx, "data": data})
        return tx

    def log_anomaly(self, anomaly_data: Dict[str, Any]) -> str:
        """Registra anomalía detectada (Sentinel)."""
        tx = self._tx_id("anomaly", anomaly_data.get("greenhouse_id"), anomaly_data.get("anomaly", {}).get("type", ""))
        self._tx_log.append({"type": "anomaly", "tx": tx, "data": anomaly_data})
        return tx

    def log_energy_optimization(self, data: Dict[str, Any]) -> str:
        """Registra optimización energética."""
        tx = self._tx_id("energy", data.get("greenhouse_id"))
        self._tx_log.append({"type": "energy", "tx": tx, "data": data})
        return tx

    def register_material_production(self, data: Dict[str, Any]) -> str:
        """Registra producción de material compuesto."""
        tx = self._tx_id("material", data.get("material_type"), data.get("kg_produced"))
        self._tx_log.append({"type": "material_production", "tx": tx, "data": data})
        return tx

    def register_material_sale(self, data: Dict[str, Any]) -> str:
        """Registra venta de material compuesto."""
        tx = self._tx_id("material_sale", data.get("buyer_id"))
        self._tx_log.append({"type": "material_sale", "tx": tx, "data": data})
        return tx

    def register_carbon_sale(self, data: Dict[str, Any]) -> str:
        """Registra venta de créditos de carbono."""
        tx = self._tx_id("carbon_sale", data.get("credits_kg"))
        self._tx_log.append({"type": "carbon_sale", "tx": tx, "data": data})
        return tx

    def register_compliance_report(self, report: Dict[str, Any]) -> str:
        """Registra informe de cumplimiento (RD 903/2025)."""
        tx = self._tx_id("compliance", report.get("facility_id", ""))
        self._tx_log.append({"type": "compliance", "tx": tx, "data": report})
        return tx

    def register_cannabis_batch(self, batch_data: Dict[str, Any]) -> str:
        """Registra lote de cannabis (cumplimiento RD 903/2025)."""
        tx = self._tx_id("batch", batch_data.get("batch_id", ""))
        self._tx_log.append({"type": "batch", "tx": tx, "data": batch_data})
        return tx

    def log_physical_access(self, access_log: Dict[str, Any]) -> str:
        """Registra acceso físico (control biométrico, RD 903/2025)."""
        tx = self._tx_id("physical", access_log.get("user", ""), access_log.get("location", ""))
        self._tx_log.append({"type": "physical_access", "tx": tx, "data": access_log})
        return tx

    def log_security_alert(self, alert_data: Dict[str, Any]) -> str:
        """Registra alerta de seguridad (Sentinel v5, IDS/EDR)."""
        tx = self._tx_id("security", alert_data.get("type", ""), alert_data.get("node_id", ""))
        self._tx_log.append({"type": "security_alert", "tx": tx, "data": alert_data})
        logger.warning("GaiaChain security_alert: %s", tx)
        return tx

    def register_verra_project(self, project_data: Dict[str, Any]) -> str:
        """Registra proyecto Verra en GaiaChain (créditos de carbono)."""
        tx = self._tx_id("verra_project", project_data.get("id", ""))
        self._tx_log.append({"type": "verra_project", "tx": tx, "data": project_data})
        return tx

    def register_verra_report(self, report_data: Dict[str, Any]) -> str:
        """Registra informe Verra en GaiaChain."""
        tx = self._tx_id("verra_report", report_data.get("verra_id", ""))
        self._tx_log.append({"type": "verra_report", "tx": tx, "data": report_data})
        return tx

    def log_data_processing(self, metadata: Dict[str, Any]) -> str:
        """Registra procesamiento de datos (ej. cifrado homomórfico)."""
        tx = self._tx_id("data_processing", metadata.get("batch_id", ""), metadata.get("processing_type", ""))
        self._tx_log.append({"type": "data_processing", "tx": tx, "data": metadata})
        return tx

    def log_tokenization(self, data: Dict[str, Any]) -> str:
        """Registra creación o uso de tokens (tokenización GDPR)."""
        tx = self._tx_id("tokenization", data.get("token", "")[:16], data.get("action", ""))
        self._tx_log.append({"type": "tokenization", "tx": tx, "data": data})
        return tx

    def log_security_event(self, event_data: Dict[str, Any]) -> str:
        """Registra evento de seguridad (ej. normalización tras alarma sísmica)."""
        tx = self._tx_id("security_event", event_data.get("sensor", ""), event_data.get("status", ""))
        self._tx_log.append({"type": "security_event", "tx": tx, "data": event_data})
        return tx

    def log_academy_event(self, event_data: Dict[str, Any]) -> str:
        """Registra evento de formación (matrícula, módulo completado)."""
        tx = self._tx_id("academy", event_data.get("user_id"), event_data.get("event", ""))
        self._tx_log.append({"type": "academy", "tx": tx, "data": event_data})
        return tx

    def log_certificate(self, cert_data: Dict[str, Any]) -> str:
        """Registra emisión de certificado (CASTUO Academy)."""
        tx = self._tx_id("certificate", cert_data.get("certificate_id", ""), cert_data.get("user_id", ""))
        self._tx_log.append({"type": "certificate", "tx": tx, "data": cert_data})
        return tx

    def get_certificate(self, certificate_code: str) -> Optional[Dict[str, Any]]:
        """Obtiene datos de certificado por código (verificación)."""
        for e in reversed(self._tx_log):
            if e.get("type") == "certificate" and e.get("data", {}).get("certificate_id") == certificate_code:
                return e.get("data")
        return None

    def log_transaction(self, data: Dict[str, Any]) -> str:
        """Registra transacción (ej. post-cuántica con firma Dilithium)."""
        tx = self._tx_id("tx", data.get("batch_id", ""), data.get("operation", ""))
        self._tx_log.append({"type": "transaction", "tx": tx, "data": data})
        return tx

    def log_security_incident(self, data: Dict[str, Any]) -> str:
        """Registra incidente de seguridad (SOC/TheHive)."""
        tx = self._tx_id("incident", data.get("incident_id", ""), data.get("type", ""))
        self._tx_log.append({"type": "security_incident", "tx": tx, "data": data})
        logger.warning("GaiaChain security_incident: %s", tx)
        return tx

    def log_incident_action(self, data: Dict[str, Any]) -> str:
        """Registra acción ejecutada en un incidente (playbook)."""
        tx = self._tx_id("incident_action", data.get("incident_id", ""), data.get("action", ""))
        self._tx_log.append({"type": "incident_action", "tx": tx, "data": data})
        return tx

    def log_compliance_document(self, data: Dict[str, Any]) -> str:
        """Registra documento de cumplimiento (AEMPS, auditoría)."""
        tx = self._tx_id("compliance_doc", data.get("document_type", ""), data.get("project_id", ""))
        self._tx_log.append({"type": "compliance_document", "tx": tx, "data": data})
        return tx

    def log_hsm_event(self, data: Dict[str, Any]) -> str:
        """Registra evento HSM (generación de claves, firma, cifrado)."""
        tx = self._tx_id("hsm", data.get("event_type", ""), data.get("key_id", ""))
        self._tx_log.append({"type": "hsm_event", "tx": tx, "data": data})
        return tx

    def log_blockchain_event(self, data: Dict[str, Any]) -> str:
        """Registra evento de blockchain post-cuántica (nodo, transacción, bloque)."""
        tx = self._tx_id("blockchain", data.get("event_type", ""), data.get("transaction_id", data.get("node_id", "")))
        self._tx_log.append({"type": "blockchain_event", "tx": tx, "data": data})
        return tx

    def log_production_event(self, data: Dict[str, Any]) -> str:
        """Registra evento de producción (órdenes, inicio/fin fabricación drones)."""
        tx = self._tx_id("production", data.get("event_type", ""), data.get("order_id", ""))
        self._tx_log.append({"type": "production_event", "tx": tx, "data": data})
        return tx

    def log_supply_chain_event(self, data: Dict[str, Any]) -> str:
        """Registra evento de cadena de suministro (pedidos a proveedores)."""
        tx = self._tx_id("supply", data.get("event_type", ""), data.get("order_id", ""))
        self._tx_log.append({"type": "supply_chain_event", "tx": tx, "data": data})
        return tx

    def log_manufacturing_event(self, data: Dict[str, Any]) -> str:
        """Registra fabricación de dron (trazabilidad, componentes, calidad)."""
        tx = self._tx_id("manufacturing", data.get("drone_id", ""), data.get("product_id", ""))
        self._tx_log.append({"type": "manufacturing_event", "tx": tx, "data": data})
        return tx

    def get_manufacturing_record(self, drone_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene registro de fabricación de un dron por ID."""
        for e in reversed(self._tx_log):
            if e.get("type") == "manufacturing_event" and e.get("data", {}).get("drone_id") == drone_id:
                return e.get("data")
        return None

    def log_certificate_event(self, data: Dict[str, Any]) -> str:
        """Registra emisión de certificado (dron, autenticidad)."""
        tx = self._tx_id("cert_event", data.get("certificate_id", ""), data.get("drone_id", ""))
        self._tx_log.append({"type": "certificate_event", "tx": tx, "data": data})
        return tx

    def log_drone_mission(self, data: Dict[str, Any]) -> str:
        """Registra misión de dron (planificación, inicio, fin, telemetría)."""
        tx = self._tx_id("drone_mission", data.get("mission_id", ""), data.get("status", ""))
        self._tx_log.append({"type": "drone_mission", "tx": tx, "data": data})
        return tx

    def get_drone_mission(self, mission_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene datos de misión de dron por ID (último registro)."""
        for e in reversed(self._tx_log):
            if e.get("type") == "drone_mission" and e.get("data", {}).get("mission_id") == mission_id:
                return e.get("data")
        return None

    def log_cross_border_request(self, data: Dict[str, Any]) -> str:
        """Registra solicitud de misión transfronteriza."""
        tx = self._tx_id("cross_border", data.get("request_id", ""), data.get("destination_country", ""))
        self._tx_log.append({"type": "cross_border_request", "tx": tx, "data": data})
        return tx

    def log_profile_activity(self, data: Dict[str, Any]) -> str:
        """Registra actividad de perfil/versión (SABIONDA: cambio de perfil, acceso por tipo de usuario)."""
        tx = self._tx_id("profile", data.get("profile_type", ""), data.get("user_id", ""))
        self._tx_log.append({"type": "profile_activity", "tx": tx, "data": data})
        return tx

    def log_user_session(self, data: Dict[str, Any]) -> str:
        """Registra sesión de usuario (apertura/cierre, perfil, acceso)."""
        tx = self._tx_id("session", data.get("session_id", ""), data.get("user_id", ""))
        self._tx_log.append({"type": "user_session", "tx": tx, "data": data})
        return tx

    def log_profile_update(self, data: Dict[str, Any]) -> str:
        """Registra actualización de configuración de perfil."""
        tx = self._tx_id("profile_update", data.get("profile_id", ""), "")
        self._tx_log.append({"type": "profile_update", "tx": tx, "data": data})
        return tx

    def log_profile_creation(self, data: Dict[str, Any]) -> str:
        """Registra creación de perfil personalizado."""
        tx = self._tx_id("profile_creation", data.get("profile_id", ""), "")
        self._tx_log.append({"type": "profile_creation", "tx": tx, "data": data})
        return tx

    def log_system_interaction(self, data: Dict[str, Any]) -> str:
        """Registra interacción del sistema (auditoría SABIONDA)."""
        tx = self._tx_id("interaction", data.get("session_id", ""), data.get("action", ""))
        self._tx_log.append({"type": "system_interaction", "tx": tx, "data": data})
        return tx

    def log_auth_event(self, data: Dict[str, Any]) -> str:
        """Registra evento de autenticación (login, cierre, sesión)."""
        tx = self._tx_id("auth", data.get("user_id", ""), data.get("status", ""))
        self._tx_log.append({"type": "auth_event", "tx": tx, "data": data})
        return tx

    def log_data_encryption(self, data: Dict[str, Any]) -> str:
        """Registra operación de cifrado de datos (HSM)."""
        tx = self._tx_id("encrypt", data.get("data_hash", "")[:16], data.get("key_label", ""))
        self._tx_log.append({"type": "data_encryption", "tx": tx, "data": data})
        return tx

    def log_data_decryption(self, data: Dict[str, Any]) -> str:
        """Registra operación de descifrado de datos (HSM)."""
        tx = self._tx_id("decrypt", data.get("data_hash", "")[:16], data.get("key_label", ""))
        self._tx_log.append({"type": "data_decryption", "tx": tx, "data": data})
        return tx

    def log_key_generation(self, data: Dict[str, Any]) -> str:
        """Registra generación de claves en HSM."""
        tx = self._tx_id("key_gen", data.get("key_label", ""), data.get("key_type", ""))
        self._tx_log.append({"type": "key_generation", "tx": tx, "data": data})
        return tx

    def log_cross_border_proposal(self, data: Dict[str, Any]) -> str:
        """Registra propuesta de misión transfronteriza."""
        tx = self._tx_id("xb_proposal", data.get("mission_id", ""), data.get("destination_operator", ""))
        self._tx_log.append({"type": "cross_border_proposal", "tx": tx, "data": data})
        return tx

    def log_cross_border_acceptance(self, data: Dict[str, Any]) -> str:
        """Registra aceptación de misión transfronteriza."""
        tx = self._tx_id("xb_accept", data.get("mission_id", ""), data.get("status", ""))
        self._tx_log.append({"type": "cross_border_acceptance", "tx": tx, "data": data})
        return tx

    def log_cross_border_start(self, data: Dict[str, Any]) -> str:
        """Registra inicio de misión transfronteriza."""
        tx = self._tx_id("xb_start", data.get("mission_id", ""), data.get("operator", ""))
        self._tx_log.append({"type": "cross_border_start", "tx": tx, "data": data})
        return tx

    def log_cross_border_completion(self, data: Dict[str, Any]) -> str:
        """Registra completado de misión transfronteriza."""
        tx = self._tx_id("xb_complete", data.get("mission_id", ""), data.get("status", ""))
        self._tx_log.append({"type": "cross_border_completion", "tx": tx, "data": data})
        return tx

    def log_smart_contract(self, data: Dict[str, Any]) -> str:
        """Registra despliegue de smart contract."""
        tx = self._tx_id("contract", data.get("contract_address", "")[:16], data.get("mission_id", ""))
        self._tx_log.append({"type": "smart_contract", "tx": tx, "data": data})
        return tx

    def log_smart_contract_update(self, data: Dict[str, Any]) -> str:
        """Registra actualización de smart contract."""
        tx = self._tx_id("contract_upd", data.get("contract_address", "")[:16], data.get("status", ""))
        self._tx_log.append({"type": "smart_contract_update", "tx": tx, "data": data})
        return tx

    def log_smart_contract_action(self, data: Dict[str, Any]) -> str:
        """Registra acción sobre smart contract (ej: release_funds)."""
        tx = self._tx_id("contract_act", data.get("contract_address", "")[:16], data.get("action", ""))
        self._tx_log.append({"type": "smart_contract_action", "tx": tx, "data": data})
        return tx

    def get_cross_border_mission(self, mission_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene el último registro de misión transfronteriza por ID."""
        for e in reversed(self._tx_log):
            if e.get("type") in ("cross_border_proposal", "cross_border_acceptance", "cross_border_start", "cross_border_completion"):
                if e.get("data", {}).get("mission_id") == mission_id:
                    return e.get("data")
        return None

    def get_smart_contract(self, contract_address: str) -> Optional[Dict[str, Any]]:
        """Obtiene el estado del smart contract por dirección."""
        for e in reversed(self._tx_log):
            if e.get("type") in ("smart_contract", "smart_contract_update", "smart_contract_action"):
                if e.get("data", {}).get("contract_address") == contract_address:
                    return e.get("data")
        return None

    def get_last_block(self) -> Optional[Dict[str, Any]]:
        """Stub: último bloque (para interfaz master)."""
        return {"block_id": "gaia-latest", "timestamp": datetime.now().isoformat()}

    def get_pending_transactions(self) -> List[Dict]:
        """Stub: transacciones pendientes (para interfaz master)."""
        return []

    def log_iot_data(self, data: Dict[str, Any]) -> str:
        """Registra datos de sensores IoT (bandejas hidropónicas, tray_id, sensors, metadata)."""
        tx = self._tx_id("iot_data", data.get("tray_id", ""), data.get("timestamp", "")[:19].replace(":", ""))
        self._tx_log.append({"type": "iot_data", "tx": tx, "data": data})
        return tx

    def log_iot_auth(self, data: Dict[str, Any]) -> str:
        """Registra autenticación de dispositivo IoT (tray_id, session_id, device_type)."""
        tx = self._tx_id("iot_auth", data.get("tray_id", ""), data.get("session_id", ""))
        self._tx_log.append({"type": "iot_auth", "tx": tx, "data": data})
        return tx

    def log_iot_command(self, data: Dict[str, Any]) -> str:
        """Registra comando enviado a dispositivo IoT (tray_id, commands)."""
        tx = self._tx_id("iot_cmd", data.get("tray_id", ""), data.get("timestamp", "")[:19].replace(":", ""))
        self._tx_log.append({"type": "iot_command", "tx": tx, "data": data})
        return tx

    def log_environmental_data(self, data: Dict[str, Any]) -> str:
        """Registra datos de control ambiental (ozono, ósmosis, UV, nutrientes)."""
        tx = self._tx_id("env", data.get("tray_id", ""), data.get("crop_type", ""))
        self._tx_log.append({"type": "environmental_data", "tx": tx, "data": data})
        return tx

    def log_microgreen_batch(self, data: Dict[str, Any]) -> str:
        """Registra lote de microgreens."""
        tx = self._tx_id("mg_batch", data.get("batch_id", ""), data.get("tray_id", ""))
        self._tx_log.append({"type": "microgreen_batch", "tx": tx, "data": data})
        return tx

    def log_microgreen_update(self, data: Dict[str, Any]) -> str:
        """Registra actualización de estado de lote microgreens."""
        tx = self._tx_id("mg_upd", data.get("batch_id", ""), data.get("status", ""))
        self._tx_log.append({"type": "microgreen_update", "tx": tx, "data": data})
        return tx

    def log_microgreen_environmental(self, data: Dict[str, Any]) -> str:
        """Registra datos ambientales asociados a un lote microgreens."""
        tx = self._tx_id("mg_env", data.get("batch_id", ""), "")
        self._tx_log.append({"type": "microgreen_environmental", "tx": tx, "data": data})
        return tx

    def log_microgreen_certificate(self, data: Dict[str, Any]) -> str:
        """Registra certificado de calidad de lote microgreens."""
        tx = self._tx_id("mg_cert", data.get("batch_id", ""), "")
        self._tx_log.append({"type": "microgreen_certificate", "tx": tx, "data": data})
        return tx

    def log_water_treatment(self, data: Dict[str, Any]) -> str:
        """Registra tratamiento de agua (ósmosis, calidad)."""
        tx = self._tx_id("water", data.get("treatment_id", ""), "")
        self._tx_log.append({"type": "water_treatment", "tx": tx, "data": data})
        return tx

    def log_product_certificate(self, data: Dict[str, Any]) -> str:
        """Registra certificado de producto (CTAEX, calidad)."""
        tx = self._tx_id("cert_prod", data.get("certificate_id", ""), data.get("product_type", ""))
        self._tx_log.append({"type": "product_certificate", "tx": tx, "data": data})
        return tx

    def log_export_certificate(self, data: Dict[str, Any]) -> str:
        """Registra certificado de exportación (fitosanitario)."""
        tx = self._tx_id("cert_exp", data.get("export_certificate_id", ""), data.get("destination_country", ""))
        self._tx_log.append({"type": "export_certificate", "tx": tx, "data": data})
        return tx

    def log_ecommerce_sync(self, data: Dict[str, Any]) -> str:
        """Registra sincronización de producto con e-commerce."""
        tx = self._tx_id("ecom_sync", data.get("platform", ""), data.get("product_id", ""))
        self._tx_log.append({"type": "ecommerce_sync", "tx": tx, "data": data})
        return tx

    def log_ecommerce_order(self, data: Dict[str, Any]) -> str:
        """Registra pedido recibido desde e-commerce."""
        tx = self._tx_id("ecom_order", data.get("order_id", ""), data.get("platform", ""))
        self._tx_log.append({"type": "ecommerce_order", "tx": tx, "data": data})
        return tx

    def get_recent_transactions(self, facility_id: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """Obtiene transacciones recientes (para verificación de integración)."""
        out = []
        for e in reversed(self._tx_log):
            if facility_id and e.get("data", {}).get("greenhouse_id") != facility_id and e.get("data", {}).get("facility_id") != facility_id:
                continue
            out.append({"tx": e["tx"], "type": e["type"]})
            if len(out) >= limit:
                break
        return out


class GaiaChainLogger:
    """Envía hashes a GaiaChain API (witness) para trazabilidad cooperativas/parcelas."""

    def __init__(self, api_url: Optional[str] = None):
        self.api_url = (api_url or os.getenv("GAIA_CHAIN_API_URL", "")).rstrip("/")

    def log(self, data_hash: str, cooperativa_id: int) -> bool:
        """Registra hash en GaiaChain; devuelve True si se envió correctamente."""
        if not self.api_url or not requests:
            return False
        try:
            r = requests.post(
                f"{self.api_url}/api/v1/witness",
                json={"hash": data_hash, "coop_id": cooperativa_id},
                timeout=5,
            )
            return r.status_code in (200, 201, 202)
        except Exception as e:
            logger.warning("GaiaChainLogger witness failed: %s", e)
            return False
