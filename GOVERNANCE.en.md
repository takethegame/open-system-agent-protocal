# OSAP Governance

> English translation of [GOVERNANCE.md](GOVERNANCE.md). The Chinese original prevails in case of conflict.

> Draft · 2026-11-10

This document defines the versioning, change, review, and liaison mechanisms of the OSAP standard. Except for the license and trademark terms in §10, it is a governance recommendation and does not constitute a legal agreement.

---

## 1. Goals

- Keep the protocol open, implementable, and testable.
- Avoid a single vendor controlling core semantics.
- Strike an auditable balance between security, privacy, and interoperability.
- Align with ecosystems such as MCP, A2A, IETF `agentproto`, OAuth WIMSE, and AAIF/LF, rather than redefining them.

---

## 2. Versions and Releases

| Version type | Rules |
|---|---|
| **Major** | Incompatible changes; a migration guide and at least one support cycle for the previous version MUST be provided |
| **Minor** | Backward-compatible additions; the changelog and schemas MUST be updated |
| **Patch** | Clarifications, errata, non-semantic changes |

- The specification version stays consistent with the wire version (the envelope `osap` field).
- Each release MUST include: a change summary, a compatibility statement, security impact, and test updates.
- A release candidate SHOULD have a public review period of at least 30 days.

---

## 3. Change Process

1. **Proposal**: submit the problem, motivation, design, alternatives, and security/privacy impact via an issue or `proposals/NNNN-*.md`.
2. **Discussion**: public discussion, with participation from at least two independent implementers.
3. **Prototype**: proposals involving protocol behavior SHOULD provide a reference implementation or pseudocode.
4. **Review**: security and privacy review is mandatory.
5. **Consensus**: rough consensus, defined as "no sustained, substantive objection".
6. **Merge and release**: update the specification, schemas, tests, and changelog.

All commits MUST carry a DCO `Signed-off-by` (see §10.1); unsigned commits must not be merged.

Urgent security issues may take a fast track, but MUST be publicly explained afterwards.

---

## 4. Roles

| Role | Responsibilities |
|---|---|
| **Maintainer** | Merge proposals, publish releases, maintain schemas and tests |
| **Editor** | Maintain the specification text and conformance |
| **Implementer** | Provide reference implementations and interoperability reports |
| **Security Reviewer** | Review threat models, cryptography, and permission boundaries |
| **Liaison** | Liaise with external standards organizations |

Roles are not bound to employers; any contributor can become a maintainer through sustained contribution.

---

## 5. Conformance and Reference Implementation

- For conformance levels, see [`docs/conformance.md`](docs/conformance.en.md).
- A reference implementation MUST pass all tests for the level it claims.
- A reference implementation SHOULD cover at least two OS platforms.
- Interoperability reports SHOULD be public (after redaction).
- The standard does not require a single "official implementation"; multiple independent implementations are allowed.

---

## 6. Schema and Namespace Registration

- Core schemas are registered by maintainers.
- Domain schemas are registered by the proposer, who must provide a maintainer, version, validation rules, and compatibility policy.
- Capability namespaces:
  - `cap://os/...` is reserved for the core domain;
  - `cap://<vendor-domain>/...` is used for vendor extensions;
  - Conflicts are disambiguated using reverse domain names.
- Event topics:
  - `event://os/...` is reserved for system events;
  - `event://app.<app-id>/...` is used for app events.

---

## 7. Security Disclosure

- Security issues MUST NOT have exploitation details published first.
- Maintainers should be contacted through a private channel, and disclosure coordinated within 90 days.
- Issues involving user data, permission bypass, or audit tampering are prioritized.
- Changes to the trust profile, TCB boundary, payload visibility, or encryption profile MUST go through security and privacy review.
- After a fix, the threat model and test cases MUST be updated.

---

## 8. Privacy

