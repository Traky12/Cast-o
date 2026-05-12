"""
Tests de auditoría inmutable — AuditLogger + API endpoints
Verifica: cadena criptográfica, búsquedas, integridad, integración invernadero.
"""

import sys
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "api"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from main import app

client = TestClient(app)


# ─────────────────────────────────────────────────────────────────────────────
# Fixture — AuditLogger con fichero temporal
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def audit_tmp():
    """AuditLogger apuntando a un fichero temporal — se descarta al terminar el test."""
    from services.audit.audit_logger import AuditLogger
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
        tmp_path = f.name
    logger = AuditLogger(log_path=tmp_path)
    yield logger
    Path(tmp_path).unlink(missing_ok=True)


# ─────────────────────────────────────────────────────────────────────────────
# 1. Tests unitarios — AuditLogger
# ─────────────────────────────────────────────────────────────────────────────

class TestAuditLogger:
    def test_log_genera_evento_con_hash(self, audit_tmp):
        ev = audit_tmp.log(
            "APERTURA_LOTE", "INVH-TEST-001", "12345678Z",
            "lote/INVH-TEST-001", {"cultivo": "tomate"},
        )
        assert len(ev.hash_propio) == 64
        assert ev.evento_id == ev.hash_propio[:16]
        assert ev.accion == "APERTURA_LOTE"

    def test_primer_evento_apunta_a_genesis(self, audit_tmp):
        ev = audit_tmp.log("APERTURA_LOTE", "LOTE-001", "NIF01", "lote", {})
        assert ev.hash_anterior == "0" * 64

    def test_segundo_evento_apunta_al_primero(self, audit_tmp):
        ev1 = audit_tmp.log("APERTURA_LOTE",    "LOTE-002", "NIF01", "lote", {})
        ev2 = audit_tmp.log("REGISTRO_SOLUCION", "LOTE-002", "NIF01", "sol",  {})
        assert ev2.hash_anterior == ev1.hash_propio

    def test_cadena_de_tres_eventos(self, audit_tmp):
        e1 = audit_tmp.log("APERTURA_LOTE",     "L1", "NIF01", "l1", {})
        e2 = audit_tmp.log("REGISTRO_CLIMA",     "L1", "NIF01", "c1", {})
        e3 = audit_tmp.log("REGISTRO_COSECHA",   "L1", "NIF01", "c2", {})
        assert e2.hash_anterior == e1.hash_propio
        assert e3.hash_anterior == e2.hash_propio

    def test_verify_chain_integra(self, audit_tmp):
        audit_tmp.log("APERTURA_LOTE",     "LV1", "NIF01", "l", {})
        audit_tmp.log("REGISTRO_SOLUCION", "LV1", "NIF01", "s", {})
        audit_tmp.log("REGISTRO_COSECHA",  "LV1", "NIF01", "c", {})
        result = audit_tmp.verify_chain()
        assert result["ok"] is True
        assert result["total_eventos"] == 3
        assert result["errores"] == []

    def test_get_by_lote_filtra_correctamente(self, audit_tmp):
        audit_tmp.log("APERTURA_LOTE", "LOTE-A", "NIF01", "l", {"cultivo": "tomate"})
        audit_tmp.log("APERTURA_LOTE", "LOTE-B", "NIF02", "l", {"cultivo": "lechuga"})
        audit_tmp.log("REGISTRO_CLIMA", "LOTE-A", "NIF01", "c", {})
        eventos_a = audit_tmp.get_by_lote("LOTE-A")
        assert len(eventos_a) == 2
        assert all(e["lote_id"] == "LOTE-A" for e in eventos_a)

    def test_get_by_operator_filtra_correctamente(self, audit_tmp):
        audit_tmp.log("APERTURA_LOTE", "L1", "OPERADOR-X", "l", {})
        audit_tmp.log("APERTURA_LOTE", "L2", "OPERADOR-Y", "l", {})
        audit_tmp.log("REGISTRO_SOLUCION", "L1", "OPERADOR-X", "s", {})
        eventos_x = audit_tmp.get_by_operator("OPERADOR-X")
        assert len(eventos_x) == 2
        assert all(e["actor_nif"] == "OPERADOR-X" for e in eventos_x)

    def test_search_multi_filtro(self, audit_tmp):
        audit_tmp.log("APERTURA_LOTE",    "L1", "NIF01", "l", {})
        audit_tmp.log("REGISTRO_COSECHA", "L1", "NIF01", "c", {})
        audit_tmp.log("REGISTRO_COSECHA", "L2", "NIF02", "c", {})
        resultados = audit_tmp.search(accion="REGISTRO_COSECHA", lote_id="L1")
        assert len(resultados) == 1
        assert resultados[0]["lote_id"] == "L1"

    def test_cadena_vacia_verify_ok(self, audit_tmp):
        result = audit_tmp.verify_chain()
        assert result["ok"] is True
        assert result["total_eventos"] == 0

    def test_to_dict_contiene_campos_requeridos(self, audit_tmp):
        ev = audit_tmp.log("APERTURA_LOTE", "L1", "NIF01", "l", {"x": 1})
        d = ev.to_dict()
        for campo in ("evento_id", "accion", "lote_id", "actor_nif",
                      "recurso", "datos", "timestamp", "hash_anterior", "hash_propio"):
            assert campo in d, f"Campo '{campo}' ausente en to_dict()"


