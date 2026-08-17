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

<!-- CASTUO-GOVERNED-README-BLOCK:START -->
## CASTÚO-SYSTEM governed operating model

This repository is part of the CASTÚO-SYSTEM evidence operating system. Its status is governed by implementation, evidence and promotion gates; repository presence or vendor language is not evidence of operational maturity.

### Three-plane architecture

| Plane | Role | Repository boundary |
|---|---|---|
| Internal control plane | Capabilities, evidence, claims, gates, passports and N3/N4/N5/N6 maturity | This repository's contracts and governed records |
| Competitive intelligence | 1/0/?/N/A comparison, 1D/1V/1R semantics, scenarios and sensitivity | Comparative records remain bounded by provenance |
| External validation | Independent review, reproducible benchmark, field pilot, KPIs and economic evidence | Promotion requires reviewable external evidence |

### Claim discipline

`CAPABILITY` is not `EVIDENCE`; `EVIDENCE` is not `MATURITY`; `MATURITY` is not `CLAIM`; and `CLAIM` is not `COMPETITIVE ADVANTAGE`. The binary matrix uses `1D` for primary-source declaration, `1V` for reproducible verification, `1R` for independent reproduction, `?` for unknown, `0` for absent in the tested boundary and `N/A` for non-comparable scope. Unknown is never silently converted into absence or proof.

### Reproducibility benchmark

The current competitive protocol is **S-001 Evidence-Ready Field Operations**: the same operational task, inputs and connectivity failure condition are replayed through CASTÚO and an alternative implementation. Its metrics cover continuity, recovery, provenance, evidence completeness, reviewability and claim generation. `P2` versions the fixture, `E3` requires independent replay and `N5` requires a signed field pilot with KPIs. A local fixture result is labelled `LOCAL REPRODUCTION / NO FIELD CLAIM`.

### Implemented progress surface

The governed integration currently covers the following evidence-scoped capabilities:

| Capability | Current state | Boundary |
|---|---|---|
| Secure SaaS connectors | Vault-first intents, rotation, revocation, owner isolation, least-privilege scopes and redacted audit | Real provider selection remains `SECURITY_HOLD` until dual approval |
| Quantum Decision Lab | Deterministic local simulator with evidence budget, heuristic confidence and factor readouts | `LOCAL RESULT / NO CLAIM`; no field or economic evidence implied |
| Assurance P0/P1/P2 | Roadmap, Trust Passports, AI Security Passport, SLO/observability contracts and open-gate register | External review, production restore and remote assurance remain pending |
| Competitive intelligence | 1/0/?/N/A matrix, weighted coverage, evidence completeness and 17 capability passports | `?` is uncertainty; it is never silently converted to 0 or 1 |
| S-001 reproducibility benchmark | Same task, inputs and failure condition; continuity, recovery, provenance, completeness, reviewability and claim generation | P2 fixture, E3 independent replay and N5 field/economic evidence are separate gates |
| Supply-chain controls | Secret scan, SBOM, dependency scan and local dependency result of 0 advisories | Local green status does not prove remote GitHub Security and quality is 0 |
| Traky12 integration | 16 remote repositories classified; 14 governed README PRs open and traceable | Protected main branches require review/checks; forks are excluded |

### Full operating plan transcription

The evolution plan is executed as a controlled chain rather than as an unbounded feature list. **Foundation** establishes repository boundaries, typed contracts, the dashboard and the capability vocabulary. **P0 Secure platform** enforces backend-only credential handling, vault-first intents, least-privilege permissions, rotation, revocation, owner isolation, redacted audit and supply-chain scanning. **P1 Evidence system** formalises sensitivity, provenance, Trust Passports, AI Security Passport, observability, SLOs, backup/restore and diagnostics. **P2 External validation** defines the second implementation, S-001 replay, independent review, field KPIs and economic evidence.

The operational backlog is maintained in `todo.md` and in the master operating index. Each task must preserve an owner, input boundary, expected output, exit criterion, evidence reference and rollback path. Completed work is marked without deleting historical entries. Blocked work remains visible with `BLOCKED`, `SECURITY_HOLD`, `EVIDENCE_REQUIRED` or `NOT_VERIFIED`; an open task is never evidence of capability.

| Control | Required transcription | Promotion rule |
|---|---|---|
| Capability | What the system can do and which repository owns it | Do not infer evidence from capability presence |
| Evidence | Source, contract, test, runtime slice, benchmark or review | Must be reproducible and provenance-linked |
| Maturity | N1–N6 plus P0/P1/P2 and E3/N5 gates | No maturity promotion without the specified gate |
| Claim | Exact permitted statement and audience | Default-deny when passport or gate is incomplete |
| Competitive advantage | Comparative and economic proposition | Prohibited until independent and economic evidence exists |

Every README update is idempotent and PR-governed. The synchronizer updates only the authorised branch, preserves one governed block, excludes forks, records the resulting PR and never writes directly to protected `main`. Recovery uses checkpoints, remote commits and contract artifacts; divergences are reconstructed through a new PR or a named checkpoint, never through destructive history rewriting.

### Pending work register

| Workstream | Current state | Exit condition |
|---|---|---|
| Remote GitHub Security and quality | `BLOCKED` by `security_events` authorization and 403 | Read both main-branch alert tables with an authorized session and record timestamped results |
| Vault provider | `SECURITY_HOLD` with provider-neutral adapter | Approve one backend-only provider and pass rotation/revocation/dual-approval tests |
| Restore and remote diagnostics | `EVIDENCE_REQUIRED` | Complete an isolated restore and a redacted reproducible diagnostic with review |
| External assurance and field evidence | `EVIDENCE_REQUIRED` | Independent S-001 replay, signed review, field KPIs and economic evidence |
| README/plan continuity | PR-governed and recoverable from checkpoints | Merge reviewed PRs only after checks and preserve rollback references |

Open tasks are operational work, not proof of capability. They must remain visible until their exit criteria are met.

### Current boundary

Claims remain evidence-scoped. Do not describe this repository as production-validated, best-in-class, independently reviewed, commercially superior or N5/N6 unless the corresponding passport, evidence package, signed review and gate record are present. The open-gate register is authoritative for vault approval, GitHub security access, remote alerts, production restore, diagnostics and external validation.

### Traceability

| Artifact | Purpose |
|---|---|
| `TRAKY12-README-INVENTORY.json` | Repository surface, sensitivity and evidence classification |
| `Competitive Capability Passport` | Capability state, provenance, maturity and forbidden claims |
| `S-001 benchmark` | Reproducible comparison protocol and promotion boundary |
| P0/P1/P2 roadmap | Exit criteria and rollback responsibility |
| `Dashboard checkpoint` | Restorable implementation state and validation result |
| `CASTUO-SYSTEM-OPERATING-INDEX.md` | Master operating plan, task registry, gates, claims boundary, checkpoints and repository traceability |

The master operating index is available at [`docs/governance/CASTUO-SYSTEM-OPERATING-INDEX.md`](https://github.com/Traky12/Castuo-system/blob/main/docs/governance/CASTUO-SYSTEM-OPERATING-INDEX.md). This block is a governed integration reference. Repository-specific build, deployment, security and operational instructions remain authoritative in the rest of this README.
<!-- CASTUO-GOVERNED-README-BLOCK:END -->