- The specification and tests MUST NOT contain real user data.
- Examples MUST use reserved domain names, example identities, and synthetic data.
- Default settings for auditing/telemetry MUST follow data minimization.
- Any cross-device/cross-organization extension MUST undergo a separate privacy impact assessment.

---

## 9. Relationship with External Standards Organizations

Recommended liaison directions:

| Organization/project | Relationship |
|---|---|
| IETF `agentproto` | Upstream alignment on conversation management and task lifecycle |
| IETF OAuth / WIMSE | Delegated authorization, credentials, consent receipts |
| AAIF / Linux Foundation (MCP, A2A) | Tool and cross-network agent semantics |
| AGNTCY | Federated directories, transport, capability schemas |
| OS vendors (Apple/Google/Microsoft) | Native registry bridges and peer authentication |
| Desktop environments (GNOME/KDE) | Linux local Bus and portal integration |

OSAP positions itself as a **local binding/federation layer** and does not replace the protocols above.

---

## 10. License and Contribution

| Content | License |
|---|---|
| Specification text (`docs/`) | Apache-2.0 |
| JSON Schema (`schemas/`) | Apache-2.0 |
| Examples (`examples/`) | Apache-2.0 |
| Tools and future reference implementations (`tools/`) | Apache-2.0 |

The entire repository uniformly uses the **Apache License 2.0**, rather than splitting into "CC for documentation + Apache for code". Reasons:

- Apache-2.0 §3 provides an explicit **patent grant**, with termination upon initiating patent litigation;
- CC BY 4.0 Section 2(b)(2) explicitly excludes patent and trademark grants, and CC is not recommended for software and schemas;
- It permits commercial implementation, modification, redistribution, and private deployment, making it suitable for vendor adoption;
- It is compatible with GPLv3 (and incompatible with GPLv2);
- It has explicit contributor license terms (§5) and trademark terms (§6).

### 10.1 Contribution

- Use the **DCO 1.1**, not a CLA; every commit MUST carry a `Signed-off-by`.
- Contributors retain copyright and grant the project an Apache-2.0 license.
- Unsigned commits must not be merged.
- For specific requirements, see [`CONTRIBUTING.md`](CONTRIBUTING.en.md).

### 10.2 Trademarks and Conformance Marks

- Apache-2.0 §6 does not grant trademark rights to the "OSAP" name or logo.
- The code may be used freely; however, conformance marks such as "OSAP-compatible" and "OSAP C4/C5"
  MUST be based on test results from [`docs/conformance.md`](docs/conformance.en.md),
  and the specific registration process is defined separately.
- It must not be implied that the project endorses a third-party implementation.

### 10.3 Translations and Derivative Versions

Apache-2.0 §4 requires modified files to carry change notices and must not imply that they are official versions. Accordingly:

- **Derivative versions** (translations, excerpts, profiles, rewrites) MUST retain [`LICENSE`](LICENSE) and
  [`NOTICE`](NOTICE), and prominently mark them as "modified" per §4(b).
- **Official translations** are published by Maintainers, with the metadata `translation: official`,
  and must state the corresponding source version and commit.
- **Other translations** MUST be marked `translation: unofficial`, MUST NOT use
  conformance marks such as "OSAP-compatible" and "OSAP C4/C5", and must not imply that they are official text.
- Translations MUST NOT introduce new normative requirements; in case of semantic conflict, the original text (`docs/standard.md`) prevails.
- Derivative specifications that change protocol semantics MUST use a different name and namespace and must not be called "OSAP 0.x".

### 10.4 License Changes

- The license of released versions is irrevocable.
- If the license is adjusted in the future (for example, donated to a foundation or submitted to the IETF), the consent of all contributors MUST be obtained,
  and this must be stated in the new version; the terms of already distributed copies must not be retroactively modified.

---

## 11. Code of Conduct

- Focus on technical arguments; no personal attacks.
- Respect the implementation constraints of different platforms and vendors.
- Be prudent about security and privacy issues.
- Independent implementations and adversarial testing are welcome.
