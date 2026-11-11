# OSAP: Open System Agent Protocol (Overall Design Draft)

> English translation of [design-draft.md](design-draft.md). The Chinese original prevails in case of conflict.

> Working name: **OSAP** (Open System Agent Protocol)
> Runtime component: **Agent Bus**
> Document status: Non-normative design description · 2026-11-10
> Positioning: cross-platform concept first, not bound to any specific OS primitive; when implemented, it can be mapped to D-Bus / XPC / Binder / named pipe.
>
> The normative text is in [`standard.md`](standard.en.md). This document is retained as background material on design motivation and architectural trade-offs.
> Note: the Bus/service split, trust profiles, state recovery, and transport semantics are governed by `standard.md` §3.6–§3.7, §7, §9.

---

## 1. Background: Apps Are Islands, Agents Are the New Connectivity Layer

Today's applications are isolated from one another: each App has its own data, accounts, UI, and permission model. When a user wants to accomplish something across apps ("summarize the meeting notes and send them to the example contact, and book a meeting for next Wednesday morning"), they can only copy and paste among multiple apps and switch context themselves.

Large-model Agents make "cross-app orchestration" feasible for the first time, but the current ecosystem has three structural gaps:

1. **There is no local common channel between Agents.** MCP solves Agent→tool, A2A solves remote Agent↔Agent, but there is no operating-system-level answer for how the Agents of two Apps on the same machine discover each other and exchange data securely.
2. **The permission model is still App-centric.** What the user authorizes is "some App can access contacts", not "in this task, this Agent can read this one record of the example contact, for the purpose of sending a message".
3. **Context cannot flow.** Every Agent repeatedly collects who the user is, what they are doing, and where the data is—which is inefficient and amplifies privacy risk.

**OSAP's core proposition**: the operating system provides a neutral **Agent Bus** so that Agents inside Apps discover and call each other by "capability" rather than "interface"; all cross-app behavior passes through identity authentication, capability authorization, user consent, and auditing; data flows by reference by default rather than being copied.

---

## 2. Design Goals and Non-Goals

### 2.1 Goals

| No. | Goal | Description |
|---|---|---|
| G1 | Cross-app discovery | Agents can declare and discover each other's capabilities, events, and data scopes |
| G2 | Structured communication | Unified message envelope, task semantics, streaming and event models |
| G3 | Least privilege | No ambient authority; permissions can only narrow along the delegation chain |
| G4 | Human-controllable | Tiered consent, intent preview, revocation at any time, full-chain auditing |
| G5 | Data does not leave its domain | References/handles are passed by default; data is resolved by the holder according to policy |
| G6 | Native supervisor/sub-agent support | Task tree, budget, cancellation propagation, result aggregation |
| G7 | Ecosystem interoperability | Can bridge MCP / A2A / OpenAPI / legacy IPC |
| G8 | Evolvable | Small protocol core; semantics extended through namespaces and schemas |

### 2.2 Non-Goals

- Does not specify an Agent's internal reasoning, model choice, or prompt format.
- Does not replace MCP (tool invocation) or A2A (cross-network Agent collaboration), but serves as the **local foundation** and interoperates with them.
- Does not require all Apps to be rewritten; provides SDKs, bridges, and an automation adaptation layer for "apps without Agents".
- Does not define a concrete UI; the consent interface is implemented by the OS/desktop environment, and the protocol only defines interaction primitives.

---

## 3. Design Principles

1. **Capability, not endpoint**
   A caller does not directly address the internal API of some App; instead it holds a verifiable capability token that declares "what I can do to which class of resources".

2. **Reference, not payload**
   Messages carry `obj://` and `ctx://` handles; the receiver resolves them according to policy only when it actually uses them, reducing the surface of data diffusion.

3. **Attenuation only**
   When a parent Agent delegates a task to a child Agent, it MUST issue a **subset capability**; a child Agent can never obtain more permission than its parent.

