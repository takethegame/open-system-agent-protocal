# Prior Art and Positioning

> 非规范性文档 · 2026-11-10
> 目的：说明 OSAP 与现有工作的重叠、边界与可能的新颖点。本文是公开资料调研，不是法律意义上的专利检索。

---

## 1. 为什么要写这份文档

OSAP 的三个关键词——**跨应用点对点协作**、**厂商能力注册表联邦**、**任务级授权**——每一个都已有大量先行工作。如果不明确边界，OSAP 很容易被理解为“把已有概念重新命名”。

本文的目标是：

1. 诚实列出最接近的先行工作；
2. 标出 OSAP 真正想填补的交叉点；
3. 给出可被证伪的新颖性主张；
4. 避免在规范中使用“首个”“唯一”等无法证明的措辞。

---

## 2. 相关工作全景

### 2.1 厂商 OS 能力注册表

| 工作 | 机制 | 与 OSAP 的关系 |
|---|---|---|
| **Apple App Intents / App Schemas** | App 声明 Intent/Entity，系统索引，Siri/Shortcuts 编排 | 提供“App 能力 → 系统 Agent”的星型模型；Apple 明确第三方 App 不能直接调用其他 App 的 Intent |
| **Android AppFunctions** | App 声明函数，Android OS 建注册表，系统特权 Agent 发现/执行；被称为 on-device MCP | 最接近“OS 级能力注册表”；调用方限定为系统 Agent |
| **Windows App Actions / Agent Launchers** | JSON action definition、包身份、COM 激活、系统发现；其他 App 可组合调用 action | 本机最接近“App 能力总线”，但仍是 action 级调用，不是 Agent 会话/任务协议 |
| **XDG Desktop Portal** | 沙箱应用通过 portal 请求文件、截图、通知等权限 | 本地权限代理的先例；不感知 Agent |

**共同点**：厂商控制注册表，系统 Agent 是唯一/主要编排者，跨厂商互操作不在范围内。

### 2.2 跨平台 Agent 协议

| 工作 | 层 | 与 OSAP 的关系 |
|---|---|---|
| **MCP** | Agent ↔ 工具/资源 | OSAP 将 MCP tool 投影为能力记录，并可桥接调用 |
| **A2A** | Agent ↔ Agent（跨网络） | OSAP 复用 Task/Artifact 思路，但补本地身份、能力、同意与引用 |
| **ACP / IETF agentproto** | Agentic dialog management | 定义对话 ID、生命周期、上下文传播、委托授权；明确不替代 MCP/A2A，也不是传输层 |
| **AGNTCY（SLIM / Agent Directory / OASF）** | 传输、联邦目录、能力 schema | 网络层的“Internet of Agents”；OSAP 是本地绑定与治理层 |
| **ANP / NANDA 等** | 去中心化 Agent 网络 | 与 OSAP 的本地跨应用场景不同 |

### 2.3 OS 级 Agent 运行时/安全架构

| 工作 | 核心思想 | 与 OSAP 的重叠 |
|---|---|---|
| **AgenticOS**（arXiv 2606.21129） | OS 从“资源管理器”变为“意图过滤器”；Intent ABI、能力合成、强制审计 | 意图级授权、能力、审计 |
| **Agent libOS**（arXiv 2606.03895） | AgentProcess、Task Authority ceilings、typed Capabilities、预算、信息流标签、敏感出口一次性放行 | 任务级能力、预算、引用、同意、审计 |
| **AgentKernel**（arXiv 2609.29647） | 身份、感知、认知、执行四支柱；处理委托滥用、提示注入、记忆投毒 | OS 级 Agent 安全、提示注入 |
| **AOS**（arXiv 2606.01508） | Agentic control plane：调度、上下文/记忆、能力注册表、策略、审计 | 组件分解与 OSAP 高度相似 |
| **Aegis OS**（arXiv 2611.08516） | 事务化多租户 Agent OS runtime；MCP/A2A；沙箱 + CAS | 授权边界、沙箱、引用存储 |
| **AIOS**（arXiv 2504.14411） | LLM Agent OS；AIOS Server 用 MCP+JSON-RPC 做 P2P | “Agent OS”概念与 P2P 发现 |

