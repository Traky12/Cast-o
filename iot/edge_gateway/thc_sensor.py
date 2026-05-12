from __future__ import annotations

import argparse
import random
import time
from typing import Any, Dict, List

import httpx


def capture_spectrum() -> List[float]:
    return [round(random.random(), 6) for _ in range(157)]


def post_json(url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    with httpx.Client(timeout=30.0) as client:
        r = client.post(url, json=payload)
        r.raise_for_status()
        return r.json()


def run_flow(server_url: str, batch_id: str, plant_id: str, zone_id: str, simulate_lims: bool) -> None:
    estimate_payload = {
        "batch_id": batch_id,
        "plant_id": plant_id,
        "zone_id": zone_id,
        "spectrum": capture_spectrum(),
    }
    estimate = post_json(f"{server_url.rstrip('/')}/thc/estimate", estimate_payload)
    print("[ESTIMATION]", estimate)

    if simulate_lims:
        time.sleep(2)
        validate_payload = {
            "batch_id": batch_id,
            "lab_certificate": "LIMS-ABC123",
            "thc_validated": 18.5,
            "validation_method": "HPLC",
        }
        validated = post_json(f"{server_url.rstrip('/')}/thc/validate_lims", validate_payload)
        print("[LIMS_VALIDATION]", validated)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simulador NIR para flujo THC")
    parser.add_argument("--server-url", default="http://localhost:8000")
    parser.add_argument("--batch-id", default=f"batch-{int(time.time())}")
    parser.add_argument("--plant-id", default="plant-001")
    parser.add_argument("--zone-id", default="default")
    parser.add_argument("--simulate-lims", action="store_true")
    args = parser.parse_args()
    run_flow(args.server_url, args.batch_id, args.plant_id, args.zone_id, args.simulate_lims)
