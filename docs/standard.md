# OSAP 0.1 — Open System Agent Protocol

> English version: [standard.en.md](standard.en.md)

**跨应用 Agent 点对点协作、能力注册表联邦与任务级授权**

| 项目 | 内容 |
|---|---|
| 文档状态 | Draft Standard（讨论稿） |
| 版本 | 0.1 |
| 日期 | 2026-11-10 |
| 规范性关键词 | RFC 2119 / RFC 8174 |
| 适用范围 | 单设备、单用户会话内的跨应用 Agent 协作 |
| 规范性文本 | 本文 |
| 设计说明 | [`design-draft.md`](design-draft.md)（非规范性） |
| 相关工作 | [`prior-art.md`](prior-art.md)（非规范性） |
| 许可 | Apache-2.0（见 [`LICENSE`](../LICENSE)） |

---

## Abstract

OSAP（Open System Agent Protocol）定义一套**本地优先**的开放协议，使不同应用所承载的 Agent 能够在同一操作系统会话内：

1. **点对点协作**：发现彼此、建立会话、委派任务、交换结果，而不需要所有流量都经过一个中心化编排 Agent；
2. **联邦能力注册表**：把 Apple App Intents、Android AppFunctions、Windows App Actions，以及 MCP、A2A、D-Bus、OpenAPI 等来源的能力，投影为统一的能力记录；
3. **任务级授权**：以可验证、可衰减、可撤销的能力凭证，替代粗粒度 App 权限；所有跨应用副作用经过策略、同意与审计。

OSAP 不替代 MCP、A2A、D-Bus 或厂商原生能力框架。它定义的是这些机制之间的**本地互操作层**：统一身份、统一发现、统一授权、统一上下文引用与统一审计。

---

## 1. Introduction

### 1.1 Problem

现代应用把数据、账号、界面和权限封装在各自边界内。用户完成一件跨应用任务时，往往需要在多个 App 之间复制粘贴、重复授权、手动传递上下文。LLM Agent 使跨应用编排成为可能，但当前生态存在四个结构性缺口：

1. **本地 Agent 之间没有公共通道**。MCP 解决 Agent→工具，A2A 解决跨网络 Agent↔Agent；同一台机器上两个 App 的 Agent 如何安全地发现彼此、建立任务、交换结果，缺少统一答案。
2. **厂商能力注册表互不联通**。App Intents、AppFunctions、App Actions 各自是封闭的星型模型：系统 Agent 可以发现和调用 App 能力，但第三方 App 的 Agent 不能平等参与。
3. **授权粒度仍以 App 为中心**。用户授权的是“某 App 可以访问通讯录”，而不是“本任务中，这个 Agent 可以读取这一条联系人，用于发送一条消息”。
4. **上下文无法安全流动**。每个 Agent 重复收集“用户是谁、正在做什么、数据在哪里”，既低效又扩大隐私与提示注入的攻击面。

### 1.2 Design goals

| 编号 | 目标 |
|---|---|
| G1 | 跨应用发现：能力、事件、schema、风险、成本可被查询，但能力声明不等于授权 |
| G2 | 点对点与主子双模：既能平级协作，也能层级委派 |
| G3 | 最小权限：无环境权限；权限只能沿委派链收窄 |
| G4 | 任务级授权：能力绑定 audience、task、资源、时间、预算 |
| G5 | 数据不出域：默认传引用，按策略解析 |
| G6 | 人类可控：分级同意、意图预览、可撤销、可审计 |
| G7 | 联邦而非替代：统一投影厂商注册表与 MCP/A2A/D-Bus |
| G8 | 可演进：内核小，语义通过命名空间与 schema 扩展 |

### 1.3 Scope

本规范定义：

- 本地 Agent 的身份、注册、会话与消息信封；
- 能力描述、能力凭证、衰减、撤销与校验规则；
- 能力注册表联邦模型与发现查询/响应；
- 任务树、点对点会话、委派、预算、取消与结果聚合；
- 上下文句柄、解析、信息流标签与任务黑板；
- 同意请求/授予/拒绝、同意回执与审计事件；
- 传输绑定、消息分帧、版本协商与一致性要求；
- 一致性等级与测试用例。

### 1.4 Non-goals

- 不规定 Agent 的内部推理、模型、提示词或规划算法。
- 不替代 MCP 的工具语义、A2A 的跨组织 Agent 语义或厂商原生能力框架。
- 不定义跨设备、跨组织、跨用户的联邦信任根；这些属于后续版本。
- 不定义具体 UI；只定义同意与审计的协议原语。
- 不提供内核级隔离；OSAP 运行在现有 OS 沙箱与 IPC 之上。
- 0.1 不定义 Bus 不可见 payload 的端到端加密 profile；该 profile 列入 0.2（见 §3.6）。因此 0.1 只适用于把 Bus 作为受信任组件的部署。
- **不定义长期语义记忆**：Bus 不是记忆库，不提供跨任务的经验检索、语义索引或用户画像。Bus 只持久化路由、幂等、恢复与授权判定所需的结构化状态（见 §3.7）。Agent 记忆属于 Agent 或独立的 memory 服务，必须通过普通能力单独授权（见 §9.3）。

### 1.5 Relationship to existing work

OSAP 的定位是**本地绑定与联邦层**，不是又一个 Agent 通信协议：

- **MCP**：Agent→工具；OSAP 将 MCP tool 投影为能力记录，并可把 OSAP 请求桥接为 MCP 调用。
- **A2A**：跨网络 Agent↔Agent；OSAP 复用其 Task/Artifact 思路，并提供本地身份、能力与同意绑定。
- **App Intents / AppFunctions / App Actions**：厂商能力注册表；OSAP 将其投影为统一能力记录，并保留来源与信任标签。
- **D-Bus / XPC / Binder**：本地 IPC；作为 OSAP 的传输绑定，而不是被替代。
- **IETF agentproto / OAuth WIMSE / AAP / DAAP / DRP / APS**：对话管理、委托授权、同意回执；OSAP 与其对齐，并在本地跨应用场景中给出绑定。

详见 [`prior-art.md`](prior-art.md)。

### 1.6 Design principles

1. **No ambient authority**：Agent 默认没有任何跨应用权限；Bus 的 payload 可见性是显式信任假设，不是隐式默认（见 §3.6）。
2. **Attenuation only**：子能力必须是父能力的子集。
3. **Audience + task binding**：能力绑定接收方与任务，不可转发、不可跨任务复用。
4. **Reference over payload**：默认传句柄，不传原始数据。
5. **Fail closed**：策略不可判定、凭证过期、审计不可写时拒绝。
6. **Human in the loop**：L3/L4 动作必须有人类同意回执。
7. **Federate, don't absorb**：保留原生注册表的权威性与来源。
8. **Small core, typed edges**：Bus Core 只做认证、信封校验、路由与背压；策略、签发、存储、审计由独立服务承担，业务语义用 schema 扩展。
9. **Explicit trust boundary**：每个组件能看到什么、能做什么 MUST 显式声明；不存在“因为在本机所以可信”。

---

## 2. Conventions and Terminology

### 2.1 Requirement keywords

本文中的 **MUST**、**MUST NOT**、**REQUIRED**、**SHALL**、**SHALL NOT**、**SHOULD**、**SHOULD NOT**、**RECOMMENDED**、**MAY**、**OPTIONAL** 按 RFC 2119 与 RFC 8174 解释。

### 2.2 Terminology

| 术语 | 定义 |
|---|---|
| **Agent** | 应用内代表用户执行任务的实体，拥有独立身份与能力 |
| **Local Agent Bus（LAB）** | 整套本地总线：Bus Core（最小路由内核）+ 独立服务（CA/RFS/PCS/CF/AL）与 Bridge 的部署视图 |
| **Bus Core** | 最小 TCB：对端认证、信封校验、路由、连接/会话与背压；不执行策略、不签发能力、不存储对象、不持久化审计 |
| **Capability Authority（CA）** | 能力凭证的签发、衰减、撤销与校验组件（独立服务） |
| **Registry Federation Service（RFS）** | 能力注册表索引与联邦投影组件（独立服务） |
| **Policy & Consent Service（PCS）** | 策略求值、同意流程与回执签发组件（独立服务） |
| **Context Fabric（CF）** | 上下文授权代理：校验能力与标签、解析句柄；默认复用 OS 句柄，独立对象存储为可选实现 |
| **Audit Ledger（AL）** | 可独立部署的只追加、哈希链式审计服务；单写者、可锚定 |
| **Bridge Adapter（BA）** | 将原生注册表/协议映射为 OSAP 的适配器 |
| **Capability** | 可验证、可衰减、可撤销的授权凭证 |
| **Capability Record（CR）** | 对某个 Agent 能力的统一描述，带来源与信任标签 |
| **Task** | 一次可追踪的工作单元，属于任务树 |
| **Session** | 两个或多个 Agent 之间的一段点对点协作上下文 |
| **Handle** | 指向数据或上下文的引用，如 `obj://`、`ctx://`、`task://` |
| **Consent Receipt** | 用户同意某次动作的签名记录 |
| **Trace** | 由一次用户意图派生的跨 Agent 调用链 |
| **Bus State（总线状态）** | 为路由、幂等、崩溃恢复与授权判定所需的结构化运行数据；有界、可过期、不含业务语义，不是记忆 |
| **Memory（记忆）** | 跨任务可检索的语义经验或用户偏好；由 Agent 或独立 memory 服务持有，需单独授权，不属于 Bus |

### 2.3 Identifiers and URIs

| 对象 | 形式 | 示例 |
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

