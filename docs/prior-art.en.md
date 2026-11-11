# Prior Art and Positioning

> English translation of [prior-art.md](prior-art.md). The Chinese original prevails in case of conflict.

> Non-normative document · 2026-11-10
> Purpose: to explain where OSAP overlaps with existing work, what its boundaries are, and where its possible novel points lie. This document is a survey of public materials, not a patent search in the legal sense.

---

## 1. Why write this document

OSAP's three keywords—**cross-application point-to-point collaboration**, **vendor capability registry federation**, and **task-level authorization**—each already has substantial prior work. Without clear boundaries, OSAP can easily be understood as "renaming existing concepts."

The goals of this document are:

1. to honestly list the closest prior work;
2. to mark the intersection points that OSAP genuinely aims to fill;
3. to give falsifiable novelty claims;
4. to avoid unprovable wording such as "first" or "only" in the specification.

---

## 2. Landscape of related work

### 2.1 Vendor OS capability registries

| Work | Mechanism | Relationship to OSAP |
|---|---|---|
| **Apple App Intents / App Schemas** | Apps declare Intents/Entities, the system indexes them, and Siri/Shortcuts orchestrate them | Provides a star model of "App capability → system Agent"; Apple explicitly states that third-party Apps cannot directly invoke another App's Intents |
| **Android AppFunctions** | Apps declare functions, the Android OS builds a registry, and a system privileged Agent discovers/executes them; described as on-device MCP | Closest to an "OS-level capability registry"; callers are limited to the system Agent |
| **Windows App Actions / Agent Launchers** | JSON action definition, package identity, COM activation, system discovery; other Apps can compose and invoke actions | The closest thing on the local machine to an "App capability bus," but it is still action-level invocation, not an Agent session/task protocol |
| **XDG Desktop Portal** | Sandboxed applications request permissions such as files, screenshots, and notifications through the portal | A precedent for local permission brokering; not Agent-aware |

**Common characteristics**: the vendor controls the registry, the system Agent is the sole/primary orchestrator, and cross-vendor interoperability is out of scope.

### 2.2 Cross-platform Agent protocols

| Work | Layer | Relationship to OSAP |
|---|---|---|
| **MCP** | Agent ↔ tools/resources | OSAP projects MCP tools as capability records and can bridge invocations |
| **A2A** | Agent ↔ Agent (across the network) | OSAP reuses the Task/Artifact approach but adds local identity, capabilities, consent, and references |
| **ACP / IETF agentproto** | Agentic dialog management | Defines dialog IDs, lifecycle, context propagation, and delegated authorization; explicitly does not replace MCP/A2A, nor is it a transport layer |
| **AGNTCY (SLIM / Agent Directory / OASF)** | Transport, federated directory, capability schema | The network-layer "Internet of Agents"; OSAP is the local binding and governance layer |
| **ANP / NANDA and others** | Decentralized Agent networks | Different from OSAP's local cross-application scenario |

### 2.3 OS-level Agent runtime/security architectures

| Work | Core idea | Overlap with OSAP |
|---|---|---|
| **AgenticOS** (arXiv 2606.21129) | The OS shifts from "resource manager" to "intent filter"; Intent ABI, capability composition, mandatory audit | Intent-level authorization, capabilities, audit |
| **Agent libOS** (arXiv 2606.03895) | AgentProcess, Task Authority ceilings, typed Capabilities, budgets, information-flow labels, one-shot release for sensitive egress | Task-level capabilities, budgets, references, consent, audit |
| **AgentKernel** (arXiv 2609.29647) | Four pillars: identity, perception, cognition, execution; addresses delegation abuse, prompt injection, and memory poisoning | OS-level Agent security, prompt injection |
| **AOS** (arXiv 2606.01508) | Agentic control plane: scheduling, context/memory, capability registry, policy, audit | Component decomposition highly similar to OSAP |
| **Aegis OS** (arXiv 2611.08516) | Transactional multi-tenant Agent OS runtime; MCP/A2A; sandbox + CAS | Authorization boundaries, sandbox, reference storage |
| **AIOS** (arXiv 2504.14411) | LLM Agent OS; AIOS Server uses MCP+JSON-RPC for P2P | The "Agent OS" concept and P2P discovery |

**Key conclusion**: OS-level Agent security, task-level capabilities, audit, and sandboxing were already a dense research area in 2026. OSAP cannot treat these as novel points.

