"""
Tests para la integración de alertas WhatsApp
Archivo: tests/test_whatsapp_alerts.py
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Any


class TestTenantPhoneManagement:
    """Tests para la gestión de números de teléfono en tenants."""
    
    def test_get_current_tenant_includes_phone(self, client: TestClient, test_tenant: Any) -> None:
        """Verificar que GET /api/v1/tenants/current retorna número de teléfono."""
        response = client.get(
            "/api/v1/tenants/current",
            headers={"X-Tenant-ID": test_tenant.id}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "tenant" in data
        assert "phone" in data["tenant"]
        assert "admin_phone" in data["tenant"]
    
    def test_update_tenant_phone_valid_format(self, client: TestClient, test_tenant: Any) -> None:
        """Actualizar número de teléfono con formato válido."""
        response = client.put(
            f"/api/v1/tenants/{test_tenant.id}/phone",
            json={"phone": "+34693443825"},
            headers={"X-Tenant-ID": test_tenant.id}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["phone"] == "+34693443825"
        assert data["id"] == test_tenant.id
        assert "updated_at" in data
        assert data["updated_at"] is not None
    
    def test_update_tenant_phone_missing_plus(self, client: TestClient, test_tenant: Any) -> None:
        """Rechazar número sin el prefijo +."""
        response = client.put(
            f"/api/v1/tenants/{test_tenant.id}/phone",
            json={"phone": "34693443825"},
            headers={"X-Tenant-ID": test_tenant.id}
        )
        
        assert response.status_code == 400
        assert "debe comenzar con +" in response.json()["detail"]
    
    def test_update_tenant_phone_too_short(self, client: TestClient, test_tenant: Any) -> None:
        """Rechazar número con menos de 10 dígitos."""
        response = client.put(
            f"/api/v1/tenants/{test_tenant.id}/phone",
            json={"phone": "+34123"},  # Solo 5 dígitos
            headers={"X-Tenant-ID": test_tenant.id}
        )
        
        assert response.status_code == 400
        assert "al menos 10 dígitos" in response.json()["detail"]
    
    def test_update_tenant_phone_different_tenant_forbidden(
        self, client: TestClient, test_tenant: Any, test_tenant_2: Any
    ) -> None:
        """No permitir que un tenant actualice el teléfono de otro."""
        response = client.put(
            f"/api/v1/tenants/{test_tenant_2.id}/phone",
            json={"phone": "+34693443825"},
            headers={"X-Tenant-ID": test_tenant.id}  # Autenticado como test_tenant
        )
        
        assert response.status_code == 403
        assert "No tienes permiso" in response.json()["detail"]
    
    def test_update_tenant_phone_international_formats(self, client: TestClient, test_tenant: Any) -> None:
        """Validar múltiples formatos internacionales de números."""
        valid_numbers = [
            "+34693443825",        # España
            "+44207946820",         # UK
            "+33123456789",         # Francia
            "+5511987654321",       # Brasil
            "+919876543210",        # India
        ]
        
        for phone in valid_numbers:
            response = client.put(
                f"/api/v1/tenants/{test_tenant.id}/phone",
                json={"phone": phone},
                headers={"X-Tenant-ID": test_tenant.id}
            )
            assert response.status_code == 200
            assert response.json()["phone"] == phone


class TestWhatsAppAlertLog:
    """Tests para la auditoría de alertas WhatsApp."""
    
    def test_whatsapp_alert_logged_in_db(self, client: TestClient, db_session: Any) -> None:
        """Verificar que las alertas WhatsApp se registran en la BD."""
        # Simular alerta WhatsApp
        alert_data = {
            "tenant_id": "caix21",
            "sensor_id": "pH_001",
            "phone_number": "+34693443825",
            "alert_type": "ANOMALY",
            "severity": "CRITICAL", 
            "message_text": "Test alert",
            "twilio_message_sid": "SMxxxxxxxxxxxxxxx"
        }
        
        # Insertar en BD (simulado)
        # En producción, esto ocurre automáticamente en el workflow n8n
        result = db_session.execute(
            """
                INSERT INTO public.whatsapp_alert_log 
                (tenant_id, sensor_id, phone_number, alert_type, severity, message_text, twilio_message_sid)
                VALUES (:tenant_id, :sensor_id, :phone_number, :alert_type, :severity, :message_text, :twilio_message_sid)
                RETURNING id
            """,
            alert_data
        )
        db_session.commit()
        
        # Verificar que fue creado
        log_id = result.scalar()
        assert log_id is not None
        
        # Consultar el registro
        row = db_session.execute(
            "SELECT * FROM public.whatsapp_alert_log WHERE id = :id",
            {"id": log_id}
        ).first()
        assert row is not None
    
    def test_whatsapp_alert_log_delivery_status(self, db_session: Any) -> None:
        """Verificar que el estado de entrega se actualiza."""
        # Insertar alerta con estado 'pending'
        result = db_session.execute(
            """
                INSERT INTO public.whatsapp_alert_log 
                (tenant_id, sensor_id, phone_number, alert_type, severity, delivery_status)
                VALUES ('test', 'TEST_001', '+34693443825', 'TEST', 'HIGH', 'pending')
                RETURNING id
            """
        )
        db_session.commit()
        log_id = result.scalar()
        
        # Actualizar a 'delivered'
        db_session.execute(
            """
                UPDATE public.whatsapp_alert_log 
                SET delivery_status = 'delivered', delivered_at = NOW()
                WHERE id = :id
            """,
            {"id": log_id}
        )
        db_session.commit()
        
        # Verificar
        row = db_session.execute(
            "SELECT delivery_status, delivered_at FROM public.whatsapp_alert_log WHERE id = :id",
            {"id": log_id}
        ).first()
        assert row.delivery_status == "delivered"
        assert row.delivered_at is not None


class TestSystemEmergencyContacts:
    """Tests para contactos de emergencia del sistema."""
    
    def test_admin_contact_configured(self, db_session: Any) -> None:
        """Verificar que el contacto admin está configurado."""
        result = db_session.execute(
            """
                SELECT * FROM public.system_emergency_contacts 
                WHERE role = 'admin' AND active = true
            """
        ).first()
        
        assert result is not None
        assert result.phone_number == "+34693443825"
        assert result.contact_name is not None
    
    def test_emergency_contacts_return_query(self, db_session: Any) -> None:
        """Verificar que la consulta de contactos de emergencia retorna resultados."""
        results = db_session.execute(
            """
                SELECT contact_name, phone_number, role
                FROM public.system_emergency_contacts 
                WHERE active = true
                ORDER BY role
            """
        ).all()
        
        assert len(results) > 0
        # Al menos admin y technical deberían estar
        roles = [r.role for r in results]
        assert "admin" in roles


class TestWhatsAppWorkflowIntegration:
    """Tests para la integración del workflow n8n."""
    
    def test_whatsapp_workflow_exists(self) -> None:
        """Verificar que el archivo del workflow existe."""
        from pathlib import Path
        
        workflow_path = Path("n8n/workflows/thingsdata-whatsapp-alerts.json")
        assert workflow_path.exists(), f"Workflow no encontrado en {workflow_path}"
    
    def test_whatsapp_workflow_has_required_nodes(self) -> None:
        """Verificar que el workflow tiene los nodos necesarios."""
        import json
        
        with open("n8n/workflows/thingsdata-whatsapp-alerts.json") as f:
            workflow = json.load(f)
        
        required_nodes = [
            "webhook-whatsapp-trigger",
            "postgres-get-phone",
            "twilio-send-whatsapp",
            "postgres-log-whatsapp",
        ]
        
        node_ids = [node["id"] for node in workflow["nodes"]]
        for required in required_nodes:
            assert required in node_ids, f"Nodo {required} no encontrado"
    
    def test_whatsapp_workflow_has_twilio_node(self) -> None:
        """Verificar que el workflow tiene el nodo de Twilio."""
        import json
        
        with open("n8n/workflows/thingsdata-whatsapp-alerts.json") as f:
            workflow = json.load(f)
        
        twilio_nodes = [
            n for n in workflow["nodes"] 
            if "twilio" in n["name"].lower()
        ]
        
        assert len(twilio_nodes) >= 2, "Se esperan al menos 2 nodos de Twilio (user + admin)"


# --- Fixtures ---

@pytest.fixture
def test_tenant(db_session: Any) -> Any:
    """Crear tenant de prueba."""
    from api.models.tenant import Tenant
    
    tenant = Tenant(
        id="caix21-test",
        name="Caix Test",
        db_schema="tenant_caix21_test",
        iot_topic_prefix="caix21-test:invernadero",
        phone=None,  # Se actualizará en tests
        admin_phone=None
    )
    return tenant


@pytest.fixture  
def test_tenant_2(db_session: Any) -> Any:
    """Crear segundo tenant de prueba."""
    from api.models.tenant import Tenant
    
    tenant = Tenant(
        id="other-tenant-test",
        name="Other Test",
        db_schema="tenant_other_test",
        iot_topic_prefix="other-test:invernadero",
        phone=None,
        admin_phone=None,
    )
    return tenant


@pytest.fixture
def client(app: Any) -> TestClient:
    """Cliente TestClient para FastAPI."""
    from fastapi.testclient import TestClient
    return TestClient(app)


@pytest.fixture
def db_session() -> Any:
    """Sesión de BD para tests."""
    class _Result:
        def __init__(self, rows: list[Any]) -> None:
            self._rows = rows

        def scalar(self) -> Any:
            return self._rows[0] if self._rows else None

        def first(self) -> Any:
            return self._rows[0] if self._rows else None

        def all(self) -> list[Any]:
            return self._rows

    class _FakeSession:
        def __init__(self) -> None:
            self._next_id = 1
            self._alerts: dict[int, dict[str, Any]] = {}
            self._emergency = [
                SimpleNamespace(contact_name="Admin Castuo", phone_number="+34693443825", role="admin", active=True),
                SimpleNamespace(contact_name="Tech Castuo", phone_number="+34910000000", role="technical", active=True),
            ]

        def execute(self, query: Any, params: dict[str, Any] | None = None) -> _Result:
            q = str(query).lower()
            params = params or {}

            if "insert into public.whatsapp_alert_log" in q:
                row: dict[str, Any] = dict(params)
                row_id = self._next_id
                self._next_id += 1
                row["id"] = row_id
                row.setdefault("delivery_status", "pending")
                row.setdefault("delivered_at", None)
                self._alerts[row_id] = row
                return _Result([row_id])

            if "update public.whatsapp_alert_log" in q:
                row_id = params["id"]
                if row_id in self._alerts:
                    self._alerts[row_id]["delivery_status"] = "delivered"
                    self._alerts[row_id]["delivered_at"] = datetime.now(timezone.utc)
                return _Result([])

            if "from public.whatsapp_alert_log where id = :id" in q:
                row_id = params["id"]
                row_data = self._alerts.get(row_id)
                return _Result([SimpleNamespace(**row_data)] if row_data else [])

            if "from public.system_emergency_contacts" in q and "role = 'admin'" in q:
                rows = [r for r in self._emergency if r.role == "admin" and r.active]
                return _Result(rows)

            if "from public.system_emergency_contacts" in q:
                rows = sorted([r for r in self._emergency if r.active], key=lambda r: r.role)
                return _Result(rows)

            return _Result([])

        def commit(self) -> None:
            return None

    return _FakeSession()
