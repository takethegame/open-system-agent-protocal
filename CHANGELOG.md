# Changelog

All notable changes to this repository are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Entries are written in English to match commit messages; the Chinese text in
`docs/standard.md` remains the normative source.

## [Unreleased]

### Added

- `conformance/`: machine-readable cases for C0 (7), C1 (6), C2 (6), C3 (12), C4 (11), C5 (11), C6 (8), and C7 (7), plus `case.schema.json`, `suite.schema.json`, `report.schema.json`, and `README.md`.
- `examples/context-handle.json`, `examples/blackboard.json`, and `examples/audit-chain.json`: context-fabric and audit-chain fixtures.
- `impl/`: reference implementation for M2.1 — envelope validation, the error model, stream and message framing, handshake, idempotency, and monotonic-clock deadlines.
- `impl/osap/crypto.py`, `identity.py`, and `registry.py` (M2.2): Ed25519 manifest signatures, agent registration with reserved-namespace and public-key binding checks, capability-record indexing with TTL, and discovery candidates that carry a static `consent_hint` only.
- `impl/osap/capability.py` (M2.3): capability-token validation, the ten attenuation rules of §5.3, stateless audience/task/subject binding, revocation with cascade, and the L3/L4 consent prerequisite.
- `impl/osap/consent.py` (M2.4): consent-receipt validation ordered as decision, expiry, scope binding, then action/resource subsets.
- `impl/osap/registry.py`: `capability_descriptor()` and `risk_of()` so an envelope route can be resolved to the receiving agent and its declared risk class.
- `impl/tests/`: 118 unit tests covering framing, validation order, idempotency, deadlines, signatures, registration rejections, registry freshness, attenuation per dimension, revocation cascade, binding, and receipt ordering.
- `tools/conformance_run.py`: loads and validates cases, applies JSON Pointer mutations, runs an implementation adapter, and emits text, JSON, or Markdown reports.
- `docs/roadmap.md`: milestone plan from 0.1 to 0.2 (M0–M5, decision gates, risk register).
- `SECURITY.md` / `SECURITY.en.md`: disclosure channel, timelines, security review triggers.
- `.github/workflows/ci.yml`: schema meta-validation, example validation, and documentation checks on Python 3.11 and 3.12.
- `tools/check_schemas.py`: validates every schema against the 2020-12 metaschema, enforces unique `urn:osap:schema:` `$id`s, and rejects unsupported `$ref` targets.
- `tools/check_docs.py`: checks JSON code blocks, fence balance, relative links, Chinese/English structural parity, and personal-identifier leakage.
- `.gitignore`, `requirements.txt`, and `CHANGELOG.md`.

### Changed

- Repository renamed from `open-system-agent-protocal` to `open-system-agent-protocol`; the GitHub URL, local directory, `origin` remote, and CI badge links were updated accordingly.
- `CONTRIBUTING.md` / `CONTRIBUTING.en.md`: state that the Chinese text is the normative original and `*.en.md` files are parallel translations.
- `schemas/envelope.schema.json`: require `session_id` when `task.mode` is `peer`, matching standard §8.4.
- `tools/conformance_run.py`: JSON output is now validated against `report.schema.json`; CI runs the same check.
- CI now runs the reference implementation unit tests and the conformance suite against `impl/adapter.py`.

### Changed

- `conformance/cases/C3-authorization.json`: C3-04…C3-07 now name the pristine capability fixture as `context`, so the parent token is derived from it rather than from the mutated child. Expected outcomes and error codes are unchanged.
- `tools/conformance_run.py --stub`: now also checks case-ID coverage against `docs/conformance.md` and materialises every `input.ref`, `context`, and mutation, so a missing fixture or a bad JSON Pointer fails CI instead of being skipped.

### Planned

- M2: reference implementation for the C0–C3 envelope, identity, registry, and authorization paths.

## [0.1.0] - 2026-11-10

First public discussion draft. No reference implementation.

### Added

- `docs/standard.md`: OSAP 0.1 Draft — architecture, identity, capability model, registry federation, message protocol, task model, context fabric, consent and audit, security considerations, conformance, versioning, and open issues.
- `docs/conformance.md`: conformance levels C0–C7 and 68 test cases.
- `docs/design-draft.md`: non-normative design background and trade-offs.
- `docs/prior-art.md`: prior work survey, comparison matrix, and falsifiable novelty claims.
- `schemas/`: 12 JSON Schemas, including 5 payload schemas.
- `examples/`: 13 example documents.
- `tools/validate_examples.py`: schema and cross-document validation (`OK: 20 checks passed`).
- `GOVERNANCE.md`: versioning, change process, roles, security disclosure, external liaison, license and trademark terms.
- `CONTRIBUTING.md`: proposal process, DCO 1.1, content rules.
- `LICENSE` (Apache-2.0) and `NOTICE`.
- `README.md`: project overview and document index.

### Notes

- New `handoff` message type; `handoff` is a one-shot ownership transfer, not a task mode.
- Two-stage validation: the Bus performs stateless envelope/signature/binding checks; the receiver performs revocation, policy, consent, risk, and business checks.
- Consent issuance order: the CA reserves `cap_id`, the receipt references it, and the CA issues the capability after the grant.
- Trust profiles: only P0 Trusted Bus is claimable in 0.1; P1 Opaque Bus (HPKE) is deferred to 0.2.

## [0.1.1-docs] - 2026-11-11

Editorial pass on the 0.1 draft, no protocol changes.

### Added

- English parallel versions: `README.en.md`, `GOVERNANCE.en.md`, `CONTRIBUTING.en.md`, `docs/standard.en.md`, `docs/conformance.en.md`, `docs/design-draft.en.md`, `docs/prior-art.en.md`.
- Cross-links between Chinese originals and English translations.

### Changed

- Tightened `handoff` semantics, consent binding, audience/task binding, and conformance wording.
- Replaced Chinese human-readable strings inside English code blocks with English equivalents.
- Removed personal identifiers and local paths from documentation and examples.