### 2.4 Task-level capabilities and delegated authorization

| Work | Mechanism | Overlap with OSAP |
|---|---|---|
| **AgentCap** (arXiv 2611.00729) | MCP wrapper; short-lived, budget-constrained capability tokens; parent-child session chains; permissions can only narrow | Task-level capabilities, budgets, attenuation, MCP boundary |
| **CAPMAS** (arXiv 2609.06500) | Macaroon + semantic scoping; multi-hop delegation; privilege-escalation prevention | Capability attenuation, multi-hop delegation |
| **tenuo** | Task-scoped warrants; A2A/MCP; signed evidence; attenuation | Task-level authorization, attenuation, A2A/MCP |
| **IETF AAP** | Agent Identity Token, Capability Grant Token, Delegation Assertion | Identity, capability grants, cross-Agent delegation |
| **IETF DAAP** | DID identity, OAuth-style consent, JWT grant, revocation, hash-chained audit | Consent, revocation, audit |
| **classical capability systems** | KeyKOS, EROS, Capsicum, seL4, object-capability | No ambient authority, unforgeable handles, least privilege |
| **Macaroons / UCAN / Biscuit** | Attenuable, offline-verifiable authorization tokens | The attenuation model for capability tokens |

### 2.5 Consent receipts and audit

| Work | Mechanism | Overlap with OSAP |
|---|---|---|
| **IETF DRP** | A user-signed Authorization Object, written to an append-only log before the action | Consent receipts, pre-action audit |
| **IETF APS** | Agent passport, delegation chains, signed action receipts | Identity, delegation, receipts |
| **IETF WIMSE credential delegation** | Short-lived attenuated credentials, consent records, cascading revocation, audit chains | Delegated authorization, revocation, audit |
| **Kantara / ISO/IEC 27560 consent receipt** | Standardized consent receipts | Receipt format and semantics |
| **OAuth RAR** | Rich authorization requests, fine-grained resources/actions | Task-level authorization requests |

### 2.6 Local IPC and context

| Work | Mechanism | Relationship to OSAP |
|---|---|---|
| **D-Bus** | Local message bus, service discovery, signals, policy | A precedent for transport and bus; no Agent semantics |
| **XPC / Binder** | OS-native IPC, peer authentication | Transport binding |
| **Blackboard / Tuple Spaces** | Shared workspace, publish/subscribe | A precedent for the task blackboard and Context Fabric |
| **Content-addressed storage** | `obj://`, CAS | Reference-based data flow |
| **MCP Resources / A2A Artifacts** | Resource/artifact references | A precedent for cross-Agent data exchange |

---

## 3. Comparison matrix

Legend: ✅ native support; ◐ partial/extensible; ❌ not supported; — not applicable. The OSAP row is a **design goal**, not an implemented state.

| Work | OS local | Point-to-point | Vendor registry federation | Task-level capabilities | Consent receipts | Cross-App context | Open standard |
|---|---|---|---|---|---|---|---|
| Apple App Intents | ✅ | ❌ | ❌ | ◐ | ◐ | ◐ | ❌ |
| Android AppFunctions | ✅ | ❌ | ❌ | ◐ | ◐ | ◐ | ❌ |
| Windows App Actions | ✅ | ◐ | ❌ | ◐ | ◐ | ◐ | ❌ |
| MCP | ◐ | ❌ | ❌ | ❌ | ❌ | ◐ | ✅ |
| A2A | ❌ | ✅ | ❌ | ◐ | ◐ | ◐ | ✅ |
| ACP / IETF agentproto | ❌ | ✅ | ❌ | ◐ | ◐ | ◐ | ✅ |
| AGNTCY | ❌ | ✅ | ◐ | ◐ | ◐ | ◐ | ✅ |
| AgenticOS | ✅ | ❌ | ❌ | ✅ | ◐ | ◐ | ❌ |
| Agent libOS | ✅ | ◐ | ❌ | ✅ | ✅ | ✅ | ❌ |
| AgentKernel | ✅ | ◐ | ❌ | ✅ | ◐ | ◐ | ❌ |
| AOS | ✅ | ◐ | ◐ | ✅ | ◐ | ✅ | ❌ |
| AgentCap | ◐ | ❌ | ❌ | ✅ | ◐ | ❌ | ◐ |
| CAPMAS | ◐ | ✅ | ❌ | ✅ | ❌ | ❌ | ◐ |
| tenuo | ◐ | ✅ | ❌ | ✅ | ◐ | ❌ | ◐ |
| AAP / DAAP / DRP / APS | ❌ | ✅ | ❌ | ✅ | ✅ | ❌ | ✅ |
| D-Bus / XDG Portal | ✅ | ✅ | ❌ | ❌ | ❌ | ◐ | ✅ |
| **OSAP (target)** | **✅** | **✅** | **✅** | **✅** | **✅** | **✅** | **✅** |