4. **Intent preview**
   Any action with external side effects or involving sensitive data must be able to generate a human-readable preview of "who, wants to do what, using which data, at what cost".

5. **Auditable by default**
   Every discovery, invocation, authorization, and data resolution across Agents produces a tamper-evident event record.

6. **Small core**
   Only the envelope, identity, capability, task, error, and transport bindings are standardized; business semantics live in namespace schemas.

7. **Fail closed**
   When policy cannot be decided, a credential has expired, or audit cannot be written, deny by default rather than allow.

---

## 4. Overall Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                 User / Desktop Shell / System Agent                  │
│       (intent input, consent UI, activity center, audit view)        │
└───────▲─────────────────────────────────────────────▲────────────────┘
        │ intent / consent decision                   │ status / notifications
┌───────┴─────────────────────────────────────────────┴────────────────┐
│                     Agent Bus (per user session)                     │
│                                                                      │
│ ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│ │ Registry │  │ Policy & │  │ Router   │  │ Context  │  │ Audit    │ │
│ │ discover │  │ Consent  │  │ msg/task │  │ Fabric   │  │ log      │ │
│ └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │
│                                                                      │
│  ┌───────────────────────── Bridge layer ─────────────────────────┐  │
│  │  MCP Bridge │ A2A Bridge │ OpenAPI/HTTP │ D-Bus/XPC/Binder     │  │
│  └────────────────────────────────────────────────────────────────┘  │
└───────▲─────────────────────▲───────────────────────▲────────────────┘
        │ local IPC (UDS / named pipe / Binder / XPC) │
┌───────┴────────┐    ┌───────┴────────┐    ┌─────────┴──────┐
│ Notes.app      │    │ Calendar.app   │    │ Messaging.app  │
│ └ Agent(notes) │    │ └ Agent(cal)   │    │ └ Agent(msg)   │
│   └ SDK        │    │   └ SDK        │    │   └ SDK        │
└────────────────┘    └────────────────┘    └────────────────┘
```

> Figure note: In the specification, Registry, Policy & Consent, Context Fabric, and Audit MUST run as separate processes or sandboxes and MUST NOT share an address space with the routing core. **Agent Bus** refers only to the **Bus Core** (peer authentication, envelope validation, routing, connection/session, backpressure); it does not enforce policy, does not issue capabilities, does not store objects, and does not persist audit records.

### 4.1 Component Responsibilities

| Component | Responsibility | Key constraint |
|---|---|---|
| **Agent Bus (Bus Core)** | Authenticate connections, route messages, manage the task lifecycle, enforce backpressure | Does not parse business payload; performs only envelope-level validation; does not enforce policy or issue capabilities |
| **Registry** | Index App manifests, Agents, capabilities, event topics, data schemas | Separate service; manifests require OS-verified signatures; a capability declaration is not authorization |
| **Policy & Consent** | Policy evaluation (user preferences, enterprise policy, risk tier), consent flow, credential issuance | Separate service; deny by default; decisions explainable and auditable |
| **Router** | Request/response, events, streams, cancellation, task tree | Part of the Bus Core; idempotency, timeout, quota |
| **Context Fabric** | Resolve `ctx://` handles, task-level shared state, object references | Separate service; holds no long-term memory; every resolution passes through policy; read operations leave a trace |
| **Audit** | Record cross-Agent events, consent receipts, data access | Separate service; append-only, tamper-evident, exportable |
| **Bridge** | Map external protocols into OSAP messages | Sandboxed; external content MUST be tagged with origin and trust label |

### 4.2 The Three Planes

- **Control plane**: registration, discovery, identity, capability, policy, consent, audit.
- **Data plane**: request/response, streams, events, cancellation, errors.
- **Context plane**: handle resolution, task blackboard, object references. Long-term memory is held by an Agent or a separate memory service, requires separate authorization, and is not part of the Bus.

---

## 5. Protocol Layering

