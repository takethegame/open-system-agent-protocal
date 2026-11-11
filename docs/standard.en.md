# OSAP 0.1 — Open System Agent Protocol

> English translation of [standard.md](standard.md). The Chinese original prevails in case of conflict.

**Point-to-point inter-application Agent collaboration, capability registry federation, and task-level authorization**

| Item | Content |
|---|---|
| Document status | Draft Standard (discussion draft) |
| Version | 0.1 |
| Date | 2026-11-10 |
| Normative keywords | RFC 2119 / RFC 8174 |
| Scope | Inter-application Agent collaboration within a single-device, single-user session |
| Normative text | This document |
| Design notes | [`design-draft.en.md`](design-draft.en.md) (non-normative) |
| Related work | [`prior-art.en.md`](prior-art.en.md) (non-normative) |
| License | Apache-2.0 (see [`LICENSE`](../LICENSE)) |

---

## Abstract

OSAP (Open System Agent Protocol) defines a **local-first** open protocol that enables Agents hosted by different applications, within the same operating system session, to:

1. **Collaborate point-to-point**: discover each other, establish sessions, delegate tasks, and exchange results without requiring all traffic to pass through a centralized orchestration Agent;
2. **Federate capability registries**: project capabilities from Apple App Intents, Android AppFunctions, Windows App Actions, as well as sources such as MCP, A2A, D-Bus, and OpenAPI, into unified capability records;
3. **Authorize at task level**: replace coarse-grained App permissions with verifiable, attenuable, and revocable capability tokens; all cross-application side effects pass through policy, consent, and audit.

OSAP does not replace MCP, A2A, D-Bus, or vendor-native capability frameworks. It defines the **local interoperability layer** among these mechanisms: unified identity, unified discovery, unified authorization, unified context referencing, and unified audit.

---

## 1. Introduction

### 1.1 Problem

Modern applications encapsulate data, accounts, UI, and permissions within their own boundaries. When a user completes a cross-application task, they often must copy and paste between multiple Apps, re-authorize, and manually pass context. LLM Agents make cross-application orchestration possible, but the current ecosystem has four structural gaps:

1. **There is no common channel between local Agents.** MCP addresses Agent→tool; A2A addresses cross-network Agent↔Agent. How the Agents of two Apps on the same machine securely discover each other, establish a task, and exchange results has no unified answer.
2. **Vendor capability registries are not interconnected.** App Intents, AppFunctions, and App Actions are each closed star-topology models: the system Agent can discover and invoke App capabilities, but third-party App Agents cannot participate on equal terms.
3. **Authorization granularity remains App-centric.** What the user authorizes is "some App may access contacts", not "in this task, this Agent may read this one contact record in order to send one message".
4. **Context cannot flow securely.** Every Agent repeatedly collects "who the user is, what is being done, where the data is", which is both inefficient and expands the attack surface for privacy leakage and prompt injection.

### 1.2 Design goals

| No. | Goal |
|---|---|
| G1 | Cross-application discovery: capabilities, events, schemas, risk, and cost can be queried, but a capability declaration does not equal authorization |
| G2 | Point-to-point and supervisor/subordinate dual mode: both peer collaboration and hierarchical delegation |
| G3 | Least privilege: no ambient authority; authority can only narrow along the delegation chain |
| G4 | Task-level authorization: capabilities bind audience, task, resources, time, and budget |
| G5 | Data does not leave its domain: references are passed by default, resolved per policy |
| G6 | Human-controllable: tiered consent, intent preview, revocable, auditable |
| G7 | Federate rather than replace: uniformly project vendor registries and MCP/A2A/D-Bus |
| G8 | Evolvable: small kernel, semantics extended through namespaces and schemas |

### 1.3 Scope

This specification defines:

- the identity, registration, sessions, and message envelope of local Agents;
- capability description, capability tokens, attenuation, revocation, and validation rules;
- the capability registry federation model and discovery queries/responses;
- task trees, point-to-point sessions, delegation, budgets, cancellation, and result aggregation;
- context handles, resolution, information-flow labels, and the task blackboard;
- consent request/grant/deny, consent receipts, and audit events;
- transport bindings, message framing, version negotiation, and conformance requirements;
- conformance levels and test cases.

### 1.4 Non-goals

- Does not specify an Agent's internal reasoning, models, prompts, or planning algorithms.
- Does not replace MCP tool semantics, A2A cross-organization Agent semantics, or vendor-native capability frameworks.
- Does not define a federated trust root across devices, organizations, or users; these belong to later versions.
- Does not define concrete UI; it defines only the protocol primitives for consent and audit.
- Does not provide kernel-level isolation; OSAP runs on top of existing OS sandboxes and IPC.
- 0.1 does not define an end-to-end encryption profile for payloads invisible to the Bus; that profile is slated for 0.2 (see §3.6). Therefore 0.1 applies only to deployments that treat the Bus as a trusted component.
- **Does not define long-term semantic memory**: the Bus is not a memory store and provides no cross-task experience retrieval, semantic indexing, or user profiling. The Bus persists only the structured state required for routing, idempotency, recovery, and authorization decisions (see §3.7). Agent memory belongs to the Agent or to a separate memory service, and MUST be separately authorized through ordinary capabilities (see §9.3).

### 1.5 Relationship to existing work

OSAP is positioned as a **local binding and federation layer**, not yet another Agent communication protocol:

- **MCP**: Agent→tool; OSAP projects MCP tools as capability records and can bridge OSAP requests into MCP calls.
- **A2A**: cross-network Agent↔Agent; OSAP reuses its Task/Artifact concept and provides local identity, capability, and consent binding.
- **App Intents / AppFunctions / App Actions**: vendor capability registries; OSAP projects them as unified capability records and preserves source and trust labels.
- **D-Bus / XPC / Binder**: local IPC; used as transport bindings for OSAP rather than replaced.
- **IETF agentproto / OAuth WIMSE / AAP / DAAP / DRP / APS**: dialogue management, delegated authorization, consent receipts; OSAP aligns with these and provides bindings in the local cross-application scenario.

See [`prior-art.en.md`](prior-art.en.md) for details.

### 1.6 Design principles

1. **No ambient authority**: an Agent has no cross-application permissions by default; the Bus's payload visibility is an explicit trust assumption, not an implicit default (see §3.6).
2. **Attenuation only**: a child capability MUST be a subset of its parent capability.
3. **Audience + task binding**: a capability binds the recipient and the task; it cannot be forwarded or reused across tasks.
4. **Reference over payload**: pass handles by default, not raw data.
5. **Fail closed**: deny when policy is undecidable, credentials have expired, or the audit cannot be written.
6. **Human in the loop**: L3/L4 actions MUST have a human consent receipt.
7. **Federate, don't absorb**: preserve the authority and provenance of native registries.
8. **Small core, typed edges**: Bus Core only performs authentication, envelope validation, routing, and backpressure; policy, issuance, storage, and audit are handled by independent services, and business semantics are extended with schemas.
9. **Explicit trust boundary**: what each component can see and can do MUST be explicitly declared; "trusted because it is on this machine" does not exist.

---

## 2. Conventions and Terminology

### 2.1 Requirement keywords

The **MUST**, **MUST NOT**, **REQUIRED**, **SHALL**, **SHALL NOT**, **SHOULD**, **SHOULD NOT**, **RECOMMENDED**, **MAY**, and **OPTIONAL** in this document are to be interpreted as described in RFC 2119 and RFC 8174.

### 2.2 Terminology

| Term | Definition |
|---|---|
| **Agent** | An entity within an application that performs tasks on behalf of the user, with an independent identity and capabilities |
| **Local Agent Bus (LAB)** | The complete local bus: the deployment view of Bus Core (minimal routing kernel) + independent services (CA/RFS/PCS/CF/AL) and Bridges |
| **Bus Core** | The minimal TCB: peer authentication, envelope validation, routing, connection/session management, and backpressure; does not enforce policy, does not issue capabilities, does not store objects, and does not persist audit |
| **Capability Authority (CA)** | The component that issues, attenuates, revokes, and validates capability tokens (an independent service) |
| **Registry Federation Service (RFS)** | The component for capability registry indexing and federated projection (an independent service) |
| **Policy & Consent Service (PCS)** | The component for policy evaluation, consent flows, and receipt issuance (an independent service) |
| **Context Fabric (CF)** | The context authorization proxy: validates capabilities and labels, resolves handles; reuses OS handles by default, with an independent object store as an optional implementation |
| **Audit Ledger (AL)** | An independently deployable append-only, hash-chained audit service; single-writer, anchorable |
| **Bridge Adapter (BA)** | An adapter that maps a native registry/protocol to OSAP |
| **Capability** | A verifiable, attenuable, revocable authorization credential |
| **Capability Record (CR)** | A unified description of a given Agent capability, with source and trust labels |
| **Task** | A trackable unit of work belonging to a task tree |
| **Session** | A period of point-to-point collaboration context among two or more Agents |
| **Handle** | A reference to data or context, such as `obj://`, `ctx://`, `task://` |
| **Consent Receipt** | A signed record of the user's consent to a given action |
| **Trace** | The cross-Agent call chain derived from a single user intent |
| **Bus State** | The structured runtime data required for routing, idempotency, crash recovery, and authorization decisions; bounded, expirable, free of business semantics, and not memory |
| **Memory** | Cross-task retrievable semantic experience or user preferences; held by an Agent or an independent memory service, requiring separate authorization, and not part of the Bus |

### 2.3 Identifiers and URIs

| Object | Form | Example |
|---|---|---|
| User | `user://<authority>/<id>` | `user://local/example-user` |
| App | `app://<bundle-id>` | `app://com.example.notes` |
| Agent | `agent://<app-id>/<agent-name>#<instance-id>` | `agent://com.example.notes/assistant#7f3a` |
| Device | `device://<device-id>` | `device://example-device` |
| Capability | `cap://<namespace>/<resource>` | `cap://os/calendar/events` |
| Task | `task://<task-id>` | `task://01JABCDEF...` |
| Session | `session://<session-id>` | `session://01JABCDEF...` |
| Object | `obj://<alg>:<digest>` | `obj://sha256:9f2c...` |
| Context | `ctx://<namespace>/<path>#<field>` | `ctx://user/profile#display_name` |

- `<instance-id>` is generated by the Agent at startup, MUST be unpredictable, and SHOULD use ULID or UUIDv7.
- `<task-id>`, `<session-id>`, and message `id` SHOULD use ULID or UUIDv7.
- All URIs MUST conform to RFC 3986.
- Timestamps MUST use RFC 3339 UTC (ending in `Z`) with at least second precision.

### 2.4 Encoding

- Control messages MUST use UTF-8 JSON.
- Objects that require signatures MUST be canonicalized using the JSON Canonicalization Scheme (RFC 8785) before signing.
- Large objects MUST be passed by `obj://` reference; control messages SHOULD be smaller than 1 MiB and MUST NOT exceed 8 MiB.
- A CBOR (RFC 8949) binding may be provided as an optional extension; its canonical encoding rules are defined separately.

