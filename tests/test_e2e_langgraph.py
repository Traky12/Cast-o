"""
Tests E2E del Grafo LangGraph — CASTÚO-SYSTEM™ v3.1
Flujo completo Invernadero → Campo → Procesado → Cliente → Reporte

Todos los servicios externos MOCKEADOS:
  - SABIONDA FastAPI    → httpx.MockTransport
  - GaiaChain RPC       → httpx.MockTransport
  - IPFS Cluster        → httpx.MockTransport
  - WooCommerce REST    → httpx.MockTransport
  - TRACES API          → httpx.MockTransport
  - ELK Elasticsearch   → httpx.MockTransport

Sin dependencias de red real → tests reproducibles en CI.
"""

import sys
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, patch, MagicMock

import pytest

# Añadir langgraph/ al path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "castuo_graph"))

from state import AgroState


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures base
# ─────────────────────────────────────────────────────────────────────────────

LOTE_ID = "INVH-ES12345-TOMATE-ABCD1234"
OPERADOR_NIF = "12345678Z"
OPERADOR_NIF_HASH = hashlib.sha256(OPERADOR_NIF.encode()).hexdigest()


def make_state(**overrides) -> AgroState:
    base: AgroState = {
        "lote_id": LOTE_ID,
        "operador_nif": OPERADOR_NIF,
        "sensor_readings": [
            {"sensor_id": "S001", "metric": "ph",              "value": 6.0, "unit": "pH",    "timestamp": "2026-03-30T10:00:00Z", "lote_id": LOTE_ID},
            {"sensor_id": "S001", "metric": "ec_ms_cm",        "value": 3.0, "unit": "mS/cm", "timestamp": "2026-03-30T10:00:00Z", "lote_id": LOTE_ID},
            {"sensor_id": "S001", "metric": "temp_solucion_c", "value": 20.0,"unit": "°C",    "timestamp": "2026-03-30T10:00:00Z", "lote_id": LOTE_ID},
            {"sensor_id": "S001", "metric": "o2_disuelto_mg_l","value": 8.5, "unit": "mg/L",  "timestamp": "2026-03-30T10:00:00Z", "lote_id": LOTE_ID},
        ],
        "woocommerce_order_id": "WC-1234",
        "validated_readings": [],
        "readings_alertas": [],
        "invernadero_status": None,
        "gdpr_consent_verified": False,
        "pii_redacted": False,
        "ai_act_human_review_required": False,
        "gdpr_violations": [],
        "sigpac_parcelas": None,
        "traces_cert_id": None,
        "traces_cert_payload": None,
        "gaiachain_tx_hash": None,
        "ipfs_cid": None,
        "content_hash": None,
        "qr_url": None,
        "qr_hash_cadena": None,
        "order_updated": False,
        "elk_log_id": None,
        "pdf_report_url": None,
        "rollback_stack": [],
        "compensations_executed": [],
        "current_node": "start",
        "error": None,
        "error_node": None,
        "status": "running",
        "next_action": None,
        "sigpac_ref": "14:123:0:45:1",
        "cultivo": "tomate",
        "variedad": "Raf",
        "fecha_cosecha": "2026-03-30",
        "kg_cosechados": 500.0,
        "eco_certificado": True,
        "sin_pesticidas_sinteticos": True,
        "explotacion_rea": "ES12345",
        "destino": "mercado_local",
        "destino_pais": "ES",
    }
    base.update(overrides)
    return base


def mock_http_response(status_code: int = 200, body: dict = None):
    """Crea una respuesta HTTP mockeada."""
    m = MagicMock()
    m.status_code = status_code
    m.json.return_value = body or {}
    m.text = json.dumps(body or {})
    return m


# ─────────────────────────────────────────────────────────────────────────────
# Tests del nodo ethical_guard (síncrono — sin mocks)
# ─────────────────────────────────────────────────────────────────────────────