- `<instance-id>` 由 Agent 启动时生成，MUST 不可预测，SHOULD 使用 ULID 或 UUIDv7。
- `<task-id>`、`<session-id>`、消息 `id` SHOULD 使用 ULID 或 UUIDv7。
- 所有 URI MUST 符合 RFC 3986。
- 时间戳 MUST 使用 RFC 3339 UTC（`Z` 结尾），精度至少到秒。

### 2.4 Encoding

- 控制消息 MUST 使用 UTF-8 JSON。
- 需要签名的对象 MUST 使用 JSON Canonicalization Scheme（RFC 8785）规范化后再签名。
- 大对象 MUST 通过 `obj://` 引用传递；控制消息 SHOULD 小于 1 MiB，MUST NOT 超过 8 MiB。
- CBOR（RFC 8949）绑定可以作为可选扩展；其 canonical encoding 规则另行定义。

### 2.5 Time and clocks

- 线上时间戳 MUST 使用 RFC 3339 UTC；能力 `iat`/`nbf`/`exp` MUST 使用 Unix epoch 秒。
- 本地超时、速率限制与重试 MUST 使用单调时钟（monotonic clock）；`deadline` 在接收时必须转换为单调时钟，不得因系统时间调整而延长。
- 系统挂起/恢复后，实现 MUST 重新检查 `deadline`、`exp` 与租约；已过期者 MUST NOT 执行副作用。
- Bus SHOULD 在 `welcome` 中公布当前时间与允许的时钟偏差；超过偏差的消息 SHOULD 拒绝并记录 `TRANSPORT_CLOCK_SKEW`。
- 不得依赖跨设备的墙钟一致性；0.1 只覆盖单设备会话。

---

## 3. Architecture

### 3.1 Planes

| 平面 | 职责 | 组件 |
|---|---|---|
| **Control plane** | 注册、发现、身份、能力、策略、同意、审计 | RFS、CA、PCS、AL（均为独立服务） |
| **Data plane** | 请求/响应、事件、流、取消、错误 | Bus Core（最小 TCB） |
| **Context plane** | 句柄解析、对象存储、任务黑板、信息流标签 | CF（授权代理；可选对象存储） |

### 3.2 Components

```
┌─────────────────────────────────────────────────────────────┐
│              User / Shell / System Agent                    │
│        （意图输入、同意 UI、活动中心、审计查看）              │
└───────────────▲─────────────────────────────▲───────────────┘
                │                             │
┌───────────────┴─────────────────────────────┴───────────────┐
│              Local Agent Bus Core（最小 TCB）                │
│   对端认证 · 信封校验 · 路由 · 会话/连接 · 背压 · 幂等索引    │
│   不执行策略 · 不签发能力 · 不存储对象 · 不持久化审计          │
└───▲───────────▲───────────▲───────────▲───────────▲─────────┘
    │           │           │           │           │
┌───┴────┐ ┌────┴───┐ ┌─────┴───┐ ┌─────┴───┐ ┌─────┴──────┐
│ RFS    │ │  CA    │ │  PCS    │ │  AL     │ │ Bridge     │
│ 独立   │ │ 独立   │ │ 独立    │ │ 独立    │ │ 沙箱       │
│ 进程   │ │ 进程   │ │ 进程    │ │ 进程    │ │ 每类适配器 │
└────────┘ └────────┘ └─────────┘ └─────────┘ └────────────┘
    ▲
┌───┴─────────────────────────────────────────────────────────┐
│ Context Fabric 服务（独立进程）                              │
│ 授权解析 · 标签 · TTL · 默认映射 OS 句柄 · 可选对象存储       │
└─────────────────────────────────────────────────────────────┘
    ▲
┌───┴────────────┐    ┌────────────────┐    ┌────────────────┐
│ Notes.app      │    │ Calendar.app   │    │ Messaging.app  │
│ └ Agent(notes) │    │ └ Agent(cal)   │    │ └ Agent(msg)   │
│   └ OSAP SDK   │    │   └ OSAP SDK   │    │   └ OSAP SDK   │
└────────────────┘    └────────────────┘    └────────────────┘
```

Bus Core 是路由路径上唯一必须被所有 Agent 信任的组件；CA/PCS/AL 的信任通过签名、回执与审计锚定建立，而不是通过共享进程地址空间。RFS/CA/PCS/CF/AL MUST 作为独立进程或独立沙箱运行，并通过 Bus 以系统命名空间通信；它们 MUST NOT 共享进程地址空间，也 MUST NOT 直接持有其他服务的私钥。Bus Core MUST NOT 解析 `body.data` 的业务语义，也 MUST NOT 把策略、签发、存储或审计逻辑内联进路由路径。

> 图中 CF 与 Bridge 同样通过 Bus Core 通信；为保持可读性省略了交叉连线。

### 3.3 Deployment models

| 模型 | 描述 | 适用 |
|---|---|---|
| **A. Per-user bus + services** | 登录会话启动一个 Bus Core 与若干独立服务进程，所有 Agent 连接本地 IPC | 桌面 OS，推荐起点 |
| **B. System bus + user broker** | 系统级身份/策略，用户级消息代理；服务按用户分区 | 多用户、企业管控 |
| **C. Library + OS mediation** | 无中心路由守护进程，OS 直接提供认证通道；服务组件可裁剪 | 资源受限设备 |

本规范不强制部署模型；一致性要求针对协议行为，而不是进程拓扑。无论采用哪种模型，TCB 边界与信任 profile MUST 显式声明（见 §3.6）。

### 3.4 Trust boundaries

- **App ↔ Bus**：通过 OS 对端凭据认证；Bus MUST 验证连接进程的 App 身份。
- **Agent ↔ Agent**：不直接建立 socket；所有消息经 Bus 路由。
- **Bus ↔ 原生注册表**：Bridge 必须保留来源与信任标签。
- **Bus ↔ 外部服务**：经 Bridge 的出站流量受 egress 策略约束。
- **User ↔ Consent**：同意回执由用户/OS 签名，Agent 不可伪造。
- **Bus Core ↔ Payload**：在 0.1 默认信任 profile 中，Bus Core 可读取 payload；它 MUST NOT 默认持久化 payload，MUST NOT 把 payload 写入审计，除非任务策略或用户明确要求。
- **Service ↔ Service**：每个服务是独立 principal，持有自己的系统能力；不得因“同属 OSAP”而互相隐式信任。
- **Bridge ↔ Agent**：Bridge 只获得完成投影所需的最小能力；外部内容 MUST 保留 `origin=external`。
- **Bus 不是信任根**：Bus 的对端认证依赖 OS 凭据；Bus 自身完整性依赖 OS 代码签名/沙箱。0.1 不声称能抵御被攻破的 Bus。

**校验分工**（对每条消息）：

| 检查 | 执行方 | 状态依赖 |
|---|---|---|
| 对端认证、信封 schema/版本/大小、分帧 | Bus Core | 无 |
| 能力签名与绑定（`audience`/`subject`/`task`）校验 | Bus Core | 无 |
| `deadline`、幂等、`to:capability` 唯一解析 | Bus Core（可经 RFS） | 幂等索引 |
| 撤销状态、策略求值、同意回执、风险重估 | 接收方 Agent（经 PCS/CA） | 有 |
| 业务 schema、副作用执行、intent/outcome 审计 | 接收方 Agent | 有 |

Bus Core MUST NOT 因策略或撤销判定拒绝路由；它只做**无状态绑定校验**与路由/配额。授权判定 MUST 在接收方执行。

### 3.5 Protocol stack

| 层 | 内容 | 规范性 |
|---|---|---|
| L0 | 传输与分帧 | MUST |
| L1 | 身份与信任 | MUST |
| L2 | 消息信封 | MUST |
| L3 | 任务与会话 | MUST |
| L4 | 能力与同意 | MUST |
| L5 | 注册表联邦 | MUST（C2+） |
| L6 | 上下文句柄 | MUST（C5+） |
| L7 | 领域 schema | OPTIONAL |

### 3.6 Trust profiles

0.1 讨论两个信任 profile；只有 P0 可以被 0.1 实现声明。

| Profile | Bus 可见性 | 适用 | 0.1 状态 |
|---|---|---|---|
| **P0 Trusted Bus** | 可见信封与明文 `body` | 单用户设备，Bus 受 OS 完整性保护 | 默认、唯一可声明 |
| **P1 Opaque Bus** | 仅见信封元数据 | 不信任 Bus 的部署 | 实验性，0.2 定义 |

P0 要求：

- Bus Core MUST 由 OS 代码签名/沙箱保护，并在可用时验证自身完整性。
- Bus Core MUST NOT 默认记录 payload；错误消息、审计与崩溃转储 MUST 脱敏。
- 部署方 MUST 向用户披露“Bus 可读取跨 App 消息内容”。
- 一致性声明 MUST 包含 `bus_visibility: "payload"`。

P1 方向（非 0.1 规范）：

- payload 使用 HPKE（RFC 9180）或等效的端到端加密；Bus 只看到路由与授权元数据。
- 0.1 实现 MUST NOT 声称支持 P1；相关 wire format 列入 §15 开放问题。

### 3.7 State and recovery

Bus Core 与各服务 MUST 明确区分易失状态与持久状态。

必须持久化的状态：