**关键结论**：OS 级 Agent 安全、任务级能力、审计、沙箱，在 2026 年已经是密集研究区。OSAP 不能把这些当作新颖点。

### 2.4 任务级能力与委托授权

| 工作 | 机制 | 与 OSAP 的重叠 |
|---|---|---|
| **AgentCap**（arXiv 2611.00729） | MCP wrapper；短时、预算受限能力 token；父子会话链；权限只能收窄 | 任务级能力、预算、衰减、MCP 边界 |
| **CAPMAS**（arXiv 2609.06500） | Macaroon + 语义 scoping；多跳委托；防提权 | 能力衰减、多跳委托 |
| **tenuo** | Task-scoped warrants；A2A/MCP；签名证据；衰减 | 任务级授权、衰减、A2A/MCP |
| **IETF AAP** | Agent Identity Token、Capability Grant Token、Delegation Assertion | 身份、能力授予、跨 Agent 委托 |
| **IETF DAAP** | DID 身份、OAuth 式同意、JWT grant、撤销、哈希链审计 | 同意、撤销、审计 |
| **classical capability systems** | KeyKOS、EROS、Capsicum、seL4、object-capability | 无环境权限、不可伪造句柄、最小权限 |
| **Macaroons / UCAN / Biscuit** | 可衰减、可离线验证的授权 token | 能力 token 的衰减模型 |

### 2.5 同意回执与审计

| 工作 | 机制 | 与 OSAP 的重叠 |
|---|---|---|
| **IETF DRP** | 用户签名的 Authorization Object，动作前写入 append-only log | 同意回执、动作前审计 |
| **IETF APS** | Agent passport、委托链、签名动作回执 | 身份、委托、回执 |
| **IETF WIMSE credential delegation** | 短期衰减凭证、同意记录、级联撤销、审计链 | 委托授权、撤销、审计 |
| **Kantara / ISO/IEC 27560 consent receipt** | 标准化同意回执 | 回执格式与语义 |
| **OAuth RAR** | 富授权请求，细粒度资源/动作 | 任务级授权请求 |

### 2.6 本地 IPC 与上下文

| 工作 | 机制 | 与 OSAP 的关系 |
|---|---|---|
| **D-Bus** | 本地消息总线、服务发现、信号、策略 | 传输与总线先例；无 Agent 语义 |
| **XPC / Binder** | OS 原生 IPC、对端认证 | 传输绑定 |
| **Blackboard / Tuple Spaces** | 共享工作区、发布/订阅 | 任务黑板、Context Fabric 的先例 |
| **Content-addressed storage** | `obj://`、CAS | 引用式数据流 |
| **MCP Resources / A2A Artifacts** | 资源/产物引用 | 跨 Agent 数据交换的先例 |

---

## 3. 对比矩阵

图例：✅ 原生支持；◐ 部分/可扩展；❌ 不支持；— 不适用。OSAP 列为**设计目标**，不是已实现状态。

| 工作 | OS 本地 | 点对点 | 厂商注册表联邦 | 任务级能力 | 同意回执 | 跨 App 上下文 | 开放标准 |
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
| **OSAP（目标）** | **✅** | **✅** | **✅** | **✅** | **✅** | **✅** | **✅** |

> 这张表是“设计空间”对比，不是功能强弱排名。很多单元格为 ◐ 的工作，在其目标场景内做得比 OSAP 更深。

---

## 4. 哪些部分明确不新颖

以下内容在 2026 年已有充分先行工作，OSAP 不应主张原创：

