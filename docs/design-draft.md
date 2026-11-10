# OSAP：开放系统 Agent 协议（总体设计草案）

> 工作名称：**OSAP**（Open System Agent Protocol）
> 运行时组件：**Agent Bus**
> 文档状态：非规范性设计说明（Non-normative）· 2026-11-10
> 定位：跨平台概念优先，不绑定具体 OS 原语；落地时可映射到 D-Bus / XPC / Binder / named pipe。
>
> 规范性文本见 [`standard.md`](standard.md)。本文保留作为设计动机与架构取舍的背景材料。
> 注：Bus/服务拆分、信任 profile、状态恢复与传输语义以 `standard.md` §3.6–§3.7、§7、§9 为准。

---

## 1. 背景：App 是孤岛，Agent 是新的连接层

今天的应用彼此隔离：每个 App 有自己的数据、账号、界面和权限模型。用户想完成一件跨应用的事（"把会议纪要整理后发给示例联系人，并约下周三上午开会"），只能自己在多个 App 之间复制粘贴、切换上下文。

大模型 Agent 让"跨应用编排"第一次变得可行，但当前生态存在三个结构性缺口：

1. **Agent 之间没有本地公共通道**。MCP 解决 Agent→工具，A2A 解决远程 Agent↔Agent，但同一台机器上两个 App 的 Agent 如何发现彼此、如何安全地交换数据，没有操作系统级答案。
2. **权限模型仍以 App 为中心**。用户授权的是"某个 App 能访问通讯录"，而不是"这次任务中，这个 Agent 能读取示例联系人这一条记录，用于发消息"。
3. **上下文无法流动**。每个 Agent 都在重复收集用户是谁、正在做什么、数据在哪里，既低效又放大隐私风险。

**OSAP 的核心主张**：操作系统提供一个中立的 **Agent Bus**，让 App 内的 Agent 以"能力"而非"接口"互相发现和调用；所有跨应用行为都经过身份认证、能力授权、用户同意与审计；数据默认以引用方式流转，而不是被复制。

---

## 2. 设计目标与非目标

### 2.1 目标

| 编号 | 目标 | 说明 |
|---|---|---|
| G1 | 跨 App 发现 | Agent 能声明并发现彼此的能力、事件与数据范围 |
| G2 | 结构化通信 | 统一的消息信封、任务语义、流式与事件模型 |
| G3 | 最小权限 | 无环境权限（no ambient authority），权限只能沿委派链收窄 |
| G4 | 人类可控 | 分级同意、意图预览、随时撤销、全链路审计 |
| G5 | 数据不出域 | 默认传递引用/句柄，数据由持有方按策略解析 |
| G6 | 主子 Agent 原生支持 | 任务树、预算、取消传播、结果聚合 |
| G7 | 生态互操作 | 能桥接 MCP / A2A / OpenAPI / 传统 IPC |
| G8 | 可演进 | 协议内核小，语义通过命名空间与 schema 扩展 |

### 2.2 非目标

- 不规定 Agent 的内部推理、模型选择或提示词格式。
- 不替代 MCP（工具调用）或 A2A（跨网络 Agent 协作），而是做**本地底座**并与它们互操作。
- 不要求所有 App 重写；提供 SDK、桥接器与"无 Agent 应用"的自动化适配层。
- 不定义具体的 UI；同意界面由 OS/桌面环境实现，协议只定义交互原语。

---

## 3. 设计原则

1. **能力而非接口（Capability, not endpoint）**
   调用方不直接寻址某个 App 的内部 API，而是持有一个可验证的能力凭证，声明"我能对哪类资源做什么"。

2. **引用而非复制（Reference, not payload）**
   消息里传 `obj://`、`ctx://` 句柄；接收方在真正使用时才按策略解析，减少数据扩散面。

3. **权限只能收窄（Attenuation only）**
   父 Agent 委派任务给子 Agent 时，必须签发**子集能力**；子 Agent 永远不能获得超过父级的权限。