| 状态 | 负责组件 | 恢复要求 |
|---|---|---|
| 任务树与任务状态 | Bus Core | 重启后重建；未完成任务 MUST 转为 `failed` 或显式重新调度 |
| 幂等索引 | Bus Core | 至少保留到 `deadline` 之后；重启后不得重复执行副作用 |
| 撤销列表 | CA | 重启后仍生效；与 `exp` 共同判定 |
| 同意回执索引 | PCS | 重启后可验证、可撤销 |
| 句柄/对象元数据（若由 CF 管理） | CF | 重启后可解析；孤儿对象按策略回收 |
| 审计链头 | AL | 重启后校验链完整性；损坏时 L3/L4 fail closed |

规则：

- 持久化 MUST 使用原子提交（WAL、日志结构存储或等价机制）；不得出现“半条记录”。
- 审计链 MUST 单写者；多实例部署 MUST 按用户分区或使用 leader election。
- 崩溃发生在副作用之前：恢复时标记任务失败，MUST NOT 自动重试非幂等副作用。
- 崩溃发生在副作用之后、结果提交之前：恢复 MUST 记录 `effect.reconciled` 并要求人工/策略对账，不得静默重放。
- 恢复事件 MUST 写入审计；用户 MUST 能看到被中断的任务。

**State is not memory.** 上表的状态是**运行状态**，不是记忆：

- 持久状态 MUST NOT 被当作跨任务上下文、语义索引或用户画像使用；其用途限于路由、幂等、恢复与授权判定。
- 持久状态 MUST NOT 保存 `body.data` 的语义副本；默认不落 payload（见 §11.11）。
- 持久状态 MUST NOT 对普通 Agent 开放为通用查询接口；只能通过所属组件的管理接口或对应能力访问。
- 幂等索引、审计日志、任务树均 MUST NOT 被复用为记忆来源；需要记忆时 MUST 作为独立能力实现（见 §9.3）。
- 删除用户数据时，属于该用户的持久状态 MUST 一并清理或去标识化，但审计链可按 §11.9 保留脱敏记录。

---

## 4. Identity and Trust

### 4.1 Principal

跨应用动作的主体是一个四元组：

```
Principal = (User, App, AgentInstance, Device)
```

- **User**：OS 账户或受管身份。
- **App**：安装包身份 + 代码签名。
- **AgentInstance**：App 启动时注册的 Agent 实例。
- **Device**：设备标识。

Bus MUST 在连接建立时验证 App 身份，并把 Agent 实例绑定到该 App。Agent 不能仅凭字符串自称属于其他 App。

`agent://` 是**本地命名**，不是自认证标识。Bus 是命名权威：它把 `(app, agent-name, instance-id)` 绑定到经过 OS 认证的 App 身份与公钥。跨设备可验证标识不在 0.1 范围内。

### 4.2 App attestation

- Linux：`SO_PEERCRED` + 可执行文件路径/哈希 + 包管理器签名（如适用）。
- macOS：audit token + code signature + designated requirement。
- Windows：named pipe client SID + package identity + 签名。
- Android：Binder UID/PID + package signature。
- 其他平台：本地 mTLS + 由 OS 信任根签发的客户端证书。

验证失败时 Bus MUST 拒绝连接，并记录 `agent.registration_denied`。

### 4.3 Agent registration

Agent 连接后 MUST 发送 `hello`：

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

Bus 返回 `welcome`，包含 `session_id`、特性开关、限制与 Bus 公钥。注册成功后，Agent 的能力记录才进入 RFS。

`hello.body.data.public_key` MUST 与该 App 清单或 OS 密钥库中的公钥绑定；Bus MUST 验证绑定关系，失败时拒绝注册。Agent 不得在未证明私钥占有的情况下注册公钥。

### 4.4 Reserved namespaces

以下命名空间保留给系统：

- `agent://system/...`
- `cap://os/...`
- `ctx://os/...`
- `event://os/...`

第三方 App MUST NOT 注册这些命名空间。违反者 MUST 被拒绝并记录审计事件。

### 4.5 Keys and signatures

- 默认签名算法：Ed25519（RFC 8032），JWS 形式（RFC 7515）。
- 签名密钥 SHOULD 由 OS 密钥库持有，Agent 通过受限句柄使用。
- 公钥通过 `hello` 或注册表分发；MUST 支持轮换与过期。
- 能力凭证、同意回执、审计锚点 MUST 可验证；消息本身依赖传输双向认证，MAY 额外签名。

### 4.6 Session

- 每个连接有一个 `session_id`。
- 点对点协作使用独立的 `session_id`，由发起方创建或由 Bus 分配。
- Session MUST 记录参与者、创建时间、过期时间与能力引用。
- Session 结束 MUST 触发未完成任务的取消或移交。

### 4.7 Naming authority

- `agent://` 的名称由 Bus 分配/确认；Agent 自报的 `instance-id` 只作为建议，Bus MAY 重新分配。
- Bus MUST 维护 name →（App 身份、公钥、会话）的绑定，并在每次路由时复核。
- 名称释放后 MUST NOT 立即复用；SHOULD 保留冷却期，避免旧消息误投。
- 0.1 不提供跨设备名称解析；跨设备场景 MUST 使用其他信任根并显式声明。

---

## 5. Capability Model

### 5.1 Capability descriptor

能力描述是注册表中的静态声明，不等于授权：

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

能力凭证 MUST 是签名对象，至少包含：

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

字段要求：

| 字段 | 要求 | 说明 |
|---|---|---|
| `issuer` | MUST | 签发主体（用户/系统/父 Agent） |
| `subject` | MUST | 持有并执行能力的 Agent；MUST 等于消息发送方 |
| `audience` | MUST | 目标 Agent；MUST 等于消息接收方 |
| `task_id` | MUST | 绑定的任务；MUST 等于信封中的任务 |
| `root_task_id` | MUST | 用于审计聚合 |
| `actions` | MUST | 允许的动作集合 |
| `resources` | MUST | 允许的资源集合 |
| `exp` | MUST | 过期时间；SHOULD 不超过 1 小时 |
| `parent_cap_id` | 条件 | 非根能力 MUST 提供 |
| `depth` | 条件 | 根为 0，每次委派 +1 |
| `consent_receipt_id` | 条件 | L3/L4 动作 MUST 提供 |
| `proof` | MUST | 签名 |

**语义说明**：`subject` 是能力被授予、并据以发起调用的 Agent（MUST 等于消息 `from`）；`audience` 是必须接受并校验该能力的 Agent（MUST 等于消息接收方）。在委派场景中，父 Agent 为子 Agent 签发新能力，`subject` 与 `audience` 都是子 Agent；父 Agent MUST NOT 把自己的 token 原样转发。

### 5.3 Attenuation

子能力 MUST 满足以下全部条件：

1. `subject` 是子 Agent，且 `audience` 是实际接收方；
2. `actions` ⊆ 父 `actions`；
3. `resources` ⊆ 父 `resources`；
4. `exp` ≤ 父 `exp`，`nbf` ≥ 父 `nbf`；
5. `max_uses` ≤ 父 `max_uses`；
6. `rate` 不宽于父 `rate`；
7. `max_budget` 每个维度 ≤ 父预算；
8. `depth` = 父 `depth` + 1，且 ≤ `max_depth`；
9. `consent_receipt_id` 仍然有效；
10. 父能力允许委派（`can_delegate=true`）。

任一条件不满足，CA MUST 拒绝签发。Bus MUST 对无状态可判定的绑定/衰减条件（`audience`、`subject`、`task_id`、`depth`）拒绝路由；撤销、`max_uses`、同意回执与预算等有状态条件由接收方在执行前拒绝。

### 5.4 Binding

- **Audience binding**：`audience` MUST 等于接收 Agent 的 ID；Bus 在路由前校验，接收方 MUST 复核。
- **Task binding**：`task_id` MUST 等于信封中的 `task.id`。例外：`delegate` 的发送方能力绑定父任务（`task.parent`），`handoff` 的发送方能力绑定被转移任务（`task.id`）。接收方 MUST 按此规则校验，跨任务复用 MUST 被拒绝。
- **Sender binding**：`subject` MUST 等于信封 `from`；禁止把收到的凭证原样转发。
- **Session binding**（可选）：`constraints.session_id` 可用于点对点会话。
- **Nonce**：高价值动作 SHOULD 使用一次性 nonce 或 `max_uses=1`。

Bus 只做无状态绑定校验；撤销、策略与同意由接收方复核（见 §3.4、§5.5）。

### 5.5 Revocation

- CA MUST 提供撤销接口，按 `cap_id` 撤销。
- 撤销父能力 MUST 级联撤销所有后代能力。
- 能力 SHOULD 短 TTL；撤销列表 SHOULD 可离线缓存。
- 接收方 Agent MUST 在执行前通过 CA 检查撤销状态；接收方或 CA 无法检查时 MUST 拒绝高风险动作。
- 撤销事件 MUST 写入审计账本，并通知受影响 Agent。

### 5.6 Authority invariants

| 编号 | 不变量 |
|---|---|
| AI1 | 无环境权限：Agent 不持有能力时不能执行任何跨应用动作 |
| AI2 | 单调收窄：子能力权限 ⊆ 父能力权限 |
| AI3 | 受众绑定：能力不能被非 `audience` 的 Agent 使用 |
| AI4 | 任务绑定：能力不能被其他任务复用 |
| AI5 | 撤销完整：撤销父能力使所有后代失效 |
| AI6 | 禁止转发：Agent 不能把自己的凭证转交他人 |
| AI7 | 同意前置：L3/L4 动作执行前必须有有效同意回执 |
| AI8 | 审计前置：L3/L4 动作的审计记录必须在副作用前可写 |
| AI9 | 深度有界：委派深度不超过 `max_depth` |
| AI10 | 预算单调：子任务预算不超过父任务剩余预算 |

### 5.7 Risk classes