### 2.5 Time and clocks

- On-the-wire timestamps MUST use RFC 3339 UTC; capability `iat`/`nbf`/`exp` MUST use Unix epoch seconds.
- Local timeouts, rate limiting, and retries MUST use a monotonic clock; `deadline` MUST be converted to the monotonic clock on receipt and MUST NOT be extended by system clock adjustments.
- After system suspend/resume, implementations MUST re-check `deadline`, `exp`, and leases; expired ones MUST NOT execute side effects.
- The Bus SHOULD announce the current time and the permitted clock skew in `welcome`; messages exceeding the skew SHOULD be rejected and logged as `TRANSPORT_CLOCK_SKEW`.
- Wall-clock consistency across devices MUST NOT be relied upon; 0.1 covers only single-device sessions.

---

## 3. Architecture

### 3.1 Planes

| Plane | Responsibilities | Components |
|---|---|---|
| **Control plane** | Registration, discovery, identity, capabilities, policy, consent, audit | RFS, CA, PCS, AL (all independent services) |
| **Data plane** | Request/response, events, streams, cancellation, errors | Bus Core (minimal TCB) |
| **Context plane** | Handle resolution, object store, task blackboard, information-flow labels | CF (authorization proxy; object store optional) |

### 3.2 Components

```
┌─────────────────────────────────────────────────────────────┐
│              User / Shell / System Agent                    │
│   (intent input, consent UI, activity center, audit view)   │
└───────────────▲─────────────────────────────▲───────────────┘
                │                             │
┌───────────────┴─────────────────────────────┴───────────────┐
│              Local Agent Bus Core (minimal TCB)             │
│   peer auth · envelope checks · routing · sessions ·        │
│   backpressure · idempotency index                          │
│   no policy · no issuance · no object store · no audit      │
└───▲───────────▲───────────▲───────────▲───────────▲─────────┘
    │           │           │           │           │
┌───┴────┐ ┌────┴───┐ ┌─────┴───┐ ┌─────┴───┐ ┌─────┴──────┐
│ RFS    │ │  CA    │ │  PCS    │ │  AL     │ │ Bridge     │
│ own    │ │ own    │ │ own     │ │ own     │ │ sandbox    │
│ process│ │ process│ │ process │ │ process │ │ per adapter│
└────────┘ └────────┘ └─────────┘ └─────────┘ └────────────┘
    ▲
┌───┴─────────────────────────────────────────────────────────┐
│ Context Fabric service (independent process)                │
│ authorization · labels · TTL · OS handle mapping · optional │
│ object store                                                │
└─────────────────────────────────────────────────────────────┘
    ▲
┌───┴────────────┐    ┌────────────────┐    ┌────────────────┐
│ Notes.app      │    │ Calendar.app   │    │ Messaging.app  │
│ └ Agent(notes) │    │ └ Agent(cal)   │    │ └ Agent(msg)   │
│   └ OSAP SDK   │    │   └ OSAP SDK   │    │   └ OSAP SDK   │
└────────────────┘    └────────────────┘    └────────────────┘
```

Bus Core is the only component on the routing path that all Agents must trust; trust in CA/PCS/AL is established through signatures, receipts, and audit anchoring rather than through a shared process address space. RFS/CA/PCS/CF/AL MUST run as independent processes or independent sandboxes and MUST communicate over the Bus using the system namespace; they MUST NOT share a process address space, and MUST NOT directly hold the private keys of other services. Bus Core MUST NOT parse the business semantics of `body.data`, and MUST NOT inline policy, issuance, storage, or audit logic into the routing path.

> CF and Bridges in the diagram likewise communicate through Bus Core; cross links are omitted for readability.

### 3.3 Deployment models

| Model | Description | Applicability |
|---|---|---|
| **A. Per-user bus + services** | A login session starts one Bus Core and several independent service processes; all Agents connect over local IPC | Desktop OS, recommended starting point |
| **B. System bus + user broker** | System-level identity/policy, user-level message broker; services partitioned per user | Multi-user, enterprise-managed |
| **C. Library + OS mediation** | No central routing daemon, the OS directly provides the authenticated channel; service components can be trimmed | Resource-constrained devices |

This specification does not mandate a deployment model; conformance requirements target protocol behavior, not process topology. Whichever model is adopted, the TCB boundary and trust profile MUST be explicitly declared (see §3.6).

### 3.4 Trust boundaries

- **App ↔ Bus**: authenticated via OS peer credentials; the Bus MUST verify the App identity of the connecting process.
- **Agent ↔ Agent**: no direct socket is established; all messages are routed through the Bus.
- **Bus ↔ native registries**: Bridges MUST preserve source and trust labels.
- **Bus ↔ external services**: outbound traffic through Bridges is governed by egress policy.
- **User ↔ Consent**: consent receipts are signed by the user/OS and cannot be forged by an Agent.
- **Bus Core ↔ Payload**: in the default 0.1 trust profile, Bus Core can read payloads; it MUST NOT persist payloads by default and MUST NOT write payloads into the audit unless required by task policy or explicitly requested by the user.
- **Service ↔ Service**: each service is an independent principal holding its own system capabilities; services MUST NOT implicitly trust each other merely because they "both belong to OSAP".
- **Bridge ↔ Agent**: a Bridge obtains only the minimum capability needed to perform projection; external content MUST retain `origin=external`.
- **The Bus is not a trust root**: the Bus's peer authentication depends on OS credentials; the Bus's own integrity depends on OS code signing/sandboxing. 0.1 does not claim resistance to a compromised Bus.

**Division of validation** (for each message):

| Check | Performed by | State dependency |
|---|---|---|
| Peer authentication, envelope schema/version/size, framing | Bus Core | None |
| Capability signature and binding (`audience`/`subject`/`task`) validation | Bus Core | None |
| `deadline`, idempotency, unique resolution of `to:capability` | Bus Core (optionally via RFS) | Idempotency index |
| Revocation status, policy evaluation, consent receipt, risk re-evaluation | Receiving Agent (via PCS/CA) | Yes |
| Business schema, side-effect execution, intent/outcome audit | Receiving Agent | Yes |

Bus Core MUST NOT refuse routing on the basis of policy or revocation decisions; it performs only **stateless binding validation** plus routing/quota. Authorization decisions MUST be made at the recipient.

### 3.5 Protocol stack

| Layer | Content | Normativity |
|---|---|---|
| L0 | Transport and framing | MUST |
| L1 | Identity and trust | MUST |
| L2 | Message envelope | MUST |
| L3 | Tasks and sessions | MUST |
| L4 | Capabilities and consent | MUST |
| L5 | Registry federation | MUST (C2+) |
| L6 | Context handles | MUST (C5+) |
| L7 | Domain schemas | OPTIONAL |

### 3.6 Trust profiles

0.1 discusses two trust profiles; only P0 may be declared by a 0.1 implementation.

| Profile | Bus visibility | Applicability | 0.1 status |
|---|---|---|---|
| **P0 Trusted Bus** | Sees envelope and plaintext `body` | Single-user device, Bus protected by OS integrity | Default, the only declarable one |
| **P1 Opaque Bus** | Sees only envelope metadata | Deployments that do not trust the Bus | Experimental, defined in 0.2 |

P0 requires:

- Bus Core MUST be protected by OS code signing/sandboxing and MUST verify its own integrity where available.
- Bus Core MUST NOT log payloads by default; error messages, audit, and crash dumps MUST be redacted.
- Deployers MUST disclose to users that "the Bus can read the content of cross-App messages".
- A conformance declaration MUST include `bus_visibility: "payload"`.

P1 direction (not 0.1 normative):

- Payloads use HPKE (RFC 9180) or equivalent end-to-end encryption; the Bus sees only routing and authorization metadata.
- 0.1 implementations MUST NOT claim support for P1; the related wire format is listed as an open issue in §15.

### 3.7 State and recovery

Bus Core and each service MUST clearly distinguish volatile state from persistent state.

State that MUST be persisted:

| State | Responsible component | Recovery requirement |
|---|---|---|
| Task tree and task state | Bus Core | Rebuilt after restart; incomplete tasks MUST transition to `failed` or be explicitly rescheduled |
| Idempotency index | Bus Core | Retained at least until after `deadline`; side effects MUST NOT be executed twice after restart |
| Revocation list | CA | Still effective after restart; evaluated together with `exp` |
| Consent receipt index | PCS | Verifiable and revocable after restart |
| Handle/object metadata (if managed by CF) | CF | Resolvable after restart; orphan objects reclaimed per policy |
| Audit chain head | AL | Chain integrity verified after restart; L3/L4 fail closed when corrupt |

Rules:

- Persistence MUST use atomic commits (WAL, log-structured storage, or an equivalent mechanism); "half records" MUST NOT occur.
- The audit chain MUST have a single writer; multi-instance deployments MUST partition by user or use leader election.
- Crash before the side effect: on recovery, mark the task failed and MUST NOT automatically retry non-idempotent side effects.
- Crash after the side effect but before the result is committed: recovery MUST record `effect.reconciled` and require manual/policy reconciliation; it MUST NOT silently replay.
- Recovery events MUST be written to the audit; the user MUST be able to see interrupted tasks.

**State is not memory.** The state in the table above is **runtime state**, not memory:

- Persistent state MUST NOT be used as cross-task context, semantic index, or user profile; its use is limited to routing, idempotency, recovery, and authorization decisions.
- Persistent state MUST NOT store a semantic copy of `body.data`; payloads are not persisted by default (see §11.11).
- Persistent state MUST NOT be exposed to ordinary Agents as a general query interface; it may only be accessed through the owning component's administrative interface or the corresponding capability.
- The idempotency index, audit log, and task tree MUST NOT be reused as memory sources; when memory is needed, it MUST be implemented as an independent capability (see §9.3).
- When user data is deleted, persistent state belonging to that user MUST be cleaned up or de-identified accordingly, while the audit chain may retain redacted records per §11.9.

---

## 4. Identity and Trust

### 4.1 Principal

The subject of a cross-application action is a four-tuple:

```
Principal = (User, App, AgentInstance, Device)
```

- **User**: the OS account or managed identity.
- **App**: install package identity + code signature.
- **AgentInstance**: the Agent instance registered when the App starts.
- **Device**: the device identifier.

The Bus MUST verify the App identity when a connection is established and bind the Agent instance to that App. An Agent cannot claim to belong to another App by string alone.

`agent://` is a **local naming** scheme, not a self-authenticating identifier. The Bus is the naming authority: it binds `(app, agent-name, instance-id)` to the OS-authenticated App identity and public key. Cross-device verifiable identity is out of scope for 0.1.

### 4.2 App attestation

