# OSAP — Open System Agent Protocol

[![ci](https://github.com/takethegame/open-system-agent-protocol/actions/workflows/ci.yml/badge.svg)](https://github.com/takethegame/open-system-agent-protocol/actions/workflows/ci.yml)

> English translation of [README.md](README.md). The Chinese original prevails in case of conflict.

> **A local-first open standard: cross-application agent peer-to-peer collaboration, capability registry federation, and task-level authorization.**
>
> Version: 0.1 Draft · 2026-11-10 · Status: discussion draft, reference implementation through M2.6 with a three-agent demo

---

## What This Is

OSAP defines an agent interoperability protocol that runs within local sessions of an operating system. It enables agents hosted by different apps to:

- **Collaborate peer-to-peer**: discover each other, establish sessions, delegate tasks, and exchange results;
- **Federate capability registries**: project the capabilities of Apple App Intents, Android AppFunctions, Windows App Actions, as well as MCP, A2A, D-Bus, and OpenAPI into a unified capability graph;
- **Authorize at task level**: replace coarse-grained app permissions with verifiable, attenuable, and revocable capability tokens.

OSAP does not replace MCP, A2A, D-Bus, or vendor-native capability frameworks. What it adds is the **local interoperability and governance layer** between these mechanisms: unified identity, unified discovery, unified authorization, unified context references, and unified auditing.

---

## Three Pillars

### 1. Cross-Application Agent Peer-to-Peer Collaboration

- The local Agent Bus routes requests, results, events, streams, and cancellations.
- It supports **Supervisor/Worker** hierarchical delegation as well as **Peer** sessions between equals.
- Task trees, budgets, deadlines, cancellation cascades, and result aggregation.

### 2. Vendor Capability Registry Federation

- App manifests declare capabilities; the Registry Federation Service establishes unified capability records.
- Bridges adapt App Intents / AppFunctions / App Actions / MCP / A2A / D-Bus / OpenAPI.
- `source`, `native_id`, `trust`, and `provenance` are preserved; the native registry remains authoritative.

### 3. Task-Level Authorization

- Capability tokens bind `subject`, `audience`, `task_id`, resources, actions, time, and budget.
- Permissions can only narrow along the delegation chain; token forwarding is prohibited; revocation cascades.
- L3/L4 actions require a user consent receipt; full-chain auditing and tracing.

---

## Why It Is Needed

The state of affairs in 2026 is:

- OS vendors have already built star-shaped registries from "system agent → app capabilities" (App Intents / AppFunctions / App Actions), but agents of third-party apps cannot participate on equal footing.
- MCP / A2A solve tool invocation and cross-network agent collaboration, but they are not OS-local and lack OS peer identity and task-level authorization.
- The research community has proposed OS-level agent security architectures, but no cross-vendor, implementable local interoperability standard has yet emerged.

OSAP's goal is not to "invent yet another agent protocol", but to define a **local binding / profile**: to connect the capabilities above and fill in the identity, authorization, context, and auditing that cross-application scenarios lack.

For a more detailed positioning and prior work, see [`docs/prior-art.md`](docs/prior-art.en.md).

---

## Documents

| Document | Contents |
|---|---|
| [`docs/standard.en.md`](docs/standard.en.md) | **Normative draft**: architecture, identity, capabilities, federation, messages, tasks, context, consent, auditing, conformance |
| [`docs/conformance.en.md`](docs/conformance.en.md) | Conformance levels, test cases, interoperability matrix, report format |
| [`docs/prior-art.en.md`](docs/prior-art.en.md) | Prior work, comparison matrix, possible novel points, and falsifiable claims |
| [`docs/design-draft.en.md`](docs/design-draft.en.md) | Early design notes (non-normative; background and trade-offs retained) |
| [`GOVERNANCE.en.md`](GOVERNANCE.en.md) | Versions, changes, roles, security disclosure, external standards liaison |
| [`CONTRIBUTING.en.md`](CONTRIBUTING.en.md) | Contribution process, DCO, content rules |
| [`docs/roadmap.md`](docs/roadmap.md) | Milestones from 0.1 to 0.2, exit criteria, risk register, decision gates (working document, Chinese) |
| [`docs/progress.md`](docs/progress.md) | Completed milestones, verification evidence, per-case breakdown (working log, Chinese) |
| [`SECURITY.en.md`](SECURITY.en.md) | Vulnerability disclosure channel, timelines, security review triggers |
| [`CHANGELOG.md`](CHANGELOG.md) | Release history |

---

## Repository Structure

```
docs/                 Specification, conformance, prior work, design notes, roadmap
schemas/              JSON Schema (envelope, capability, task, manifest, capability record, receipt, audit, payload)
conformance/          Machine-readable conformance cases, case schemas, report schema
examples/             Example messages and objects
tools/                Validation scripts (examples, schemas, docs, conformance)
.github/workflows/    CI
GOVERNANCE.md         Governance draft
CONTRIBUTING.md       Contribution process and DCO
SECURITY.md           Security disclosure
CHANGELOG.md          Release history
requirements.txt      Python dependencies
LICENSE               Apache-2.0
NOTICE                Copyright and trademark notices
README.en.md          This file
```

English parallel versions use the same name with an `.en.md` suffix and sit alongside the Chinese originals.

---

## Quick Validation

```bash
python3 -m pip install -r requirements.txt
python3 tools/check_schemas.py     # schema meta-validation and $id uniqueness
python3 tools/validate_examples.py # examples and cross-document checks
python3 tools/check_docs.py        # JSON blocks, links, zh/en parity
python3 tools/conformance_run.py --stub  # conformance case format
python3 demo/run_demo.py           # three-agent end-to-end demo
```

All three run in CI; dependencies are in `requirements.txt` (Python 3.9+).

---

## Current Status

- **Specification**: 0.1 discussion draft; core mechanisms are defined; open questions are in Section 15 of the specification.
- **Trust boundary**: the Bus Core is the minimal TCB; RFS/CA/PCS/CF/AL are independent services. The 0.1 Bus can read payloads, which is an explicit trust assumption; a P1 encrypted profile that does not trust the Bus is planned for 0.2.
- **State semantics**: task trees, idempotency indexes, revocation lists, and audit chain heads must be persisted and support crash recovery. Bus state is not memory: long-term semantic memory is held by agents or a separate memory service and must be authorized separately (see [`docs/standard.md`](docs/standard.en.md) §3.7, §9.3).
- **Implementation**: a Python reference implementation lives in `impl/`, covers M2.1–M2.6, and passes all 60 automated conformance cases; `demo/` provides a three-agent end-to-end demo.
- **Conformance**: C0–C7 levels are defined, and test cases are listed.
- **Standards home**: undetermined; recommended to align as a local profile with IETF `agentproto`-related discussions, OAuth WIMSE, and the AAIF/LF ecosystem (whether a working group is formed is subject to the IETF's official position).
- **License**: Apache-2.0 (uniform across specification, schemas, examples, and tools); contributions use DCO 1.1.

---

## How to Participate

Issues / proposals / implementation reports are welcome in the following areas:

1. A minimal prototype with two example apps plus one Bus;
2. Bridge adapters for App Intents / AppFunctions / App Actions;
3. Formalization and testing of capability attenuation, revocation, and audit chains;
4. Adversarial testing of prompt injection and data egress;
5. Interoperability mapping with MCP / A2A / IETF drafts.

For the governance and proposal process, see [`GOVERNANCE.md`](GOVERNANCE.en.md).

---

## License

This repository uniformly uses the [Apache License 2.0](LICENSE): the specification text, JSON Schema, examples, and tools are all released under the same license.

- Commercial use, modification, redistribution, and private deployment are permitted;
- It includes a patent grant (Apache-2.0 §3) and trademark terms (Apache-2.0 §6);
- It is compatible with GPLv3 and incompatible with GPLv2;
- Contributions use the [DCO 1.1](https://developercertificate.org/), and commits must carry a `Signed-off-by`.

Rules for use of the "OSAP" name and conformance marks are in [`GOVERNANCE.md`](GOVERNANCE.en.md) §10.

---

## Non-Goals

- It does not specify an agent's internal reasoning, model, or prompts.
- It does not replace MCP / A2A / D-Bus / vendor-native capability frameworks.
- It does not define a federation trust root across devices, organizations, or users (future versions).
- It does not provide kernel-level isolation; OSAP runs on top of existing OS sandboxes and IPC.