4. **意图可解释（Intent preview）**
   任何有外部副作用或涉及敏感数据的动作，都要能生成人类可读的"谁、要做什么、用哪些数据、花多少成本"预览。

5. **默认审计（Auditable by default）**
   跨 Agent 的每次发现、调用、授权、数据解析都产生不可篡改的事件记录。

6. **协议内核最小化（Small core）**
   只标准化信封、身份、能力、任务、错误和传输绑定；业务语义放在命名空间 schema 中。

7. **失败安全（Fail closed）**
   策略不可判定、凭证过期、审计不可写时，默认拒绝而不是放行。

---

## 4. 总体架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                         用户 / 桌面 Shell / 系统 Agent               │
│                  （意图输入、同意 UI、活动中心、审计查看）             │
└───────────────▲─────────────────────────────────────▲───────────────┘
                │ 意图 / 同意决策                       │ 状态 / 通知
┌───────────────┴─────────────────────────────────────┴───────────────┐
│                         Agent Bus（每用户会话）                      │
│                                                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────┐ │
│  │ Registry │  │ Policy & │  │  Router  │  │ Context  │  │ Audit │ │
│  │ 发现/清单 │  │ Consent  │  │ 消息/任务 │  │ Fabric   │  │ 日志  │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └───────┘ │
│                                                                     │
│  ┌──────────────────────── 桥接层 ────────────────────────────────┐  │
│  │  MCP Bridge │ A2A Bridge │ OpenAPI/HTTP │ D-Bus/XPC/Binder   │  │
│  └───────────────────────────────────────────────────────────────┘  │
└───────▲──────────────────────▲──────────────────────▲───────────────┘
        │ 本地 IPC（UDS / named pipe / Binder / XPC）  │
┌───────┴────────┐    ┌────────┴───────┐    ┌─────────┴──────────┐
│ Notes.app      │    │ Calendar.app   │    │ Messaging.app      │
│ └ Agent(notes) │    │ └ Agent(cal)   │    │ └ Agent(msg)       │
│   └ SDK        │    │   └ SDK        │    │   └ SDK            │
└────────────────┘    └────────────────┘    └────────────────────┘
```

> 图注：图中 Registry、Policy & Consent、Context Fabric、Audit 在规范中 MUST 作为独立进程或沙箱运行，不得与路由内核共享地址空间。**Agent Bus** 仅指 **Bus Core**（对端认证、信封校验、路由、连接/会话、背压）；它不执行策略、不签发能力、不存储对象、不持久化审计。

### 4.1 组件职责

| 组件 | 职责 | 关键约束 |
|---|---|---|
| **Agent Bus (Bus Core)** | 认证连接、路由消息、管理任务生命周期、执行背压 | 不解析业务 payload；只做信封级校验；不执行策略或签发能力 |
| **Registry** | 索引 App 清单、Agent、能力、事件主题、数据 schema | 独立服务；清单需 OS 验证签名；能力声明不等于授权 |
| **Policy & Consent** | 策略求值（用户偏好、企业策略、风险等级）、同意流程、凭证签发 | 独立服务；默认拒绝；决策可解释、可审计 |
| **Router** | 请求/响应、事件、流、取消、任务树 | 属于 Bus Core；幂等、超时、配额 |
| **Context Fabric** | 解析 `ctx://` 句柄、任务级共享状态、对象引用 | 独立服务；不持有长期记忆；每次解析都过策略；读操作留痕 |
| **Audit** | 记录跨 Agent 事件、同意回执、数据访问 | 独立服务；只追加、防篡改、可导出 |
| **Bridge** | 把外部协议映射为 OSAP 消息 | 沙箱化；外部内容必须打来源与信任标签 |

### 4.2 三个平面

- **控制平面**：注册、发现、身份、能力、策略、同意、审计。
- **数据平面**：请求/响应、流、事件、取消、错误。
- **上下文平面**：句柄解析、任务黑板、对象引用。长期记忆由 Agent 或独立 memory 服务持有，需单独授权，不属于 Bus。

