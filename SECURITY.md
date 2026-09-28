# Security Policy

## Scope

Cast-o is testing and assurance tooling for CASTÚO-SYSTEM™. It is not a
production service and publishes no versioned releases. This policy covers the
code, workflows and configuration in this repository.

## Supported versions

| Version | Supported |
|---|---|
| `main` branch (latest commit) | :white_check_mark: |
| Any other branch, fork or tag | :x: |

There are no numbered releases yet. Security fixes are applied to `main` only.

## Reporting a vulnerability

Do **not** open a public issue for a vulnerability.

Report it privately through GitHub:
**Security → Report a vulnerability** on this repository
(<https://github.com/Traky12/Cast-o/security/advisories/new>).

Include the affected file or workflow, the steps to reproduce, and the impact
you observed.

Expectations. This is a single-maintainer project; the times below are
targets, not contractual SLAs:

- Acknowledgement: within 7 days.
- Initial assessment (accepted / declined, with reasoning): within 30 days.
- If accepted: a fix on `main` and, where relevant, a GitHub Security Advisory
  crediting the reporter unless they prefer to stay anonymous.

## Out of scope

- Findings in third-party dependencies that are already tracked by Dependabot
  alerts on this repository (they are handled through Dependabot updates).
- Example or template files (`.env.example`, `.env.*.example`) that contain
  placeholders, not real secrets.
- Systems not in this repository (for example the private `Castuo-system`
  deployment); report those through the repository that owns them.

## Secrets

Secrets must never be committed. If you find a real credential in this
repository or its history, report it privately as above.