| Layer | Name | Content | Required |
|---|---|---|---|
| L0 | Transport binding | UDS / named pipe / Binder / XPC / localhost TLS | Required |
| L1 | Identity and trust | App identity, Agent instance, user principal, device, signature | Required |
| L2 | Message envelope | Version, ID, type, routing, time, tracing, errors | Required |
| L3 | Task and context | Task tree, budget, cancellation, references, streams | Required (minimal set) |
| L4 | Semantics and policy | Capability, schema, event topic, risk tier, consent | Required |
| L5 | Domain extensions | Standard schemas for calendar, contacts, files, email, etc. | Optional |

**Transport-agnostic**: L1 and above use a unified JSON/CBOR envelope; L0 can be any IPC that provides "local, authenticatable peers". Recommended first reference bindings:
- Linux: Unix domain socket + `SO_PEERCRED`;
- macOS: XPC / Mach service + audit token;
- Windows: named pipe + client SID;
- Containers/cross-process sandboxes: localhost mTLS as a fallback.

---

## 6. Core Objects and Identity

### 6.1 Identity Quad

```
Principal = (User, App, AgentInstance, Device)
```

| Object | Example | Issuer |
|---|---|---|
| User | `user://local/example-user` | OS account |
| App | `app://com.example.notes` + code signature | OS installer/app store |
| Agent | `agent://com.example.notes/assistant#7f3a` | Registered with the Bus when the App starts |
| Device | `device://example-device/...` | OS |

> Key point: **An Agent identity is bound to the App identity and process credentials.** The Bus verifies the peer process (peer credential) when a connection is established; an App cannot claim to be someone else merely by a string. Sensitive namespaces such as system Agents and system settings are reserved and cannot be registered by third parties.

### 6.2 Capability

```json
{
  "cap": "cap://os/calendar/events",
  "actions": ["read", "propose"],
  "constraints": {
    "audience": "agent://com.example.notes/assistant#7f3a",
    "task": "task_01J...",
    "time_window": ["2026-11-10T00:00:00Z", "2026-11-17T00:00:00Z"],
    "data_scope": "calendar:primary",
    "max_uses": 20,
    "rate": "5/min"
  },
  "issuer": "user://local/example-user",
  "signature": "…"
}
```

Design points:
- Uses **macaroon-style** chained signatures, supporting offline attenuation;
- Every capability is bound to **audience + task** to prevent replay by other Agents;
- Capabilities can be revoked (short TTL + revocation list);
- A capability is not policy: even when holding a capability, Policy can still deny based on context.

### 6.3 Task

```
task_id, parent_task_id, root_task_id
owner_agent, assignee_agent
goal, input_refs, output_refs
budget {wall_ms, tokens, tool_calls, money, depth}
deadline, priority
status: pending | running | waiting_consent | done | failed | cancelled
```

The task tree naturally expresses "supervisor Agent decomposes → sub-agent executes". `root_task_id` lets auditing string together a single user intent.

---

## 7. Message Model

### 7.1 Unified Envelope

```json
{
  "osap": "0.1",
  "id": "msg_01JABCDEF...",
  "trace_id": "trace_01J...",
  "causation_id": "msg_parent...",
  "type": "request",
  "from": "agent://com.example.orchestrator/main#1a2b",
  "to": { "capability": "cap://os/messaging/send" },
  "task": {
    "id": "task_01J...",
    "parent": "task_01H...",
    "budget": { "wall_ms": 15000, "tool_calls": 3 }
  },
  "auth": { "token": "cap_…", "audience": "agent://com.example.messaging/agent#9c" },
  "body": {
    "schema": "osap.messaging.send/v1",
    "data": { "to": "contact://local/example-contact", "text_ref": "obj://sha256:..." }
  },
  "refs": ["obj://sha256:...", "ctx://user/profile#display_name"],
  "reply_to": "msg_01J...",
  "deadline": "2026-11-10T10:15:00Z",
  "priority": "normal",
  "consent": { "receipt": "consent_01J..." },
  "ts": "2026-11-10T10:14:45Z"
}
```

