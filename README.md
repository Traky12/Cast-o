<!-- CASTUO:BRAND:START -->
<p align="center">
  <img src="https://raw.githubusercontent.com/Traky12/Traky12/main/assets/brand/castuo-system-logo-square.jpg" alt="CASTÚO-SYSTEM official logo" width="180" />
</p>
<!-- CASTUO:BRAND:END -->

# 🧪 Cast-o — Automated Testing & Benchmarking

![Status](https://img.shields.io/badge/Status-Active%20Engineering-blue)
![Maturity](https://img.shields.io/badge/Maturity-Implementado-informational)
![License](https://img.shields.io/badge/License-AGPL--3.0-yellow)

> **Automated testing and performance benchmarking engine for CASTÚO-SYSTEM™**

---

## 1. Purpose & Scope
**Cast-o** is the quality assurance and performance engine of the ecosystem. It provides a unified environment to structure, automate, and validate the CASTÚO-SYSTEM ecosystem through tests, infrastructure-as-code, and integration tools.

Its scope covers:
- **Automated Testing:** Unit, integration, and E2E tests (`pytest`, Playwright).
- **Infrastructure Validation:** Terraform (Hetzner) and Kubernetes manifests.
- **IoT & Edge Simulation:** ESP32 code and MQTT integration testing.
- **Performance Benchmarking:** Regression detection and resource usage analysis.
- **CI/CD Support:** Reusable pipelines and hardening checklists.

---

## 2. Ecosystem Position
Cast-o acts as the **TOOLING** anchor, providing the necessary infrastructure for technical validation across all layers.

```text
Cast-o (Tooling)
     │
     ├── CASTÚO-SYSTEM (Core)
     │      Validation target
     │
     ├── GOLDfish (Assurance)
     │      Evidence provider
     │
     └── castuo-agro-edge (Edge)
            Performance benchmark target
```

---

## 3. Core Components
- **Testing Framework:** Unit, integration, and E2E tests for AI and IoT components.
- **Dockerized Environments:** Modular `docker-compose` files for IoT, Cloud, and HA scenarios.
- **Infrastructure as Code:** Terraform assets for Hetzner and K8s manifests.
- **Observability:** Monitoring configurations for Prometheus and Grafana.
- **Documentation & Diagnostics:** System diagnostics, integration checklists, and contingency reports.

---

## 4. Engineering & Evidence
Following the **Evidence-First** principle, Cast-o provides the raw data that supports maturity claims in the ecosystem.
- **Implemented:** Unit and integration test suites, Docker environments, and IaC bases.
- **Validated:** Performance benchmarking for core API endpoints and CI/CD automation.

Every test run generates a verifiable record linked to the target commit, federated in **CASTÚO-EVOLUTION**.

---

## 5. Quick Start
```bash
git clone https://github.com/Traky12/Cast-o.git
cd Cast-o
cp .env.example .env
docker compose up -d
pytest tests/ -v
```

---

## 6. Navigation
[← Ecosystem Profile](https://github.com/Traky12) | [→ Core Platform](https://github.com/Traky12/Castuo-system) | [→ Assurance](https://github.com/Traky12/goldfish) | [→ Architecture Docs](docs/)

---

## 🌐 Connect
- 🌍 [Website](https://castuo-system.es/)
- 🧪 [Cast-o Repository](https://github.com/Traky12/Cast-o)

**Build · Validate · Observe · Document · Evolve**

## Architecture governance boundary

This repository is governed through the CASTÚO-SYSTEM evidence chain. Its current role, visibility boundary, required provenance, security baseline and promotion rules are defined in [`docs/CASTUO_ARCHITECTURE_GOVERNANCE.md`](docs/CASTUO_ARCHITECTURE_GOVERNANCE.md). A repository artifact or green workflow proves only the declared scope; it does not by itself prove certification, production operation, funding, customer contracts or commercial success.

## Negative assurance boundary

The assurance suite must test both accepted and rejected paths: unregistered agent, unauthorised tool, incorrect tenant, revoked credential, duplicate replay, missing evidence hash, unapproved model, sensitive action without approval, disconnected node, synchronisation conflict, rollback request and incompatible version.

The minimum failure contract is:

```text
denied request → logged → explainable → recoverable
```

A passing local test proves only the declared test scope. It does not prove federated operation, production security, customer adoption or regulatory conformity.

## Private-cloud and evidence boundary

This repository is part of the CASTÚO-SYSTEM private-cloud target architecture. Its repository scope does not by itself prove cloud provisioning, DNS, production operation, customer traction, financing, certification or independent validation. The service identity is a governed target boundary until a deployment record, access control, health check, observability, backup, restore, rollback, owner and dated Evidence Center record are published.

The public state model is `DOCUMENTED` → `IMPLEMENTED_LOCAL` → `TESTED` → `VALIDATED` → `OPERATIONAL`. OpenClaw and n8n, where referenced, are optional compatibility adapters and not the sovereign governance control plane.\n

<!-- CASTUO:PUBLIC-SURFACE -->
## CASTÚO integration boundary

This repository exposes only a bounded public integration surface. Its role, current state and claims are subordinate to the `Traky12/castuo-evolution` control plane.

This repository does not by itself claim production operation, certification, independent validation, customer contracts, revenue, autonomous authority, global federation or legal compliance. Do not publish secrets, credentials, private endpoints, customer data, private evidence or unpublished security findings.

See [`docs/CASTUO_PUBLIC_SURFACE.md`](docs/CASTUO_PUBLIC_SURFACE.md) for the public boundary. `Claim != Evidence`; `CURRENT != TARGET`; promotion requires control-plane authorization.
<!-- CASTUO:PUBLIC-SURFACE-END -->