- Linux: `SO_PEERCRED` + executable path/hash + package manager signature (if applicable).
- macOS: audit token + code signature + designated requirement.
- Windows: named pipe client SID + package identity + signature.
- Android: Binder UID/PID + package signature.
- Other platforms: local mTLS + client certificate issued by an OS trust root.

On verification failure, the Bus MUST refuse the connection and log `agent.registration_denied`.

### 4.3 Agent registration

After connecting, an Agent MUST send `hello`:

```json
{
  "osap": "0.1",
  "type": "hello",
  "id": "msg_01J...",
  "from": "agent://com.example.notes/assistant#7f3a",
  "to": { "agent": "agent://system/bus#0" },
  "body": {
    "schema": "osap.hello/v1",
    "data": {
      "app": "app://com.example.notes",
      "agent": "agent://com.example.notes/assistant#7f3a",
      "display_name": "Notes Assistant",
      "manifest_version": "1.0.0",
      "features": ["discover", "delegate", "context", "consent", "stream"],
      "encodings": ["json"],
      "public_key": "base64url..."
    }
  },
  "ts": "2026-11-10T10:14:45Z"
}
```

The Bus returns `welcome`, containing the `session_id`, feature switches, limits, and the Bus public key. Only after successful registration does the Agent's capability record enter the RFS.

`hello.body.data.public_key` MUST be bound to the public key in the App manifest or the OS key store; the Bus MUST verify the binding and refuse registration on failure. An Agent MUST NOT register a public key without proving possession of the corresponding private key.

### 4.4 Reserved namespaces

The following namespaces are reserved for the system:

- `agent://system/...`
- `cap://os/...`
- `ctx://os/...`
- `event://os/...`

Third-party Apps MUST NOT register these namespaces. Violators MUST be rejected and an audit event recorded.

### 4.5 Keys and signatures

- Default signature algorithm: Ed25519 (RFC 8032), in JWS form (RFC 7515).
- Signing keys SHOULD be held by the OS key store and used by Agents through restricted handles.
- Public keys are distributed via `hello` or the registry; rotation and expiry MUST be supported.
- Capability tokens, consent receipts, and audit anchors MUST be verifiable; messages themselves rely on transport mutual authentication and MAY be additionally signed.

### 4.6 Session

- Every connection has a `session_id`.
- Point-to-point collaboration uses a separate `session_id`, created by the initiator or assigned by the Bus.
- A Session MUST record the participants, creation time, expiry time, and capability references.
- Session termination MUST trigger cancellation or handoff of incomplete tasks.

### 4.7 Naming authority

- `agent://` names are assigned/confirmed by the Bus; an Agent's self-reported `instance-id` is only a suggestion, and the Bus MAY reassign it.
- The Bus MUST maintain the binding name → (App identity, public key, session) and re-check it on every route.
- After release, a name MUST NOT be reused immediately; a cooling-off period SHOULD be retained to prevent misdelivery of old messages.
- 0.1 provides no cross-device name resolution; cross-device scenarios MUST use another trust root and declare it explicitly.

---

## 5. Capability Model

### 5.1 Capability descriptor

A capability descriptor is a static declaration in the registry and does not equal authorization:

```json
{
  "cap": "cap://os/calendar/events",
  "name": "calendar.events",
  "actions": ["read", "propose", "create"],
  "resources": ["calendar:primary"],
  "schemas": ["osap.calendar.event/v1", "osap.calendar.propose/v1", "osap.calendar.proposal/v1"],
  "risk": "L2",
  "cost": { "latency_ms_p50": 300 },
  "constraints": {
    "max_window_days": 31,
    "requires_consent": "first_use"
  }
}
```

### 5.2 Capability token

A capability token MUST be a signed object containing at least:

```json
{
  "osap_cap": "0.1",
  "cap_id": "cap_01J...",
  "issuer": "user://local/example-user",
  "subject": "agent://com.example.notes/assistant#7f3a",
  "audience": "agent://com.example.calendar/agent#9c",
  "task_id": "task_01J...",
  "root_task_id": "task_01H...",
  "actions": ["propose"],
  "resources": ["calendar:primary"],
  "constraints": {
    "time_window": ["2026-11-10T00:00:00Z", "2026-11-17T00:00:00Z"],
    "max_uses": 5,
    "rate": "5/min",
    "max_depth": 2,
    "max_budget": { "wall_ms": 5000, "tool_calls": 2 }
  },
  "iat": 1794305685,
  "nbf": 1794305685,
  "exp": 1794309285,
  "parent_cap_id": "cap_01H...",
  "depth": 1,
  "consent_receipt_id": "consent_01J...",
  "proof": {
    "alg": "EdDSA",
    "kid": "user-key-1",
    "sig": "base64url..."
  }
}
```

Field requirements:

| Field | Requirement | Description |
|---|---|---|
| `issuer` | MUST | Issuing principal (user/system/parent Agent) |
| `subject` | MUST | The Agent that holds and exercises the capability; MUST equal the message sender |
| `audience` | MUST | Target Agent; MUST equal the message recipient |
| `task_id` | MUST | Bound task; MUST equal the task in the envelope |
| `root_task_id` | MUST | Used for audit aggregation |
| `actions` | MUST | Set of allowed actions |
| `resources` | MUST | Set of allowed resources |
| `exp` | MUST | Expiration time; SHOULD not exceed 1 hour |
| `parent_cap_id` | Conditional | MUST be provided for non-root capabilities |
| `depth` | Conditional | 0 for the root, +1 per delegation |
| `consent_receipt_id` | Conditional | MUST be provided for L3/L4 actions |
| `proof` | MUST | Signature |

**Semantic note**: `subject` is the Agent to which the capability is granted and on whose behalf the call is initiated (MUST equal the message `from`); `audience` is the Agent that MUST accept and validate the capability (MUST equal the message recipient). In a delegation scenario, the parent Agent issues a new capability for the child Agent, so both `subject` and `audience` are the child Agent; the parent Agent MUST NOT forward its own token as-is.

### 5.3 Attenuation

A child capability MUST satisfy all of the following conditions:

1. `subject` is the child Agent, and `audience` is the actual recipient;
2. `actions` ⊆ parent `actions`;
3. `resources` ⊆ parent `resources`;
4. `exp` ≤ parent `exp`, `nbf` ≥ parent `nbf`;
5. `max_uses` ≤ parent `max_uses`;
6. `rate` is not broader than parent `rate`;
7. each dimension of `max_budget` ≤ the parent budget;
8. `depth` = parent `depth` + 1, and ≤ `max_depth`;
9. `consent_receipt_id` is still valid;
10. the parent capability permits delegation (`can_delegate=true`).

If any condition is not satisfied, the CA MUST refuse to issue. The Bus MUST refuse routing for binding/attenuation conditions that are statelessly decidable (`audience`, `subject`, `task_id`, `depth`); stateful conditions such as revocation, `max_uses`, consent receipts, and budget are refused by the recipient before execution.

### 5.4 Binding

- **Audience binding**: `audience` MUST equal the ID of the receiving Agent; the Bus validates it before routing, and the recipient MUST re-check it.
- **Task binding**: `task_id` MUST equal `task.id` in the envelope. Exceptions: the sender's capability for `delegate` binds the parent task (`task.parent`), and the sender's capability for `handoff` binds the task being transferred (`task.id`). The recipient MUST validate according to this rule; reuse across tasks MUST be rejected.
- **Sender binding**: `subject` MUST equal the envelope `from`; forwarding a received credential as-is is prohibited.
- **Session binding** (optional): `constraints.session_id` may be used for point-to-point sessions.
- **Nonce**: high-value actions SHOULD use a one-time nonce or `max_uses=1`.

The Bus performs only stateless binding validation; revocation, policy, and consent are re-checked by the recipient (see §3.4, §5.5).

### 5.5 Revocation

- The CA MUST provide a revocation interface, revoking by `cap_id`.
- Revoking a parent capability MUST cascade to revoke all descendant capabilities.
- Capabilities SHOULD have short TTLs; the revocation list SHOULD be cacheable offline.
- The receiving Agent MUST check revocation status via the CA before execution; if the recipient or the CA cannot check, it MUST refuse high-risk actions.
- Revocation events MUST be written to the audit ledger, and affected Agents MUST be notified.

### 5.6 Authority invariants

| No. | Invariant |
|---|---|
| AI1 | No ambient authority: an Agent cannot perform any cross-application action without holding a capability |
| AI2 | Monotonic narrowing: child capability authority ⊆ parent capability authority |
| AI3 | Audience binding: a capability cannot be used by an Agent other than the `audience` |
| AI4 | Task binding: a capability cannot be reused by another task |
| AI5 | Revocation completeness: revoking a parent capability invalidates all descendants |
| AI6 | No forwarding: an Agent cannot hand its own credential to another party |
| AI7 | Consent precedence: L3/L4 actions MUST have a valid consent receipt before execution |
| AI8 | Audit precedence: the audit record for an L3/L4 action MUST be writable before the side effect |
| AI9 | Bounded depth: delegation depth does not exceed `max_depth` |
| AI10 | Monotonic budget: a child task's budget does not exceed the parent task's remaining budget |

### 5.7 Risk classes

| Tier | Name | Examples | Default consent |
|---|---|---|---|
| L0 | Public read | Public weather, public directory | Automatically allowed |
| L1 | Personal read | Calendar, contacts, notes | First-use consent or task-level consent |
| L2 | Local write | Create a local draft, modify a to-do | Automatic + notification |
| L3 | External side effect | Send a message, send email, submit a form | Consent per use (batchable/time-limited) |
| L4 | High impact | Payments, deletion, external publication | Strong confirmation + secondary authentication |

Risk tiers are declared by the capability record; the PCS may raise but not lower them.

### 5.8 Consent linkage

- L3/L4 capabilities MUST reference a valid `consent_receipt_id`.
- The `actions`, `resources`, `task_id`, and `audience` in the receipt MUST cover the capability request.
- When the receipt expires or is revoked, the capability MUST become invalid.
- Batch consent MUST have an explicit task scope, time window, and action set.

---

## 6. Registry Federation

### 6.1 App manifest

An App registers a manifest on installation or first run:

```json
{
  "osap_manifest": "0.1",
  "app": "app://com.example.calendar",
  "version": "3.2.1",
  "signature": "base64url...",
  "agents": [
    {
      "agent": "agent://com.example.calendar/agent",
      "display_name": "Calendar Agent",
      "public_key": "base64url...",
      "capabilities": [
        {
          "cap": "cap://os/calendar/events",
          "actions": ["read", "propose", "create"],
          "resources": ["calendar:primary"],
          "schemas": ["osap.calendar.event/v1", "osap.calendar.propose/v1", "osap.calendar.proposal/v1"],
          "risk": "L2",
          "consent": "first_use"
        }
      ],
      "events": {
        "publishes": ["event://app.com.example.calendar/event_changed"],
        "subscribes": ["event://os/user/activity"]
      },
      "data_scopes": ["calendar:primary"]
    }
  ]
}
```

