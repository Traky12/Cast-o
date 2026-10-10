# Cast-o — Bounded Assurance Distribution

Cast-o is the technical assurance and negative-validation surface of CASTÚO-SYSTEM. It runs bounded tests and produces reproducible evidence; it is **not a certification service**.

## Position in the ecosystem

`Cast-o` validates declared scopes. `castuo-evidence` owns portable evidence contracts, `Castuo-system` owns integration and governance, and `castuo-evolution` owns promotion policy. These repositories are linked authorities, not copies of one another.

## Reproducible offline demo

Requirements: Node.js 18 or newer.

```bash
npm install
npm run demo:offline
```

The command executes a frozen `SIMULATION_ONLY` fixture and writes:

```text
artifacts/bounded-assurance/offline-demo/evidence-pack.json
```

Expected output:

```text
FIELD OPERATION COMPLETED
LOSS OF CONNECTIVITY ........ PASS
LOCAL BUFFER ................ PASS
RECOVERY .................... PASS
SYNC ......................... PASS
EVIDENCE HASH ............... PASS
REPLAY ....................... PASS
CLAIM BOUNDARY ............... SIMULATION_ONLY
PROMOTION .................... BLOCKED
```

The artifact contains operation ID, events, connectivity intervals, recovery, synchronization, integrity hash, replay result, final status and promotion effect. It is a bounded simulation and must not be presented as field, staging or production evidence.

## Validation

```bash
npm test
npm run validate:package
npm run demo:offline
```

A local pass means `VALIDATED_LOCAL` for the declared scope only. Independent replay, remote CI, field evidence, production operation and certification remain separate gates.

## Governance boundary

The minimum failure contract is:

```text
denied request → logged → explainable → recoverable
```

Promotion remains fail-closed when provenance, negative tests, replay, security, review or rollback evidence is missing.

## License

AGPL-3.0.