> This table compares the "design space", not a ranking of feature strength. Many works with ◐ cells go deeper than OSAP within their target scenarios.

---

## 4. What is explicitly not novel

The following already had ample prior work by 2026, and OSAP should not claim originality:

1. **"OS-level Agent security"**: covered by AgenticOS, AgentKernel, Agent libOS, and AOS.
2. **"Task-level capability tokens"**: covered by AgentCap, CAPMAS, tenuo, and AAP.
3. **"Capabilities can only narrow"**: covered by macaroons, UCAN, Biscuit, and CAPMAS.
4. **"Consent receipts + audit chains"**: covered by DRP, APS, DAAP, WIMSE, and Kantara.
5. **"App capability registries"**: covered by App Intents, AppFunctions, and App Actions.
6. **"Agent message buses"**: covered by D-Bus, A2A, AGNTCY, and BusMA.
7. **"Context references/blackboards"**: covered by MCP Resources, A2A Artifacts, blackboard/tuple spaces, and CAS.
8. **"Supervisor/Worker task trees"**: covered by multi-Agent orchestration frameworks and A2A Task.
9. **"Action gating for prompt injection"**: covered by AgentKernel, Agent libOS, AgentCap, and CaMeL.

---

## 5. Possible novel points

OSAP's novelty lies not in any single mechanism, but in the **intersection points**. The following claims need to be verified one by one and cannot simply be written as "first."

### 5.1 Cross-vendor local capability graph

> Without modifying the OS kernel, project the capabilities of Apple App Intents, Android AppFunctions, Windows App Actions, MCP, A2A, and D-Bus onto the same local capability graph, while preserving provenance, trust, and native authority.

- Existing work each builds one layer; there is no unified cross-vendor projection.
- Risk: vendors may extend their registries themselves; the semantic mapping performed by Bridge adapters may be incomplete.

### 5.2 A unified authorization model for point-to-point + supervisor/worker

> Support both peer sessions and hierarchical delegation in the same protocol, and constrain both with the same set of invariants: no ambient authority, monotonic attenuation, audience/task binding, revocation cascading, and monotonic budgets.

- A2A leans toward peer relationships while AgentCap leans toward parent-child; little work unifies the two under one set of authority invariants.
- Risk: insufficient formalization turns it into "a mishmash of two modes."

### 5.3 Cross-App Context Fabric

> Capability-addressed, reference-first context handles with information-flow labels and TTL flow across Apps; resolution is audit; sensitive egress requires one-shot release.

- Agent libOS has source references and one-shot release, but mainly within a single runtime; MCP Resources are server-scoped; there is no unified handle layer across Apps.
- Risk: the boundary with OS file pickers, portals, and content providers needs to be clearly stated.

### 5.4 Cross-App binding of consent receipts to task traces

> Make "what the user consented to, which Agent, which task, which data was used, and how to revoke" a cross-App verifiable object, and bind it to the task trace.

- DRP/APS do receipts, but do not combine them with local cross-App Agent task trees.
- Risk: compatibility with Kantara/ISO receipts and WIMSE delegation credentials.

### 5.5 Federated local bus

> A user-space overlay bus that does not require OS vendors to adopt it, yet can provide cross-App Agent collaboration and governance on existing platforms.

- Existing OS vendor solutions are closed star models; existing cross-platform protocols are network-layer; the overlay combination is a gap.
- Risk: without OS vendor support, peer authentication, sandbox traversal, and system Agent integration are all limited.

---

## 6. Falsifiable novelty claims

Suggested wording for papers/standards proposals (rather than "first"):

> OSAP defines a local binding: on top of existing OS sandboxes and IPC, it projects vendor capability registries, MCP/A2A capabilities, and Apps' native Agents into a unified capability graph, and uses task-level, attenuable, audience/task-bound capability tokens to support cross-application point-to-point and hierarchical collaboration, while binding consent receipts, context references, and audit to the same task trace.

