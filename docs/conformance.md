# OSAP Conformance

> 非规范性文档 · 2026-11-10
> English version: [conformance.en.md](conformance.en.md)
> 配套规范：[`standard.md`](standard.md)

本文定义 OSAP 实现的一致性等级、测试方法、互操作要求与报告格式。

---

## 1. Conformance claim

实现 MUST 在文档或 `hello` 中声明：

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

- `level` MUST 是 `C0`–`C7` 之一。
- `features` MUST 只包含已实现并测试的特性。
- `bus_visibility` MUST 是 `payload`（0.1 唯一值）。
- `transport_kind` MUST 列出 `stream` / `message`。
- `state_recovery` MUST 是 `durable` 或 `best_effort`；声明 C4+ 时 MUST 为 `durable`。
- `cf_mode` MUST 是 `os_handles` 或 `managed_store`。
- 声明高于实际能力的行为属于不一致实现。

---

## 2. Levels

| 等级 | 名称 | 必备能力 | 可选 |
|---|---|---|---|
| C0 | Transport | 连接、分帧（按 stream/message 类型）、`hello`/`welcome`、错误、版本协商 | CBOR |
| C1 | Identity | 对端认证、Agent 注册、公钥绑定、保留命名空间、密钥轮换 | 硬件密钥 |
| C2 | Registry | 清单、能力记录、发现、静态 `consent_hint`、缓存失效 | 语义排序 |
| C3 | Authorization | 能力 token、衰减、绑定、撤销、同意回执、时钟语义 | 批量同意 |
| C4 | Collaboration | 任务、委派、peer、预算、取消、结果、恢复、handoff | 流式结果 |
| C5 | Context | 句柄、解析、标签、黑板、OS 句柄映射（可选对象存储）、记忆授权、egress | 加密对象 |
| C6 | Federation | 至少两类 Bridge（厂商注册表 + MCP/A2A/D-Bus） | 全部 Bridge |
| C7 | Full | C0–C6 + 审计导出/回放 + 多用户扩展 | 跨设备 |

> 等级是累积的：声明 C4 意味着 C0–C3 全部满足。

---

## 3. Test suite

### 3.1 结构

机器可读用例位于 [`conformance/cases/`](../conformance/cases/)，每个等级一个文件：

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

每个用例 MUST 包含 `id`、`level`、`title`、`expect`；可选 `mode`、`preconditions`、`operation`、`input`、`steps`、`audit`、`notes`。字段定义见 [`conformance/README.md`](../conformance/README.md)。

### 3.2 测试格式

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

### 3.3 运行

```bash
python3 tools/conformance_run.py --impl path/to/adapter.py --format md
```

适配器 API 与 mutation 语义见 [`conformance/README.md`](../conformance/README.md)；报告格式见 [`conformance/report.schema.json`](../conformance/report.schema.json)。

---

## 4. Required test cases

### C0 — Transport

| 编号 | 场景 | 期望 |
|---|---|---|
| C0-01 | 未完成 `hello` 就发送 `request` | 拒绝，`TRANSPORT_HANDSHAKE_REQUIRED` |
| C0-02 | 主版本不兼容 | 拒绝，`TRANSPORT_VERSION_UNSUPPORTED` |
| C0-03 | 帧长度超过 8 MiB | 拒绝，`TRANSPORT_FRAME_TOO_LARGE` |
| C0-04 | 未知消息类型 | `SCHEMA_UNSUPPORTED` |
| C0-05 | 重复 `id` 的 `request` | 不重复执行副作用 |
| C0-06 | 消息型传输被强制长度前缀 | 视为不一致 |
| C0-07 | 系统时间回拨/挂起恢复 | 超时不延长，过期请求被拒绝 |

### C1 — Identity

| 编号 | 场景 | 期望 |
|---|---|---|
| C1-01 | 未注册 Agent 连接 | 拒绝 |
| C1-02 | 第三方注册 `agent://system/...` | 拒绝 |
| C1-03 | App 签名不匹配 | 拒绝 |
| C1-04 | Agent 自称属于其他 App | 拒绝 |
| C1-05 | 密钥轮换后旧签名 | 按策略拒绝或仅允许过渡期 |
| C1-06 | `hello.public_key` 未绑定 App 身份 | 拒绝注册 |

### C2 — Registry

| 编号 | 场景 | 期望 |
|---|---|---|
| C2-01 | 未签名清单 | 拒绝索引 |
| C2-02 | 发现私有数据 | 只返回能力，不返回数据 |
| C2-03 | 发现结果返回实时 `policy_verdict` 或缺少 `consent_hint` | 视为不一致 |
| C2-04 | 过期能力记录 | 不用于授权决策 |
| C2-05 | 原生能力删除 | TTL 内失效 |
| C2-06 | 联邦记录缺少 `provenance` | 拒绝索引 |

### C3 — Authorization

| 编号 | 场景 | 期望 |
|---|---|---|
| C3-01 | `audience` 不匹配 | `CAPABILITY_AUDIENCE_MISMATCH` |
| C3-02 | `task_id` 不匹配 | `CAPABILITY_TASK_MISMATCH` |
| C3-03 | `subject != from` | `CAPABILITY_SUBJECT_MISMATCH` |
| C3-04 | 扩大 `actions` | `CAPABILITY_ATTENUATION_INVALID` |
| C3-05 | 扩大 `resources` | 拒绝 |
| C3-06 | 延长 `exp` | 拒绝 |
| C3-07 | 超过 `max_depth` | 拒绝 |
| C3-08 | 父能力撤销后使用子能力 | `CAPABILITY_REVOKED` |
| C3-09 | 无回执执行 L3 | `POLICY_CONSENT_REQUIRED` |
| C3-10 | 回执过期 | `POLICY_CONSENT_EXPIRED` |
| C3-11 | 回执范围不足 | `POLICY_CONSENT_SCOPE_MISMATCH` |
| C3-12 | 回执 `audience` 与接收方不一致 | 拒绝，`POLICY_CONSENT_SCOPE_MISMATCH` |