---

## 5. 协议分层

| 层 | 名称 | 内容 | 是否必须 |
|---|---|---|---|
| L0 | 传输绑定 | UDS / named pipe / Binder / XPC / localhost TLS | 必须 |
| L1 | 身份与信任 | App 身份、Agent 实例、用户主体、设备、签名 | 必须 |
| L2 | 消息信封 | 版本、ID、类型、路由、时间、追踪、错误 | 必须 |
| L3 | 任务与上下文 | 任务树、预算、取消、引用、流 | 必须（最小集） |
| L4 | 语义与策略 | 能力、schema、事件主题、风险等级、同意 | 必须 |
| L5 | 领域扩展 | 日历、通讯录、文件、邮件等标准 schema | 可选 |

**传输无关**：L1 以上用统一的 JSON/CBOR 信封；L0 可以是任何提供"本地、可认证对端"的 IPC。首个参考绑定建议：
- Linux：Unix domain socket + `SO_PEERCRED`；
- macOS：XPC / Mach service + audit token；
- Windows：named pipe + client SID；
- 容器/跨进程沙箱：localhost mTLS 作为兜底。

---

## 6. 核心对象与身份

### 6.1 身份四元组

```
Principal = (User, App, AgentInstance, Device)
```

| 对象 | 示例 | 签发方 |
|---|---|---|
| User | `user://local/example-user` | OS 账户 |
| App | `app://com.example.notes` + 代码签名 | OS 安装器/商店 |
| Agent | `agent://com.example.notes/assistant#7f3a` | App 启动时向 Bus 注册 |
| Device | `device://example-device/...` | OS |

> 关键点：**Agent 身份绑定到 App 身份与进程凭据**。Bus 在连接建立时验证对端进程（peer credential），App 不能仅靠字符串自称是别人。系统 Agent、系统设置等敏感命名空间保留，第三方不可注册。

### 6.2 能力（Capability）

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

设计要点：
- 采用 **macaroon 风格**的链式签名，支持离线收窄（attenuation）；
- 每个能力都绑定 **audience + task**，防止被其他 Agent 重放；
- 能力可以撤销（短 TTL + 撤销列表）；
- 能力不等于策略：即使持有能力，Policy 仍可因上下文拒绝。

### 6.3 任务（Task）

```
task_id, parent_task_id, root_task_id
owner_agent, assignee_agent
goal, input_refs, output_refs
budget {wall_ms, tokens, tool_calls, money, depth}
deadline, priority
status: pending | running | waiting_consent | done | failed | cancelled
```

任务树天然表达"主 Agent 拆解 → 子 Agent 执行"。`root_task_id` 让审计可以把一次用户意图串起来。

---

## 7. 消息模型

### 7.1 统一信封

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

字段原则：
- `to` 可以是**具体 Agent**，也可以是**能力**。后者由 Router 结合 Registry + Policy 解析到唯一持有者；多个候选时触发选择或同意。
- `body` 必须带 `schema`，Bus 不解析 `data`，但可做大小/类型/敏感字段检查。
- 所有二进制/大对象走 `refs`，不内联。
- `consent.receipt` 指向用户同意记录，便于事后追责。

### 7.2 消息类型（动词）

| 类型 | 方向 | 语义 | 幂等 |
|---|---|---|---|
| `discover` / `describe` | 请求 | 查询能力、schema、风险、成本 | 是 |
| `request` | 请求 | 调用一个能力/执行一个任务 | 是（`id` 去重） |
| `result` | 响应 | 成功结果 + 引用 | — |
| `error` | 响应 | 结构化错误（可重试/不可重试） | — |
| `event` | 单向 | 主题事件，最多一次投递 | 否 |
| `stream.open/chunk/close` | 双向 | 流式输出、进度、增量结果 | 分片序号 |
| `cancel` | 单向 | 取消任务，沿任务树向下传播 | 是 |
| `delegate` | 单向 | 把子任务交给另一个 Agent | 是 |
| `status` | 单向 | 心跳、进度、预算消耗 | 否 |
| `consent.request/grant/deny` | 双向 | 同意流程 | 是 |

