from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: Path) -> str:
    assert path.exists(), f"Falta archivo requerido: {path}"
    return path.read_text(encoding="utf-8")


def test_hybrid_security_runbook_exists_and_mentions_compliance() -> None:
    doc_path = ROOT / "docs" / "ops" / "RUNBOOK-SEGURIDAD-HIBRIDA.md"
    doc = _read(doc_path)

    assert "NIST SP 800-41" in doc
    assert "ISO 27001:2022" in doc
    assert "NIS2" in doc
    assert "CRA" in doc
    assert "AI Act" in doc
    assert "OPNsense" in doc
    assert "ModSecurity" in doc
    assert "Calico" in doc
    assert "Suricata" in doc
    assert "Algorand" in doc


def test_k8s_network_policies_for_api_and_mqtt_exist() -> None:
    deny_all = ROOT / "k8s" / "network-policies" / "deny-all-except-api.yaml"
    allow_mqtt = ROOT / "k8s" / "network-policies" / "allow-mqtt.yaml"

    deny_content = _read(deny_all)
    mqtt_content = _read(allow_mqtt)

    assert "kind: NetworkPolicy" in deny_content
    assert "namespace: castuo-system" in deny_content
    assert "port: 8000" in deny_content
    assert "port: 5432" in deny_content

    assert "kind: NetworkPolicy" in mqtt_content
    assert "namespace: castuo-system" in mqtt_content
    assert "port: 1883" in mqtt_content


def test_modsecurity_and_suricata_configs_exist() -> None:
    modsec_compose = ROOT / "infrastructure" / "security" / "docker-compose.security.yml"
    modsec_rules = ROOT / "infrastructure" / "security" / "modsecurity" / "custom_rules.conf"
    suricata_rules = ROOT / "infrastructure" / "security" / "suricata" / "custom.rules"

    compose_content = _read(modsec_compose)
    rules_content = _read(modsec_rules)
    suricata_content = _read(suricata_rules)

    assert "modsecurity" in compose_content
    assert "suricata" in compose_content
    assert "elasticsearch" in compose_content
    assert "kibana" in compose_content

    assert "SQL Injection Attempt" in rules_content
    assert "XSS Attempt" in rules_content
    assert "Rate Limit Exceeded" in rules_content

    assert "Port Scan Detected" in suricata_content
    assert "SSH Brute Force" in suricata_content


def test_hybrid_security_script_and_make_target_exist() -> None:
    script_path = ROOT / "scripts" / "security-hybrid-check.sh"
    script = _read(script_path)

    assert script.startswith("#!/usr/bin/env bash")
    assert "kubectl get networkpolicies" in script
    assert "docker compose -f infrastructure/security/docker-compose.security.yml" in script
    assert "artifacts/security-hybrid" in script

    makefile = _read(ROOT / "Makefile")
    assert "security-hybrid-check" in makefile