| 等级 | 名称 | 示例 | 默认同意 |
|---|---|---|---|
| L0 | Public read | 公开天气、公开目录 | 自动允许 |
| L1 | Personal read | 日历、联系人、笔记 | 首次同意或任务级同意 |
| L2 | Local write | 创建本地草稿、修改待办 | 自动 + 通知 |
| L3 | External side effect | 发消息、发邮件、提交表单 | 每次同意（可批量/限时） |
| L4 | High impact | 支付、删除、对外发布 | 强确认 + 二次认证 |

风险等级由能力记录声明，PCS 可以提升但不能降低。

### 5.8 Consent linkage

- L3/L4 能力 MUST 引用有效 `consent_receipt_id`。
- 回执中的 `actions`、`resources`、`task_id`、`audience` MUST 覆盖能力请求。
- 回执过期或被撤销时，能力 MUST 失效。
- 批量同意 MUST 有明确的任务范围、时间窗口与动作集合。

---

## 6. Registry Federation

### 6.1 App manifest

App 安装或首次运行时注册清单：

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

清单 MUST 由 App 签名；RFS MUST 验证签名后才索引。

### 6.2 Capability Record

统一能力记录：

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

| `source.kind` | 说明 |
|---|---|
| `vendor_registry` | Apple App Intents、Android AppFunctions、Windows App Actions |
| `mcp` | MCP Server / Tool |
| `a2a` | A2A Agent Card / Skill |
| `dbus` | D-Bus service / interface / method |
| `openapi` | OpenAPI operation |
| `native` | App 直接通过 OSAP SDK 注册 |
| `bridge` | 其他自定义桥接 |

### 6.4 Provenance and trust

| `trust` | 含义 |
|---|---|
| `system` | OS 厂商注册表或系统签名 |
| `verified` | 签名已验证的第三方注册表/协议 |
| `unverified` | 用户手动添加或未验证来源 |

- 发现结果 MUST 包含 `source`、`trust`、`freshness`。
- 来自外部协议的内容 MUST 标记 `origin=external`，默认信任等级最低。
- RFS MUST NOT 把未验证来源提升为 `system`。

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
      "intent": "为一次会议找空闲时间",
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

规则：

- 发现结果 MUST 附带 `consent_hint`（`none`、`first_use`、`per_task`、`per_use`），它来自能力记录的静态策略，不是实时授权。
- 发现结果 MUST NOT 返回实时 `policy_verdict`；实时判决 MUST 在 `request`/`delegate` 时由 PCS 求值（见 §6.9）。
- 调用方 MUST NOT 把 `consent_hint` 当作授权；`match` 只是排序信号，不能替代结构化过滤。
- 发现接口 MUST NOT 枚举用户隐私数据，也不得泄漏“某 Agent 当前是否被策略拒绝”。

### 6.7 Federation adapters

每个 Bridge Adapter MUST：

1. 读取原生描述符；
2. 投影为 `Capability Record`；
3. 保留 `source`、`native_id`、`version`、`provenance`；
4. 映射 schema 与风险等级；
5. 在原生描述符变化时更新或失效记录；
6. 不修改原生注册表的权威状态。

映射建议：

| 原生 | `source.registry` | `native_id` |
|---|---|---|
| Apple App Intent | `apple.app_intents` | intent identifier |
| Android AppFunction | `android.appfunctions` | function id |
| Windows App Action | `windows.app_actions` | action id |
| MCP Tool | `mcp` | server + tool name |
| A2A Skill | `a2a` | agent card + skill id |
| D-Bus Method | `dbus` | bus + path + interface + method |
| OpenAPI Operation | `openapi` | operationId |

### 6.8 Namespace mapping

- 原生命名空间与 OSAP 能力名之间 MUST 有确定性映射。
- 冲突时 MUST 使用 `source.registry` 前缀消歧。
- schema 映射 MUST 保留原始 schema URI 与版本。
- 无法安全映射的能力 MUST 标记 `visibility=hidden`，不得静默暴露。

### 6.9 Policy verdict

Policy verdict 是**调用时**判决，不是发现结果的一部分。PCS 在收到 `request`/`delegate` 时综合以下输入：

- 用户偏好与历史同意；
- App 清单与签名；
- 能力风险等级；
- 当前任务、会话、前台状态；
- 企业/MDM 策略；
- 数据范围与出口策略；
- Agent 的信任等级与行为记录。

输出：

| 判决 | 含义 |
|---|---|
| `allow` | 可直接执行 |
| `allow_with_logging` | 可执行，但必须记录 |
| `require_consent` | 需要用户同意回执 |
| `deny` | 拒绝 |

无法判定时 MUST 返回 `deny`。

### 6.10 Caching and freshness

- 能力记录 MUST 有 `observed_at` 与 `expires_at`。
- 过期记录 MUST 重新验证，不得用于授权决策。
- 发现缓存 SHOULD 有上限，并按来源隔离。
- 原生注册表删除能力时，RFS MUST 在 TTL 内失效对应记录。

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

字段规则：

- `osap` MUST 存在；主版本不兼容时 MUST 拒绝。
- `id` MUST 全局唯一；用于幂等去重。
- `trace_id` MUST 在一次用户意图内保持一致。
- `causation_id` SHOULD 指向直接触发本消息的消息。
- `session_id` 在点对点协作中 MUST 存在。
- `to` MUST 是 `{ "agent": ... }`、`{ "capability": ... }` 或 `{ "user": ... }` 之一；`{ "user": ... }` 仅用于同意与系统通知流程。
- 当 `to` 使用 `capability` 时，Bus MUST 通过 RFS 解析出唯一 `audience` Agent；无法唯一解析，或解析结果与 `auth.token.audience` 不一致时，MUST 返回 `ROUTING_AMBIGUOUS` 或 `CAPABILITY_AUDIENCE_MISMATCH`。
- `auth.token` MUST 是有效能力凭证；`auth.cap_id` 用于索引。
- `body.schema` MUST 存在；Bus 不解析 `body.data`。
- `refs` 中的句柄 MUST 由发送方有权传递。
- `deadline` 是绝对墙钟时间；接收方 MUST 转换为单调时钟，过期后 MUST NOT 执行副作用。
- `priority` 只是调度提示，不构成实时保证；实现 MUST 防止低优先级任务饿死。
- `origin` 用于提示注入防护与信任判断。

### 7.2 Message types

| 类型 | 语义 | 幂等 |
|---|---|---|
| `hello` / `welcome` | 注册与版本协商 | 是 |
| `discover` | 查询能力 | 是 |
| `describe` | 获取能力/Agent 详情 | 是 |
| `request` | 调用能力/执行任务 | 是（按 `id`） |
| `result` | 成功结果 | — |
| `error` | 结构化错误 | — |
| `event` | 主题事件 | 否 |
| `stream.open` / `stream.chunk` / `stream.close` | 流 | 按序号 |
| `cancel` | 取消任务 | 是 |
| `delegate` | 委派子任务（创建子任务树） | 是 |
| `handoff` | 转移既有任务的所有权 | 是（按 `id`） |
| `status` | 进度/预算/心跳 | 否 |
| `consent.request` / `consent.grant` / `consent.deny` | 同意流程 | 是 |

`handoff` 是一次性消息：接收方 MUST 以 `result`（接受/拒绝）或 `error` 结束，不引入额外的确认往返。`handoff` 与 `delegate` 的区别见 §8.9。

### 7.3 Request/response

- `request` MUST 携带 `task.id`、`auth`、`deadline`。
- 接收方 MUST 在 `deadline` 前返回 `result`、`error` 或 `status`（表示仍在处理）。
- 调用方 MUST 使用 `id` 去重；接收方 SHOULD 缓存最近结果。
- 重试 MUST 使用相同 `id`，或使用新的 `id` + 幂等键扩展。
- `result` MUST 通过 `causation_id` 关联请求。
- `delegate` MUST 携带新子任务的 `task.id` 与 `task.parent`；`auth.cap_id` 对应能力的 `task_id` MUST 等于 `task.parent`。
- `handoff` MUST 携带既有任务的 `task.id`；`auth.cap_id` 对应能力的 `task_id` MUST 等于 `task.id`。

### 7.4 Events

- 事件主题使用 `event://<namespace>/<topic>`。
- 订阅需要 `cap://os/events/subscribe` 能力 + 主题过滤 + 数据范围。
- 默认投递语义：最多一次。
- 事件 MUST 携带 `origin` 与最小 payload；敏感内容通过 `refs`。
- 用户 MUST 能查看和撤销订阅。

### 7.5 Streams

- `stream.open` 携带 `stream_id`、`schema`、`total_estimate`（可选）。
- `stream.chunk` 携带 `stream_id`、`seq`、`data` 或 `ref`。
- `stream.close` 携带 `stream_id`、`status`、`summary`。
- 接收方 MUST 按 `seq` 去重/排序；缺失分片 SHOULD 请求重传。
- 取消 MUST 终止流并释放资源。

### 7.6 Cancel

- `cancel` MUST 携带 `task.id` 与原因。
- Bus MUST 沿任务树向下传播，除非子任务被显式标记为 `detached`。
- 接收方 MUST 尽快停止；无法停止时 MUST 返回 `CANCELLED` 或 `ERROR`。
- 取消 MUST 记录审计事件。

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
      "message": "需要用户确认发送外部消息",
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

标准错误码：