### 7.3 错误模型

```json
{
  "type": "error",
  "body": {
    "schema": "osap.error/v1",
    "code": "POLICY_DENIED",
    "message": "需要用户确认发送外部消息",
    "retryable": false,
    "details": { "policy": "external_side_effect", "consent_url": "osap://consent/01J..." }
  }
}
```

标准错误码分段：`AUTH_*`、`POLICY_*`、`CAPABILITY_*`、`TASK_*`、`SCHEMA_*`、`TRANSPORT_*`、`RATE_LIMIT`、`TIMEOUT`、`CANCELLED`。

---

## 8. 任务与主子 Agent 模型

### 8.1 三种关系

| 关系 | 含义 | 权限 |
|---|---|---|
| **Supervisor → Worker** | 主 Agent 拆解任务，委派子任务 | 子能力 ⊆ 父能力，预算递减 |
| **Peer ↔ Peer** | 两个 App Agent 平等协作 | 各自持有独立能力，不能互相提权 |
| **System Agent → App Agent** | OS 调度器发起系统级任务（如"整理今日待办"） | 受系统策略约束，仍需用户同意 |

### 8.2 委派语义

主 Agent 发起 `delegate` 时必须附带：

1. **任务目标**与输入引用（不是全量数据）；
2. **收窄后的能力凭证**；
3. **预算**（时间、调用次数、金额、深度）；
4. **截止时间**与优先级；
5. **结果契约**（期望 schema、质量门槛）。

```json
{
  "type": "delegate",
  "from": "agent://com.example.orchestrator/main#1a2b",
  "to": "agent://com.example.calendar/agent#9c",
  "task": {
    "id": "task_cal_01",
    "parent": "task_root_01",
    "goal": "在下周三 9:00-12:00 中找到 60 分钟空档并创建 tentative 事件",
    "budget": { "wall_ms": 8000, "tool_calls": 2, "depth": 1 },
    "result_schema": "osap.calendar.proposal/v1"
  },
  "auth": { "token": "cap_…（仅 calendar:primary 的 propose，audience=calendar agent）" }
}
```

### 8.3 规则

- **深度限制**：默认最大委派深度 2–3，防止无限递归与责任稀释。
- **预算单调递减**：子任务预算不能超过父任务剩余预算。
- **取消级联**：父任务取消 → 所有子任务收到 `cancel`；子任务失败可选择上报或降级。
- **结果聚合**：父 Agent 只接收 `result` 与引用，不自动获得子 Agent 的中间上下文。
- **责任可追溯**：每个任务记录 `owner_agent` 与发起它的用户意图 `root_task_id`。

---

## 9. 能力、同意与安全

### 9.1 风险分级与同意策略

| 等级 | 示例 | 默认策略 |
|---|---|---|
| L0 公开读 | 读取公开天气 | 自动允许 |
| L1 个人读 | 读日历、联系人、笔记 | 首次同意，可记住范围/时长 |
| L2 本地写 | 创建本地草稿、修改待办 | 低风险自动 + 通知 |
| L3 外部副作用 | 发消息、发邮件、提交表单 | 每次确认（可批量授权） |
| L4 高影响/不可逆 | 支付、删除、对外发布 | 强确认 + 二次认证 |

同意回执包含：`who`（哪个 Agent）、`what`（能力与动作）、`data`（引用的数据范围）、`cost`（金额/配额）、`ttl`、`receipt_id`。

### 9.2 威胁模型与对策