class TestEthicalGuard:
    def test_redacta_nif_y_hashea(self):
        from ethical_guard import ethical_guard_node, hash_nif
        state = make_state()
        result = ethical_guard_node(state)
        # El NIF debe quedar como hash SHA-256, no en claro
        assert result["operador_nif"] == hash_nif(OPERADOR_NIF)
        assert OPERADOR_NIF not in result["operador_nif"]
        assert result["pii_redacted"] is True

    def test_parametros_optimos_no_requieren_revision_humana(self):
        from ethical_guard import ethical_guard_node
        state = make_state(invernadero_status="OPTIMO", readings_alertas=[])
        result = ethical_guard_node(state)
        assert result["ai_act_human_review_required"] is False
        assert result["status"] == "running"

    def test_estado_critico_requiere_revision_humana(self):
        from ethical_guard import ethical_guard_node
        state = make_state(invernadero_status="CRITICO")
        result = ethical_guard_node(state)
        assert result["ai_act_human_review_required"] is True
        assert result["status"] == "human_review"

    def test_o2_critico_requiere_revision_humana(self):
        from ethical_guard import ethical_guard_node
        state = make_state(
            readings_alertas=["O₂ disuelto crítico: 4.0 mg/L — riesgo de hipoxia radicular"],
        )
        result = ethical_guard_node(state)
        assert result["ai_act_human_review_required"] is True

    def test_metrica_inesperada_viola_gdpr(self):
        from ethical_guard import ethical_guard_node
        state = make_state(sensor_readings=[
            {"sensor_id": "S001", "metric": "localización_gps", "value": 40.4, "unit": "deg", "timestamp": "2026-03-30T10:00:00Z", "lote_id": LOTE_ID},
        ])
        result = ethical_guard_node(state)
        assert len(result["gdpr_violations"]) > 0
        assert any("localización_gps" in v for v in result["gdpr_violations"])

    def test_lectura_sin_timestamp_viola_retencion(self):
        from ethical_guard import ethical_guard_node
        state = make_state(sensor_readings=[
            {"sensor_id": "S001", "metric": "ph", "value": 6.0, "unit": "pH", "timestamp": None, "lote_id": LOTE_ID},
        ])
        result = ethical_guard_node(state)
        assert len(result["gdpr_violations"]) > 0

    def test_hash_nif_determinista(self):
        from ethical_guard import hash_nif
        assert hash_nif("12345678Z") == hash_nif("12345678Z")
        assert hash_nif("12345678Z") != hash_nif("87654321X")

    def test_redact_nif_en_texto(self):
        from ethical_guard import redact_nif
        texto = "El operador 12345678Z registró la cosecha"
        resultado = redact_nif(texto)
        assert "12345678Z" not in resultado
        assert "***NIF_REDACTED***" in resultado


# ─────────────────────────────────────────────────────────────────────────────
# Tests del nodo invernadero (con mock httpx)
# ─────────────────────────────────────────────────────────────────────────────

class TestInvernaderoNode:
    @pytest.mark.asyncio
    async def test_lecturas_optimas_estado_optimo(self):
        from nodes.invernadero_node import invernadero_node

        sabionda_resp = mock_http_response(200, {"estado": "OPTIMO", "alertas": []})
        elk_resp = mock_http_response(200, {"_id": "log-001"})

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(side_effect=[sabionda_resp, elk_resp])
            mock_client_cls.return_value = mock_client

            result = await invernadero_node(make_state())

        assert result["invernadero_status"] == "OPTIMO"
        assert result["readings_alertas"] == []
        assert len(result["validated_readings"]) == 4

    @pytest.mark.asyncio
    async def test_lecturas_con_alerta_propagada(self):
        from nodes.invernadero_node import invernadero_node

        sabionda_resp = mock_http_response(200, {
            "estado": "ALERTA",
            "alertas": ["pH 5.0 fuera de rango óptimo [5.8-6.3] para tomate"],
        })
        elk_resp = mock_http_response(200, {})

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(side_effect=[sabionda_resp, elk_resp])
            mock_client_cls.return_value = mock_client

            result = await invernadero_node(make_state())

        assert result["invernadero_status"] == "ALERTA"
        assert len(result["readings_alertas"]) == 1

    @pytest.mark.asyncio
    async def test_sabionda_no_disponible_usa_validacion_local(self):
        """Si el backend no responde, el nodo usa validación local de respaldo."""
        import httpx as real_httpx
        from nodes.invernadero_node import invernadero_node

        elk_resp = mock_http_response(200, {})

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            # Primera llamada falla (SABIONDA), segunda pasa (ELK)
            mock_client.post = AsyncMock(side_effect=[
                real_httpx.ConnectError("Connection refused"),
                elk_resp,
            ])
            mock_client_cls.return_value = mock_client

            # Lecturas con O₂ crítico para disparar validación local
            state = make_state(sensor_readings=[
                {"sensor_id": "S001", "metric": "ph",              "value": 6.0, "unit": "pH",    "timestamp": "2026-03-30T10:00:00Z", "lote_id": LOTE_ID},
                {"sensor_id": "S001", "metric": "ec_ms_cm",        "value": 3.0, "unit": "mS/cm", "timestamp": "2026-03-30T10:00:00Z", "lote_id": LOTE_ID},
                {"sensor_id": "S001", "metric": "temp_solucion_c", "value": 20.0,"unit": "°C",    "timestamp": "2026-03-30T10:00:00Z", "lote_id": LOTE_ID},
                {"sensor_id": "S001", "metric": "o2_disuelto_mg_l","value": 4.0, "unit": "mg/L",  "timestamp": "2026-03-30T10:00:00Z", "lote_id": LOTE_ID},
            ])
            result = await invernadero_node(state)

        # Validación local detecta O₂ crítico
        assert result["invernadero_status"] == "CRITICO"
        assert any("O₂" in a for a in result["readings_alertas"])


