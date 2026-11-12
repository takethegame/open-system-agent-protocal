# OSAP Conformance

> English translation of [conformance.md](conformance.md). The Chinese original prevails in case of conflict.

> Non-normative document · 2026-11-10
> Companion specification: [`standard.en.md`](standard.en.md)

This document defines the conformance levels, test methods, interoperability requirements, and reporting format for OSAP implementations.

---

## 1. Conformance claim

An implementation MUST declare the following in its documentation or in `hello`:

```json
{
  "osap": "0.1",
  "conformance": {
    "level": "C5",
    "features": ["discover", "delegate", "handoff", "peer", "context", "consent", "stream"],
    "encodings": ["json"],
    "transports": ["uds"],
    "bus_visibility": "payload",
    "transport_kind": ["stream"],
    "state_recovery": "durable",
    "cf_mode": "os_handles"
  }
}
```

- `level` MUST be one of `C0`–`C7`.
- `features` MUST contain only features that are implemented and tested.
- `bus_visibility` MUST be `payload` (the only value in 0.1).
- `transport_kind` MUST list `stream` / `message`.
- `state_recovery` MUST be `durable` or `best_effort`; when claiming C4+, it MUST be `durable`.
- `cf_mode` MUST be `os_handles` or `managed_store`.
- Behavior that claims more than the actual capability constitutes a non-conforming implementation.

---

## 2. Levels

| Level | Name | Required capabilities | Optional |
|---|---|---|---|
| C0 | Transport | Connection, framing (by stream/message type), `hello`/`welcome`, errors, version negotiation | CBOR |
| C1 | Identity | Peer authentication, Agent registration, public key binding, reserved namespaces, key rotation | Hardware keys |
| C2 | Registry | Manifest, capability records, discovery, static `consent_hint`, cache invalidation | Semantic ordering |
| C3 | Authorization | Capability tokens, attenuation, binding, revocation, consent receipts, clock semantics | Batch consent |
| C4 | Collaboration | Tasks, delegation, peer, budget, cancellation, results, recovery, handoff | Streaming results |
| C5 | Context | Handles, resolution, labels, blackboard, OS handle mapping (optional object storage), memory authorization, egress | Encrypted objects |
| C6 | Federation | At least two Bridge types (vendor registry + MCP/A2A/D-Bus) | All Bridges |
| C7 | Full | C0–C6 + audit export/replay + multi-user extension | Cross-device |

> Levels are cumulative: claiming C4 implies that C0–C3 are all satisfied.

---

## 3. Test suite

### 3.1 Structure

Machine-readable cases live in [`conformance/cases/`](../conformance/cases/), one file per level:

```
conformance/
  README.md
  case.schema.json
  suite.schema.json
  report.schema.json
  cases/
    C0-transport.json
    C1-identity.json
    ...
```

Each case MUST contain `id`, `level`, `title`, and `expect`; optional fields are `mode`, `preconditions`, `operation`, `input`, `steps`, `audit`, and `notes`. Field definitions are in [`conformance/README.md`](../conformance/README.md).

### 3.2 Test format

```json
{
  "id": "C3-04",
  "level": "C3",
  "title": "widening actions during attenuation is rejected",
  "mode": "automated",
  "operation": "attenuate",
  "input": {
    "ref": "../../examples/capability.json",
    "mutations": [
      { "op": "replace", "path": "/actions", "value": ["propose", "create"] }
    ]
  },
  "expect": { "outcome": "reject", "error": "CAPABILITY_ATTENUATION_INVALID" }
}
```

### 3.3 Running

```bash
python3 tools/conformance_run.py --impl path/to/adapter.py --format md
```

The adapter API and mutation semantics are in [`conformance/README.md`](../conformance/README.md); the report format is in [`conformance/report.schema.json`](../conformance/report.schema.json).

---

## 4. Required test cases

### C0 — Transport

