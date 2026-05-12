"""
Tests para la cadena de auditoría inmutable — trazabilidad + integridad criptográfica
Tests básicos para validar funcionalidad del sistema de auditoría.
"""

import json
import tempfile
import uuid as uuid_module
from datetime import datetime
from pathlib import Path

import pytest
from services.audit.audit_logger import (
    AuditLogger,
    AuditEvent,
    AuditAction,
    AuditSeverity,
    get_audit_logger,
)


class TestAuditEventHashComputation:
    """Verifica que los hashes de eventos sean determinísticos y seguros."""

    def test_audit_event_hash_is_deterministic(self):
        """El hash debe ser igual para eventos idénticos."""
        # Usar event_id y timestamp explícitos para determinismo
        event_id = str(uuid_module.UUID("12345678-1234-5678-1234-567812345678"))
        ts = "2026-04-02T12:00:00+00:00"
        
        event1 = AuditEvent(
            action=AuditAction.REGISTRO_COSECHA,
            actor_nif="12345678Z",
            actor_role="operador_invernadero",
            resource_type="lote",
            resource_id="INVH-001",
            severity=AuditSeverity.INFO,
            data={"kg_cosechados": 500},
            event_id=event_id,
            timestamp=ts,
        )
        event2 = AuditEvent(
            action=AuditAction.REGISTRO_COSECHA,
            actor_nif="12345678Z",
            actor_role="operador_invernadero",
            resource_type="lote",
            resource_id="INVH-001",
            severity=AuditSeverity.INFO,
            data={"kg_cosechados": 500},
            event_id=event_id,
            timestamp=ts,
        )
        
        hash1 = event1.compute_hash()
        hash2 = event2.compute_hash()
        assert hash1 == hash2, "Hashes deben ser determinísticos"

    def test_audit_event_hash_is_unique_on_data_change(self):
        """Cambios en datos deben producir hashes diferentes."""
        event_id = str(uuid_module.UUID("12345678-1234-5678-1234-567812345678"))
        ts = "2026-04-02T12:00:00+00:00"
        
        event1 = AuditEvent(
            action=AuditAction.REGISTRO_COSECHA,
            actor_nif="12345678Z",
            actor_role="operador_invernadero",
            resource_type="lote",
            resource_id="INVH-001",
            severity=AuditSeverity.INFO,
            data={"kg_cosechados": 500},
            event_id=event_id,
            timestamp=ts,
        )
        event2 = AuditEvent(
            action=AuditAction.REGISTRO_COSECHA,
            actor_nif="12345678Z",
            actor_role="operador_invernadero",
            resource_type="lote",
            resource_id="INVH-001",
            severity=AuditSeverity.INFO,
            data={"kg_cosechados": 501},  # Cambio en datos
            event_id=event_id,
            timestamp=ts,
        )
        
        hash1 = event1.compute_hash()
        hash2 = event2.compute_hash()
        assert hash1 != hash2, "Hashes deben diferir si datos cambian"