Field principles:
- `to` can be a **specific Agent** or a **capability**. The latter is resolved by the Router, combining Registry + Policy, to a unique holder; when there are multiple candidates, selection or consent is triggered.
- `body` MUST carry `schema`; the Bus does not parse `data`, but can perform size/type/sensitive-field checks.
- All binary/large objects go through `refs` and are not inlined.
- `consent.receipt` points to the user consent record, facilitating accountability afterwards.

### 7.2 Message Types (Verbs)

| Type | Direction | Semantics | Idempotent |
|---|---|---|---|
| `discover` / `describe` | Request | Query capabilities, schema, risk, cost | Yes |
| `request` | Request | Invoke a capability / execute a task | Yes (`id` deduplication) |
| `result` | Response | Successful result + references | — |
| `error` | Response | Structured error (retryable/non-retryable) | — |
| `event` | One-way | Topic event, at-most-once delivery | No |
| `stream.open/chunk/close` | Bidirectional | Streaming output, progress, incremental results | Chunk sequence number |
| `cancel` | One-way | Cancel a task, propagating downward along the task tree | Yes |
| `delegate` | One-way | Hand a subtask to another Agent | Yes |
| `status` | One-way | Heartbeat, progress, budget consumption | No |
| `consent.request/grant/deny` | Bidirectional | Consent flow | Yes |

### 7.3 Error Model

```json
{
  "type": "error",
  "body": {
    "schema": "osap.error/v1",
    "code": "POLICY_DENIED",
    "message": "User confirmation is required to send an external message",
    "retryable": false,
    "details": { "policy": "external_side_effect", "consent_url": "osap://consent/01J..." }
  }
}
```

Standard error code segments: `AUTH_*`, `POLICY_*`, `CAPABILITY_*`, `TASK_*`, `SCHEMA_*`, `TRANSPORT_*`, `RATE_LIMIT`, `TIMEOUT`, `CANCELLED`.

---

## 8. Task and Supervisor/Sub-Agent Model

### 8.1 Three Relationships

| Relationship | Meaning | Permission |
|---|---|---|
| **Supervisor → Worker** | The supervisor Agent decomposes the task and delegates subtasks | Child capability ⊆ parent capability, budget decreasing |
| **Peer ↔ Peer** | Two App Agents collaborate as equals | Each holds independent capabilities; neither can escalate the other's privileges |
| **System Agent → App Agent** | The OS scheduler initiates system-level tasks (e.g., "organize today's to-dos") | Constrained by system policy, still requires user consent |

### 8.2 Delegation Semantics

When a supervisor Agent initiates `delegate`, it MUST include:

1. **Task goal** and input references (not the full data);
2. **Narrowed capability token**;
3. **Budget** (time, call count, money, depth);
4. **Deadline** and priority;
5. **Result contract** (expected schema, quality threshold).

```json
{
  "type": "delegate",
  "from": "agent://com.example.orchestrator/main#1a2b",
  "to": "agent://com.example.calendar/agent#9c",
  "task": {
    "id": "task_cal_01",
    "parent": "task_root_01",
    "goal": "Find a 60-minute slot next Wednesday between 9:00 and 12:00 and create a tentative event",
    "budget": { "wall_ms": 8000, "tool_calls": 2, "depth": 1 },
    "result_schema": "osap.calendar.proposal/v1"
  },
  "auth": { "token": "cap_...(propose only on calendar:primary, audience=calendar agent)" }
}
```

### 8.3 Rules

- **Depth limit**: default maximum delegation depth 2–3, to prevent unbounded recursion and diffusion of responsibility.
- **Monotonically decreasing budget**: a subtask budget cannot exceed the parent task's remaining budget.
- **Cascading cancellation**: parent task cancelled → all subtasks receive `cancel`; a failed subtask may choose to report upward or degrade.
- **Result aggregation**: the parent Agent receives only `result` and references and does not automatically gain the sub-agent's intermediate context.
- **Traceable responsibility**: each task records `owner_agent` and the user intent `root_task_id` that initiated it.