# ─────────────────────────────────────────────────────────────────────────────
# 2. Tests de integración — API /audit endpoints (dev-mode JWT)
# ─────────────────────────────────────────────────────────────────────────────

class TestAuditAPI:
    """Usa la instancia global del AuditLogger, alimentada por el flujo de invernadero."""

    # Primero generar eventos via API invernadero para que haya datos
    LOTE_ID = "INVH-AUDIT-TEST-12345678"
    OPERADOR = "99999999Z"

    def _abrir_lote(self) -> str:
        resp = client.post("/api/v1/invernadero/lote/apertura", json={
            "explotacion_rea": "AUDIT-TEST",
            "operador_nif":    self.OPERADOR,
            "cultivo":         "tomate",
            "variedad":        "Raf",
            "sistema":         "goteo",
            "zona":            "zona-audit",
            "superficie_m2":   100.0,
            "fecha_siembra":   "2026-01-01",
            "semilla_origen":  "Test",
            "semilla_certificada": True,
        })
        assert resp.status_code == 200
        return resp.json()["lote_id"]

    def test_actions_endpoint_sin_auth(self):
        resp = client.get("/api/v1/audit/actions")
        assert resp.status_code == 200
        data = resp.json()
        assert "acciones" in data
        ids = [a["id"] for a in data["acciones"]]
        assert "APERTURA_LOTE" in ids
        assert "REGISTRO_COSECHA" in ids

    def test_apertura_lote_genera_evento_audit(self):
        lote_id = self._abrir_lote()
        resp = client.get(f"/api/v1/audit/lote/{lote_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        acciones = [e["accion"] for e in data["eventos"]]
        assert "APERTURA_LOTE" in acciones

    def test_cosecha_genera_evento_audit(self):
        lote_id = self._abrir_lote()
        client.post("/api/v1/invernadero/cosecha", json={
            "lote_id":       lote_id,
            "fecha_cosecha": "2026-04-01",
            "kg_cosechados": 500.0,
            "destino":       "mercado_local",
            "operador_nif":  self.OPERADOR,
        })
        resp = client.get(f"/api/v1/audit/lote/{lote_id}")
        assert resp.status_code == 200
        acciones = [e["accion"] for e in resp.json()["eventos"]]
        assert "REGISTRO_COSECHA" in acciones

    def test_fitosanitario_registrado_en_audit(self):
        lote_id = self._abrir_lote()
        client.post("/api/v1/invernadero/fitosanitario", json={
            "lote_id":        lote_id,
            "fecha":          "2026-02-01",
            "tipo":           "biocontrol",
            "producto":       "Trichoderma",
            "justificacion":  "Prevención",
            "operador_nif":   self.OPERADOR,
        })
        resp = client.get(f"/api/v1/audit/lote/{lote_id}")
        acciones = [e["accion"] for e in resp.json()["eventos"]]
        assert "REGISTRO_FITOSANITARIO" in acciones

    def test_verify_chain_endpoint(self):
        self._abrir_lote()
        resp = client.get("/api/v1/audit/verify")
        assert resp.status_code == 200
        data = resp.json()
        assert "ok" in data
        assert "total_eventos" in data
        assert "errores" in data
        # La cadena debe ser íntegra
        assert data["ok"] is True

    def test_search_por_accion(self):
        self._abrir_lote()
        resp = client.get("/api/v1/audit/search", params={"accion": "APERTURA_LOTE"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        assert all(e["accion"] == "APERTURA_LOTE" for e in data["eventos"])

    def test_search_sin_filtros_422(self):
        resp = client.get("/api/v1/audit/search")
        assert resp.status_code == 422

    def test_action_tipo_invalido_422(self):
        resp = client.get("/api/v1/audit/action/ACCION_INEXISTENTE")
        assert resp.status_code == 422

    def test_operator_endpoint(self):
        lote_id = self._abrir_lote()
        # El operador debe aparecer en el endpoint de operador
        resp = client.get(f"/api/v1/audit/operator/{self.OPERADOR}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1

    def test_lote_inexistente_retorna_lista_vacia(self):
        resp = client.get("/api/v1/audit/lote/INVH-NOEXISTE-00000000")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0