The manifest MUST be signed by the App; the RFS MUST verify the signature before indexing.

### 6.2 Capability Record

Unified capability record:

```json
{
  "record_id": "cr_01J...",
  "source": {
    "kind": "vendor_registry",
    "registry": "android.appfunctions",
    "native_id": "com.example.calendar.createEvent",
    "version": "1.0.0"
  },
  "app": "app://com.example.calendar",
  "agent": "agent://com.example.calendar/agent#9c",
  "capability": {
    "cap": "cap://os/calendar/events",
    "actions": ["create"],
    "resources": ["calendar:primary"],
    "schemas": ["osap.calendar.event/v1"],
    "risk": "L2"
  },
  "policy": {
    "visibility": "discoverable",
    "consent": "first_use"
  },
  "provenance": {
    "trust": "system",
    "signature": "base64url...",
    "attested_at": "2026-11-10T10:00:00Z"
  },
  "freshness": {
    "observed_at": "2026-11-10T10:00:00Z",
    "expires_at": "2026-11-11T10:00:00Z"
  }
}
```

### 6.3 Source kinds

| `source.kind` | Description |
|---|---|
| `vendor_registry` | Apple App Intents, Android AppFunctions, Windows App Actions |
| `mcp` | MCP Server / Tool |
| `a2a` | A2A Agent Card / Skill |
| `dbus` | D-Bus service / interface / method |
| `openapi` | OpenAPI operation |
| `native` | The App registers directly through the OSAP SDK |
| `bridge` | Other custom bridges |

### 6.4 Provenance and trust

| `trust` | Meaning |
|---|---|
| `system` | OS vendor registry or system signature |
| `verified` | Third-party registry/protocol with a verified signature |
| `unverified` | Manually added by the user or an unverified source |

- Discovery results MUST include `source`, `trust`, and `freshness`.
- Content originating from external protocols MUST be marked `origin=external` and has the lowest default trust level.
- The RFS MUST NOT promote an unverified source to `system`.

### 6.5 Discovery query

```json
{
  "osap": "0.1",
  "type": "discover",
  "id": "msg_01J...",
  "from": "agent://com.example.orchestrator/main#1a2b",
  "to": { "agent": "agent://system/registry#0" },
  "body": {
    "schema": "osap.discover/v1",
    "data": {
      "intent": "Find a free slot for a meeting",
      "requires": ["calendar.read", "calendar.propose"],
      "schemas": ["osap.calendar.propose/v1", "osap.calendar.proposal/v1"],
      "risk_max": "L2",
      "sources": ["native", "vendor_registry", "mcp", "a2a"],
      "limit": 5
    }
  },
  "ts": "2026-11-10T10:14:45Z"
}
```

### 6.6 Discovery response

```json
{
  "osap": "0.1",
  "type": "result",
  "id": "msg_02",
  "causation_id": "msg_01",
  "from": "agent://system/registry#0",
  "to": { "agent": "agent://com.example.orchestrator/main#1a2b" },
  "body": {
    "schema": "osap.discover.result/v1",
    "data": {
      "candidates": [
        {
          "record_id": "cr_01J...",
          "agent": "agent://com.example.calendar/agent#9c",
          "capability": "cap://os/calendar/events",
          "match": 0.94,
          "risk": "L2",
          "consent_hint": "first_use",
          "source": { "kind": "vendor_registry", "registry": "android.appfunctions" },
          "trust": "system",
          "schemas": ["osap.calendar.propose/v1", "osap.calendar.proposal/v1"]
        }
      ]
    }
  },
  "ts": "2026-11-10T10:14:46Z"
}
```

Rules:

- Discovery results MUST include `consent_hint` (`none`, `first_use`, `per_task`, `per_use`), which comes from the static policy of the capability record and is not real-time authorization.
- Discovery results MUST NOT return a real-time `policy_verdict`; real-time verdicts MUST be evaluated by the PCS at `request`/`delegate` time (see §6.9).
- Callers MUST NOT treat `consent_hint` as authorization; `match` is only a ranking signal and cannot replace structured filtering.
- The discovery interface MUST NOT enumerate user private data, and MUST NOT leak "whether some Agent is currently denied by policy".

### 6.7 Federation adapters

Each Bridge Adapter MUST:

1. read the native descriptor;
2. project it into a `Capability Record`;
3. preserve `source`, `native_id`, `version`, and `provenance`;
4. map schemas and risk tiers;
5. update or invalidate the record when the native descriptor changes;
6. not modify the authoritative state of the native registry.

Mapping recommendations:

| Native | `source.registry` | `native_id` |
|---|---|---|
| Apple App Intent | `apple.app_intents` | intent identifier |
| Android AppFunction | `android.appfunctions` | function id |
| Windows App Action | `windows.app_actions` | action id |
| MCP Tool | `mcp` | server + tool name |
| A2A Skill | `a2a` | agent card + skill id |
| D-Bus Method | `dbus` | bus + path + interface + method |
| OpenAPI Operation | `openapi` | operationId |

### 6.8 Namespace mapping

- There MUST be a deterministic mapping between native namespaces and OSAP capability names.
- On conflict, disambiguation MUST use the `source.registry` prefix.
- Schema mapping MUST preserve the original schema URI and version.
- Capabilities that cannot be mapped safely MUST be marked `visibility=hidden` and MUST NOT be silently exposed.

### 6.9 Policy verdict

A policy verdict is a **call-time** decision, not part of a discovery result. When receiving a `request`/`delegate`, the PCS combines the following inputs:

- user preferences and consent history;
- App manifest and signature;
- capability risk tier;
- current task, session, and foreground state;
- enterprise/MDM policy;
- data scope and egress policy;
- the Agent's trust level and behavior record.

Output:

| Verdict | Meaning |
|---|---|
| `allow` | May be executed directly |
| `allow_with_logging` | May be executed, but MUST be logged |
| `require_consent` | Requires a user consent receipt |
| `deny` | Denied |

When it cannot be determined, `deny` MUST be returned.

### 6.10 Caching and freshness

- Capability records MUST have `observed_at` and `expires_at`.
- Expired records MUST be re-verified and MUST NOT be used for authorization decisions.
- The discovery cache SHOULD be bounded and isolated per source.
- When a native registry deletes a capability, the RFS MUST invalidate the corresponding record within the TTL.

---

## 7. Message Protocol

### 7.1 Envelope

```json
{
  "osap": "0.1",
  "id": "msg_01J...",
  "type": "request",
  "trace_id": "trace_01J...",
  "causation_id": "msg_parent...",
  "session_id": "session_01J...",
  "from": "agent://com.example.orchestrator/main#1a2b",
  "to": { "capability": "cap://os/calendar/events" },
  "task": {
    "id": "task_01J...",
    "parent": "task_01H...",
    "root": "task_01G...",
    "mode": "supervisor"
  },
  "auth": {
    "cap_id": "cap_01J...",
    "token": "base64url..."
  },
  "body": {
    "schema": "osap.calendar.propose/v1",
    "data": {
      "window": "2026-11-18T09:00:00Z/2026-11-18T12:00:00Z",
      "duration_min": 60
    }
  },
  "refs": ["obj://sha256:9f2c..."],
  "reply_to": "msg_01H...",
  "deadline": "2026-11-10T10:15:00Z",
  "priority": "normal",
  "consent": { "receipt_id": "consent_01J..." },
  "origin": { "kind": "agent", "trust": "verified" },
  "ts": "2026-11-10T10:14:45Z",
  "extensions": {}
}
```

Field rules:

- `osap` MUST be present; incompatible major versions MUST be rejected.
- `id` MUST be globally unique; it is used for idempotent deduplication.
- `trace_id` MUST remain consistent within a single user intent.
- `causation_id` SHOULD point to the message that directly triggered this message.
- `session_id` MUST be present in point-to-point collaboration.
- `to` MUST be one of `{ "agent": ... }`, `{ "capability": ... }`, or `{ "user": ... }`; `{ "user": ... }` is used only for consent and system notification flows.
- When `to` uses `capability`, the Bus MUST resolve a unique `audience` Agent through the RFS; if it cannot be uniquely resolved, or the resolution result is inconsistent with `auth.token.audience`, it MUST return `ROUTING_AMBIGUOUS` or `CAPABILITY_AUDIENCE_MISMATCH`.
- `auth.token` MUST be a valid capability token; `auth.cap_id` is used for indexing.
- `body.schema` MUST be present; the Bus does not parse `body.data`.
- Handles in `refs` MUST be ones the sender is entitled to pass.
- `deadline` is an absolute wall-clock time; the recipient MUST convert it to the monotonic clock and MUST NOT execute side effects after it has passed.
- `priority` is only a scheduling hint and does not constitute a real-time guarantee; implementations MUST prevent low-priority tasks from starving.
- `origin` is used for prompt injection protection and trust decisions.

### 7.2 Message types

| Type | Semantics | Idempotent |
|---|---|---|
| `hello` / `welcome` | Registration and version negotiation | Yes |
| `discover` | Query capabilities | Yes |
| `describe` | Retrieve capability/Agent details | Yes |
| `request` | Invoke a capability/execute a task | Yes (by `id`) |
| `result` | Successful result | — |
| `error` | Structured error | — |
| `event` | Topic event | No |
| `stream.open` / `stream.chunk` / `stream.close` | Stream | By sequence number |
| `cancel` | Cancel a task | Yes |
| `delegate` | Delegate a subtask (create a child task tree) | Yes |
| `handoff` | Transfer ownership of an existing task | Yes (by `id`) |
| `status` | Progress/budget/heartbeat | No |
| `consent.request` / `consent.grant` / `consent.deny` | Consent flow | Yes |

`handoff` is a one-shot message: the recipient MUST conclude with `result` (accept/reject) or `error` and does not introduce an additional confirmation round trip. See §8.9 for the difference between `handoff` and `delegate`.

### 7.3 Request/response

- `request` MUST carry `task.id`, `auth`, and `deadline`.
- The recipient MUST return `result`, `error`, or `status` (indicating that processing continues) before the `deadline`.
- The caller MUST deduplicate by `id`; the recipient SHOULD cache recent results.
- Retries MUST use the same `id`, or a new `id` plus an idempotency-key extension.
- `result` MUST be correlated with the request through `causation_id`.
- `delegate` MUST carry the new subtask's `task.id` and `task.parent`; the `task_id` of the capability corresponding to `auth.cap_id` MUST equal `task.parent`.
- `handoff` MUST carry the `task.id` of the existing task; the `task_id` of the capability corresponding to `auth.cap_id` MUST equal `task.id`.

### 7.4 Events

- Event topics use `event://<namespace>/<topic>`.
- Subscribing requires the `cap://os/events/subscribe` capability + topic filter + data scope.
- Default delivery semantics: at most once.
- Events MUST carry `origin` and a minimal payload; sensitive content is passed via `refs`.
- Users MUST be able to view and revoke subscriptions.

### 7.5 Streams

