# -*- coding: utf-8 -*-
"""Pruebas de carga con Locust para SABIONDA Pro (cannabis y microgreens).
Requisito: pip install locust
Uso:
  locust -f tests/load_test_locust.py --host=http://localhost:8000
  Abrir http://localhost:8089 y lanzar usuarios.
Para línea de comandos (sin UI):
  locust -f tests/load_test_locust.py --host=http://localhost:8000 --headless -u 10 -r 2 -t 60s
"""
from __future__ import annotations

import uuid
from locust import HttpUser, task, between


# Cuenta de prueba. Si usas cuenta existente, define env LOCUST_ACCOUNT_ID y LOCUST_USER_ID.
# Si no, cada usuario Locust crea una cuenta en on_start y usa su account_id / user_id.


class CannabisUser(HttpUser):
    """Simula usuarios que crean y listan lotes de cannabis."""

    wait_time = between(1, 5)
    account_id = None
    user_id = None
    license_id = "CAN-20250101-1"

    def on_start(self):
        import os
        self.account_id = os.getenv("LOCUST_ACCOUNT_ID")
        self.user_id = os.getenv("LOCUST_USER_ID")
        if self.account_id and self.user_id:
            return
        r = self.client.post(
            "/pro-accounts/",
            json={
                "email": f"loadtest-{uuid.uuid4().hex[:8]}@example.com",
                "full_name": "Load Test",
                "tier": "enterprise",
                "ethics": {"privacy": 1.0, "transparency": 1.0},
                "restrictions": {},
            },
            name="/pro-accounts/ [POST create]",
        )
        if r.status_code == 200:
            data = r.json()
            self.account_id = data.get("account_id")
            owner = data.get("owner") or {}
            self.user_id = owner.get("user_id")
        if not self.account_id:
            return
        self.client.headers["X-User-ID"] = self.user_id or ""
        # Crear una licencia para que create_batch pueda usarla
        from datetime import datetime, timedelta
        now = datetime.utcnow()
        r2 = self.client.post(
            f"/pro-accounts/{self.account_id}/cannabis/licenses",
            json={
                "holder": owner.get("email", "loadtest@example.com"),
                "valid_from": now.isoformat(),
                "valid_until": (now + timedelta(days=365)).isoformat(),
                "allowed_strains": ["Test Strain"],
                "max_cultivation_area": 100,
                "aemps_reference": "AEMPS-LOAD-TEST",
                "status": "active",
            },
            name="/pro-accounts/[id]/cannabis/licenses [POST]",
        )
        if r2.status_code == 200:
            self.license_id = r2.json().get("license_id", "CAN-20250101-1")
        else:
            self.license_id = "CAN-20250101-1"

    @task(3)
    def list_batches(self):
        if not self.account_id:
            return
        self.client.get(
            f"/pro-accounts/{self.account_id}/cannabis/batches",
            name="/pro-accounts/[id]/cannabis/batches",
        )

    @task(1)
    def create_batch(self):
        if not self.account_id:
            return
        batch_id = f"LOAD-{uuid.uuid4().hex[:8]}"
        self.client.post(
            f"/pro-accounts/{self.account_id}/cannabis/batches",
            json={
                "batch_id": batch_id,
                "strain": {
                    "strain_id": "test_strain",
                    "name": "Test Strain",
                    "thc_percentage": 0.2,
                    "cbd_percentage": 12.0,
                    "cultivation_license": getattr(self, "license_id", "CAN-20250101-1"),
                    "batch_size": 10,
                    "compliance_standards": ["RD_903_2025", "GMP"],
                },
                "cultivation_site": "CTAEX-Badajoz",
                "planting_date": "2025-01-01T00:00:00",
                "weight": 0,
                "account_id": self.account_id,
            },
            name="/pro-accounts/[id]/cannabis/batches [POST]",
        )


class MicrogreensUser(HttpUser):
    """Simula usuarios que listan variedades y lotes de microgreens."""

    wait_time = between(1, 4)
    account_id = None
    user_id = None

    def on_start(self):
        import os
        self.account_id = os.getenv("LOCUST_ACCOUNT_ID")
        self.user_id = os.getenv("LOCUST_USER_ID")
        if self.account_id and self.user_id:
            self.client.headers["X-User-ID"] = self.user_id
            return
        r = self.client.post(
            "/pro-accounts/",
            json={
                "email": f"loadtest-mg-{uuid.uuid4().hex[:8]}@example.com",
                "full_name": "Load Test Microgreens",
                "tier": "enterprise",
                "ethics": {},
                "restrictions": {},
            },
            name="/pro-accounts/ [POST create]",
        )
        if r.status_code == 200:
            data = r.json()
            self.account_id = data.get("account_id")
            owner = data.get("owner") or {}
            self.user_id = owner.get("user_id")
            self.client.headers["X-User-ID"] = self.user_id or ""

    @task(2)
    def list_varieties(self):
        if not self.account_id:
            return
        self.client.get(
            f"/pro-accounts/{self.account_id}/microgreens/varieties",
            name="/pro-accounts/[id]/microgreens/varieties",
        )

    @task(1)
    def list_batches(self):
        if not self.account_id:
            return
        self.client.get(
            f"/pro-accounts/{self.account_id}/microgreens/batches",
            name="/pro-accounts/[id]/microgreens/batches",
        )