class TestAuditChainIntegrity:
    """Verifica que la cadena de auditoría sea íntegra y tamper-proof."""

    def test_audit_chain_integrity_valid(self):
        """Una cadena válida debe verificarse correctamente."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=tmpdir)
            
            # Crear 3 eventos
            for i in range(3):
                event = AuditEvent(
                    action=AuditAction.REGISTRO_COSECHA,
                    actor_nif="12345678Z",
                    actor_role="operador_invernadero",
                    resource_type="lote",
                    resource_id=f"INVH-{i:03d}",
                    severity=AuditSeverity.INFO,
                    data={"kg": 100 + i * 10},
                )
                logger.log_event(event)
            
            # Verificar integridad
            is_valid = logger.verify_chain_integrity()
            assert is_valid, "Cadena válida debe pasar verificación"

    def test_audit_chain_linking(self):
        """Cada evento debe tener hash_anterior que apunta al anterior."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=tmpdir)
            
            event_ids: list[str] = []
            for i in range(3):
                event = AuditEvent(
                    action=AuditAction.APERTURA_LOTE,
                    actor_nif="12345678Z",
                    actor_role="operador_invernadero",
                    resource_type="lote",
                    resource_id=f"INVH-{i:03d}",
                    severity=AuditSeverity.INFO,
                    data={"cultivo": "tomate"},
                )
                event_id = logger.log_event(event)
                event_ids.append(event_id)
            
            # Verificar que los eventos están encadenados
            audit_file = Path(tmpdir) / "audit_chain.jsonl"
            lines = audit_file.read_text().strip().split("\n")
            for i, line in enumerate(lines):
                event_json = json.loads(line)
                if i == 0:
                    # Primer evento debe tener hash_anterior None
                    assert event_json["hash_anterior"] is None
                else:
                    # Otros eventos deben tener hash_anterior = hash del anterior
                    prev_event_json = json.loads(lines[i - 1])
                    assert event_json["hash_anterior"] == prev_event_json["hash_evento"]