| 错误码 | 触发条件 | 可重试 |
|---|---|---|
| `TRANSPORT_HANDSHAKE_REQUIRED` | 连接尚未完成 `hello`/`welcome` | 否（先握手） |
| `TRANSPORT_VERSION_UNSUPPORTED` | `osap` 主版本不兼容 | 否 |
| `TRANSPORT_FRAME_TOO_LARGE` | 单帧/单消息超过 8 MiB | 否 |
| `TRANSPORT_CLOCK_SKEW` | 时间戳超出允许偏差 | 否 |
| `SCHEMA_UNSUPPORTED` | 未知消息类型或不支持的 `body.schema` | 否 |
| `SCHEMA_INVALID` | `body.data` 不符合声明 schema | 否 |
| `AUTH_DENIED` | 对端认证或签名校验失败 | 否 |
| `ROUTING_AMBIGUOUS` | `to.capability` 无法唯一解析 | 否 |
| `ROUTING_NOT_FOUND` | 目标 Agent 或能力不存在 | 否 |
| `CAPABILITY_AUDIENCE_MISMATCH` | `audience` 与接收方不一致 | 否 |
| `CAPABILITY_SUBJECT_MISMATCH` | `subject` 与信封 `from` 不一致 | 否 |
| `CAPABILITY_TASK_MISMATCH` | `task_id` 与信封 `task.id` 不一致 | 否 |
| `CAPABILITY_ATTENUATION_INVALID` | 子能力扩大范围、延长时限或违反 `max_depth` | 否 |
| `CAPABILITY_REVOKED` | 能力已撤销或过期 | 否 |
| `POLICY_DENIED` | 策略拒绝本次动作 | 否 |
| `POLICY_CONSENT_REQUIRED` | L3/L4 动作缺少有效同意回执 | 否（先征得同意） |
| `POLICY_CONSENT_EXPIRED` | 回执已过期或被撤销 | 否（重新同意） |
| `POLICY_CONSENT_SCOPE_MISMATCH` | 回执的 actions/resources/task/audience 未覆盖请求 | 否 |
| `TASK_BUDGET_EXCEEDED` | 预算耗尽 | 否 |
| `CONTEXT_DENIED` | 无权限解析句柄 | 否 |
| `CONTEXT_EXPIRED` | 句柄已过期 | 否（重新获取） |
| `CONTEXT_NOT_FOUND` | 句柄不存在 | 否 |
| `DUPLICATE` | 重复 `id`，且未缓存原结果 | 是（读取原结果） |
| `RATE_LIMIT` | 超过速率/配额 | 是（退避） |
| `TIMEOUT` | 超过 `deadline` | 视操作幂等性 |
| `CANCELLED` | 任务或流被取消 | 否 |
| `INTERNAL` | 实现内部错误 | 视情况 |

新增前缀 MUST 在 `AUTH_`、`POLICY_`、`CAPABILITY_`、`TASK_`、`SCHEMA_`、`CONTEXT_`、`ROUTING_`、`TRANSPORT_` 之内；领域错误 MAY 使用扩展命名空间。

### 7.8 Idempotency, deadlines, ordering

- 每个 `request` MUST 有唯一 `id`；接收方 MUST 对重复 `id` 返回相同结果或 `DUPLICATE`。
- `deadline` 是绝对墙钟时间；过期后不得执行副作用。
- 幂等索引 MUST 持久化或可重建，至少覆盖 `deadline` 之后的重试窗口；Bus 重启后不得因缓存丢失重复执行副作用。
- 重试 MUST 退避；非幂等副作用不得自动重试，除非业务 schema 声明幂等键。
- 同一 `session_id` 内的消息 SHOULD 保持因果顺序；Bus MAY 并行投递无依赖消息。
- 事件不保证顺序；需要顺序时使用 `stream` 或带 `seq` 的扩展。

### 7.9 Framing

- 流式传输（UDS、named pipe、localhost mTLS）MUST 使用 4 字节大端长度前缀 + UTF-8 JSON。
- 消息型传输（XPC、Binder、D-Bus）MUST 使用原生消息边界；MUST NOT 强制再套一层长度前缀。
- 单帧/单消息 MUST NOT 超过 8 MiB。
- 连接建立后 MUST 先交换 `hello` / `welcome`。
- 未知消息类型 MUST 返回 `SCHEMA_UNSUPPORTED`，不得静默丢弃。

### 7.10 Transport bindings

| 平台 | 推荐绑定 | 类型 | 对端认证 |
|---|---|---|---|
| Linux | Unix domain socket | stream | `SO_PEERCRED` + 可执行文件校验 |
| macOS | XPC / Mach service | message | audit token + code signature |
| Windows | named pipe | stream 或 message | client SID + package identity |
| Android | Binder | message | UID/PID + package signature |
| 跨沙箱/容器 | localhost mTLS | stream | 客户端证书 |

传输绑定 MUST 提供：双向认证、消息完整性、连接级隔离、对端身份可验证。仅提供明文回环 TCP 且无认证的绑定 MUST NOT 用于 L2 以上动作。

传输绑定 MUST 声明自己是 `stream` 还是 `message` 类型；分帧规则按类型选择。消息型绑定 MUST 保留发送方身份与消息边界。

### 7.11 Flow control and scheduling

- Bus MUST 实施 admission control：每 Agent 的连接数、在途请求数、队列长度与速率上限。
- 背压 MUST 使用显式信号：`RATE_LIMIT`、`status` 中的队列深度，或流式传输的 credit。
- 流式传输 SHOULD 使用 credit-based flow control；接收方 MUST 能暂停发送方。
- Bus MUST 按发送方隔离队列，避免一个 Agent 占满全局队列（head-of-line blocking）。
- `priority` 只是提示；实现 SHOULD 使用加权公平队列，并 MUST 防止低优先级任务永久饥饿。
- 调度 MUST NOT 提供硬实时保证；对时限敏感的任务应使用 `deadline` 与预算，而不是依赖优先级。

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
  "goal": "在下周三 9:00-12:00 中找到 60 分钟空档并创建 tentative 事件",
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

- 每个任务 MUST 有 `task_id` 与 `root_task_id`。
- `parent_task_id` 在层级委派中 MUST 存在；点对点任务 MAY 为空。
- Bus MUST 维护任务树索引，用于取消、预算与审计聚合。
- 任务树 MUST 持久化，恢复语义见 §3.7。
- 任务树深度 MUST 受 `max_depth` 限制；超过时 MUST 拒绝委派。
- 任务结束（成功/失败/取消）MUST 通知父任务与审计账本。

### 8.3 Supervisor mode

- `mode=supervisor` 时，`parent_task_id` MUST 存在。
- 子任务能力 MUST 由父任务能力衰减而来。
- 子任务预算 MUST ≤ 父任务剩余预算。
- 父任务取消 MUST 级联取消子任务。
- 子任务结果 MUST 通过 `result` 返回父任务，不自动共享中间上下文。

### 8.4 Peer mode

- `mode=peer` 时，双方是平等参与者；`session_id` MUST 存在。
- 每方 MUST 持有独立能力；一方不能凭会话身份获得另一方的权限。
- 点对点消息 MUST 仍然携带 `auth`；`audience` 与 `subject` 绑定。
- 一方请求另一方执行动作时，使用 `request`；需要新建子任务时使用 `delegate`。
- Peer 不能命令对方提升权限；任何提权 MUST 经过 PCS 与用户同意。
- Session 结束 MUST 清理临时上下文与未完成任务。

### 8.5 Delegation

`delegate` 消息 MUST 包含：

1. 子任务目标与输入引用；
2. 衰减后的能力凭证；
3. 预算（时间、调用次数、金额、深度）；
4. 截止时间（`deadline`，MUST）与优先级（`priority`，MAY）；
5. 结果契约（`result_schema`）。

规则：

- 委派者 MUST 持有 `can_delegate=true` 的能力。
- 子能力 MUST 满足 §5.3 的全部衰减条件。
- 委派者 MUST NOT 把自己的凭证原样传给子 Agent。
- 子 Agent MUST 校验凭证链、预算与深度。
- 委派失败 MUST 返回结构化错误，不得静默降级。

### 8.6 Budgets

| 维度 | 说明 |
|---|---|
| `wall_ms` | 墙钟时间 |
| `tool_calls` | 工具/外部调用次数 |
| `tokens` | 模型 token 预算 |
| `money` | 金额与币种 |
| `depth` | 剩余委派深度 |

- 预算 MUST 单调递减。
- 超预算 MUST 停止执行并返回 `TASK_BUDGET_EXCEEDED`。
- 预算消耗 SHOULD 通过 `status` 上报。
- Bus MAY 在预算耗尽时强制取消任务。

### 8.7 Cancellation

- `cancel` 沿任务树向下传播。
- 标记 `detached=true` 的子任务 MAY 继续运行，但 MUST 失去父任务能力。
- 取消 MUST 释放上下文句柄、流与临时对象。
- 已产生的副作用 MUST 记录审计；不可逆副作用 MUST 在同意时明确提示。

### 8.8 Results

- 结果 MUST 携带 `result_schema` 与 `output_refs`。
- 大结果 MUST 通过 `obj://` 引用。
- 父任务 MUST 校验结果 schema；不匹配时返回 `SCHEMA_INVALID`。
- 结果 MAY 包含 `confidence`、`cost`、`warnings` 等扩展字段。
- 结果聚合 MUST NOT 自动合并子 Agent 的全部上下文。

### 8.9 Handoff

`handoff` 与 `delegate` 的区别：`delegate` **创建**子任务并新增任务树节点；`handoff` **转移既有任务**的所有权，不创建新任务、不改变 `mode`。