To prove that this holds, one needs to:

1. compare item by item with at least 6 of the closest works (Section 3 of this document);
2. provide formal authority invariants, and prove that attenuation/revocation/cancellation satisfy monotonicity;
3. implement at least two Apps + one system Agent + one Bridge;
4. measure: P95 latency, permission bypass rate, prompt injection blocking rate, revocation propagation time, and audit integrity;
5. prove that existing work cannot be directly composed to obtain the same properties (for example: A2A + AgentCap still lacks OS peer identity and cross-App context handles).

---

## 7. Questions that could overturn novelty

Before further investment, one should first answer:

1. **Is the combination of A2A + AgentCap + D-Bus already sufficient?** If it is merely "stitching the three together," the novelty is weak.
2. **Does Agent libOS's source reference + one-shot release already cover Context Fabric?** An item-by-item comparison is needed.
3. **Will AppFunctions/App Actions open third-party Agent interoperation in 2027?** If so, OSAP's vendor federation value decreases.
4. **Will IETF agentproto define a local binding?** If so, OSAP should be a profile of it rather than a standalone protocol.
5. **Is there already a cross-App standard for consent receipts?** The coverage of Kantara/ISO/WIMSE needs verification.

---

## 8. Conclusion

- **Concept layer**: OSAP is not an entirely new concept; by 2026 there is already substantial overlapping work.
- **Intersection layer**: cross-vendor local capability graph + unified point-to-point/supervisor-worker authorization + cross-App context + receipt/trace binding still leaves room.
- **Evidence layer**: there is currently no implementation or evaluation, so it cannot yet be called a research contribution.
- **Strategy layer**: the safest path is to position itself as a **"local binding / profile"** aligned with MCP, A2A, IETF agentproto, and OAuth WIMSE, rather than starting yet another Agent protocol.

---

## 9. Reference links

### Vendor OS

- Apple App Intents: https://developer.apple.com/documentation/appintents
- Apple WWDC26 App Intents Group Lab: https://developer.apple.com/videos/play/wwdc2026/8011/
- Android AppFunctions: https://developer.android.com/ai/appfunctions
- Android Intelligence System: https://developer.android.com/ai/intelligence-system
- Windows App Actions: https://learn.microsoft.com/en-us/windows/ai/app-actions
- Windows agentic security: https://learn.microsoft.com/en-us/windows/security/book/operating-system-agentic-security

### Agent protocols and standards

- MCP: https://modelcontextprotocol.io
- A2A: https://a2a-protocol.org
- IETF agentproto: https://datatracker.ietf.org/wg/agentproto/about/
- IETF AAP: https://www.ietf.org/archive/id/draft-fane-opena2a-aap-01.html
- IETF DAAP: https://www.ietf.org/archive/id/draft-mishra-oauth-agent-grants-00.html
- IETF DRP: https://datatracker.ietf.org/doc/draft-nelson-agent-delegation-receipts/
- IETF APS: https://datatracker.ietf.org/doc/draft-pidlisnyi-aps/
- IETF WIMSE credential delegation: https://www.ietf.org/archive/id/draft-sweeney-wimse-credential-delegation-00.html
- AGNTCY: https://docs.agntcy.org/

### OS / systems research

- AgenticOS: https://arxiv.org/abs/2606.21129
- Agent libOS: https://arxiv.org/abs/2606.03895
- AgentKernel: https://arxiv.org/abs/2609.29647
- AOS: https://arxiv.org/abs/2606.01508
- AgentCap: https://arxiv.org/abs/2611.00729
- CAPMAS: https://arxiv.org/abs/2609.06500
- Aegis OS: https://arxiv.org/abs/2611.08516
- AIOS: https://arxiv.org/abs/2504.14411
- agent-os ("POSIX for AI agents"): https://github.com/isaacsight/agent-os
- BusMA: https://arxiv.org/html/2609.15054v1

### Local IPC and capability systems

- D-Bus specification: https://dbus.freedesktop.org/doc/dbus-specification.html
- XDG Desktop Portal: https://flatpak.github.io/xdg-desktop-portal/
- Macaroons: https://research.google/pubs/pub41892/
- UCAN: https://ucan.xyz/
- Biscuit: https://www.biscuitsec.org/
- Capsicum: https://www.cl.cam.ac.uk/research/security/capsicum/
- seL4: https://sel4.systems/
