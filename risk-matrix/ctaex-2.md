# CTAEX Risk Matrix v2

Date: 2026-04-03

## Top risks and mitigations

1. Data quality drift in IoT telemetry
- Impact: High
- Likelihood: Medium
- Mitigation: Automated range/type checks for pH, EC, VPD in API ingestion.
- Control evidence: tests/test_api.py (iot telemetry quality tests)

2. Merge of non-certified changes to main
- Impact: High
- Likelihood: Medium
- Mitigation: TRL9 operativity certification workflow and branch protection check.
- Control evidence: .github/workflows/github-operativity-certification.yml

3. Partial legal compliance record completeness
- Impact: High
- Likelihood: Medium
- Mitigation: Progressive formalization of GDPR Art.30 register and audit exports.
- Control evidence: docs/ops/CTAEX-CUMPLIMIENTO-ANALISIS.md

4. External integration degradation (TRACES/Hyperledger)
- Impact: Medium
- Likelihood: Medium
- Mitigation: fallback states + explicit queue status + roadmap closure.
- Control evidence: api/main.py (traces_status queued/disabled)

## Governance
- Review cadence: monthly.
- Owner: Platform Security + Compliance.
