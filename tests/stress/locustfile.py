"""
Carga opcional contra el robotics lab stub (inferencia neuromórfica).
Requisitos: pip install locust; lab en marcha; `CASTUO_ROBOTICS_LAB_BEARER_TOKEN` (o alias `CASTUO_LAB_BEARER_TOKEN`) coherente con el servidor.

  locust -f tests/stress/locustfile.py --host http://127.0.0.1:8011
"""

from __future__ import annotations

import os

from locust import HttpUser, between, task


class RoboticsLabNeuroUser(HttpUser):
    wait_time = between(0.3, 1.5)

    def on_start(self) -> None:
        self.token = (
            os.environ.get("CASTUO_ROBOTICS_LAB_BEARER_TOKEN")
            or os.environ.get("CASTUO_LAB_BEARER_TOKEN")
            or "dev-castuo-lab-bearer"
        ).strip()

    @task
    def neuro_hydro_infer(self) -> None:
        self.client.post(
            "/api/robotics/lab/neuromorphic/hydroponics/infer",
            json={
                "humedad": 42.0,
                "ph": 6.2,
                "ec": 1.5,
                "luz_umol": 400.0,
            },
            headers={"Authorization": f"Bearer {self.token}"},
            name="neuro_hydro_infer",
        )