- `stream.open` carries `stream_id`, `schema`, and `total_estimate` (optional).
- `stream.chunk` carries `stream_id`, `seq`, and `data` or `ref`.
- `stream.close` carries `stream_id`, `status`, and `summary`.
- The recipient MUST deduplicate/order by `seq`; missing fragments SHOULD be requested for retransmission.
- Cancellation MUST terminate the stream and release resources.

### 7.6 Cancel

- `cancel` MUST carry `task.id` and a reason.
- The Bus MUST propagate it down the task tree, unless a subtask is explicitly marked `detached`.
- The recipient MUST stop as soon as possible; if it cannot stop, it MUST return `CANCELLED` or `ERROR`.
- Cancellation MUST record an audit event.

### 7.7 Errors

```json
{
  "osap": "0.1",
  "type": "error",
  "id": "msg_02",
  "causation_id": "msg_01",
  "from": "agent://com.example.calendar/agent#9c",
  "to": { "agent": "agent://com.example.orchestrator/main#1a2b" },
  "body": {
    "schema": "osap.error/v1",
    "data": {
      "code": "POLICY_DENIED",
      "message": "User confirmation is required to send an external message",
      "retryable": false,
      "details": {
        "policy": "external_side_effect",
        "consent_url": "osap://consent/consent_01J..."
      }
    }
  },
  "ts": "2026-11-10T10:14:46Z"
}
```

Standard error codes:

| Error code | Trigger condition | Retryable |
|---|---|---|
| `TRANSPORT_HANDSHAKE_REQUIRED` | The connection has not yet completed `hello`/`welcome` | No (handshake first) |
| `TRANSPORT_VERSION_UNSUPPORTED` | The `osap` major version is incompatible | No |
| `TRANSPORT_FRAME_TOO_LARGE` | A single frame/message exceeds 8 MiB | No |
| `TRANSPORT_CLOCK_SKEW` | The timestamp exceeds the permitted skew | No |
| `SCHEMA_UNSUPPORTED` | Unknown message type or unsupported `body.schema` | No |
| `SCHEMA_INVALID` | `body.data` does not conform to the declared schema | No |
| `AUTH_DENIED` | Peer authentication or signature verification failed | No |
| `ROUTING_AMBIGUOUS` | `to.capability` cannot be uniquely resolved | No |
| `ROUTING_NOT_FOUND` | The target Agent or capability does not exist | No |
| `CAPABILITY_AUDIENCE_MISMATCH` | `audience` is inconsistent with the recipient | No |
| `CAPABILITY_SUBJECT_MISMATCH` | `subject` is inconsistent with the envelope `from` | No |
| `CAPABILITY_TASK_MISMATCH` | `task_id` is inconsistent with the envelope `task.id` | No |
| `CAPABILITY_ATTENUATION_INVALID` | The child capability widens scope, extends the time limit, or violates `max_depth` | No |
| `CAPABILITY_REVOKED` | The capability has been revoked or has expired | No |
| `POLICY_DENIED` | Policy denies this action | No |
| `POLICY_CONSENT_REQUIRED` | An L3/L4 action lacks a valid consent receipt | No (obtain consent first) |
| `POLICY_CONSENT_EXPIRED` | The receipt has expired or been revoked | No (obtain consent again) |
| `POLICY_CONSENT_SCOPE_MISMATCH` | The receipt's actions/resources/task/audience do not cover the request | No |
| `TASK_BUDGET_EXCEEDED` | The budget is exhausted | No |
| `CONTEXT_DENIED` | No permission to resolve the handle | No |
| `CONTEXT_EXPIRED` | The handle has expired | No (acquire again) |
| `CONTEXT_NOT_FOUND` | The handle does not exist | No |
| `DUPLICATE` | Duplicate `id`, and the original result is not cached | Yes (read the original result) |
| `RATE_LIMIT` | The rate/quota is exceeded | Yes (back off) |
| `TIMEOUT` | The `deadline` is exceeded | Depends on operation idempotency |
| `CANCELLED` | The task or stream was cancelled | No |
| `INTERNAL` | Internal implementation error | Depends |

New prefixes MUST fall within `AUTH_`, `POLICY_`, `CAPABILITY_`, `TASK_`, `SCHEMA_`, `CONTEXT_`, `ROUTING_`, `TRANSPORT_`; domain errors MAY use an extension namespace.

### 7.8 Idempotency, deadlines, ordering

- Every `request` MUST have a unique `id`; the recipient MUST return the same result or `DUPLICATE` for a duplicate `id`.
- `deadline` is an absolute wall-clock time; side effects MUST NOT be executed after it has passed.
- The idempotency index MUST be persisted or reconstructible, covering at least the retry window after `deadline`; after a Bus restart, side effects MUST NOT be executed again due to cache loss.
- Retries MUST back off; non-idempotent side effects MUST NOT be retried automatically unless the business schema declares an idempotency key.
- Messages within the same `session_id` SHOULD preserve causal order; the Bus MAY deliver independent messages in parallel.
- Events do not guarantee ordering; when ordering is required, use `stream` or an extension carrying `seq`.

### 7.9 Framing

- Streaming transports (UDS, named pipe, localhost mTLS) MUST use a 4-byte big-endian length prefix + UTF-8 JSON.
- Message-oriented transports (XPC, Binder, D-Bus) MUST use native message boundaries; they MUST NOT be forced to add another length prefix.
- A single frame/message MUST NOT exceed 8 MiB.
- After a connection is established, `hello` / `welcome` MUST be exchanged first.
- Unknown message types MUST return `SCHEMA_UNSUPPORTED` and MUST NOT be silently dropped.

### 7.10 Transport bindings

| Platform | Recommended binding | Type | Peer authentication |
|---|---|---|---|
| Linux | Unix domain socket | stream | `SO_PEERCRED` + executable verification |
| macOS | XPC / Mach service | message | audit token + code signature |
| Windows | named pipe | stream or message | client SID + package identity |
| Android | Binder | message | UID/PID + package signature |
| Cross-sandbox/container | localhost mTLS | stream | client certificate |

Transport bindings MUST provide: mutual authentication, message integrity, connection-level isolation, and verifiable peer identity. A binding that offers only plaintext loopback TCP without authentication MUST NOT be used for actions above L2.

A transport binding MUST declare whether it is of type `stream` or `message`; framing rules are selected according to the type. Message-oriented bindings MUST preserve the sender identity and message boundaries.

### 7.11 Flow control and scheduling

- The Bus MUST implement admission control: per-Agent connection count, in-flight request count, queue length, and rate limits.
- Backpressure MUST use explicit signals: `RATE_LIMIT`, queue depth in `status`, or credits in streaming transports.
- Streaming transports SHOULD use credit-based flow control; the recipient MUST be able to pause the sender.
- The Bus MUST isolate queues by sender to prevent one Agent from occupying the global queue (head-of-line blocking).
- `priority` is only a hint; implementations SHOULD use weighted fair queuing and MUST prevent permanent starvation of low-priority tasks.
- Scheduling MUST NOT provide hard real-time guarantees; time-sensitive tasks should use `deadline` and budgets rather than relying on priority.

---

## 8. Task Model

### 8.1 Task object

```json
{
  "task_id": "task_01J...",
  "parent_task_id": "task_01H...",
  "root_task_id": "task_01G...",
  "session_id": "session_01J...",
  "mode": "supervisor",
  "goal": "Find a 60-minute slot next Wednesday between 9:00 and 12:00 and create a tentative event",
  "owner": "agent://com.example.orchestrator/main#1a2b",
  "assignee": "agent://com.example.calendar/agent#9c",
  "input_refs": ["obj://sha256:..."],
  "output_refs": [],
  "budget": {
    "wall_ms": 8000,
    "tool_calls": 2,
    "tokens": 2000,
    "money": { "currency": "USD", "amount": 0 },
    "depth": 1
  },
  "deadline": "2026-11-10T10:15:00Z",
  "priority": "normal",
  "status": "created",
  "result_schema": "osap.calendar.proposal/v1",
  "authority": { "cap_id": "cap_01J..." }
}
```

### 8.2 Task tree

- Every task MUST have a `task_id` and a `root_task_id`.
- `parent_task_id` MUST be present in hierarchical delegation; point-to-point tasks MAY have it empty.
- The Bus MUST maintain a task tree index for cancellation, budget, and audit aggregation.
- The task tree MUST be persisted; see §3.7 for recovery semantics.
- Task tree depth MUST be limited by `max_depth`; delegations exceeding it MUST be rejected.
- Task termination (success/failure/cancellation) MUST notify the parent task and the audit ledger.

### 8.3 Supervisor mode

- When `mode=supervisor`, `parent_task_id` MUST be present.
- The subtask's capability MUST be attenuated from the parent task's capability.
- The subtask budget MUST be ≤ the parent task's remaining budget.
- Cancelling the parent task MUST cascade to cancel subtasks.
- The subtask result MUST be returned to the parent task via `result`, without automatically sharing intermediate context.

### 8.4 Peer mode

- When `mode=peer`, both parties are equal participants; `session_id` MUST be present.
- Each party MUST hold an independent capability; one party cannot obtain the other party's permissions by virtue of session identity.
- Point-to-point messages MUST still carry `auth`; `audience` and `subject` are bound.
- When one party requests the other to perform an action, it uses `request`; when a new subtask must be created, it uses `delegate`.
- A peer cannot command the other to elevate privileges; any privilege elevation MUST go through the PCS and user consent.
- Session termination MUST clean up temporary context and incomplete tasks.

### 8.5 Delegation

A `delegate` message MUST include:

1. the subtask goal and input references;
2. the attenuated capability token;
3. the budget (time, call count, money, depth);
4. the deadline (`deadline`, MUST) and priority (`priority`, MAY);
5. the result contract (`result_schema`).

Rules:

- The delegator MUST hold a capability with `can_delegate=true`.
- The child capability MUST satisfy all attenuation conditions in §5.3.
- The delegator MUST NOT pass its own credential as-is to the child Agent.
- The child Agent MUST validate the credential chain, budget, and depth.
- Delegation failure MUST return a structured error and MUST NOT degrade silently.

### 8.6 Budgets

| Dimension | Description |
|---|---|
| `wall_ms` | Wall-clock time |
| `tool_calls` | Number of tool/external calls |
| `tokens` | Model token budget |
| `money` | Amount and currency |
| `depth` | Remaining delegation depth |

- Budgets MUST decrease monotonically.
- Exceeding the budget MUST stop execution and return `TASK_BUDGET_EXCEEDED`.
- Budget consumption SHOULD be reported via `status`.
- The Bus MAY forcibly cancel a task when its budget is exhausted.

### 8.7 Cancellation

- `cancel` propagates down the task tree.
- Subtasks marked `detached=true` MAY continue running, but MUST lose the parent task's capabilities.
- Cancellation MUST release context handles, streams, and temporary objects.
- Side effects that have already occurred MUST be recorded in the audit; irreversible side effects MUST be clearly indicated at consent time.