1. **“OS 级 Agent 安全”**：AgenticOS、AgentKernel、Agent libOS、AOS 已覆盖。
2. **“任务级能力凭证”**：AgentCap、CAPMAS、tenuo、AAP 已覆盖。
3. **“能力只能收窄”**：macaroons、UCAN、Biscuit、CAPMAS 已覆盖。
4. **“同意回执 + 审计链”**：DRP、APS、DAAP、WIMSE、Kantara 已覆盖。
5. **“App 能力注册表”**：App Intents、AppFunctions、App Actions 已覆盖。
6. **“Agent 消息总线”**：D-Bus、A2A、AGNTCY、BusMA 已覆盖。
7. **“上下文引用/黑板”**：MCP Resources、A2A Artifacts、blackboard/tuple spaces、CAS 已覆盖。
8. **“Supervisor/Worker 任务树”**：多 Agent 编排框架与 A2A Task 已覆盖。
9. **“提示注入的动作闸门”**：AgentKernel、Agent libOS、AgentCap、CaMeL 已覆盖。

---

## 5. 可能的新颖点

OSAP 的新颖性不在单个机制，而在**交叉点**。以下主张需要逐条验证，不能直接写“首个”。

### 5.1 跨厂商本地能力图

> 在不修改 OS 内核的前提下，把 Apple App Intents、Android AppFunctions、Windows App Actions、MCP、A2A、D-Bus 的能力投影到同一张本地能力图，并保留来源、信任与原生权威。

- 现有工作各自做一层，没有统一的跨厂商投影。
- 风险：厂商可能自己扩展注册表；Bridge 适配器的语义映射可能不完整。

### 5.2 点对点 + 主子的统一权限模型

> 在同一协议中同时支持平级会话与层级委派，并用同一组不变量约束两者：无环境权限、单调衰减、audience/task 绑定、撤销级联、预算单调。

- A2A 偏平级，AgentCap 偏父子；把两者统一到一套 authority invariants 的工作较少。
- 风险：形式化不足会变成“两个模式的拼盘”。

### 5.3 跨 App 的 Context Fabric

> 以能力寻址、引用优先、带信息流标签与 TTL 的上下文句柄，跨 App 流转；解析即审计；敏感出口需一次性放行。

- Agent libOS 有 source reference 与 one-shot release，但主要在单 runtime 内；MCP Resources 是 server-scoped；没有跨 App 的统一句柄层。
- 风险：与 OS 文件选择器、portal、content provider 的边界需要说清楚。

### 5.4 同意回执与任务 trace 的跨 App 绑定

> 把“用户同意了什么、哪个 Agent、哪个任务、用了哪份数据、如何撤销”做成跨 App 可验证对象，并与任务 trace 绑定。

- DRP/APS 做了回执，但没有和本地跨 App Agent 任务树结合。
- 风险：与 Kantara/ISO 回执、WIMSE 委托凭证的兼容性。

### 5.5 联邦式本地总线

> 一个用户态 overlay bus，不要求 OS 厂商采用，就能在现有平台上提供跨 App Agent 协作与治理。

- 现有 OS 厂商方案是封闭星型；现有跨平台协议是网络层；overlay 组合是空档。
- 风险：没有 OS 厂商支持时，对端认证、沙箱穿透、系统 Agent 接入都受限。

---

## 6. 可证伪的新颖性主张

建议在论文/标准提案中使用如下措辞（而不是“首个”）：

> OSAP 定义一种本地绑定：它在现有 OS 沙箱与 IPC 之上，把厂商能力注册表、MCP/A2A 能力与 App 原生 Agent 投影为统一能力图，并用任务级、可衰减、audience/task 绑定的能力凭证，支持跨应用的点对点与层级协作，同时把同意回执、上下文引用与审计绑定到同一任务 trace。

要证明它成立，需要：

1. 与至少 6 个最接近的工作做逐项对比（本文第 3 节）；
2. 给出形式化的 authority invariants，并证明衰减/撤销/取消满足单调性；
3. 实现至少两个 App + 一个系统 Agent + 一个 Bridge；
4. 测量：P95 延迟、权限绕过率、提示注入阻断率、撤销传播时间、审计完整性；
5. 证明现有工作无法直接组合出同样性质（例如：A2A + AgentCap 仍缺少 OS 对端身份与跨 App 上下文句柄）。

