"""
CASTÚO-SYSTEM™ v3.0 — Orquestador Central Soberano
Motor de integración para todos los servicios europeos.
Gestiona: Claude · Cursor · n8n · Mistral · SABIONDA · GaiaChain · IPFS · LoRaWAN · QR
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

import httpx

from config.global_config import SovereignOrchestrator, orchestrator

logger = logging.getLogger("castuo.orchestrator")


class ServiceStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


@dataclass
class ServiceHealthResult:
    service: str
    status: ServiceStatus
    latency_ms: float
    endpoint: str
    checked_at: str
    error: Optional[str] = None


@dataclass
class OrchestratorTask:
    task_id: str
    task_type: str
    payload: Dict[str, Any]
    priority: int = 5  # 1 = máxima prioridad, 10 = mínima
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()


class CastouSovereignOrchestrator:
    """
    Orquestador Central Soberano de CASTÚO-SYSTEM™ v3.0

    Responsabilidades:
    - Health checking de todos los servicios integrados
    - Enrutamiento inteligente de tareas entre servicios
    - Failover automático ante fallos de servicio
    - Auditoría y trazabilidad conforme RGPD
    - Integración con GaiaChain para inmutabilidad de eventos
    """

    def __init__(self, config: SovereignOrchestrator = orchestrator) -> None:
        self.config = config
        self._http_client: Optional[httpx.AsyncClient] = None

    @property
    def http_client(self) -> httpx.AsyncClient:
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0),
                headers={"User-Agent": "CASTUO-SYSTEM/3.0 (SovereignOrchestrator)"},
            )
        return self._http_client

    async def close(self) -> None:
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()

    # -------------------------------------------------------------------------
    # Health Checking
    # -------------------------------------------------------------------------

    async def check_service_health(self, name: str, endpoint: str) -> ServiceHealthResult:
        """Verifica el estado de un servicio individual con medición de latencia."""
        start = asyncio.get_event_loop().time()
        try:
            # Para PostgreSQL usamos el endpoint de texto; solo HTTP es checkeable aquí
            if endpoint.startswith("postgresql://"):
                return ServiceHealthResult(
                    service=name,
                    status=ServiceStatus.UNKNOWN,
                    latency_ms=0.0,
                    endpoint=endpoint,
                    checked_at=datetime.now(timezone.utc).isoformat(),
                    error="TCP check not implemented for PostgreSQL in HTTP orchestrator",
                )

            health_url = endpoint.rstrip("/") + "/health"
            response = await self.http_client.get(health_url)
            latency_ms = (asyncio.get_event_loop().time() - start) * 1000

            status = ServiceStatus.HEALTHY if response.status_code < 400 else ServiceStatus.DEGRADED
            return ServiceHealthResult(
                service=name,
                status=status,
                latency_ms=round(latency_ms, 2),
                endpoint=endpoint,
                checked_at=datetime.now(timezone.utc).isoformat(),
            )
        except Exception as exc:
            latency_ms = (asyncio.get_event_loop().time() - start) * 1000
            logger.warning("Health check failed for %s: %s", name, exc)
            return ServiceHealthResult(
                service=name,
                status=ServiceStatus.UNAVAILABLE,
                latency_ms=round(latency_ms, 2),
                endpoint=endpoint,
                checked_at=datetime.now(timezone.utc).isoformat(),
                error=str(exc),
            )

    async def health_check_all(self) -> Dict[str, ServiceHealthResult]:
        """Health check paralelo de todos los servicios registrados."""
        endpoints = self.config.get_service_endpoints()
        tasks = {
            name: self.check_service_health(name, url)
            for name, url in endpoints.items()
        }
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        health_map: Dict[str, ServiceHealthResult] = {}
        for name, result in zip(tasks.keys(), results):
            if isinstance(result, ServiceHealthResult):
                health_map[name] = result
            else:
                health_map[name] = ServiceHealthResult(
                    service=name,
                    status=ServiceStatus.UNAVAILABLE,
                    latency_ms=0.0,
                    endpoint=endpoints[name],
                    checked_at=datetime.now(timezone.utc).isoformat(),
                    error=str(result),
                )
        return health_map

    def get_system_summary(self, health: Dict[str, ServiceHealthResult]) -> Dict[str, Any]:
        """Genera resumen del estado global del sistema."""
        healthy = sum(1 for r in health.values() if r.status == ServiceStatus.HEALTHY)
        total = len(health)
        degraded = sum(1 for r in health.values() if r.status == ServiceStatus.DEGRADED)
        unavailable = sum(1 for r in health.values() if r.status == ServiceStatus.UNAVAILABLE)

        overall = ServiceStatus.HEALTHY
        if unavailable > 0:
            overall = ServiceStatus.DEGRADED
        if unavailable > total // 2:
            overall = ServiceStatus.UNAVAILABLE

        return {
            "overall_status": overall,
            "sovereignty": "EU_COMPLIANT" if self.config.is_sovereign else "NON_COMPLIANT",
            "services": {
                "total": total,
                "healthy": healthy,
                "degraded": degraded,
                "unavailable": unavailable,
            },
            "compliance": {
                "rgpd": self.config.security.rgpd_compliant,
                "ai_act": self.config.security.ai_act_compliant,
                "eidas": self.config.security.eidas_compliant,
            },
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }

    # -------------------------------------------------------------------------
    # Task Routing
    # -------------------------------------------------------------------------

    async def route_task(self, task: OrchestratorTask) -> Dict[str, Any]:
        """
        Enruta una tarea al servicio apropiado según el tipo de tarea.
        Implementa failover automático si el servicio primario no responde.
        """
        routing_map = {
            "ai_inference": self._route_ai_inference,
            "blockchain_register": self._route_blockchain,
            "qr_generate": self._route_qr,
            "workflow_trigger": self._route_n8n_workflow,
            "iot_alert": self._route_iot_alert,
            "document_generate": self._route_document,
        }

        handler = routing_map.get(task.task_type)
        if handler is None:
            return {
                "task_id": task.task_id,
                "status": "error",
                "error": f"Tipo de tarea desconocido: {task.task_type}",
            }

        try:
            result = await handler(task)
            logger.info(
                "Task %s (%s) completed successfully",
                task.task_id,
                task.task_type,
            )
            return result
        except Exception as exc:
            logger.error("Task %s failed: %s", task.task_id, exc, exc_info=True)
            return {
                "task_id": task.task_id,
                "status": "error",
                "error": str(exc),
            }

    async def _route_ai_inference(self, task: OrchestratorTask) -> Dict[str, Any]:
        """Enruta inferencia AI: Mistral (primario) → SABIONDA (fallback)."""
        prompt = task.payload.get("prompt", "")
        model = task.payload.get("model", self.config.mistral.inference_model)

        # Intentar Mistral AI primero (soberanía europea)
        try:
            response = await self.http_client.post(
                f"{self.config.mistral.endpoint}/chat/completions",
                headers={"Authorization": f"Bearer {self.config.mistral.api_key}"},
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.2,
                },
                timeout=self.config.mistral.timeout,
            )
            response.raise_for_status()
            data = response.json()
            return {
                "task_id": task.task_id,
                "status": "completed",
                "provider": "mistral",
                "model": model,
                "result": data["choices"][0]["message"]["content"],
            }
        except Exception as mistral_err:
            logger.warning("Mistral unavailable, falling back to SABIONDA: %s", mistral_err)

        # Fallback a SABIONDA
        response = await self.http_client.post(
            f"{self.config.sabionda.endpoint}/inference",
            headers={"Authorization": f"Bearer {self.config.sabionda.api_key}"},
            json={"prompt": prompt, "model": self.config.sabionda.decision_engine_model},
            timeout=self.config.sabionda.timeout,
        )
        response.raise_for_status()
        return {
            "task_id": task.task_id,
            "status": "completed",
            "provider": "sabionda_fallback",
            "result": response.json(),
        }

    async def _route_blockchain(self, task: OrchestratorTask) -> Dict[str, Any]:
        """Registra un evento en GaiaChain 3.0 para inmutabilidad."""
        contract = task.payload.get("contract", "trazabilidad")
        contract_address = self.config.gaia_chain.contracts.get(contract)

        response = await self.http_client.post(
            f"{self.config.gaia_chain.endpoint}/transactions",
            headers={"Authorization": f"Bearer {self.config.gaia_chain.api_key}"},
            json={
                "contract_address": contract_address,
                "data": task.payload.get("data", {}),
                "chain_id": self.config.gaia_chain.chain_id,
            },
            timeout=self.config.gaia_chain.timeout,
        )
        response.raise_for_status()
        return {
            "task_id": task.task_id,
            "status": "registered",
            "blockchain": "GaiaChain 3.0",
            "contract": contract,
            "tx_hash": response.json().get("tx_hash"),
        }

    async def _route_qr(self, task: OrchestratorTask) -> Dict[str, Any]:
        """Genera QR con cifrado ECC-256 y lo ancla en IPFS + blockchain."""
        response = await self.http_client.post(
            f"{self.config.qr.endpoint}/generate",
            headers={"Authorization": f"Bearer {self.config.qr.api_key}"},
            json={
                "data": task.payload,
                "format": self.config.qr.output_format,
                "encryption": self.config.qr.encryption,
            },
            timeout=self.config.qr.timeout,
        )
        response.raise_for_status()
        return {
            "task_id": task.task_id,
            "status": "generated",
            "qr_data": response.json(),
        }

    async def _route_n8n_workflow(self, task: OrchestratorTask) -> Dict[str, Any]:
        """Dispara un workflow n8n via webhook."""
        workflow_id = task.payload.get("workflow_id", "")
        response = await self.http_client.post(
            f"{self.config.n8n.endpoint}/webhook/{workflow_id}",
            headers={"X-N8N-API-KEY": self.config.n8n.api_key},
            json=task.payload.get("data", {}),
            timeout=self.config.n8n.workflow_timeout,
        )
        response.raise_for_status()
        return {
            "task_id": task.task_id,
            "status": "triggered",
            "workflow_id": workflow_id,
            "n8n_response": response.json(),
        }

    async def _route_iot_alert(self, task: OrchestratorTask) -> Dict[str, Any]:
        """Procesa alerta IoT LoRaWAN y la enruta al sistema correspondiente."""
        sensor_id = task.payload.get("sensor_id", "")
        metric = task.payload.get("metric", "")
        value = task.payload.get("value", 0)
        thresholds = self.config.lorawan.alert_thresholds

        alert_type = None
        if metric == "temperatura_vacuno" and value > thresholds["temperatura_vacuno_max_c"]:
            alert_type = "veterinary_emergency"
        elif metric == "humedad_suelo" and value < thresholds["humedad_suelo_min_pct"]:
            alert_type = "irrigation_required"
        elif metric == "tension_matricial" and value < thresholds["tension_matricial_min_cb"]:
            alert_type = "irrigation_critical"
        elif metric == "co2_ppm":
            if value < thresholds["co2_invernadero_min_ppm"] or value > thresholds["co2_invernadero_max_ppm"]:
                alert_type = "co2_regulation"

        return {
            "task_id": task.task_id,
            "status": "processed",
            "sensor_id": sensor_id,
            "alert_type": alert_type,
            "metric": metric,
            "value": value,
            "action_required": alert_type is not None,
        }

    async def _route_document(self, task: OrchestratorTask) -> Dict[str, Any]:
        """Enruta generación de documentos al backend FastAPI SABIONDA."""
        doc_type = task.payload.get("doc_type", "")
        endpoint_map = {
            "siex": "/api/v1/siex/cuaderno-campo",
            "traces": "/api/v1/traces/certificado",
            "pac": "/api/v1/pac/eco-esquema",
            "regepa": "/api/v1/regepa/explotacion",
            "sigpac": "/api/v1/sigpac/parcelas",
        }
        path = endpoint_map.get(doc_type)
        if not path:
            return {"task_id": task.task_id, "status": "error", "error": f"Tipo de documento desconocido: {doc_type}"}

        fastapi_base = "http://fastapi:8000"
        response = await self.http_client.post(
            f"{fastapi_base}{path}",
            json=task.payload.get("data", {}),
            timeout=60,
        )
        response.raise_for_status()
        return {
            "task_id": task.task_id,
            "status": "generated",
            "doc_type": doc_type,
            "document": response.json(),
        }