### 8.8 Results

- Results MUST carry `result_schema` and `output_refs`.
- Large results MUST be referenced via `obj://`.
- The parent task MUST validate the result schema and return `SCHEMA_INVALID` on mismatch.
- Results MAY include extension fields such as `confidence`, `cost`, and `warnings`.
- Result aggregation MUST NOT automatically merge the entire context of child Agents.

### 8.9 Handoff

The difference between `handoff` and `delegate`: `delegate` **creates** a subtask and adds a new task tree node; `handoff` **transfers ownership of an existing task**, creating no new task and not changing `mode`.

- `handoff` is a one-shot message; the recipient MUST conclude with `result` (accept or reject) or `error`, and MUST NOT introduce an additional confirmation type.
- The sender MUST be the current `owner` and MUST hold a capability that permits the transfer; the recipient MUST validate the `subject`, `audience`, and `task_id` bindings.
- The original owner MUST explicitly relinquish control; the new owner MUST obtain a **new** capability token (the old token MUST NOT be forwarded as-is; attenuate/re-issue per §5.4).
- If the recipient rejects or times out, the task MUST remain with the original owner, with unchanged state and budget.
- When a handoff involves L3/L4 actions, user consent MUST be obtained again, and the receipt's `audience` MUST point to the new owner.
- A handoff MUST record a `task.handoff` audit event, including the original owner, new owner, `cap_id`, and `consent_receipt_id` (if any).
- The task state machine does not add `handoff_pending`; an ownership change does not change the task state.

### 8.10 Task state machine

```
created ──accept──> accepted ──start──> running
   │                    │                 │
   │                    │                 ├──> waiting_consent ──grant──> running
   │                    │                 ├──> succeeded
   │                    │                 ├──> failed
   │                    │                 └──> cancelled
   └──reject──> rejected
```

State transitions MUST be recorded by the Bus; illegal transitions MUST be rejected.

After a Bus restart, tasks in a non-terminal state MUST transition to `failed` or be explicitly rescheduled according to policy; they MUST NOT silently remain `running`. Recovery MUST record an audit event.

### 8.11 Recovery and reconciliation

- Task records, budget consumption, and result references MUST be persisted; after recovery it MUST be possible to determine whether a task has already produced side effects.
- For irreversible side effects, an `effect.intent` audit MUST be written before execution; on recovery, if there is an intent but no outcome, it MUST be marked `unknown` and reconciliation required.
- Automatic retries are permitted only for idempotent operations; retries MUST use the same `id` or an explicit idempotency key.
- Interrupted tasks MUST notify the parent task and the user; `detached` tasks MUST make their independent lifecycle explicit.
- Reconciliation results MUST be written back to the task state and the audit; "replay" MUST NOT be substituted for reconciliation.

---

## 9. Context Fabric

CF is positioned as an **authorization proxy and handle resolution layer**, not a new file system. The default implementation MUST reuse existing OS mechanisms such as file descriptors, security-scoped bookmarks, content URIs, portals, or equivalents; an independent object store is an optional implementation and MUST satisfy the storage responsibilities of §9.10.

### 9.1 Handle schemes

| Scheme | Example | Description |
|---|---|---|
| `ctx://` | `ctx://user/profile#display_name` | User/session/device context |
| `obj://` | `obj://sha256:9f2c...` | Content-addressed object; mapped to the OS content service when there is no independent store |
| `task://` | `task://task_01J/blackboard/plan` | Task-level blackboard |
| `file://` | `file://fh_01J...` | Opaque file handle; mapped to an OS handle |
| `contact://` | `contact://directory/example-contact` | Resolved by a directory service |
| `event://` | `event://os/user/activity` | Event topic |

- `file://` MUST NOT expose raw absolute paths; use opaque handles.
- Handles MUST be revocable, expirable, and auditable.
- Handles themselves MAY be passed; the permission to resolve them is determined by capabilities.

### 9.2 Resolution

- To resolve a handle, an Agent MUST hold a capability that includes the `resolve` action and covers the resource.
- CF MUST validate `audience`, `task_id`, `subject`, `exp`, and information-flow labels.
- The resolution result MAY be data or another handle.
- Every resolution MUST record a `context.resolve` audit event, including the caller, handle, labels, and decision.
- Resolution failure MUST return `CONTEXT_DENIED` or `CONTEXT_NOT_FOUND` and MUST NOT leak information beyond existence.

### 9.3 Scopes and TTL

| Scope | Lifetime |
|---|---|
| `task` | Invalidated when the task ends |
| `session` | Invalidated when the session ends |
| `user` | Revoked by the user or expired |
| `device` | Controlled by device policy |

- Handles MUST have a `ttl` or `expires_at`.
- Expired handles MUST be rejected; automatic renewal MUST NOT occur.
- Long-term memory MUST be separately authorized, user-visible, and user-deletable.

Long-term memory is not part of the Bus, nor a default use of any task handle:

- Writing long-term memory MUST be authorized by an explicit capability (e.g. `memory.write`) and MUST record the purpose, source, and retention period.
- Reading long-term memory MUST be separately authorized and MUST NOT be implicitly obtained by holding a task capability.
- Long-term memory MUST be deletable at user/App/entry granularity; deletion MUST trigger invalidation of derived indexes.
- The task blackboard, object metadata, and Bus persistent state MUST NOT be automatically promoted to long-term memory (see §3.7, §9.5).
- 0.1 does not define the wire format of a memory service; if an implementation provides one, it MUST register it as an ordinary capability and declare its data scope and consent mode.

### 9.4 Information-flow labels

Every handle/object MUST carry labels:

```json
{
  "label": "personal",
  "origin": { "kind": "app", "id": "app://com.example.notes" },
  "trust": "verified",
  "derived_from": ["obj://sha256:..."],
  "constraints": {
    "allow_egress": false,
    "allowed_agents": ["agent://com.example.orchestrator/main#1a2b"]
  }
}
```

Label levels: `public` < `personal` < `sensitive` < `secret`.

Rules:

- Derived objects MUST inherit a label no lower than that of their source.
- `secret` objects MUST NOT leave this device unless the user explicitly permits it.
- External content MUST be marked `origin.kind=external`, with `trust=unverified` by default.
- On label conflict, the stricter value MUST be used.

### 9.5 Task blackboard

- `task://<task_id>/blackboard` is a controlled key-value area shared by task participants.
- Reading and writing MUST require capabilities; write operations MUST record audit.
- The blackboard lifetime = the task lifetime; when the task ends it MUST be cleaned up or archived per policy.
- The blackboard MUST NOT be automatically promoted to long-term memory.
- Concurrent writes SHOULD use version numbers or CAS to avoid overwriting.

### 9.6 Object store

- If an independent object store is implemented, `obj://` MUST use content addressing (e.g. SHA-256).
- Object writes MUST record the owner, labels, creator, and reference count.
- Object reads MUST go through CF policy; path traversal MUST NOT be used to bypass it.
- Object deletion MUST check references; referenced objects SHOULD be deleted lazily or marked with tombstones.
- Objects MAY be stored encrypted; keys are managed by the OS key store.
- If no object store is built, CF MUST map `obj://` to the OS content service and preserve label and TTL semantics.

### 9.7 Revocation and deletion

- Revoking a handle MUST invalidate all handles derived from it.
- Deleting an object MUST trigger reference cleanup and an audit event.
- Users MUST be able to view "who resolved which handle and when".
- Revoked handles MUST be invalidated in caches; the cache TTL MUST NOT exceed the handle TTL.
- Revocation SHOULD map to OS handle revocation where possible; where revocation is not possible, it MUST fall back to TTL and denial of resolution.

### 9.8 Egress

- Any data leaving this device MUST pass through egress policy.
- Egress of `sensitive`/`secret` data MUST require one-time user permission or explicit authorization.
- Egress events MUST record the destination, data labels, and consent receipt.
- Bridges to external protocols (A2A/HTTP/remote MCP) MUST preserve source and labels.

### 9.9 Relationship to OS primitives

CF MUST prefer reusing OS primitives rather than duplicating their semantics:

| OSAP handle | Default mapping | Description |
|---|---|---|
| `file://` | fd / security-scoped bookmark / content URI / portal | Does not expose absolute paths; permissions are checked by both the OS and CF |
| `contact://` | OS contacts provider | Returns only the resolution result, does not cache plaintext |
| `ctx://` | OS session/user context service | Read-only snapshot, with source and TTL |
| `task://` | Bus/CF task metadata | Cleaned up when the task ends |
| `obj://` | OS content service or optional CAS | If a CAS is built, see §9.10 |

- If a platform has no corresponding primitive, CF MAY provide a minimal substitute implementation, but MUST annotate `cf_mode: "managed_store"` in the conformance declaration.
- CF MUST NOT use handles to bypass OS sandboxes or file permissions.

### 9.10 Storage responsibilities

If an independent object store is implemented (`cf_mode: "managed_store"`), the following MUST be defined and implemented:

- quotas and admission: per-user/per-App object count and byte limits;
- garbage collection: reference counting, tombstones, orphan scanning, and retention periods;
- crash recovery: write atomicity, consistency of metadata and content, orphan handling after restart;
- encryption: encryption at rest and key rotation, with keys managed by the OS key store;
- path and handle security: prohibition of path traversal, symlink escape, and handle guessing;
- deletion and revocation: reference checking, invalidation of derived handles, audit events.

If these responsibilities are not implemented, CF MUST act only as an authorization proxy and map `obj://` to the OS content service; it MUST NOT claim to provide an independent object store.

---

## 10. Consent and Audit

### 10.1 Risk tiers

See §5.7. The PCS MUST compute the final risk from the capability record, data labels, target, and context; it may raise but not lower it.

### 10.2 Consent request

```json
{
  "osap": "0.1",
  "type": "consent.request",
  "id": "msg_03",
  "from": "agent://system/policy#0",
  "to": { "user": "user://local/example-user" },
  "body": {
    "schema": "osap.consent.request/v1",
    "data": {
      "request_id": "creq_01J...",
      "task_id": "task_01J...",
      "agent": "agent://com.example.orchestrator/main#1a2b",
      "audience": "agent://com.example.messaging/agent#4d",
      "actions": ["messaging.send"],
      "resources": ["contact://directory/example-contact"],
      "risk": "L3",
      "summary": "Send a meeting-summary message to the example contact",
      "intent_preview": {
        "actor": "Orchestrator Agent",
        "what": "Send 1 message",
        "data": ["Meeting summary (by reference)", "Contact: example contact"],
        "cost": { "money": 0, "external_calls": 1 },
        "ttl": "PT10M",
        "irreversible": false
      },
      "options": ["allow_once", "allow_task", "deny"]
    }
  },
  "ts": "2026-11-10T10:14:45Z"
}
```

### 10.3 Grant and deny