- `handoff` 是一次性消息；接收方 MUST 以 `result`（接受或拒绝）或 `error` 结束，MUST NOT 引入额外的确认类型。
- 发送方 MUST 是当前 `owner`，且 MUST 持有允许转移的能力；接收方 MUST 校验 `subject`、`audience` 与 `task_id` 绑定。
- 原 owner MUST 明确放弃控制权；新 owner MUST 获得**新的**能力凭证（旧凭证不得原样转发，按 §5.4 衰减/重签）。
- 接收方拒绝或超时时，任务 MUST 留在原 owner，状态与预算不变。
- Handoff 涉及 L3/L4 动作时 MUST 重新征得用户同意，且回执的 `audience` MUST 指向新 owner。
- Handoff MUST 记录 `task.handoff` 审计事件，包含原 owner、新 owner、`cap_id` 与 `consent_receipt_id`（如有）。
- 任务状态机不新增 `handoff_pending`；所有权变更不改变任务状态。

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

状态转换 MUST 由 Bus 记录；非法转换 MUST 被拒绝。

Bus 重启后，非终态任务 MUST 转为 `failed` 或按策略重新调度；不得静默保持 `running`。恢复 MUST 记录审计事件。

### 8.11 Recovery and reconciliation

- 任务记录、预算消耗与结果引用 MUST 持久化；恢复后 MUST 能判断任务是否已产生副作用。
- 对不可逆副作用，执行前 MUST 写入 `effect.intent` 审计；恢复时若只有 intent 没有 outcome，MUST 标记为 `unknown` 并要求对账。
- 自动重试只允许幂等操作；重试 MUST 使用相同 `id` 或显式幂等键。
- 被中断的任务 MUST 通知父任务与用户；`detached` 任务 MUST 明确其独立生命周期。
- 对账结果 MUST 写回任务状态与审计；不得用“重放”代替对账。

---

## 9. Context Fabric

CF 的定位是**授权代理与句柄解析层**，不是新的文件系统。默认实现 MUST 复用 OS 已有的文件描述符、security-scoped bookmark、content URI、portal 或等价机制；独立对象存储是可选实现，且必须满足 §9.10 的存储责任。

### 9.1 Handle schemes

| Scheme | 示例 | 说明 |
|---|---|---|
| `ctx://` | `ctx://user/profile#display_name` | 用户/会话/设备上下文 |
| `obj://` | `obj://sha256:9f2c...` | 内容寻址对象；无独立存储时映射到 OS 内容服务 |
| `task://` | `task://task_01J/blackboard/plan` | 任务级黑板 |
| `file://` | `file://fh_01J...` | 不透明文件句柄；映射到 OS 句柄 |
| `contact://` | `contact://directory/example-contact` | 目录服务解析 |
| `event://` | `event://os/user/activity` | 事件主题 |

- `file://` MUST NOT 暴露原始绝对路径；使用不透明句柄。
- 句柄 MUST 可撤销、可过期、可审计。
- 句柄本身 MAY 被传递；解析权限由能力决定。

### 9.2 Resolution

- Agent 解析句柄 MUST 持有包含 `resolve` 动作且覆盖该资源的 capability。
- CF MUST 校验 `audience`、`task_id`、`subject`、`exp`、信息流标签。
- 解析结果 MAY 是数据或另一个句柄。
- 每次解析 MUST 记录 `context.resolve` 审计事件，包含调用者、句柄、标签、决策。
- 解析失败 MUST 返回 `CONTEXT_DENIED` 或 `CONTEXT_NOT_FOUND`，不得泄漏存在性以外的信息。

### 9.3 Scopes and TTL

| Scope | 生命周期 |
|---|---|
| `task` | 任务结束即失效 |
| `session` | 会话结束即失效 |
| `user` | 用户撤销或过期 |
| `device` | 设备策略控制 |

- 句柄 MUST 有 `ttl` 或 `expires_at`。
- 过期句柄 MUST 被拒绝；不得自动续期。
- 长期记忆 MUST 单独授权，用户可见、可删除。

长期记忆不属于 Bus，也不属于任何任务句柄的默认用途：

- 写入长期记忆 MUST 由显式能力授权（如 `memory.write`），并记录用途、来源与保留期限。
- 读取长期记忆 MUST 单独授权，不得因持有任务能力而隐含获得。
- 长期记忆 MUST 可按用户/App/条目粒度删除；删除 MUST 触发派生索引失效。
- 任务黑板、对象元数据与 Bus 持久状态 MUST NOT 自动晋升为长期记忆（见 §3.7、§9.5）。
- 0.1 不定义记忆服务的 wire format；实现若提供，MUST 作为普通能力注册，并声明数据范围与同意模式。

### 9.4 Information-flow labels

每个句柄/对象 MUST 带标签：

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

标签等级：`public` < `personal` < `sensitive` < `secret`。

规则：

- 派生对象 MUST 继承不低于其来源的标签。
- `secret` 对象 MUST NOT 离开本设备，除非用户显式放行。
- 外部内容 MUST 标记 `origin.kind=external`，默认 `trust=unverified`。
- 标签冲突时 MUST 取更严格的值。

### 9.5 Task blackboard

- `task://<task_id>/blackboard` 是任务参与者共享的受控键值区。
- 读写 MUST 需要能力；写操作 MUST 记录审计。
- 黑板生命周期 = 任务生命周期；任务结束 MUST 清理或按策略归档。
- 黑板 MUST NOT 自动升级为长期记忆。
- 并发写 SHOULD 使用版本号或 CAS 避免覆盖。

### 9.6 Object store

- 若实现独立对象存储，`obj://` MUST 使用内容寻址（如 SHA-256）。
- 对象写入 MUST 记录所有者、标签、创建者、引用计数。
- 对象读取 MUST 经过 CF 策略；不得通过路径遍历绕过。
- 对象删除 MUST 检查引用；被引用对象 SHOULD 延迟删除或标记墓碑。
- 对象 MAY 加密存储；密钥由 OS 密钥库管理。
- 若不自建对象存储，CF MUST 把 `obj://` 映射到 OS 内容服务，并保留标签与 TTL 语义。

### 9.7 Revocation and deletion

- 撤销句柄 MUST 使其所有派生句柄失效。
- 删除对象 MUST 触发引用清理与审计事件。
- 用户 MUST 能查看“谁在何时解析了哪个句柄”。
- 被撤销的句柄 MUST 在缓存中失效；缓存 TTL 不得超过句柄 TTL。
- 撤销 SHOULD 尽量映射到 OS 句柄撤销；无法撤销时 MUST 通过 TTL 与拒绝解析兜底。

### 9.8 Egress

- 任何离开本设备的数据 MUST 经过 egress 策略。
- `sensitive`/`secret` 数据出口 MUST 需要用户一次性放行或明确授权。
- 出口事件 MUST 记录目标、数据标签、同意回执。
- Bridge 到外部协议（A2A/HTTP/MCP 远程）MUST 保留来源与标签。

### 9.9 Relationship to OS primitives

CF MUST 优先复用 OS 原语，而不是复制其语义：

| OSAP 句柄 | 默认映射 | 说明 |
|---|---|---|
| `file://` | fd / security-scoped bookmark / content URI / portal | 不暴露绝对路径；权限由 OS 与 CF 双重校验 |
| `contact://` | OS 联系人 provider | 只返回解析结果，不缓存明文 |
| `ctx://` | OS 会话/用户上下文服务 | 只读快照，带来源与 TTL |
| `task://` | Bus/CF 任务元数据 | 任务结束清理 |
| `obj://` | OS 内容服务或可选 CAS | 若自建 CAS，见 §9.10 |

- 若平台没有对应原语，CF MAY 提供最小替代实现，但 MUST 在一致性声明中标注 `cf_mode: "managed_store"`。
- CF MUST NOT 通过句柄绕过 OS 沙箱或文件权限。

### 9.10 Storage responsibilities

若实现独立对象存储（`cf_mode: "managed_store"`），MUST 定义并实现：

- 配额与准入：每用户/每 App 的对象数量与字节上限；
- 垃圾回收：引用计数、墓碑、孤儿扫描与保留期；
- 崩溃恢复：写入原子性、元数据与内容的一致性、重启后的孤儿处理；
- 加密：静态加密与密钥轮换，密钥由 OS 密钥库管理；
- 路径与句柄安全：禁止路径遍历、符号链接逃逸与句柄猜测；
- 删除与撤销：引用检查、派生句柄失效、审计事件。

未实现上述责任时，CF MUST 只做授权代理，并把 `obj://` 映射到 OS 内容服务；MUST NOT 声称提供独立对象存储。

---

## 10. Consent and Audit

### 10.1 Risk tiers

