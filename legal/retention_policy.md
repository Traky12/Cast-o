# Data Retention Policy

Version: 1.0
Date: 2026-04-03

## Principles
- Data minimization by design.
- Purpose limitation.
- Retention limits with documented exceptions.

## Retention windows
- Elasticsearch operational logs: 30 days (ILM policy managed in ELK stack).
- SQL operational records: up to 5 years when legally/operationally required.
- Blockchain records: immutable hash-only evidence; off-chain references follow legal retention.

## Review cadence
- Monthly operational review.
- Quarterly legal/compliance review.