- `consent.grant` MUST return `receipt_id`, `cap_id`, `expires_at`, and `constraints`.
- `consent.deny` MUST return a reason code and optional alternatives.
- Consent MUST bind: user, Agent, task, action, resource, `audience`, risk, and TTL.
- Batch/task-level consent MUST have an explicit scope; it MUST NOT be implicitly extended to other tasks.
- User revocation MUST take effect immediately and cascade to invalidate related capabilities.

**Issuance ordering.** A capability requires a `consent_receipt_id`, and the receipt requires a `cap_id`. To avoid circular dependency, the following order MUST be used:

1. the recipient (via the PCS) evaluates the action and determines that consent is required;
2. the CA **reserves** a `cap_id` (allocates the identifier; not signed, not usable);
3. the user/OS issues the receipt, referencing the reserved `cap_id` and the target `audience`;
4. after validating the receipt, the CA issues the capability, writes `consent_receipt_id`, and activates it;
5. if the receipt is denied, expires, or is revoked, the reserved `cap_id` MUST NOT enter a usable state.

An unactivated reserved `cap_id` MUST NOT pass any routing validation.

### 10.4 Consent receipt

```json
{
  "osap_receipt": "0.1",
  "receipt_id": "consent_01J...",
  "user": "user://local/example-user",
  "agent": "agent://com.example.orchestrator/main#1a2b",
  "task_id": "task_01J...",
  "cap_id": "cap_01J...",
  "audience": "agent://com.example.messaging/agent#4d",
  "actions": ["messaging.send"],
  "resources": ["contact://directory/example-contact"],
  "risk": "L3",
  "decision": "grant",
  "constraints": {
    "max_uses": 1,
    "expires_at": "2026-11-10T10:24:45Z"
  },
  "policy_hash": "sha256:...",
  "issued_at": "2026-11-10T10:14:46Z",
  "proof": {
    "alg": "EdDSA",
    "kid": "os-consent-key-1",
    "sig": "base64url..."
  }
}
```

Receipts MUST be signed by the user/OS; an Agent cannot issue them itself. Receipts MUST be verifiable offline by auditors.

### 10.5 Audit events

Every audit event contains at least:

```json
{
  "audit_id": "audit_01J...",
  "trace_id": "trace_01J...",
  "task_id": "task_01J...",
  "session_id": "session_01J...",
  "actor": "agent://com.example.orchestrator/main#1a2b",
  "action": "effect.executed",
  "phase": "outcome",
  "target": "calendar:primary",
  "decision": "allow",
  "policy": "calendar_first_use",
  "consent_receipt_id": "consent_01J...",
  "context_refs": ["obj://sha256:..."],
  "ts": "2026-11-10T10:14:45Z",
  "prev_hash": "sha256:...",
  "hash": "sha256:..."
}
```

Event types that MUST be recorded:

`agent.registered`, `agent.registration_denied`, `capability.issued`, `capability.attenuated`, `capability.attenuation_denied`, `capability.exercised`, `capability.revoked`, `discovery.query`, `discovery.result`, `message.sent`, `message.delivered`, `task.created`, `task.delegated`, `task.handoff`, `task.cancelled`, `task.completed`, `task.failed`, `context.resolve`, `context.denied`, `consent.requested`, `consent.granted`, `consent.denied`, `effect.intent`, `effect.executed`, `effect.reconciled`, `egress.blocked`, `error`.

`phase` is used only for `effect.*` events: `effect.intent` MUST carry `phase=intent`, and `effect.executed` MUST carry `phase=outcome`; other events MUST NOT carry `phase`.

L3/L4 side effects MUST use two-phase audit:

1. before execution, write `effect.intent` (`phase=intent`), containing the target, parameter summary, consent receipt, and idempotency key;
2. after execution, write `effect.executed` (`phase=outcome`), referencing `intent_ref`.

When there is only an intent and no outcome, recovery MUST mark it `unknown` and require reconciliation (see §8.11).

### 10.6 Trace

- A single user intent MUST have one `trace_id`.
- Every Agent hop MUST record a `causation_id`.
- Users MUST be able to view the cross-App collaboration chain by `trace_id`.
- Audit export MUST preserve `hash`/`prev_hash` and chain integrity; sensitive fields MAY be replaced with commitments using a salt unique to each export.
- A redacted export can only prove "the chain is untampered + field commitments are consistent" and cannot recover plaintext; verifiers MUST be aware of this limitation.
- Replay MUST be constrained by permissions and MUST NOT re-execute side effects.

### 10.7 Revocation

- User revokes a consent receipt → the associated capability becomes invalid → the task receives `CAPABILITY_REVOKED`.
- Revocation MUST cascade to child capabilities, subtasks, and sessions.
- Revocation events MUST be written to the audit, and all affected Agents MUST be notified.
- Irreversible side effects that have already occurred cannot be "revoked", but MUST be marked in the audit.

### 10.8 User visibility

Users MUST be able to view:

- which Agents are running;
- which capabilities each Agent holds;
- who is listening to which events;
- cross-App calls and data resolutions over the past 24 hours/7 days;
- how to revoke a given capability/receipt/session.

---

## 11. Security Considerations

### 11.1 Threat model

| Threat | Scenario | Countermeasure |
|---|---|---|
| Identity spoofing | A malicious App claims to be the system Agent | Peer credentials + code signature + reserved namespaces |
| Confused deputy | A low-privilege Agent gets a high-privilege Agent to act on its behalf | audience + task binding; forwarding prohibited |
| Prompt injection | Instructions hidden in message content | origin/trust labels; separation of instructions and data; action gate |
| Data exfiltration | A child Agent sends data outside | Handle labels + egress policy + user permission |
| Replay | Replaying a legitimate message | nonce + exp + max_uses + task binding |
| DoS | A flood of requests overwhelms the Bus/target App | Quotas, rates, backpressure, budgets |
| Supply chain | Malicious App/dependency | Signatures, manifest review, capability allowlists |
| Audit tampering | Deleting unfavorable records | Append-only + hash chain + external anchors |
| Compromised Bus | The Bus is compromised or malicious | 0.1 explicitly trusts P0; OS integrity, minimal TCB, payload not persisted; P1 see §3.6 |
| Clock manipulation | The wall clock is adjusted or the system suspends/resumes | Monotonic clock, skew checks, short TTLs |
| State rollback | Crashes/rollbacks cause duplication or loss | Persistence + anchoring + idempotency + reconciliation |
| Privilege escalation | A child Agent widens its capability | Monotonic attenuation + CA validation + depth limits |
| Cross-user leakage | Multiple users share a device | Per-user Bus; cross-user prohibited by default |

### 11.2 Identity spoofing

- The Bus MUST verify the peer process identity at connection time and bind it to `app://`.
- Agent IDs MUST be assigned/confirmed by the Bus at registration and cannot be self-asserted via `hello` alone.
- `agent://` is a local naming scheme, not a self-authenticating identifier; the Bus MUST maintain the binding from name to `(app, public_key, session)`.
- `hello.public_key` MUST be bound to the App manifest or OS key store; the Bus MUST verify proof of private key possession.
- `agent://system/...` and `cap://os/...` are reserved; third-party registration MUST fail.
- A change in code signature/package identity MUST trigger re-registration and capability re-validation.

### 11.3 Confused deputy

- Capabilities MUST bind both `audience` and `task_id`.
- Agents MUST NOT forward a received token as-is; they may only issue a new token after attenuation.
- The Bus MUST validate `subject == from` and `audience` before routing and refuse token borrowing; revocation and `max_uses` counting MUST be re-checked by the recipient.
- High-risk actions MUST be re-evaluated in the PCS and MUST NOT be released on the basis of the token alone.

### 11.4 Prompt injection

OSAP does not attempt to detect all malicious text; it does three things:

1. **Source labeling**: every message/handle carries `origin.kind`, `trust`, and `derived_from`;
2. **Instruction/data separation**: `body.data` is always data and cannot change the Agent's system policy; Agents SHOULD treat external content as untrusted input;
3. **Action gate**: L2+ actions MUST pass through the PCS; L3/L4 MUST have a human consent receipt.

Additional requirements:

- External content MUST be marked `origin.kind=external`.
- Content from email/web pages/documents MUST NOT be used directly as system instructions.
- The `intent_preview` of a high-risk action MUST show the data source and target.
- Even after injection, an Agent must not be able to silently produce external side effects; this is the protocol layer's minimum guarantee.

### 11.5 Data exfiltration

- Pass references by default; raw data does not enter the message body.
- Handle resolution is constrained by capability, labels, and audience.
- Egress of `sensitive`/`secret` requires user permission.
- Bridges to external protocols MUST preserve labels and enforce egress policy.
- The audit MUST record every resolution and egress.

### 11.6 Replay

- Capabilities MUST have `exp`; high-value actions SHOULD use `max_uses=1` or a nonce.
- The message `id` is used for idempotency; duplicate messages MUST NOT re-execute side effects.
- The Bus MUST reject requests with an expired `deadline`.
- Reusing a token across tasks MUST fail.

### 11.7 DoS

- The Bus MUST implement admission control, per-Agent quotas, in-flight request limits, and queue isolation.
- Requests MUST have a `deadline` and a budget.
- Large objects MUST go through references; control messages have a size limit.
- Backpressure MUST use explicit signals; streaming transports SHOULD use credit-based flow control.
- Under backpressure, the implementation MUST return `RATE_LIMIT` or make the sender wait; unbounded queuing is not permitted.
- `priority` MUST NOT cause starvation; implementations SHOULD use weighted fair scheduling.
- Task tree depth and the number of subtasks MUST be bounded.

### 11.8 Supply chain

- App manifests MUST be signed; the RFS MUST verify them.
- Bridge adapters MUST be provided by trustworthy sources and labeled with a version.
- Capability mapping from native registries MUST be auditable; permissions MUST NOT be silently widened.
- Dependency/plugin upgrades SHOULD trigger capability re-validation.

### 11.9 Audit integrity

- The audit log MUST be append-only and MUST have a single writer; multi-instance deployments MUST partition by user or use leader election.
- Every event MUST contain `prev_hash` and `hash`; `prev_hash` MUST come from the persisted chain head.
- After restart, the chain head and recent events MUST be verified; on verification failure, L3/L4 MUST fail closed and raise an alert.
- High-value scenarios SHOULD periodically anchor the chain head to OS integrity protection or an external transparency log.
- When the audit cannot be written, the **intent** audit for L3/L4 MUST fail closed; if the outcome audit for an already-executed side effect fails, it MUST be retried and alerted, and the external side effect that has already occurred MUST NOT be rolled back.
- User data deletion MUST record a deletion event; audit events themselves may be redacted but cannot be deleted.

### 11.10 Cross-user isolation

- By default, one Bus per user session; cross-user communication MUST be explicitly enabled and consented to by both parties.
- Agents on a shared device MUST be bound to the logged-in user.
- Multi-user sessions (family displays, collaboration spaces) belong to later versions; the current version MUST deny them by default.