---

## 9. Capability, Consent, and Security

### 9.1 Risk Tiers and Consent Policy

| Tier | Example | Default policy |
|---|---|---|
| L0 Public read | Read public weather | Allow automatically |
| L1 Personal read | Read calendar, contacts, notes | Consent on first use; scope/duration may be remembered |
| L2 Local write | Create a local draft, modify a to-do | Auto-allow for low risk + notify |
| L3 External side effect | Send a message, send email, submit a form | Confirm every time (batch authorization allowed) |
| L4 High impact / irreversible | Payment, deletion, external publishing | Strong confirmation + second-factor authentication |

A consent receipt contains: `who` (which Agent), `what` (capability and action), `data` (referenced data scope), `cost` (amount/quota), `ttl`, `receipt_id`.

### 9.2 Threat Model and Countermeasures

| Threat | Scenario | Countermeasure |
|---|---|---|
| Identity spoofing | A malicious App claims to be a system Agent | Process credential binding + reserved namespace + code signature |
| Confused deputy | A low-privilege Agent gets a high-privilege Agent to do things | Capability bound to audience + task; never forward raw credentials |
| Prompt injection | Message content hides "ignore previous instructions" | Content origin/trust label; separation of instructions and data; policy filtering; mandatory human confirmation for high-risk actions |
| Data leakage | A sub-agent sends contacts to an external party | Data handles resolved according to the recipient's policy; egress policy; reference instead of copy |
| Replay | Intercepted legitimate messages are re-sent | nonce + deadline + capability `max_uses` |
| DoS | A flood of requests overwhelms the Bus/target App | Quota, rate limiting, backpressure, task budget |
| Audit tampering | Deleting unfavorable records | Append-only log + hash chain / system integrity protection |

### 9.3 Protocol-Level Handling of Prompt Injection

OSAP does not attempt to "detect all malicious text"; instead it does three things:

1. **Origin tagging**: every message carries `origin` (App, Agent, user, external network) and a trust level;
2. **Instruction/data separation**: `body.data` is always data and cannot change the caller's system policy; an Agent SHOULD NOT execute message content as system instructions;
3. **Action gate**: any action at L2 or above MUST pass through Policy; L3/L4 MUST have human consent. Even if an Agent is injected, it cannot silently produce external side effects.

---

## 10. Discovery Mechanism

### 10.1 App Manifest

Registered at App installation/first run:

```json
{
  "app": "com.example.calendar",
  "version": "3.2.1",
  "signature": "…",
  "agents": [
    {
      "id": "agent://com.example.calendar/agent",
      "display_name": "Calendar Assistant",
      "capabilities": [
        {
          "cap": "cap://os/calendar/events",
          "actions": ["read", "propose", "create"],
          "schemas": ["osap.calendar.event/v1", "osap.calendar.proposal/v1"],
          "risk": "L2",
          "cost": { "latency_ms_p50": 300 }
        }
      ],
      "events": {
        "publishes": ["app.com.example.calendar.event_changed"],
        "subscribes": ["os.user.activity.location_changed"]
      },
      "data_scopes": ["calendar:primary"]
    }
  ]
}
```

### 10.2 Discovery Query

```json
{
  "type": "discover",
  "body": {
    "schema": "osap.discover/v1",
    "intent": "Find a free slot for a meeting",
    "requires": ["calendar.read"],
    "accepts_risk": "L1",
    "limit": 5
  }
}
```

What is returned is **candidates + policy verdicts**, not a bare list of interfaces:

```json
{
  "candidates": [
    {
      "agent": "agent://com.example.calendar/agent",
      "capability": "cap://os/calendar/events",
      "match": 0.94,
      "risk": "L1",
      "policy": "allow",
      "schema": "osap.calendar.proposal/v1"
    }
  ]
}
```