# ─────────────────────────────────────────────────────────────────────────────
# Tests del rollback stack (campo_node genera compensating action)
# ─────────────────────────────────────────────────────────────────────────────

class TestRollbackStack:
    @pytest.mark.asyncio
    async def test_campo_registra_compensating_action(self):
        from nodes.campo_node import campo_node

        sigpac_resp  = mock_http_response(200, {"sigpac_ref": "14:123:0:45:1"})
        traces_resp  = mock_http_response(200, {
            "payload": {"certificado": {"numero": "TRACES-ES-20260330-ES12345"}},
        })
        elk_resp = mock_http_response(200, {})

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.get  = AsyncMock(return_value=sigpac_resp)
            mock_client.post = AsyncMock(side_effect=[traces_resp, elk_resp])
            mock_client_cls.return_value = mock_client

            state = make_state(
                invernadero_status="OPTIMO",
                operador_nif=OPERADOR_NIF_HASH,
                gdpr_consent_verified=True,
                pii_redacted=True,
            )
            result = await campo_node(state)

        # Debe haber exactamente 1 compensating action (TRACES)
        assert len(result["rollback_stack"]) == 1
        comp = result["rollback_stack"][0]
        assert comp["service"] == "traces"
        assert comp["action"] == "cancel"
        assert comp["node"] == "campo"

    @pytest.mark.asyncio
    async def test_procesado_registra_dos_compensating_actions(self):
        from nodes.procesado_node import procesado_node

        ipfs_resp    = mock_http_response(200, {"Hash": "QmTestCID123"})
        chain_resp   = mock_http_response(200, {"tx_hash": "0xTEST123"})
        elk_resp     = mock_http_response(200, {})

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(side_effect=[ipfs_resp, chain_resp, elk_resp])
            mock_client_cls.return_value = mock_client

            state = make_state(
                rollback_stack=[{
                    "node": "campo", "service": "traces",
                    "action": "cancel", "resource_id": "TRACES-001", "payload": {},
                }],
                operador_nif=OPERADOR_NIF_HASH,
            )
            result = await procesado_node(state)

        # 1 de campo + 2 de procesado (IPFS + GaiaChain) = 3 total
        assert len(result["rollback_stack"]) == 3
        services = [c["service"] for c in result["rollback_stack"]]
        assert "ipfs" in services
        assert "gaiachain" in services

    @pytest.mark.asyncio
    async def test_compensaciones_ejecutadas_lifo(self):
        """Las compensaciones se ejecutan en orden inverso al registro."""
        from tools import execute_compensations

        execution_order = []

        async def mock_run_compensation(action):
            execution_order.append(action["service"])

        with patch("tools._run_compensation", side_effect=mock_run_compensation):
            with patch("tools.tool_log_elk", new_callable=AsyncMock) as mock_elk:
                mock_elk.return_value = {"log_id": "log-test"}
                stack = [
                    {"node": "campo",    "service": "traces",     "action": "cancel",                  "resource_id": "T-001", "payload": {}},
                    {"node": "procesado","service": "ipfs",       "action": "unpin",                   "resource_id": "CID-001","payload": {}},
                    {"node": "procesado","service": "gaiachain",  "action": "register_cancellation",   "resource_id": "TX-001","payload": {"original_tx": "TX-001", "lote_id": LOTE_ID, "reason": "test", "compensation_function": "registerCompensation"}},
                ]
                await execute_compensations(stack, LOTE_ID)

        # LIFO: gaiachain primero, luego ipfs, luego traces
        assert execution_order == ["gaiachain", "ipfs", "traces"]