见 §5.7。PCS MUST 根据能力记录、数据标签、目标与上下文计算最终风险；可以提升，不能降低。

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
      "summary": "向示例联系人发送一条会议纪要消息",
      "intent_preview": {
        "actor": "Orchestrator Agent",
        "what": "发送 1 条消息",
        "data": ["会议纪要（引用）", "联系人：示例联系人"],
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

- `consent.grant` MUST 返回 `receipt_id`、`cap_id`、`expires_at`、`constraints`。
- `consent.deny` MUST 返回原因码与可选替代方案。
- 同意 MUST 绑定：用户、Agent、任务、动作、资源、`audience`、风险、TTL。
- 批量/任务级同意 MUST 明确范围；不得隐式扩展到其他任务。
- 用户撤销 MUST 立即生效，并级联失效相关能力。

**Issuance ordering.** 能力需要 `consent_receipt_id`，回执需要 `cap_id`。为避免循环依赖，MUST 按以下顺序：

1. 接收方（经 PCS）评估动作，判定需要同意；
2. CA **预约** `cap_id`（分配标识，不签名、不可用）；
3. 用户/OS 签发回执，引用该预约的 `cap_id` 与目标 `audience`；
4. CA 校验回执后签发能力，写入 `consent_receipt_id` 并激活；
5. 回执被拒绝、过期或撤销时，预约的 `cap_id` MUST NOT 进入可用状态。

未激活的预约 `cap_id` MUST NOT 通过任何路由校验。

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

回执 MUST 由用户/OS 签名；Agent 不能自行签发。回执 MUST 可被审计方离线验证。

### 10.5 Audit events

每个审计事件至少包含：

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

必须记录的事件类型：

`agent.registered`、`agent.registration_denied`、`capability.issued`、`capability.attenuated`、`capability.attenuation_denied`、`capability.exercised`、`capability.revoked`、`discovery.query`、`discovery.result`、`message.sent`、`message.delivered`、`task.created`、`task.delegated`、`task.handoff`、`task.cancelled`、`task.completed`、`task.failed`、`context.resolve`、`context.denied`、`consent.requested`、`consent.granted`、`consent.denied`、`effect.intent`、`effect.executed`、`effect.reconciled`、`egress.blocked`、`error`。

`phase` 只用于 `effect.*` 事件：`effect.intent` MUST 带 `phase=intent`，`effect.executed` MUST 带 `phase=outcome`；其他事件 MUST NOT 带 `phase`。

L3/L4 副作用 MUST 采用两段审计：

1. 执行前写入 `effect.intent`（`phase=intent`），包含目标、参数摘要、同意回执与幂等键；
2. 执行后写入 `effect.executed`（`phase=outcome`），引用 `intent_ref`。

只有 intent 没有 outcome 时，恢复 MUST 标记 `unknown` 并要求对账（见 §8.11）。

### 10.6 Trace

- 一次用户意图 MUST 有一个 `trace_id`。
- 每次 Agent 跳转 MUST 记录 `causation_id`。
- 用户 MUST 能按 `trace_id` 查看跨 App 协作链。
- 审计导出 MUST 保留 `hash`/`prev_hash` 与链完整性；敏感字段 MAY 用每次导出唯一的盐值承诺替换。
- 脱敏后的导出只能证明“链未被篡改 + 字段承诺一致”，不能恢复明文；验证方 MUST 知道这一限制。
- 回放 MUST 受权限约束，不得重新执行副作用。

### 10.7 Revocation

- 用户撤销同意回执 → 关联能力失效 → 任务收到 `CAPABILITY_REVOKED`。
- 撤销 MUST 级联到子能力、子任务、会话。
- 撤销事件 MUST 写入审计，并通知所有受影响 Agent。
- 已发生的不可逆副作用不能“撤销”，但 MUST 在审计中标注。

### 10.8 User visibility

用户 MUST 能查看：

- 哪些 Agent 正在运行；
- 每个 Agent 持有哪些能力；
- 谁在监听哪些事件；
- 过去 24 小时/7 天的跨 App 调用与数据解析；
- 如何撤销某个能力/回执/会话。

---

## 11. Security Considerations

### 11.1 Threat model

| 威胁 | 场景 | 对策 |
|---|---|---|
| Identity spoofing | 恶意 App 自称系统 Agent | 对端凭据 + 代码签名 + 保留命名空间 |
| Confused deputy | 低权限 Agent 借高权限 Agent 做事 | audience + task 绑定；禁止转发 |
| Prompt injection | 消息内容藏指令 | origin/trust 标签；指令与数据分离；动作闸门 |
| Data exfiltration | 子 Agent 把数据发给外部 | 句柄标签 + egress 策略 + 用户放行 |
| Replay | 重放合法消息 | nonce + exp + max_uses + task 绑定 |
| DoS | 大量请求拖垮 Bus/目标 App | 配额、速率、背压、预算 |
| Supply chain | 恶意 App/依赖 | 签名、清单审查、能力白名单 |
| Audit tampering | 删除不利记录 | 只追加 + 哈希链 + 外部锚点 |
| Compromised Bus | Bus 被攻破或恶意 | 0.1 显式信任 P0；OS 完整性、最小 TCB、payload 不落盘；P1 见 §3.6 |
| Clock manipulation | 墙钟被调整或挂起/恢复 | 单调时钟、偏差检查、短 TTL |
| State rollback | 崩溃/回滚导致重复或丢失 | 持久化 + 锚定 + 幂等 + 对账 |
| Privilege escalation | 子 Agent 扩大能力 | 单调衰减 + CA 校验 + 深度限制 |
| Cross-user leakage | 多用户共享设备 | 每用户 Bus；默认禁止跨用户 |

### 11.2 Identity spoofing

- Bus MUST 在连接时验证对端进程身份，并把它绑定到 `app://`。
- Agent ID MUST 由 Bus 在注册时分配/确认，不能仅凭 `hello` 自称。
- `agent://` 是本地命名，不是自认证标识；Bus MUST 维护名称到 `(app, public_key, session)` 的绑定。
- `hello.public_key` MUST 与 App 清单或 OS 密钥库绑定；Bus MUST 校验私钥占有证明。
- `agent://system/...` 与 `cap://os/...` 保留；第三方注册 MUST 失败。
- 代码签名/包身份变化 MUST 触发重新注册与能力复核。

### 11.3 Confused deputy

- 能力 MUST 同时绑定 `audience` 与 `task_id`。
- Agent MUST NOT 把收到的 token 原样转发；只能衰减后签发新 token。
- Bus MUST 在路由前校验 `subject == from` 与 `audience`，拒绝 token 借用；撤销与 `max_uses` 计数 MUST 由接收方复核。
- 高风险动作 MUST 在 PCS 重新求值，不能仅凭 token 放行。

### 11.4 Prompt injection

OSAP 不试图检测所有恶意文本，而是做三件事：

1. **来源标注**：每条消息/句柄携带 `origin.kind`、`trust`、`derived_from`；
2. **指令/数据分离**：`body.data` 永远是数据，不能改变 Agent 的系统策略；Agent SHOULD 把外部内容视为不可信输入；
3. **动作闸门**：L2+ 动作必须经过 PCS；L3/L4 必须有人类同意回执。

补充要求：

- 外部内容 MUST 标记 `origin.kind=external`。
- 来自邮件/网页/文档的内容 MUST NOT 直接作为系统指令。
- 高风险动作的 `intent_preview` MUST 展示数据来源与目标。
- Agent 被注入后仍不能静默产生外部副作用；这是协议层的最低保证。

### 11.5 Data exfiltration

- 默认传引用；原始数据不进入消息体。
- 句柄解析受能力、标签、audience 约束。
- `sensitive`/`secret` 出口需要用户放行。
- Bridge 到外部协议 MUST 保留标签并执行 egress 策略。
- 审计 MUST 记录每次解析与出口。

### 11.6 Replay

- 能力 MUST 有 `exp`；高价值动作 SHOULD 使用 `max_uses=1` 或 nonce。
- 消息 `id` 用于幂等；重复消息不得重复执行副作用。
- Bus MUST 拒绝过期 `deadline` 的请求。
- 跨任务复用 token MUST 失败。

### 11.7 DoS

- Bus MUST 实施 admission control、每 Agent 配额、在途请求上限与队列隔离。
- 请求 MUST 有 `deadline` 与预算。
- 大对象 MUST 走引用；控制消息有大小上限。
- 背压 MUST 使用显式信号；流式传输 SHOULD 使用 credit-based flow control。
- 背压时 MUST 返回 `RATE_LIMIT` 或让发送方等待，不得无限排队。
- `priority` 不得导致饥饿；实现 SHOULD 使用加权公平调度。
- 任务树深度与子任务数量 MUST 有上限。

### 11.8 Supply chain

- App 清单 MUST 签名；RFS MUST 验证。
- Bridge 适配器 MUST 由可信来源提供，并标记版本。
- 原生注册表的能力映射 MUST 可审计；不得静默扩大权限。
- 依赖/插件升级 SHOULD 触发能力复核。

### 11.9 Audit integrity

- 审计日志 MUST 只追加，MUST 单写者；多实例部署 MUST 按用户分区或使用 leader election。
- 每条事件 MUST 包含 `prev_hash` 与 `hash`；`prev_hash` MUST 来自持久化链头。
- 重启后 MUST 校验链头与最近事件；校验失败时 L3/L4 MUST fail closed 并告警。
- 高价值场景 SHOULD 定期把链头锚定到 OS 完整性保护或外部透明日志。
- 审计不可写时，L3/L4 的 **intent** 审计 MUST 失败关闭；已执行副作用的 outcome 审计失败 MUST 重试并告警，不得回滚已发生的外部副作用。
- 用户删除数据 MUST 记录删除事件；审计事件本身可脱敏但不能删除。

### 11.10 Cross-user isolation

- 默认每个用户会话一个 Bus；跨用户通信 MUST 显式启用并经过双方同意。
- 共享设备上的 Agent MUST 绑定到登录用户。
- 多用户会话（家庭屏、协作空间）属于后续版本；当前版本 MUST 默认拒绝。

### 11.11 Privacy

- 数据最小化：只请求完成任务所需的最小范围。
- 目的绑定：能力/回执 MUST 记录用途，不得二次利用。
- 保留期限：句柄、对象、审计按策略过期。
- 用户访问：用户 MUST 能查看、导出、撤销、删除自己的数据。
- 脱敏：审计导出默认脱敏；原始数据需额外授权。
- Bus MUST NOT 默认持久化 payload；日志、错误消息与崩溃转储 MUST 脱敏。

---

## 12. Conformance

### 12.1 Conformance levels

| 等级 | 名称 | 必须实现 |
|---|---|---|
| C0 | Transport | 分帧、连接、`hello`/`welcome`、错误、传输类型声明 |
| C1 | Identity | 对端认证、Agent 注册、保留命名空间、公钥绑定 |
| C2 | Registry | 清单、能力记录、发现、静态 `consent_hint` |
| C3 | Authorization | 能力 token、衰减、绑定、撤销、同意回执 |
| C4 | Collaboration | 任务、委派、handoff、peer、预算、取消、结果、恢复 |
| C5 | Context | 句柄、解析、标签、黑板、OS 句柄映射（可选对象存储）、记忆授权 |
| C6 | Federation | App Intents/AppFunctions/App Actions/MCP/A2A/D-Bus 适配 |
| C7 | Full | C0–C6 + 审计/可观测性/多用户扩展 |

实现 MAY 声明支持子集，但 MUST 明确声明等级与可选特性：

- `bus_visibility`：0.1 仅 `payload`；
- `transport_kind`：数组，取值 `stream` / `message`；实现 MUST 声明其支持的传输类型；
- `state_recovery`：`durable` / `best_effort`；C4+ MUST 为 `durable`；
- `cf_mode`：`os_handles` / `managed_store`。

### 12.2 Required behaviors

- C0+ MUST 按传输类型选择分帧；消息型传输 MUST NOT 强制长度前缀。
- C2+ MUST 在发现结果中返回静态 `consent_hint`，MUST NOT 返回实时 `policy_verdict`。
- C3+ MUST 拒绝 audience/task/subject 不匹配的 token。
- C3+ MUST 拒绝非子集衰减。
- C3+ MUST 对 L3/L4 动作要求有效回执。
- C3+ MUST 使用单调时钟处理 `deadline`，并在挂起/恢复后重新检查。
- C4+ MUST 传播取消并执行预算。
- C4+ MUST 把 `handoff` 当作一次性所有权转移：接收方以 `result`/`error` 结束，拒绝或超时时任务保持原 owner。
- C4+ MUST 持久化任务状态；重启后未完成任务 MUST 转为 `failed` 或显式重新调度。
- C5+ MUST 对每次句柄解析记录审计。
- C5+ MUST 声明 `cf_mode`；独立对象存储 MUST 满足 §9.10。
- C6+ MUST 保留 `source` 与 `provenance`。

### 12.3 Test cases

规范性测试集以 [`conformance.md`](conformance.md) 为唯一来源；编号 `C<level>-<nn>`。本节只列代表性检查，便于实现者快速自测：

| 检查 | 对应测试 |
|---|---|
| 未注册 Agent 连接 | C1-01 |
| 伪造 `audience` 的 token | C3-01 |
| 跨任务复用 token | C3-02 |
| 子能力扩大范围或延长时限 | C3-04 / C3-06 |
| 撤销父能力后使用子能力 | C3-08 |
| L3 动作无回执 / 回执过期 | C3-09 / C3-10 |
| 取消父任务 | C4-01 |
| 预算耗尽 | C4-07 |
| 未授权句柄解析 | C5-01 |
| `secret` 对象出口 | C5-04 |
| 审计链篡改 | C7-02 |
| 幂等索引被用作记忆检索 | C5-11 |

新增测试 MUST 先进入 `conformance.md`；本表不单独维护编号。

### 12.4 Interop

- 实现 SHOULD 提供 `osap-conformance` 测试工具或报告。
- 互操作测试 SHOULD 覆盖至少两个不同 App、一个系统 Agent、一个 Bridge。
- 通过 C7 的实现 MAY 申请登记为参考实现（登记流程另行定义）。

---

## 13. Versioning and Extensibility

### 13.1 Version negotiation

- 信封 `osap` 字段使用 `major.minor`。
- 主版本不兼容；次版本向后兼容。
- `hello`/`welcome` MUST 交换支持版本与特性列表。
- 双方无共同主版本时 MUST 拒绝连接。
- schema 校验 MUST 只强制主版本；次版本 MUST 被接受。实现 MUST NOT 因次版本号更高而拒绝消息，除非缺少必需特性。

### 13.2 Schema identifiers

- 业务 schema 使用 `osap.<domain>.<type>/v<major>`。
- 次版本变更 MUST 保持向后兼容；破坏性变更 MUST 提升 major。
- schema MUST 可解析、可验证；SHOULD 提供 JSON Schema。

### 13.3 Extensions

- 扩展字段 MUST 放在顶层 `extensions` 对象中；`extensions` MUST 参与签名规范化。
- 未知顶层字段 MUST 被拒绝；`body.data` 是开放对象，由业务 schema 约束。
- 扩展不得改变核心授权语义。
- 扩展 SHOULD 有命名空间，避免冲突。
- 标准化后的扩展 SHOULD 进入正式 schema。

### 13.4 Deprecation

- 弃用字段 MUST 至少保留一个次版本周期。
- 弃用 MUST 在 changelog 与 schema 中标注。
- 移除破坏性字段 MUST 提升主版本。

### 13.5 Schema compatibility

- schema 的版本字段 MUST 使用模式匹配主版本（如 `^0\.[0-9]+$`），不得使用精确常量。
- 新增可选字段属于 minor；删除或改变语义属于 major。
- 兼容性测试 MUST 覆盖“旧实现接收新 minor 消息”。

---

## 14. Registration and Governance

### 14.1 Schema registry

- 核心 schema 由标准维护方登记。
- 领域 schema 由社区/厂商登记，需提供维护者、版本、验证规则。
- 冲突命名 MUST 使用反向域名前缀。

### 14.2 Capability namespaces

- `cap://os/...` 保留给核心域（日历、联系人、文件、消息、通知等）。
- `cap://<vendor-domain>/...` 用于厂商扩展。
- 注册能力 MUST 提供：名称、动作、资源、schema、风险、成本、同意模式。

### 14.3 Event topics

- `event://os/...` 保留给系统事件。
- `event://app.<app-id>/...` 用于 App 事件。
- 订阅 MUST 声明过滤器与数据范围。

### 14.4 Change process

建议的开放标准流程：

1. 提案（issue / proposal）；
2. 参考实现与互操作报告；
3. 安全与隐私评审；
4. 粗略共识（rough consensus）；
5. 版本发布与变更日志；
6. 与 IETF `agentproto`、OAuth WIMSE、AAIF/LF 等标准组织联络。

治理细则见 [`GOVERNANCE.md`](../GOVERNANCE.md)。

---

## 15. Open Issues

1. Bus 的所有权：OS 厂商、桌面环境、运行时，还是独立守护进程？
2. 无 Agent 的旧应用：UI 自动化桥接，还是要求轻量适配器？
3. 跨设备/跨组织：如何与 A2A、WIMSE、SPIFFE 对齐信任根？
4. 多用户共享会话：主体切换与数据边界。
5. 同意疲劳：任务级授权与细粒度撤销的平衡。
6. 语义发现：如何在结构化能力匹配之外引入 embedding，同时避免隐私泄漏。
7. 提示注入责任：协议闸门、App 内容防护、模型层防护的责任划分。
8. 性能：每次解析都过策略的开销；本地策略缓存与短期租约。
9. 厂商采用：如何让 App Intents/AppFunctions/App Actions 的适配器进入官方 SDK。
10. 标准归属：独立基金会、LF/AAIF、IETF，还是厂商联盟？
11. Bus 不可见 payload 的 P1 profile：HPKE wire format、密钥发现与前向保密。
12. 崩溃恢复与副作用对账的形式化模型（intent/outcome、unknown 状态）。
13. Context Fabric 与 OS 句柄/portals 的标准化映射。
14. 多实例 Bus 的 leader election 与审计链分区。

---

## Appendix A: Examples

完整示例见 [`examples/`](../examples/)：

- `manifest.json` — App 清单
- `capability.json` — 能力凭证
- `capability-record.json` — 联邦能力记录
- `task.json` — 任务对象
- `discovery-request.json` / `discovery-result.json` — 发现
- `request.json` / `result.json` — 请求/结果
- `delegate.json` — 委派
- `consent-receipt.json` — 同意回执
- `audit-event.json` — 审计事件

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

见 [`prior-art.md`](prior-art.md)，包括 MCP、A2A、ACP、AGNTCY、App Intents、AppFunctions、App Actions、AgenticOS、AgentKernel、Agent libOS、AOS、AgentCap、CAPMAS、tenuo、AAP、DAAP、DRP、APS、WIMSE、D-Bus、XPC、Binder 等。

## Appendix E: JSON Schema Index

| Schema | 文件 |
|---|---|
| Envelope | [`../schemas/envelope.schema.json`](../schemas/envelope.schema.json) |
| Capability | [`../schemas/capability.schema.json`](../schemas/capability.schema.json) |
| Task | [`../schemas/task.schema.json`](../schemas/task.schema.json) |
| Manifest | [`../schemas/manifest.schema.json`](../schemas/manifest.schema.json) |
| Capability Record | [`../schemas/capability-record.schema.json`](../schemas/capability-record.schema.json) |
| Consent Receipt | [`../schemas/consent-receipt.schema.json`](../schemas/consent-receipt.schema.json) |
| Audit Event | [`../schemas/audit-event.schema.json`](../schemas/audit-event.schema.json) |

所有 schema 的版本字段使用主版本模式匹配（如 `^0\.[0-9]+$`），不得使用精确常量；扩展字段统一放在顶层 `extensions`，并参与签名规范化。

---

*本草案以“可实现、可测试、可联邦”为目标。欢迎针对第 15 节开放问题提交提案与参考实现。*