Principles:
- **A capability declaration ≠ authorization**; discovery results MUST include a `policy` verdict;
- Supports filtering by schema, action, risk, and cost; semantic matching is only a ranking signal;
- The discovery interface MUST NOT be usable to enumerate user private data.

---

## 11. Event and Context Plane

### 11.1 Event Bus

- Topics use reverse-domain naming: `os.user.activity.*`, `os.calendar.*`, `app.<app-id>.*`.
- Subscription requires a capability (`cap://os/events/subscribe` + topic filter + data scope).
- Default delivery semantics: **events at most once**, task requests at least once (deduplicated by idempotency key).
- Events carry only a minimal payload + references; sensitive content is resolved on demand by the subscriber.
- Users can view "who is listening to what" and revoke with one click.

### 11.2 Context Fabric

| Handle | Meaning | Resolution policy |
|---|---|---|
| `ctx://user/profile#display_name` | User profile field | Field-level authorization |
| `ctx://session/current#activity` | Current foreground activity | Session-level, short TTL |
| `ctx://screen/current` | Current screen content | High risk, requires explicit consent |
| `obj://sha256:...` | Content-addressed object | Reading requires holding an object capability |
| `file://...` | User file | File picker / sandbox authorization |
| `task://<id>/blackboard` | Task-level shared state | Task participants only; not memory |

**Task blackboard**: Agents within the same task tree can read and write a controlled shared area to exchange intermediate results without having to stuff everything into messages. It is reclaimed when the task ends (or archived according to policy).

**Long-term memory**: authorized separately; writes must be visible to and deletable by the user; an App cannot silently write to global memory.

---

## 12. Interoperability with the Existing Ecosystem

| Existing protocol | Problem it solves | Relationship to OSAP |
|---|---|---|
| **MCP** | Agent → tools/resources | MCP Servers exposed by Apps are wrapped by the Bridge into OSAP capabilities |
| **A2A** | Remote Agent ↔ Agent | A local Agent can act as an A2A endpoint; cross-device messages are forwarded by the Bridge with origin labels preserved |
| **OpenAPI / HTTP** | Traditional service interfaces | The Bridge generates capability descriptions; policy and auditing are unified at the outer layer |
| **D-Bus / XPC / Binder** | System IPC | Used as L0 transport bindings; the transport layer is not reinvented |
| **OAuth / OIDC** | User authorization | Can serve as the upstream issuance mechanism for cross-device/cloud-side capability tokens |

Mapping principles:
1. Capabilities of external protocols are first "translated" into OSAP capability descriptions, then participate in discovery;
2. External content is always tagged `origin=external` and has the lowest trust level by default;
3. External side effects likewise go through L3/L4 consent;
4. Semantics already defined by MCP/A2A are not redefined within OSAP; only local policy and identity wrapping are added.

---

## 13. Reliability and Observability

### 13.1 Delivery Semantics

- `request`: at least once + idempotency key (`id`); the receiver needs to deduplicate.
- `result`: paired with the request; after a timeout, `TIMEOUT` is returned, and whether to retry is up to the caller.
- `event`: at most once; when reliable events are needed, use `request` + subscription acknowledgement.
- `stream`: chunks carry sequence numbers and `stream_id`, supporting resumable transfer/cancellation.
- Backpressure: the Bus exposes queue watermarks; over-limit returns `RATE_LIMIT` or makes the sender wait.

### 13.2 Tracing

- One user intent = one `trace_id`;
- Each Agent hop = one span (chained by `causation_id`);
- Audit events include: discovery, authorization, consent, invocation, data resolution, results, errors, cancellation;
- Supports replaying a cross-App collaboration by `trace_id` for debugging and accountability (sensitive fields redacted).

### 13.3 Observability Interfaces