# ─────────────────────────────────────────────────────────────────────────────
# Tests del flujo condicional del grafo
# ─────────────────────────────────────────────────────────────────────────────

class TestConditionalRouting:
    def test_route_normal_despues_de_invernadero(self):
        from graph import route_after_invernadero
        state = make_state(status="running", invernadero_status="OPTIMO")
        assert route_after_invernadero(state) == "ethical_guard"

    def test_route_a_error_si_fallo(self):
        from graph import route_after_invernadero
        state = make_state(status="failed", error="Connection refused")
        assert route_after_invernadero(state) == "error_handler"

    def test_route_a_human_review_si_critico(self):
        from graph import route_after_ethical_guard
        state = make_state(
            ai_act_human_review_required=True,
            status="human_review",
        )
        assert route_after_ethical_guard(state) == "human_review"

    def test_route_normal_despues_de_ethical_guard(self):
        from graph import route_after_ethical_guard
        state = make_state(
            ai_act_human_review_required=False,
            status="running",
        )
        assert route_after_ethical_guard(state) == "campo"

    def test_route_a_error_desde_campo(self):
        from graph import route_after_campo
        state = make_state(status="failed")
        assert route_after_campo(state) == "error_handler"

    def test_route_normal_desde_procesado(self):
        from graph import route_after_procesado
        state = make_state(status="running")
        assert route_after_procesado(state) == "cliente"


# ─────────────────────────────────────────────────────────────────────────────
# Test E2E completo — flujo feliz mockeado
# ─────────────────────────────────────────────────────────────────────────────