| 威胁 | 场景 | 对策 |
|---|---|---|
| 身份伪造 | 恶意 App 自称系统 Agent | 进程凭据绑定 + 保留命名空间 + 代码签名 |
| 困惑的副手（confused deputy） | 低权限 Agent 借高权限 Agent 做事 | 能力绑定 audience + task；不转发原始凭证 |
| 提示注入 | 消息内容里藏"忽略之前的指令" | 内容来源/信任标签；指令与数据分离；策略过滤；高风险动作强制人工确认 |
| 数据外泄 | 子 Agent 把通讯录发给外部 | 数据句柄按接收方策略解析；出口策略；引用而非复制 |
| 重放 | 截获合法消息重复发送 | nonce + deadline + 能力 `max_uses` |
| DoS | 大量请求拖垮 Bus/目标 App | 配额、速率限制、背压、任务预算 |
| 审计篡改 | 删掉不利记录 | 只追加日志 + 哈希链/系统完整性保护 |

### 9.3 提示注入的协议级处理

OSAP 不试图"检测所有恶意文本"，而是做三件事：

1. **来源标注**：每条消息携带 `origin`（App、Agent、用户、外部网络）与信任等级；
2. **指令/数据分离**：`body.data` 永远是数据，不能改变调用方的系统策略；Agent 不应把消息内容当系统指令执行；
3. **动作闸门**：任何 L2 以上动作必须经过 Policy；L3/L4 必须有人类同意。即使 Agent 被注入，也无法静默产生外部副作用。

---

## 10. 发现机制

### 10.1 App 清单（Manifest）

App 安装/首次运行时注册：

```json
{
  "app": "com.example.calendar",
  "version": "3.2.1",
  "signature": "…",
  "agents": [
    {
      "id": "agent://com.example.calendar/agent",
      "display_name": "日历助手",
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

### 10.2 发现查询

```json
{
  "type": "discover",
  "body": {
    "schema": "osap.discover/v1",
    "intent": "为一次会议找空闲时间",
    "requires": ["calendar.read"],
    "accepts_risk": "L1",
    "limit": 5
  }
}
```

返回的是**候选 + 策略判决**，而不是裸接口列表：

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

原则：
- **能力声明 ≠ 授权**，发现结果必须附带 `policy` 判定；
- 支持按 schema、动作、风险、成本过滤，语义匹配只是排序信号；
- 不允许通过发现接口枚举用户隐私数据。

---

## 11. 事件与上下文平面

### 11.1 事件总线

- 主题采用反向域名式命名：`os.user.activity.*`、`os.calendar.*`、`app.<app-id>.*`。
- 订阅需要能力（`cap://os/events/subscribe` + 主题过滤 + 数据范围）。
- 默认投递语义：**事件最多一次**，任务请求至少一次（幂等键去重）。
- 事件只携带最小 payload + 引用，敏感内容由订阅方按需解析。
- 用户可查看"谁在监听什么"，并一键撤销。

### 11.2 上下文 Fabric

| 句柄 | 含义 | 解析策略 |
|---|---|---|
| `ctx://user/profile#display_name` | 用户资料字段 | 字段级授权 |
| `ctx://session/current#activity` | 当前前台活动 | 会话级、短 TTL |
| `ctx://screen/current` | 当前屏幕内容 | 高风险，需显式同意 |
| `obj://sha256:...` | 内容寻址对象 | 读取需持有对象能力 |
| `file://...` | 用户文件 | 文件选择器/沙箱授权 |
| `task://<id>/blackboard` | 任务级共享状态 | 仅任务参与者；非记忆 |

**任务黑板**：同一任务树内的 Agent 可以读写一块受控共享区，用于交换中间结果，而不必把所有内容塞进消息。任务结束即回收（或按策略归档）。

**长期记忆**：单独授权，写入需用户可见、可删除；不能由某个 App 静默写入全局记忆。

---

## 12. 与现有生态互操作

| 现有协议 | 解决的问题 | OSAP 的关系 |
|---|---|---|
| **MCP** | Agent → 工具/资源 | App 暴露的 MCP Server 由 Bridge 包装成 OSAP 能力 |
| **A2A** | 远程 Agent ↔ Agent | 本地 Agent 可作为 A2A 端点；跨设备消息经 Bridge 转发并保留来源标签 |
| **OpenAPI / HTTP** | 传统服务接口 | Bridge 生成能力描述，策略与审计在外层统一 |
| **D-Bus / XPC / Binder** | 系统 IPC | 作为 L0 传输绑定，不重复造传输层 |
| **OAuth / OIDC** | 用户授权 | 可作为跨设备/云侧能力凭证的上游签发机制 |

