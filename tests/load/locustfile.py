"""
Carga sobre API de aleaciones vegetales (prefijo /vegetal-alloys).
Objetivo operativo: validar p95 y errores en staging; el limite real lo marca cluster + DB.
"""

from __future__ import annotations

import random

from locust import HttpUser, between, task


class VegetalAlloyUser(HttpUser):
    wait_time = between(0.5, 2.0)
    alloy_id: int = 1

    def on_start(self) -> None:
        payload = {
            "name": f"load-{random.randint(1, 10_000_000)}",
            "source_crop": random.choice(["stevia", "microgreens", "algae", "hemp"]),
            "chemical_composition": {
                "cellulose": round(random.uniform(30, 60), 2),
                "lignin": round(random.uniform(10, 30), 2),
                "hemicellulose": round(random.uniform(5, 20), 2),
            },
            "physical_properties": {
                "tensile_strength": round(random.uniform(20, 60), 2),
                "density": round(random.uniform(0.8, 1.5), 3),
                "biodegradability": round(random.uniform(70, 100), 2),
            },
        }
        with self.client.post(
            "/vegetal-alloys/alloys/",
            json=payload,
            catch_response=True,
            name="POST /vegetal-alloys/alloys/",
        ) as r:
            if r.status_code == 200:
                try:
                    self.alloy_id = int(r.json().get("id", 1))
                except (TypeError, ValueError):
                    r.failure("respuesta sin id valido")
            else:
                r.failure(f"status {r.status_code}")

    @task(4)
    def create_alloy(self) -> None:
        payload = {
            "name": f"BioPLA-{random.randint(1, 10_000_000)}",
            "source_crop": random.choice(["stevia", "cannabis_medicinal", "microgreens", "algae"]),
            "chemical_composition": {
                "cellulose": round(random.uniform(30, 60), 2),
                "lignin": round(random.uniform(10, 30), 2),
                "hemicellulose": round(random.uniform(5, 20), 2),
            },
            "physical_properties": {
                "tensile_strength": round(random.uniform(20, 60), 2),
                "density": round(random.uniform(0.8, 1.5), 3),
                "biodegradability": round(random.uniform(70, 100), 2),
            },
        }
        self.client.post("/vegetal-alloys/alloys/", json=payload, name="POST /vegetal-alloys/alloys/")

    @task(2)
    def get_alloy(self) -> None:
        aid = random.randint(1, max(self.alloy_id, 1))
        self.client.get(f"/vegetal-alloys/alloys/{aid}", name="GET /vegetal-alloys/alloys/[id]")

    @task(1)
    def chemaxon_analysis(self) -> None:
        smiles = random.choice(
            [
                "CC(O)C",
                "C1=CC=C(C=C1)O",
                "C(=O)O",
                "CCCCCC",
                "CC(=O)O",
            ]
        )
        self.client.post(
            f"/vegetal-alloys/alloys/{self.alloy_id}/chemaxon",
            json={"smiles": smiles},
            name="POST /vegetal-alloys/alloys/[id]/chemaxon",
        )