class TestAuditSearch:
    """Tests para búsqueda de eventos en la auditoría."""

    def test_search_by_lote_id_returns_all_events(self):
        """Búsqueda por lote_id debe retornar todos los eventos del lote."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=tmpdir)
            
            # Crear eventos para 2 lotes
            for lote_num in range(2):
                lote_id = f"INVH-{lote_num:03d}"
                for action_idx, action in enumerate([
                    AuditAction.APERTURA_LOTE,
                    AuditAction.REGISTRO_SOLUCION,
                    AuditAction.REGISTRO_COSECHA,
                ]):
                    event = AuditEvent(
                        action=action,
                        actor_nif="12345678Z",
                        actor_role="operador_invernadero",
                        resource_type="lote",
                        resource_id=lote_id,
                        severity=AuditSeverity.INFO,
                        data={"index": action_idx},
                    )
                    logger.log_event(event)
            
            # Búsqueda por lote_id
            events = logger.search_by_lote_id("INVH-000")
            assert len(events) == 3, "Debe retornar 3 eventos para INVH-000"
            assert all(e.resource_id == "INVH-000" for e in events)

    def test_search_by_operator_shows_accountability(self):
        """Búsqueda por operador debe mostrar todas sus acciones."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=tmpdir)
            
            # Crear eventos de 2 operadores
            operators = ["12345678Z", "87654321A"]
            for op_idx, operator in enumerate(operators):
                for lote_num in range(2):
                    event = AuditEvent(
                        action=AuditAction.REGISTRO_COSECHA,
                        actor_nif=operator,
                        actor_role="operador_invernadero",
                        resource_type="lote",
                        resource_id=f"INVH-{op_idx:03d}-{lote_num}",
                        severity=AuditSeverity.INFO,
                        data={},
                    )
                    logger.log_event(event)
            
            # Búsqueda por operador
            events = logger.search_by_operator("12345678Z")
            assert len(events) == 2, "Operador debe tener 2 eventos"
            assert all(e.actor_nif == "12345678Z" for e in events)

    def test_search_by_action_returns_only_matching_type(self):
        """Búsqueda por acción debe retornar solo eventos del tipo."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=tmpdir)
            
            # Crear eventos de 2 tipos
            actions = [
                AuditAction.APERTURA_LOTE,
                AuditAction.APERTURA_LOTE,
                AuditAction.REGISTRO_COSECHA,
                AuditAction.REGISTRO_COSECHA,
                AuditAction.REGISTRO_COSECHA,
            ]
            for idx, action in enumerate(actions):
                event = AuditEvent(
                    action=action,
                    actor_nif="12345678Z",
                    actor_role="operador_invernadero",
                    resource_type="lote",
                    resource_id=f"INVH-{idx:03d}",
                    severity=AuditSeverity.INFO,
                    data={},
                )
                logger.log_event(event)
            
            # Búsqueda por acción
            events = logger.search_by_action(AuditAction.REGISTRO_COSECHA)
            assert len(events) == 3, "Debe retornar 3 eventos REGISTRO_COSECHA"
            assert all(e.action == AuditAction.REGISTRO_COSECHA for e in events)


class TestAuditSafety:
    """Tests para seguridad de la auditoría."""

    def test_audit_logger_singleton_pattern(self):
        """get_audit_logger() debe retornar la misma instancia."""
        logger1 = get_audit_logger()
        logger2 = get_audit_logger()
        assert logger1 is logger2, "get_audit_logger() debe retornar singleton"

    def test_audit_timestamp_always_utc(self):
        """Los timestamps deben ser sempre en UTC ISO format."""
        event = AuditEvent(
            action=AuditAction.REGISTRO_COSECHA,
            actor_nif="12345678Z",
            actor_role="operador_invernadero",
            resource_type="lote",
            resource_id="INVH-001",
            severity=AuditSeverity.INFO,
            data={},
        )
        
        # Verificar que timestamp es ISO format y UTC
        assert event.timestamp.endswith("+00:00") or event.timestamp.endswith("Z")
        
        # Verificar que es parseable como datetime
        try:
            datetime.fromisoformat(event.timestamp.replace("Z", "+00:00"))
        except ValueError:
            pytest.fail("Timestamp debe ser ISO format válido")


class TestAuditIntegration:
    """Tests de integración para escenarios realistas."""

    def test_full_lote_lifecycle_with_audit_trail(self):
        """Test completo: ciclo de lote con trazabilidad auditada."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=tmpdir)
            
            lote_id = "INVH-TOMATE-001"
            operator_nif = "12345678Z"
            
            # Apertura de lote
            event_apertura = AuditEvent(
                action=AuditAction.APERTURA_LOTE,
                actor_nif=operator_nif,
                actor_role="operador_invernadero",
                resource_type="lote",
                resource_id=lote_id,
                severity=AuditSeverity.INFO,
                data={"cultivo": "tomate", "superficie_m2": 100},
            )
            logger.log_event(event_apertura)
            
            # Registro de solución nutritiva
            event_solucion = AuditEvent(
                action=AuditAction.REGISTRO_SOLUCION,
                actor_nif=operator_nif,
                actor_role="operador_invernadero",
                resource_type="lote",
                resource_id=lote_id,
                severity=AuditSeverity.INFO,
                data={"ph": 6.5, "ec": 1.8},
            )
            logger.log_event(event_solucion)
            
            # Registro de clima
            event_clima = AuditEvent(
                action=AuditAction.REGISTRO_CLIMA,
                actor_nif=operator_nif,
                actor_role="operador_invernadero",
                resource_type="lote",
                resource_id=lote_id,
                severity=AuditSeverity.INFO,
                data={"temp": 22, "hr": 65, "co2": 800},
            )
            logger.log_event(event_clima)
            
            # Cosecha
            event_cosecha = AuditEvent(
                action=AuditAction.REGISTRO_COSECHA,
                actor_nif=operator_nif,
                actor_role="operador_invernadero",
                resource_type="lote",
                resource_id=lote_id,
                severity=AuditSeverity.INFO,
                data={"kg_cosechados": 5000, "brix": 8.5},
            )
            logger.log_event(event_cosecha)
            
            # Búsqueda de toda la cadena del lote
            events = logger.search_by_lote_id(lote_id)
            assert len(events) == 4
            
            # Verificar que el operador es el mismo
            assert all(e.actor_nif == operator_nif for e in events)
            
            # Verificar orden cronológico
            assert events[0].action == AuditAction.APERTURA_LOTE
            assert events[1].action == AuditAction.REGISTRO_SOLUCION
            assert events[2].action == AuditAction.REGISTRO_CLIMA
            assert events[3].action == AuditAction.REGISTRO_COSECHA
            
            # Verificar integridad de cadena
            assert logger.verify_chain_integrity()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