- `osap.trace.get/v1`: retrieve a trace (subject to permission constraints);
- `osap.audit.query/v1`: the user views "who accessed my data in the past 24 hours";
- `osap.bus.stats/v1`: queue, latency, error rate (for system diagnostics).

---

## 14. Deployment Forms

| Form | Description | Applicability |
|---|---|---|
| **A. Per-user Bus daemon** | One Bus is started per login session; Apps connect via UDS/XPC | Desktop OS, recommended starting point |
| **B. System Bus + user Broker** | The system-level Bus manages identity/policy; the user-level Broker manages messages | Multi-user, enterprise management |
| **C. Library mode + OS mediation** | No central daemon; the OS provides an authenticated channel | Resource-constrained devices (mobile/embedded) |

The first reference implementation suggests A: single machine, single user, UDS; get discovery/request/consent/audit working first, then discuss multi-user and cross-device.

---

## 15. Typical Scenario Walkthrough

**The user says: "Summarize yesterday's meeting notes and send them to the example contact, and while you're at it, book a meeting for next Wednesday morning."**

1. **Intent entry**: the system Agent (or a supervisor Agent designated by the user) creates a `root_task`, and a `trace_id` is generated.
2. **Discovery**: the supervisor Agent queries `notes.read`, `contacts.resolve`, `messaging.send`, `calendar.propose`, and obtains candidates and policy verdicts.
3. **Consent**: Policy determines "read notes" as L1 and "send an external message" as L3. The OS displays an intent preview:
   - Read: Notes / yesterday's 14:00 meeting notes
   - Send: Messaging / Contact: example contact / 1 message
   - Create: Calendar / next Wednesday 9:00–12:00 / tentative
4. **Delegation**:
   - The Notes Agent uses the narrowed capability to read the notes → returns `obj://sha256:...`
   - The Contacts Agent resolves "example contact" → returns `contact://...`
   - The Calendar Agent checks availability → returns 2 candidate time slots
5. **Composition**: the supervisor Agent generates a message draft and a meeting proposal, referencing rather than copying the original notes.
6. **External side effects**: confirm again before sending (L3); Calendar creates a tentative event (L2, notification).
7. **Audit**: one trace strings together 4 Apps, 6 invocations, and 2 consents; the user can view and revoke subsequent authorizations in the activity center.

---

## 16. Evolution Roadmap

| Phase | Scope | Acceptance criteria |
|---|---|---|
| **P0 Skeleton** | Envelope, identity, registration/discovery, request/response, audit | Two example Apps can call each other securely |
| **P1 Controllable** | Capability tokens, policy, consent UI, error model | L1–L3 actions can be correctly intercepted and authorized |
| **P2 Collaboration** | Task tree, delegation, budget, cancellation, streaming | The supervisor Agent can decompose and aggregate 3 sub-agents |
| **P3 Context** | Event bus, Context Fabric, task blackboard | Cross-App event-driven collaboration, data does not leave its domain |
| **P4 Interop** | MCP/A2A Bridge, standard domain schemas | Existing MCP Servers can be integrated with zero modification |
| **P5 Scale** | Multi-user, cross-device, enterprise policy, performance | 100+ Agents, P95 local call < 20ms |

---

## 17. Open Questions

1. **Should the Bus have built-in orchestration?** The inclination is to do only transport and governance, leaving orchestration to the system Agent/App Agent, so as to avoid the Bus becoming a "super Agent".
2. **What about legacy apps without Agents?** Use UI automation/script bridging, or require Apps to provide a lightweight adapter?
3. **Who standardizes capability schemas?** OS vendors define the core domains (calendar/contacts/files/messaging), and the long tail is customized by the ecosystem.
4. **Consent fatigue**: how to strike a balance between security and smoothness? "Task-level one-time authorization + fine-grained revocation" could be considered.
5. **Cross-device federation**: how does the local Bus align identity and capabilities with cloud-side A2A? Should a device-to-device trust root be introduced?
6. **Multi-user shared sessions** (family displays, collaboration spaces): how do principals switch, and how are data boundaries divided?
7. **Attribution of prompt injection responsibility**: the protocol layer only provides the gate; the App/model layer still needs content protection, so how is responsibility divided?
8. **The trade-off between performance and privacy**: will passing through policy on every data resolution be too slow? Local policy caching and short-term handle leases are needed.
9. **Who implements the Bus**: OS vendors, desktop environments, runtimes (such as Electron/Flutter), or an independent daemon?
10. **Relationship with the clipboard/drag-and-drop/share panel**: is OSAP a supplement or a replacement? The inclination is complementarity, upgrading "share" to "reference passing with capabilities".

