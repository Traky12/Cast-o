from __future__ import annotations

from pathlib import Path


def test_iot_grafana_dashboard_provisioning_path_exists() -> None:
    compose_file = Path("docker-compose.iot.yml")
    compose_text = compose_file.read_text(encoding="utf-8")

    # Garantiza que el volumen de dashboards de Grafana apunte a una ruta real del repo.
    expected_mapping = (
        "./infrastructure/thingsdata/grafana-dashboard.json:"
        "/etc/grafana/provisioning/dashboards/grafana-dashboard.json:ro"
    )
    assert expected_mapping in compose_text
    assert Path("infrastructure/thingsdata/grafana-dashboard.json").exists()
