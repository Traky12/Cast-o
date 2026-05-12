# ISO 27001:2022 Annex A.13 Evidence

Scope: Network security controls for CASTUO-SYSTEM.

Implemented controls:
- A.13.1.1 Network controls: hybrid firewall architecture in place.
- A.13.1.2 Security of network services: segmented traffic with policies.
- A.13.1.3 Segregation in networks / application protection: WAF rules via ModSecurity.

Technical evidence pointers:
- infrastructure/security/modsecurity/custom_rules.conf
- k8s/network-policies/deny-all-except-api.yaml
- k8s/network-policies/allow-mqtt.yaml
- tests/test_hybrid_firewall_stack.py

Operational status:
- Control baseline implemented and test-verified.