映射原则：
1. 外部协议的能力先"翻译"为 OSAP 能力描述，再参与发现；
2. 外部内容一律标记 `origin=external`，默认信任等级最低；
3. 外部副作用同样走 L3/L4 同意；
4. 不在 OSAP 内重新定义 MCP/A2A 已有的语义，只做本地策略与身份包装。

---

## 13. 可靠性与可观测性

### 13.1 投递语义

- `request`：至少一次 + 幂等键（`id`）；接收方需去重。
- `result`：与请求配对；超时后返回 `TIMEOUT`，是否重试由调用方决定。
- `event`：最多一次；需要可靠事件时使用 `request` + 订阅确认。
- `stream`：分片带序号与 `stream_id`，支持断点续传/取消。
- 背压：Bus 暴露队列水位，超限返回 `RATE_LIMIT` 或让发送方等待。

### 13.2 追踪

- 一次用户意图 = 一个 `trace_id`；
- 每次 Agent 跳转 = 一个 span（`causation_id` 串起来）；
- 审计事件包含：发现、授权、同意、调用、数据解析、结果、错误、取消；
- 支持按 `trace_id` 回放一次跨 App 协作，用于调试与问责（敏感字段脱敏）。

### 13.3 可观测性接口

- `osap.trace.get/v1`：取回 trace（受权限约束）；
- `osap.audit.query/v1`：用户查看"过去 24 小时谁访问了我的数据"；
- `osap.bus.stats/v1`：队列、延迟、错误率（系统诊断用）。

---

## 14. 部署形态

| 形态 | 描述 | 适用 |
|---|---|---|
| **A. 每用户 Bus 守护进程** | 登录会话启动一个 Bus，App 通过 UDS/XPC 连接 | 桌面 OS，推荐起点 |
| **B. 系统 Bus + 用户 Broker** | 系统级 Bus 管身份/策略，用户级 Broker 管消息 | 多用户、企业管控 |
| **C. 库模式 + OS 中介** | 无中心守护进程，OS 提供认证通道 | 资源受限设备（移动/嵌入式） |

首个参考实现建议 A：单机、单用户、UDS，先跑通发现/请求/同意/审计，再谈多用户与跨设备。

---

## 15. 典型场景走查

**用户说："把昨天的会议纪要整理一下发给示例联系人，顺便约下周三上午开会。"**

1. **意图入口**：系统 Agent（或用户指定的主 Agent）创建 `root_task`，`trace_id` 生成。
2. **发现**：主 Agent 查询 `notes.read`、`contacts.resolve`、`messaging.send`、`calendar.propose`，得到候选与策略判决。
3. **同意**：Policy 判定"读取笔记"为 L1、"对外发消息"为 L3。OS 弹出意图预览：
   - 读取：Notes / 昨天 14:00 的会议纪要
   - 发送：Messaging / 联系人：示例联系人 / 1 条消息
   - 创建：Calendar / 下周三 9:00–12:00 / tentative
4. **委派**：
   - Notes Agent 用收窄能力读取纪要 → 返回 `obj://sha256:...`
   - Contacts Agent 解析"示例联系人" → 返回 `contact://...`
   - Calendar Agent 查空闲 → 返回 2 个候选时段
5. **组合**：主 Agent 生成消息草稿与会议提议，引用而非复制原始纪要。
6. **外部副作用**：发送前再次确认（L3）；Calendar 创建 tentative 事件（L2，通知）。
7. **审计**：一条 trace 串起 4 个 App、6 次调用、2 次同意；用户可在活动中心查看与撤销后续授权。

---

## 16. 演进路线

