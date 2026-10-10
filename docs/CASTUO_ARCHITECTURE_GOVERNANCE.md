# CASTÚO-SYSTEM™ — Architecture governance scope

## Repository role

- **Role:** TOOLING
- **Function:** Tests y regresión; benchmarking = `TARGET` (no implementado)
- **Repository visibility:** PUBLIC_TEMPLATE
- **Canonical authority:** `Castuo-system` (private) — current authority for code, operational documentation and technical evolution
- **`castuo-evolution`:** prepared external surface; not the current GitHub authority nor a synchronised SSOT
- **Public evidence index:** [`Traky12/Traky12`](https://github.com/Traky12/Traky12)
- **Evidence Center:** [`evidence-center`](https://github.com/Traky12/Traky12/tree/main/evidence-center)

## Current truth boundary

Un benchmark es válido solo con dataset, versión, entorno y método.

A README, template, fork, commit or green workflow is evidence of an artifact or test within its scope. It is not automatically proof of certification, legal conformity, production operation, customer contract, funding, cash receipt or commercial success.

## Required evidence envelope

Every promoted capability must identify: repository, commit/tag, environment, owner, policy version, protocol, baseline, KPI definitions, raw results, artifact hashes, reviewer, decision and reassessment triggers.

## Claim status taxonomy

| Status | Meaning |
|---|---|
| `CURRENT` | Implemented and verifiable (commit, test, result, artifact, hash or release) |
| `TARGET` | Approved objective, not implemented yet |
| `EXPERIMENTAL` | Prototype or proof, not consolidated |
| `PENDING` | Planned work, or evidence incomplete |
| `NOT_CLAIMED` | Not implemented; must not be presented as a capability |

Words such as "validated", "production", "federated", "complete", "secure" or "ready for…" require concrete evidence: commit, test, result, artifact, hash or release.

A model, provider, key, tenant, schema, dataset, chain or environment change activates `REASSESSMENT_REQUIRED`.

## Security baseline

Secrets remain outside Git. Public artifacts contain no credentials or unnecessary personal data. Inputs are validated, access is least-privilege, TLS and encryption-at-rest are configured by environment, device identities are revocable, logs avoid secrets, and backups have a restoration test.

## Promotion Gate

No capability is promoted without a reproducible test and evidence appropriate to its state. Negative results are retained as findings and followed by remediation and re-test.
