# 🧪 Cast-o — Automated Testing & Assurance

![Status](https://img.shields.io/badge/Status-Active%20Engineering-blue)
![Claims](https://img.shields.io/badge/Claims-see%20status%20table-informational)
![License](https://img.shields.io/badge/License-PENDING-lightgrey)

> **Automated testing and assurance tooling for CASTÚO-SYSTEM™. Performance benchmarking is a `TARGET`, not a current capability — see [§4](#4-claims-status).**

> **License: `PENDING`.** No open-source license has been granted yet. Until a `LICENSE` file is published, default copyright applies (all rights reserved by the author). The previous AGPL-3.0 badge was removed because no license file backed it.

---

## 1. Purpose & Scope
**Cast-o** is the quality assurance and performance engine of the ecosystem. It provides a unified environment to structure, automate, and validate the CASTÚO-SYSTEM ecosystem through tests, infrastructure-as-code, and integration tools.

Its scope covers:
- **Automated Testing:** Unit and integration tests (`pytest`).
- **Infrastructure Validation:** Terraform (Hetzner) and Kubernetes manifests.
- **IoT & Edge Simulation:** ESP32 code and MQTT integration testing.
- **Performance Benchmarking (`TARGET`):** Regression detection and resource usage analysis — not implemented yet.
- **CI/CD Support:** Reusable pipelines and hardening checklists.

---

## 2. Ecosystem Position
Cast-o acts as the **TOOLING** anchor, providing the necessary infrastructure for technical validation across all layers.

```text
Cast-o (Assurance)
     │
     ├── castuo-evidence (Public Fabric)
     │      Evidence verification target
     │
     ├── CASTÚO-SYSTEM (Private Core)
     │      Execution engine
     │
     └── castuo-evolution (External surface)
            Prepared external surface — not the current
            GitHub authority nor a synchronised SSOT
```

**Canonical authority:** `Castuo-system` (private) is the current authority for code, operational documentation and technical evolution. `castuo-evolution` is an external, prepared surface; it is not presented as the current GitHub authority or a synchronised source of truth.

---

## 3. Core Components
- **Testing Framework:** Unit, integration, and E2E tests for AI and IoT components.
- **Dockerized Environments:** Modular `docker-compose` files for IoT, Cloud, and HA scenarios.
- **Infrastructure as Code:** Terraform assets for Hetzner and K8s manifests.
- **Observability:** Monitoring configurations for Prometheus and Grafana.
- **Documentation & Diagnostics:** System diagnostics, integration checklists, and contingency reports.

---

## 4. Claims status
Every claim uses one status: `CURRENT` (implemented and verifiable) · `TARGET` (approved objective, not implemented) · `EXPERIMENTAL` (prototype, not consolidated) · `PENDING` (planned, or evidence incomplete) · `NOT_CLAIMED` (not implemented; not presented as a capability).

| Claim | Status | Evidence / limitation |
|---|---|---|
| Unit and integration test suite (`pytest`) | `CURRENT` (partial) | Commit `d57936c`, local run 2026-09-28 (Windows, Python 3.12): 463 passed, 3 failed, 7 errors, plus 1 collection error (`tests/test_router_hardening.py`). The `Python validation` workflow fails on `main` (flake8 E999: `test_e2e.py` is a bash script). |
| CI/CD automation (GitHub Actions) | `CURRENT` (partial) | Several workflows run on schedule. Known reds on `main`: Agent Sync Hardening (drift false positive, fix in PR #27), Reconcile CI/CD, 48h Operativity Gate, docker-security. |
| Docker Compose environments | `PENDING` | Compose files exist (IoT, cloud, HA, …); no recorded run evidence. |
| Infrastructure as Code (Terraform, Kubernetes) | `PENDING` | 3 `.tf` files and K8s manifests exist; no `plan`/`apply` evidence. |
| Observability (Prometheus, Grafana) | `PENDING` | Configuration files exist; no deployment evidence from this repository. |
| IoT / ESP32 / MQTT simulation | `EXPERIMENTAL` | Sample code present; not consolidated or tested end to end. |
| Performance benchmarking | `TARGET` | No benchmark code, dataset, method or results in this repository. Per [`docs/CASTUO_ARCHITECTURE_GOVERNANCE.md`](docs/CASTUO_ARCHITECTURE_GOVERNANCE.md), a benchmark is valid only with dataset, version, environment and method. |
| E2E browser tests (Playwright) | `NOT_CLAIMED` | Playwright is not present in this repository. |
| Test records federated into CASTÚO-EVOLUTION | `NOT_CLAIMED` | No federation mechanism is implemented. |

---

## 5. Quick Start
```bash
git clone https://github.com/Traky12/Cast-o.git
cd Cast-o
cp .env.example .env
pytest tests/ -v   # partial: see §4 for current failures
```

`docker compose up -d` is `PENDING` verification (see §4).

---

## 6. Navigation
[← Profile](https://github.com/Traky12) | [→ Evidence](https://github.com/Traky12/castuo-evidence) | [→ Governance scope](docs/CASTUO_ARCHITECTURE_GOVERNANCE.md) | [→ Architecture Docs](docs/)

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

Public claims use the status taxonomy in [§4](#4-claims-status). OpenClaw and n8n, where referenced, are optional third-party compatibility adapters and not the sovereign governance control plane.