| 阶段 | 范围 | 验收标准 |
|---|---|---|
| **P0 骨架** | 信封、身份、注册/发现、请求/响应、审计 | 两个示例 App 能安全互调 |
| **P1 可控** | 能力凭证、策略、同意 UI、错误模型 | L1–L3 动作可被正确拦截与授权 |
| **P2 协作** | 任务树、委派、预算、取消、流式 | 主 Agent 能拆解并聚合 3 个子 Agent |
| **P3 上下文** | 事件总线、Context Fabric、任务黑板 | 跨 App 事件驱动协作，数据不出域 |
| **P4 互操作** | MCP/A2A Bridge、标准领域 schema | 现有 MCP Server 零改造接入 |
| **P5 规模化** | 多用户、跨设备、企业策略、性能 | 100+ Agent、P95 本地调用 < 20ms |

---

## 17. 开放问题

1. **Bus 是否应内置编排？** 倾向只做传输与治理，编排交给系统 Agent/App Agent，避免 Bus 变成"超级 Agent"。
2. **无 Agent 的旧应用怎么办？** 用 UI 自动化/脚本桥接，还是要求 App 提供轻量适配器？
3. **能力 schema 由谁标准化？** OS 厂商定义核心域（日历/联系人/文件/消息），长尾由生态自定义。
4. **同意疲劳**：如何在安全与流畅之间取平衡？可考虑"任务级一次性授权 + 细粒度撤销"。
5. **跨设备联邦**：本地 Bus 如何与云端 A2A 对齐身份与能力？是否引入设备间互信根？
6. **多用户共享会话**（家庭屏、协作空间）：主体如何切换，数据边界如何划分？
7. **提示注入责任归属**：协议层只做闸门，App/模型层仍需内容防护，责任如何划分？
8. **性能与隐私的权衡**：每次数据解析都过策略会不会太慢？需要本地策略缓存与句柄短期租约。
9. **谁来实现 Bus**：OS 厂商、桌面环境、运行时（如 Electron/Flutter）还是独立守护进程？
10. **与剪贴板/拖拽/分享面板的关系**：OSAP 是补充还是替代？倾向互补，把"分享"升级为"带能力的引用传递"。

---

## 附录 A：术语表

| 术语 | 含义 |
|---|---|
| Agent | App 内代表用户执行任务的实体，拥有独立身份与能力 |
| Agent Bus | OS 提供的本地消息与治理总线 |
| Capability | 可验证、可收窄、可撤销的授权凭证 |
| Task Tree | 由一次用户意图派生的任务层级结构 |
| Context Fabric | 以句柄方式提供用户/会话/对象上下文的子系统 |
| Consent Receipt | 用户同意某次动作的不可否认记录 |
| Reference | `obj://` / `ctx://` 等数据句柄，替代内联数据 |
| Trust Label | 消息来源与可信等级标注，用于注入防护 |

## 附录 B：与相关系统的对比

| 维度 | D-Bus / XPC | MCP | A2A | **OSAP** |
|---|---|---|---|---|
| 范围 | 本机 IPC | Agent→工具 | 远程 Agent↔Agent | 本机 Agent↔Agent + 治理 |
| 身份 | 进程/服务 | 客户端配置 | Agent Card | App+Agent+用户+设备四元组 |
| 授权 | 粗粒度 | 配置/环境 | 端点级 | 能力凭证 + 策略 + 同意 |
| 任务语义 | 无 | 无 | 有（Task） | 有（任务树/预算/取消） |
| 数据流转 | 复制 | 工具返回 | 消息 | 引用 + 句柄解析 |
| 审计 | 有限 | 无 | 有限 | 默认全链路 |
| 定位 | 传输层 | 工具层 | 网络层 | **本地协作底座** |

## 附录 C：最小消息样例

**请求**

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

**结果**

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

*本文是总体设计草案，目的是先对齐问题、边界与关键机制；下一步可拆分为正式规范（信封/能力/任务/策略）与可运行原型。*