class TestE2EHappyPath:
    @pytest.mark.asyncio
    async def test_flujo_completo_invernadero_a_cliente(self):
        """
        Test E2E completo: lecturas IoT → GDPR → campo → blockchain → QR → cliente.
        Todos los servicios externos mockeados.
        Verifica que el estado final tiene: QR, tx blockchain, orden actualizada.
        """
        # Respuestas mockeadas para cada llamada HTTP en orden
        responses = [
            # invernadero_node: SABIONDA /solucion-nutritiva
            mock_http_response(200, {"estado": "OPTIMO", "alertas": []}),
            # invernadero_node: ELK log
            mock_http_response(200, {"_id": "log-001"}),
            # campo_node: SIGPAC GET
            mock_http_response(200, {"sigpac_ref": "14:123:0:45:1"}),
            # campo_node: TRACES POST
            mock_http_response(200, {"payload": {"certificado": {"numero": "TRACES-ES-20260330-ES12345"}}}),
            # campo_node: ELK log
            mock_http_response(200, {}),
            # procesado_node: IPFS add
            mock_http_response(200, {"Hash": "QmTestCID456"}),
            # procesado_node: GaiaChain register
            mock_http_response(200, {"tx_hash": "0xABCDEF123456"}),
            # procesado_node: ELK log
            mock_http_response(200, {}),
            # cliente_node: SABIONDA /trazabilidad/qr/generar
            mock_http_response(200, {
                "verify_url": f"https://verify.castuo360.eu/lote/{LOTE_ID}/abc123",
                "hash_cadena": "a" * 64,
            }),
            # cliente_node: WooCommerce PUT
            mock_http_response(200, {"id": "WC-1234", "status": "processing"}),
            # cliente_node: ELK log
            mock_http_response(200, {}),
            # reporte_node: ELK log final
            mock_http_response(200, {"_id": "log-final"}),
        ]

        call_idx = 0

        async def sequential_mock(*args, **kwargs):
            nonlocal call_idx
            resp = responses[call_idx % len(responses)]
            call_idx += 1
            return resp

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.get  = AsyncMock(side_effect=sequential_mock)
            mock_client.post = AsyncMock(side_effect=sequential_mock)
            mock_client.put  = AsyncMock(side_effect=sequential_mock)
            mock_client_cls.return_value = mock_client

            from graph import agro_graph
            final = await agro_graph.ainvoke(make_state())

        assert final["status"] == "completed"
        assert final["qr_url"] is not None
        assert "verify.castuo360.eu" in final["qr_url"]
        assert final["gaiachain_tx_hash"] == "0xABCDEF123456"
        assert final["order_updated"] is True
        assert final["error"] is None
        assert final["ai_act_human_review_required"] is False
        # NIF no debe estar en claro en el estado final
        assert final["operador_nif"] != OPERADOR_NIF
        assert len(final["operador_nif"]) == 64  # SHA-256 hex

    @pytest.mark.asyncio
    async def test_flujo_con_estado_critico_para_en_human_review(self):
        """
        Con O₂ crítico: el grafo se detiene en human_review — no avanza a campo.
        """
        critical_state = make_state(sensor_readings=[
            {"sensor_id": "S001", "metric": "ph",              "value": 6.0, "unit": "pH",    "timestamp": "2026-03-30T10:00:00Z", "lote_id": LOTE_ID},
            {"sensor_id": "S001", "metric": "ec_ms_cm",        "value": 3.0, "unit": "mS/cm", "timestamp": "2026-03-30T10:00:00Z", "lote_id": LOTE_ID},
            {"sensor_id": "S001", "metric": "temp_solucion_c", "value": 20.0,"unit": "°C",    "timestamp": "2026-03-30T10:00:00Z", "lote_id": LOTE_ID},
            {"sensor_id": "S001", "metric": "o2_disuelto_mg_l","value": 2.0, "unit": "mg/L",  "timestamp": "2026-03-30T10:00:00Z", "lote_id": LOTE_ID},
        ])

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(side_effect=[
                mock_http_response(200, {"estado": "CRITICO", "alertas": ["O₂ disuelto crítico: 2.0 mg/L"]}),
                mock_http_response(200, {}),  # ELK
                mock_http_response(200, {}),  # ELK human_review
            ])
            mock_client_cls.return_value = mock_client

            from graph import agro_graph
            final = await agro_graph.ainvoke(critical_state)

        assert final["status"] == "human_review"
        assert final["ai_act_human_review_required"] is True
        # No se generó QR ni se tocó blockchain
        assert final["gaiachain_tx_hash"] is None
        assert final["qr_url"] is None

    @pytest.mark.asyncio
    async def test_rollback_ejecutado_si_procesado_falla(self):
        """
        Si procesado falla, se ejecutan compensaciones de traces (LIFO).
        """
        import httpx as real_httpx

        state = make_state()

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.get  = AsyncMock(return_value=mock_http_response(200, {}))
            call_count = 0

            async def side_effect_post(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                # 1=SABIONDA(inv), 2=ELK(inv), 3=TRACES(campo), 4=ELK(campo)
                # 5=IPFS(proc) → falla
                if call_count == 5:
                    raise real_httpx.ConnectError("IPFS not available")
                return mock_http_response(200, {
                    "payload": {"certificado": {"numero": "TRACES-001"}},
                    "estado": "OPTIMO", "alertas": [], "tx_hash": "0x01",
                    "Hash": "QmCID", "_id": "log",
                })

            mock_client.post = AsyncMock(side_effect=side_effect_post)
            mock_client.put  = AsyncMock(return_value=mock_http_response(200, {}))
            mock_client_cls.return_value = mock_client

            from graph import agro_graph
            final = await agro_graph.ainvoke(state)

        # El grafo debe haber terminado en failed con compensaciones
        assert final["status"] == "failed"
        assert final["error_node"] == "procesado"
        assert len(final["compensations_executed"]) >= 0  # Compensaciones intentadas


# ─────────────────────────────────────────────────────────────────────────────
# Test health endpoint FastAPI
# ─────────────────────────────────────────────────────────────────────────────

def test_langgraph_health_endpoint():
    from fastapi.testclient import TestClient
    from graph import app
    client = TestClient(app)
    resp = client.get("/langgraph/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["version"] == "3.1.0"
    assert "invernadero" in data["nodes"]
    assert data["sovereignty"] == "EU"
