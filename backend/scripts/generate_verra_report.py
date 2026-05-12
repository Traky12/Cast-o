#!/usr/bin/env python3
"""
Genera informes en formato VCS para Verra (créditos de carbono).
Uso: python3 scripts/generate_verra_report.py <farm_id> <co2_saved_kg> [project_id]
Ejemplo: python3 scripts/generate_verra_report.py farm-eu-001 12 VCS-1234
"""
import json
import os
import sys
from datetime import datetime


def generate_verra_report(
    farm_id: str,
    co2_saved_kg: float,
    project_id: str = "VCS-1234",
    sensors_data: dict = None,
    gaiachain_tx: str = "",
    output_dir: str = "verra_reports",
) -> dict:
    report = {
        "project_id": project_id,
        "farm_id": farm_id,
        "co2_saved_kg": co2_saved_kg,
        "methodology": "VM0042",
        "date": datetime.now().isoformat(),
        "sensors_data": sensors_data or {"ec": 1.8, "ph": 6.1, "temperature": 22.5},
        "gaiachain_tx": gaiachain_tx or "0x...",
    }
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, f"{farm_id}_{datetime.now().date()}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    return report


def main():
    if len(sys.argv) < 3:
        print("Uso: generate_verra_report.py <farm_id> <co2_saved_kg> [project_id]", file=sys.stderr)
        sys.exit(1)
    farm_id = sys.argv[1]
    co2_saved_kg = float(sys.argv[2])
    project_id = sys.argv[3] if len(sys.argv) > 3 else "VCS-1234"
    report = generate_verra_report(farm_id, co2_saved_kg, project_id=project_id)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