| ID | Scenario | Expected |
|---|---|---|
| C0-01 | Sending `request` before completing `hello` | Rejected, `TRANSPORT_HANDSHAKE_REQUIRED` |
| C0-02 | Incompatible major version | Rejected, `TRANSPORT_VERSION_UNSUPPORTED` |
| C0-03 | Frame length exceeding 8 MiB | Rejected, `TRANSPORT_FRAME_TOO_LARGE` |
| C0-04 | Unknown message type | `SCHEMA_UNSUPPORTED` |
| C0-05 | `request` with duplicate `id` | Side effects not executed twice |
| C0-06 | Message-type transport forced into length prefixing | Considered non-conforming |
| C0-07 | System clock rollback / suspend-resume | Timeouts are not extended; expired requests are rejected |

### C1 — Identity

| ID | Scenario | Expected |
|---|---|---|
| C1-01 | Unregistered Agent connection | Rejected |
| C1-02 | Third party registers `agent://system/...` | Rejected |
| C1-03 | App signature mismatch | Rejected |
| C1-04 | Agent claims to belong to another App | Rejected |
| C1-05 | Old signature after key rotation | Rejected per policy, or allowed only during a transition period |
| C1-06 | `hello.public_key` not bound to the App identity | Registration rejected |

### C2 — Registry

| ID | Scenario | Expected |
|---|---|---|
| C2-01 | Unsigned manifest | Indexing rejected |
| C2-02 | Discovery of private data | Return only capabilities, not data |
| C2-03 | Discovery result returns a live `policy_verdict` or lacks `consent_hint` | Considered non-conforming |
| C2-04 | Expired capability record | Not used for authorization decisions |
| C2-05 | Native capability deleted | Invalidated within TTL |
| C2-06 | Federated record lacks `provenance` | Indexing rejected |

### C3 — Authorization

| ID | Scenario | Expected |
|---|---|---|
| C3-01 | `audience` mismatch | `CAPABILITY_AUDIENCE_MISMATCH` |
| C3-02 | `task_id` mismatch | `CAPABILITY_TASK_MISMATCH` |
| C3-03 | `subject != from` | `CAPABILITY_SUBJECT_MISMATCH` |
| C3-04 | Widening `actions` | `CAPABILITY_ATTENUATION_INVALID` |
| C3-05 | Widening `resources` | Rejected |
| C3-06 | Extending `exp` | Rejected |
| C3-07 | Exceeding `max_depth` | Rejected |
| C3-08 | Using a child capability after the parent capability is revoked | `CAPABILITY_REVOKED` |
| C3-09 | Executing L3 without a receipt | `POLICY_CONSENT_REQUIRED` |
| C3-10 | Expired receipt | `POLICY_CONSENT_EXPIRED` |
| C3-11 | Insufficient receipt scope | `POLICY_CONSENT_SCOPE_MISMATCH` |
| C3-12 | Receipt `audience` inconsistent with the recipient | Rejected, `POLICY_CONSENT_SCOPE_MISMATCH` |

### C4 — Collaboration

| ID | Scenario | Expected |
|---|---|---|
| C4-01 | Parent task cancelled | Child tasks receive `cancel` |
| C4-02 | Child budget exceeds the parent's remaining budget | Delegation rejected |
| C4-03 | Child task result schema mismatch | `SCHEMA_INVALID` |
| C4-04 | peer without `session_id` | Rejected |
| C4-05 | peer attempts to use the other party's capability | Rejected |
| C4-06 | handoff without renewed L3 consent | Rejected |
| C4-07 | Budget exceeded | `TASK_BUDGET_EXCEEDED` |
| C4-08 | Unfinished tasks after Bus restart | Transition to failed/rescheduled + audit |
| C4-09 | Crash before a side effect (intent only) | Marked unknown, not automatically replayed |
| C4-10 | Original owner still sends requests for that task after handoff | Rejected |
| C4-11 | handoff rejected, task remains with the original owner | State and budget unchanged |

### C5 — Context