### C4 — Collaboration

| 编号 | 场景 | 期望 |
|---|---|---|
| C4-01 | 父任务取消 | 子任务收到 `cancel` |
| C4-02 | 子预算超过父剩余 | 拒绝委派 |
| C4-03 | 子任务结果 schema 不匹配 | `SCHEMA_INVALID` |
| C4-04 | peer 无 `session_id` | 拒绝 |
| C4-05 | peer 试图使用对方能力 | 拒绝 |
| C4-06 | handoff 未重新同意 L3 | 拒绝 |
| C4-07 | 超预算 | `TASK_BUDGET_EXCEEDED` |
| C4-08 | Bus 重启后未完成任务 | 转为 failed/重新调度 + 审计 |
| C4-09 | 副作用前崩溃（只有 intent） | 标记 unknown，不自动重放 |
| C4-10 | handoff 后原 owner 仍发送该任务请求 | 拒绝 |
| C4-11 | handoff 被拒绝，任务仍留在原 owner | 状态与预算不变 |

### C5 — Context

| 编号 | 场景 | 期望 |
|---|---|---|
| C5-01 | 无 `resolve` 能力解析句柄 | `CONTEXT_DENIED` |
| C5-02 | 过期句柄 | `CONTEXT_EXPIRED` |
| C5-03 | 派生对象降低标签 | 拒绝或提升标签 |
| C5-04 | `secret` 出口 | 拒绝/要求放行 |
| C5-05 | 任务结束 | 黑板清理 |
| C5-06 | 删除对象 | 引用检查 + 审计 |
| C5-07 | 缓存超过句柄 TTL | 失效 |
| C5-08 | `cf_mode=managed_store` 但无配额/GC | 视为不一致 |
| C5-09 | 通过句柄绕过 OS 文件权限 | 拒绝 |
| C5-10 | 无 `memory.read` 能力读取长期记忆 | `CONTEXT_DENIED` |
| C5-11 | 把幂等索引/审计日志/任务树当记忆检索 | 视为不一致 |

### C6 — Federation

| 编号 | 场景 | 期望 |
|---|---|---|
| C6-01 | AppFunction 投影 | 保留 `native_id`、`source`、`trust` |
| C6-02 | App Intent 投影 | 同上 |
| C6-03 | App Action 投影 | 同上 |
| C6-04 | MCP tool 投影 | 保留 server/tool 与 schema |
| C6-05 | A2A skill 投影 | 保留 Agent Card 与 skill |
| C6-06 | D-Bus method 投影 | 保留 bus/path/interface/method |
| C6-07 | 外部内容 | `origin=external`、`trust` 不高于 `unverified` |
| C6-08 | 原生能力变更 | TTL 内更新/失效 |

### C7 — Full

| 编号 | 场景 | 期望 |
|---|---|---|
| C7-01 | 跨 3 个 App 的任务 | trace 完整、审计可回放 |
| C7-02 | 审计链篡改 | 校验失败 |
| C7-03 | 用户导出审计 | 脱敏且链完整性可验证（不承诺恢复明文） |
| C7-04 | 跨用户请求 | 默认拒绝 |
| C7-05 | 回放 | 不重复执行副作用 |
| C7-06 | L3 副作用只有 intent 无 outcome | 标记 unknown + 告警 |
| C7-07 | 被攻破的 Bus | 0.1 明确失败；P1 另行评估 |

---

## 5. Interop matrix

推荐的最小互操作组合：

| 角色 | 示例 | 必须验证 |
|---|---|---|
| 主 Agent | 编排 App | 发现、委派、handoff、预算、取消 |
| 子 Agent | 日历 App | 能力校验、结果 schema |
| Peer Agent | 消息 App | 点对点会话、独立能力 |
| 系统 Agent | OS 助手 | 保留命名空间、系统能力 |
| Bridge | AppFunctions/MCP | 来源、信任、schema 映射 |
| 用户界面 | 同意/活动中心 | 意图预览、回执、撤销 |

互操作测试 SHOULD 至少覆盖：

- 一次 L1 读取；
- 一次 L2 本地写；
- 一次 L3 外部副作用 + 同意；
- 一次 handoff（接受与拒绝各一次）；
- 一次取消/预算耗尽；
- 一次撤销级联；
- 一次句柄解析与出口阻断。

---

## 6. Reporting

实现 SHOULD 提供机器可读报告：

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

报告 MUST 不包含用户数据、密钥或未脱敏的对象内容。

---

## 7. Security testing

除功能测试外，SHOULD 覆盖：

- 伪造对端身份；
- 重放请求；
- token 借用；
- 跨任务复用；
- 提示注入内容通过 `origin` 标记；
- 句柄路径遍历；
- 审计日志截断；
- 大消息/慢连接 DoS；
- Bridge 来源伪装。

高风险测试 MUST 在隔离环境运行，不得使用真实用户数据。