---

## 7. 可能推翻新颖性的问题

在继续投入前，应先回答：

1. **A2A + AgentCap + D-Bus 的组合是否已经足够？** 如果只是“把三者拼起来”，新颖性弱。
2. **Agent libOS 的 source reference + one-shot release 是否已经覆盖 Context Fabric？** 需要逐条对比。
3. **AppFunctions/App Actions 是否会在 2027 年开放第三方 Agent 互调？** 如果开放，OSAP 的厂商联邦价值下降。
4. **IETF agentproto 是否会定义本地绑定？** 如果会，OSAP 应作为其 profile，而不是独立协议。
5. **同意回执是否已有跨 App 标准？** Kantara/ISO/WIMSE 的覆盖范围需要核实。

---

## 8. 结论

- **概念层**：OSAP 不是全新概念；2026 年已有大量重叠工作。
- **交叉层**：跨厂商本地能力图 + 点对点/主子统一权限 + 跨 App 上下文 + 回执/trace 绑定，仍有空间。
- **证据层**：当前没有实现与评估，因此还不能称为研究贡献。
- **策略层**：最稳妥的路径是把自己定位为 **“本地绑定 / profile”**，与 MCP、A2A、IETF agentproto、OAuth WIMSE 对齐，而不是另起一个 Agent 协议。

---

## 9. 参考链接

### 厂商 OS

- Apple App Intents: https://developer.apple.com/documentation/appintents
- Apple WWDC26 App Intents Group Lab: https://developer.apple.com/videos/play/wwdc2026/8011/
- Android AppFunctions: https://developer.android.com/ai/appfunctions
- Android Intelligence System: https://developer.android.com/ai/intelligence-system
- Windows App Actions: https://learn.microsoft.com/en-us/windows/ai/app-actions
- Windows agentic security: https://learn.microsoft.com/en-us/windows/security/book/operating-system-agentic-security

### Agent 协议与标准

- MCP: https://modelcontextprotocol.io
- A2A: https://a2a-protocol.org
- IETF agentproto: https://datatracker.ietf.org/wg/agentproto/about/
- IETF AAP: https://www.ietf.org/archive/id/draft-fane-opena2a-aap-01.html
- IETF DAAP: https://www.ietf.org/archive/id/draft-mishra-oauth-agent-grants-00.html
- IETF DRP: https://datatracker.ietf.org/doc/draft-nelson-agent-delegation-receipts/
- IETF APS: https://datatracker.ietf.org/doc/draft-pidlisnyi-aps/
- IETF WIMSE credential delegation: https://www.ietf.org/archive/id/draft-sweeney-wimse-credential-delegation-00.html
- AGNTCY: https://docs.agntcy.org/

### OS / 系统研究

- AgenticOS: https://arxiv.org/abs/2606.21129
- Agent libOS: https://arxiv.org/abs/2606.03895
- AgentKernel: https://arxiv.org/abs/2609.29647
- AOS: https://arxiv.org/abs/2606.01508
- AgentCap: https://arxiv.org/abs/2611.00729
- CAPMAS: https://arxiv.org/abs/2609.06500
- Aegis OS: https://arxiv.org/abs/2611.08516
- AIOS: https://arxiv.org/abs/2504.14411
- agent-os (“POSIX for AI agents”): https://github.com/isaacsight/agent-os
- BusMA: https://arxiv.org/html/2609.15054v1

### 本地 IPC 与能力系统

- D-Bus specification: https://dbus.freedesktop.org/doc/dbus-specification.html
- XDG Desktop Portal: https://flatpak.github.io/xdg-desktop-portal/
- Macaroons: https://research.google/pubs/pub41892/
- UCAN: https://ucan.xyz/
- Biscuit: https://www.biscuitsec.org/
- Capsicum: https://www.cl.cam.ac.uk/research/security/capsicum/
- seL4: https://sel4.systems/