| ID | Scenario | Expected |
|---|---|---|
| C5-01 | Resolving a handle without the `resolve` capability | `CONTEXT_DENIED` |
| C5-02 | Expired handle | `CONTEXT_EXPIRED` |
| C5-03 | Derived object lowers the label | Rejected or label raised |
| C5-04 | `secret` egress | Rejected / requires release |
| C5-05 | Task ends | Blackboard cleaned up |
| C5-06 | Object deleted | Reference check + audit |
| C5-07 | Cache outlives the handle TTL | Invalidated |
| C5-08 | `cf_mode=managed_store` but no quota/GC | Considered non-conforming |
| C5-09 | Bypassing OS file permissions via a handle | Rejected |
| C5-10 | Reading long-term memory without the `memory.read` capability | `CONTEXT_DENIED` |
| C5-11 | Retrieving the idempotency index / audit log / task tree as memory | Considered non-conforming |

### C6 — Federation

| ID | Scenario | Expected |
|---|---|---|
| C6-01 | AppFunction projection | Preserve `native_id`, `source`, `trust` |
| C6-02 | App Intent projection | Same as above |
| C6-03 | App Action projection | Same as above |
| C6-04 | MCP tool projection | Preserve server/tool and schema |
| C6-05 | A2A skill projection | Preserve the Agent Card and skill |
| C6-06 | D-Bus method projection | Preserve bus/path/interface/method |
| C6-07 | External content | `origin=external`, `trust` no higher than `unverified` |
| C6-08 | Native capability changes | Updated/invalidated within TTL |

### C7 — Full

| ID | Scenario | Expected |
|---|---|---|
| C7-01 | Task spanning 3 Apps | Complete trace, replayable audit |
| C7-02 | Audit chain tampering | Verification fails |
| C7-03 | User exports the audit | Redacted, and chain integrity is verifiable (no promise of plaintext recovery) |
| C7-04 | Cross-user request | Denied by default |
| C7-05 | Replay | Side effects not executed twice |
| C7-06 | L3 side effect with intent but no outcome | Marked unknown + alert |
| C7-07 | Compromised Bus | Fails explicitly in 0.1; separately assessed in P1 |

---

## 5. Interop matrix

Recommended minimal interoperability combinations:

| Role | Example | Must verify |
|---|---|---|
| Main Agent | Orchestrating App | Discovery, delegation, handoff, budget, cancellation |
| Sub Agent | Calendar App | Capability validation, result schema |
| Peer Agent | Messaging App | Point-to-point session, independent capabilities |
| System Agent | OS assistant | Reserved namespaces, system capabilities |
| Bridge | AppFunctions/MCP | Provenance, trust, schema mapping |
| User interface | Consent/activity center | Intent preview, receipts, revocation |

Interop tests SHOULD cover at least:

- one L1 read;
- one L2 local write;
- one L3 external side effect + consent;
- one handoff (one accept and one reject);
- one cancellation/budget exhaustion;
- one revocation cascade;
- one handle resolution and egress block.

---

## 6. Reporting

An implementation SHOULD provide a machine-readable report:

```json
{
  "implementation": "example-osap-bus",
  "version": "0.1.0",
  "osap": "0.1",
  "level": "C5",
  "bus_visibility": "payload",
  "state_recovery": "durable",
  "cf_mode": "os_handles",
  "tests": {
    "total": 68,
    "passed": 62,
    "failed": 2,
    "skipped": 0
  },
  "failures": [
    {
      "id": "C3-07",
      "reason": "max_depth not enforced on delegate"
    }
  ],
  "date": "2026-11-10T12:00:00Z"
}
```

The report MUST NOT contain user data, keys, or unredacted object contents.

---

## 7. Security testing

In addition to functional tests, SHOULD cover:

- forged peer identity;
- replayed requests;
- token borrowing;
- cross-task reuse;
- prompt injection content marked via `origin`;
- handle path traversal;
- audit log truncation;
- large-message/slow-connection DoS;
- Bridge provenance spoofing.

High-risk tests MUST run in an isolated environment and MUST NOT use real user data.