---

## Appendix A: Glossary

| Term | Meaning |
|---|---|
| Agent | An entity inside an App that performs tasks on behalf of the user, with an independent identity and capabilities |
| Agent Bus | The local messaging and governance bus provided by the OS |
| Capability | A verifiable, attenuable, revocable authorization credential |
| Task Tree | The hierarchical task structure derived from a single user intent |
| Context Fabric | The subsystem that provides user/session/object context by way of handles |
| Consent Receipt | A non-repudiable record of the user consenting to a particular action |
| Reference | A data handle such as `obj://` / `ctx://`, replacing inline data |
| Trust Label | An annotation of message origin and trust level, used for injection defense |

## Appendix B: Comparison with Related Systems

| Dimension | D-Bus / XPC | MCP | A2A | **OSAP** |
|---|---|---|---|---|
| Scope | Local IPC | Agent→tool | Remote Agent↔Agent | Local Agent↔Agent + governance |
| Identity | Process/service | Client configuration | Agent Card | App+Agent+user+device quad |
| Authorization | Coarse-grained | Configuration/environment | Endpoint-level | Capability token + policy + consent |
| Task semantics | None | None | Yes (Task) | Yes (task tree/budget/cancellation) |
| Data flow | Copy | Tool return | Message | Reference + handle resolution |
| Audit | Limited | None | Limited | Full chain by default |
| Positioning | Transport layer | Tool layer | Network layer | **Local collaboration foundation** |

## Appendix C: Minimal Message Samples

**Request**

```json
{
  "osap": "0.1",
  "id": "msg_01",
  "trace_id": "trace_01",
  "type": "request",
  "from": "agent://com.example.orchestrator/main#1a2b",
  "to": { "capability": "cap://os/calendar/events" },
  "task": { "id": "task_01", "parent": "task_root", "budget": { "wall_ms": 5000 } },
  "auth": { "token": "cap_abc", "audience": "agent://com.example.calendar/agent#9c" },
  "body": {
    "schema": "osap.calendar.propose/v1",
    "data": { "window": "2026-11-18T09:00:00+08:00/2026-11-18T12:00:00+08:00", "duration_min": 60 }
  },
  "deadline": "2026-11-10T10:15:00Z",
  "ts": "2026-11-10T10:14:45Z"
}
```

**Result**

```json
{
  "osap": "0.1",
  "id": "msg_02",
  "trace_id": "trace_01",
  "causation_id": "msg_01",
  "type": "result",
  "from": "agent://com.example.calendar/agent#9c",
  "to": "agent://com.example.orchestrator/main#1a2b",
  "task": { "id": "task_01", "status": "done" },
  "body": {
    "schema": "osap.calendar.proposal/v1",
    "data": {
      "slots": [
        { "start": "2026-11-18T10:00:00+08:00", "end": "2026-11-18T11:00:00+08:00" }
      ],
      "event_draft_ref": "obj://sha256:9f2c..."
    }
  },
  "ts": "2026-11-10T10:14:46Z"
}
```

---

*This document is an overall design draft whose purpose is to first align on the problem, the boundaries, and the key mechanisms; the next step can split it into a formal specification (envelope/capability/task/policy) and a runnable prototype.*
