from __future__ import annotations

import json
from pathlib import Path


def test_holo_k8s_manifests_exist_and_have_expected_kinds() -> None:
    deployment_file = Path("k8s/holo/holo-api-deployment.yaml")
    service_file = Path("k8s/holo/holo-api-service.yaml")
    network_policy_file = Path("k8s/holo/holo-network-policy.yaml")

    assert deployment_file.exists()
    assert service_file.exists()
    assert network_policy_file.exists()

    deployment_text = deployment_file.read_text(encoding="utf-8")
    service_text = service_file.read_text(encoding="utf-8")
    network_policy_text = network_policy_file.read_text(encoding="utf-8")

    assert "kind: Deployment" in deployment_text
    assert "app: castuo-holo-api" in deployment_text
    assert "kind: Service" in service_text
    assert "name: castuo-holo-api-service" in service_text
    assert "kind: NetworkPolicy" in network_policy_text
    assert "name: castuo-holo-api-restricted" in network_policy_text


def test_holo_n8n_workflow_chain_tracking_mistral_haptics() -> None:
    workflow_file = Path("n8n/workflows/holo-tracking-mistral-haptics.json")
    assert workflow_file.exists()

    payload = json.loads(workflow_file.read_text(encoding="utf-8"))
    assert payload["name"] == "Holo - Tracking -> Mistral -> Haptics"

    node_names = {node["name"] for node in payload.get("nodes", [])}
    assert "Webhook - Tracking Event" in node_names
    assert "HTTP - Mistral Analyze" in node_names
    assert "HTTP - Trigger Haptics" in node_names