### 11.11 Privacy

- Data minimization: request only the minimum scope needed to complete the task.
- Purpose binding: capabilities/receipts MUST record the purpose and MUST NOT be reused for other purposes.
- Retention: handles, objects, and audit expire per policy.
- User access: users MUST be able to view, export, revoke, and delete their own data.
- Redaction: audit export is redacted by default; raw data requires additional authorization.
- The Bus MUST NOT persist payloads by default; logs, error messages, and crash dumps MUST be redacted.

---

## 12. Conformance

### 12.1 Conformance levels

| Level | Name | Required implementation |
|---|---|---|
| C0 | Transport | Framing, connection, `hello`/`welcome`, errors, transport type declaration |
| C1 | Identity | Peer authentication, Agent registration, reserved namespaces, public key binding |
| C2 | Registry | Manifest, capability record, discovery, static `consent_hint` |
| C3 | Authorization | Capability token, attenuation, binding, revocation, consent receipt |
| C4 | Collaboration | Tasks, delegation, handoff, peer, budget, cancellation, results, recovery |
| C5 | Context | Handles, resolution, labels, blackboard, OS handle mapping (optional object store), memory authorization |
| C6 | Federation | App Intents/AppFunctions/App Actions/MCP/A2A/D-Bus adapters |
| C7 | Full | C0–C6 + audit/observability/multi-user extensions |

An implementation MAY declare support for a subset, but MUST explicitly declare its level and optional features:

- `bus_visibility`: only `payload` in 0.1;
- `transport_kind`: an array with values `stream` / `message`; implementations MUST declare the transport types they support;
- `state_recovery`: `durable` / `best_effort`; C4+ MUST be `durable`;
- `cf_mode`: `os_handles` / `managed_store`.

### 12.2 Required behaviors

- C0+ MUST select framing according to the transport type; message-oriented transports MUST NOT be forced to use a length prefix.
- C2+ MUST return a static `consent_hint` in discovery results and MUST NOT return a real-time `policy_verdict`.
- C3+ MUST reject tokens whose audience/task/subject do not match.
- C3+ MUST reject non-subset attenuation.
- C3+ MUST require a valid receipt for L3/L4 actions.
- C3+ MUST use a monotonic clock for `deadline` and re-check it after suspend/resume.
- C4+ MUST propagate cancellation and enforce budgets.
- C4+ MUST treat `handoff` as a one-shot ownership transfer: the recipient concludes with `result`/`error`, and on rejection or timeout the task remains with the original owner.
- C4+ MUST persist task state; after restart, incomplete tasks MUST transition to `failed` or be explicitly rescheduled.
- C5+ MUST record an audit for every handle resolution.
- C5+ MUST declare `cf_mode`; an independent object store MUST satisfy §9.10.
- C6+ MUST preserve `source` and `provenance`.

### 12.3 Test cases

The normative test set uses [`conformance.en.md`](conformance.en.md) as its sole source; identifiers are `C<level>-<nn>`. This section lists only representative checks for implementers to self-test quickly:

| Check | Corresponding test |
|---|---|
| Unregistered Agent connects | C1-01 |
| Token with a forged `audience` | C3-01 |
| Reusing a token across tasks | C3-02 |
| Child capability widens scope or extends the time limit | C3-04 / C3-06 |
| Using a child capability after the parent is revoked | C3-08 |
| L3 action without a receipt / expired receipt | C3-09 / C3-10 |
| Cancelling the parent task | C4-01 |
| Budget exhausted | C4-07 |
| Unauthorized handle resolution | C5-01 |
| `secret` object egress | C5-04 |
| Audit chain tampering | C7-02 |
| Idempotency index used as memory retrieval | C5-11 |

New tests MUST first enter `conformance.en.md`; this table does not maintain identifiers independently.

### 12.4 Interop

- Implementations SHOULD provide an `osap-conformance` test tool or report.
- Interoperability tests SHOULD cover at least two different Apps, one system Agent, and one Bridge.
- An implementation passing C7 MAY apply to be registered as a reference implementation (the registration process is defined separately).

---

## 13. Versioning and Extensibility

### 13.1 Version negotiation

- The envelope `osap` field uses `major.minor`.
- Major versions are incompatible; minor versions are backward compatible.
- `hello`/`welcome` MUST exchange supported versions and feature lists.
- If the two parties share no common major version, the connection MUST be rejected.
- Schema validation MUST enforce only the major version; minor versions MUST be accepted. Implementations MUST NOT reject a message because of a higher minor version number, unless a required feature is missing.

### 13.2 Schema identifiers

- Business schemas use `osap.<domain>.<type>/v<major>`.
- Minor version changes MUST remain backward compatible; breaking changes MUST bump the major.
- Schemas MUST be parseable and validatable; they SHOULD provide JSON Schema.

### 13.3 Extensions

- Extension fields MUST be placed in the top-level `extensions` object; `extensions` MUST participate in signature canonicalization.
- Unknown top-level fields MUST be rejected; `body.data` is an open object constrained by the business schema.
- Extensions MUST NOT change core authorization semantics.
- Extensions SHOULD have a namespace to avoid conflicts.
- Extensions that become standardized SHOULD enter a formal schema.

### 13.4 Deprecation

- Deprecated fields MUST be retained for at least one minor version cycle.
- Deprecation MUST be noted in the changelog and the schema.
- Removing a field in a breaking way MUST bump the major version.

### 13.5 Schema compatibility

- The version field of a schema MUST use a pattern match for the major version (e.g. `^0\.[0-9]+$`) and MUST NOT use an exact constant.
- Adding an optional field is minor; removing a field or changing semantics is major.
- Compatibility tests MUST cover "an old implementation receiving a new minor message".

---

## 14. Registration and Governance

### 14.1 Schema registry

- Core schemas are registered by the standard maintainers.
- Domain schemas are registered by the community/vendors and MUST provide maintainers, versions, and validation rules.
- Conflicting names MUST use a reverse-domain prefix.

### 14.2 Capability namespaces

- `cap://os/...` is reserved for core domains (calendar, contacts, files, messaging, notifications, etc.).
- `cap://<vendor-domain>/...` is used for vendor extensions.
- Registering a capability MUST provide: name, actions, resources, schema, risk, cost, and consent mode.

### 14.3 Event topics

- `event://os/...` is reserved for system events.
- `event://app.<app-id>/...` is used for App events.
- Subscriptions MUST declare filters and data scope.

### 14.4 Change process

Recommended open standards process:

1. proposal (issue / proposal);
2. reference implementation and interoperability report;
3. security and privacy review;
4. rough consensus;
5. release and changelog;
6. liaison with standards bodies such as IETF `agentproto`, OAuth WIMSE, and AAIF/LF.

See [`GOVERNANCE.en.md`](../GOVERNANCE.en.md) for governance details.

---

## 15. Open Issues

1. Ownership of the Bus: the OS vendor, the desktop environment, a runtime, or an independent daemon?
2. Legacy applications without Agents: UI automation bridging, or requiring a lightweight adapter?
3. Cross-device/cross-organization: how to align trust roots with A2A, WIMSE, and SPIFFE?
4. Multi-user shared sessions: principal switching and data boundaries.
5. Consent fatigue: the balance between task-level authorization and fine-grained revocation.
6. Semantic discovery: how to introduce embeddings beyond structured capability matching while avoiding privacy leakage.
7. Prompt injection responsibility: the division of responsibility among protocol gates, App content protection, and model-layer protection.
8. Performance: the overhead of going through policy on every resolution; local policy caching and short-term leases.
9. Vendor adoption: how to get adapters for App Intents/AppFunctions/App Actions into official SDKs.
10. Standards ownership: an independent foundation, LF/AAIF, IETF, or a vendor alliance?
11. The P1 profile for payloads invisible to the Bus: HPKE wire format, key discovery, and forward secrecy.
12. A formal model for crash recovery and side-effect reconciliation (intent/outcome, unknown state).
13. Standardized mapping between Context Fabric and OS handles/portals.
14. Leader election and audit chain partitioning for multi-instance Buses.

---

## Appendix A: Examples

Complete examples are in [`examples/`](../examples/):

- `manifest.json` — App manifest
- `capability.json` — capability token
- `capability-record.json` — federated capability record
- `task.json` — task object
- `discovery-request.json` / `discovery-result.json` — discovery
- `request.json` / `result.json` — request/result
- `delegate.json` — delegation
- `consent-receipt.json` — consent receipt
- `audit-event.json` — audit event

## Appendix B: State Machines

### B.1 Capability lifecycle

```
issued ──attenuate──> attenuated ──use──> exercised
   │                       │
   ├──revoke───────────────┴──> revoked
   └──expire──────────────────> expired
```

### B.2 Consent lifecycle

```
requested ──grant──> granted ──use──> consumed
     │                  │
     └──deny──> denied  └──revoke──> revoked
```

## Appendix C: Normative References

- RFC 2119 — Key words for use in RFCs
- RFC 8174 — Ambiguity of Uppercase vs Lowercase in RFC 2119
- RFC 3339 — Date and Time on the Internet
- RFC 3986 — Uniform Resource Identifier
- RFC 7515 — JSON Web Signature
- RFC 8032 — EdDSA
- RFC 8259 — JSON
- RFC 8785 — JSON Canonicalization Scheme
- RFC 8949 — CBOR
- RFC 8693 — OAuth 2.0 Token Exchange
- RFC 9396 — OAuth 2.0 Rich Authorization Requests

## Appendix D: Informative References

See [`prior-art.en.md`](prior-art.en.md), including MCP, A2A, ACP, AGNTCY, App Intents, AppFunctions, App Actions, AgenticOS, AgentKernel, Agent libOS, AOS, AgentCap, CAPMAS, tenuo, AAP, DAAP, DRP, APS, WIMSE, D-Bus, XPC, and Binder.

## Appendix E: JSON Schema Index

| Schema | File |
|---|---|
| Envelope | [`../schemas/envelope.schema.json`](../schemas/envelope.schema.json) |
| Capability | [`../schemas/capability.schema.json`](../schemas/capability.schema.json) |
| Task | [`../schemas/task.schema.json`](../schemas/task.schema.json) |
| Manifest | [`../schemas/manifest.schema.json`](../schemas/manifest.schema.json) |
| Capability Record | [`../schemas/capability-record.schema.json`](../schemas/capability-record.schema.json) |
| Consent Receipt | [`../schemas/consent-receipt.schema.json`](../schemas/consent-receipt.schema.json) |
| Audit Event | [`../schemas/audit-event.schema.json`](../schemas/audit-event.schema.json) |

The version field of all schemas uses major-version pattern matching (e.g. `^0\.[0-9]+$`) and MUST NOT use an exact constant; extension fields are uniformly placed in the top-level `extensions` and participate in signature canonicalization.

---

*This draft aims to be "implementable, testable, and federatable". Proposals and reference implementations addressing the open issues in Section 15 are welcome.*
