# 参考实现（M2.1 – M2.6）

本目录是 OSAP 0.1 的最小参考实现。已完成路线图的 **M2.1a（信封 + 分帧 + 错误模型）**、**M2.2（身份 + 签名 + 注册表）**、**M2.3（能力模型）**、**M2.4（同意回执）**、**M2.5a（任务模型）**、**M2.5b（上下文织构）**、**M2.5c（联邦适配器）** 与 **M2.6（审计链）**；端到端串接见 [`../demo/`](../demo/README.md)。

规范性内容以 [`../docs/standard.md`](../docs/standard.md) 为准；本目录只回答“这段文字如何落成代码”。

## 1. 范围

| 已实现 | 章节 | 说明 |
|---|---|---|
| 信封模型与校验 | §7.1、§7.9 | 版本、消息类型、JSON Schema、路由键、`task`/`auth`/`deadline` 约束 |
| 错误模型 | §7.7 | 27 个标准错误码、`retryable` 默认值、`osap.error/v1` body |
| 流式分帧 | §7.9 | 4 字节大端长度前缀 + UTF-8 JSON，增量解码 |
| 消息型分帧 | §7.9、§7.10 | 保留原生消息边界，不强制长度前缀 |
| 8 MiB 上限 | §7.9 | 两种绑定都按 UTF-8 JSON 字节数校验 |
| 握手 | §7.1、§7.9 | `hello` → `welcome`，未握手时拒绝其他消息 |
| 幂等索引 | §7.8 | 同一 `id` 只执行一次副作用 |
| 单调时钟 deadline | §7.8 | 墙钟回拨或挂起恢复不得延长超时 |
| Ed25519 签名 | §4.5 | 清单签名、验证、基钥轮换宽限期 |
| Agent 注册 | §4.1–§4.3 | `hello` 校验、App 绑定、公钥绑定、`welcome` 签发 |
| 保留命名空间 | §4.4 | `agent://system/`、`cap://os/`、`ctx://os/`、`event://os/` |
| 注册表索引 | §6.1、§6.2、§6.10 | 清单验签后才索引；能力记录校验、TTL、过期即失效 |
| 发现响应 | §6.5、§6.6 | 只带静态 `consent_hint`，不返回 `policy_verdict`，不泄漏 payload |
| 能力凭证 | §5.2 | schema 校验、签发登记、`cap_id` 索引 |
| 衰减 | §5.3 | 10 条规则逐项检查，返回全部违例维度 |
| 绑定 | §5.4 | `audience` / `task_id` / `subject` 三项无状态校验 |
| 撤销 | §5.5 | 父能力撤销级联到全部后代，撤销可跨“仅持有子凭证”的场景生效 |
| 风险分级 | §5.7 | L3/L4 必须有 `consent_receipt_id`，否则 `POLICY_CONSENT_REQUIRED` |
| 同意回执 | §5.8 | 决策 → 过期 → `cap_id`/`task_id`/`audience` → `actions`/`resources` 的顺序校验 |
| 任务树 | §8.2、§8.10 | 父/子索引、状态机与非法转换拒绝 |
| 委派 | §8.3、§8.5 | 子任务预算 ≤ 父剩余、深度 = 父 + 1、重复 `task_id` 拒绝 |
| 预算 | §8.6 | 逐维比较；运行期超支报 `TASK_BUDGET_EXCEEDED` |
| 取消 | §8.7 | 沿任务树向下传播，`detached` 子任务继续运行 |
| 结果 | §8.8 | 只接受 assignee 的 `result`，`body.schema` 必须等于 `result_schema` |
| 所有权转移 | §8.9 | `handoff` 一次性转移、拒绝即不变、L3/L4 需新回执 |
| 句柄解析 | §9.2 | `resolve` 授权、`audience`/`allowed_agents`、每次解析写 `context.resolve` 审计 |
| 句柄 TTL | §9.3 | `expires_at` 或 `created_at + ttl`；过期即拒绝，不自动续期 |
| 长期记忆 | §9.3 | 记忆句柄必须单独持有 `memory.read`，任务能力不隐含 |
| 信息流标签 | §9.4 | `public < personal < sensitive < secret`；派生对象不得降低标签 |
| 任务黑板 | §9.5 | 任务结束即清理/归档，不自动晋升为长期记忆 |
| 对象删除 | §9.6、§9.7 | 先查引用；被引用对象墓碑化，不硬删；写审计事件 |
| 缓存窗口 | §9.7 | 缓存 TTL 钳制到句柄 TTL，被撤销的句柄不会命中 |
| 数据出口 | §9.8 | `sensitive`/`secret` 离开设备需要用户显式放行 |
| OS 权限 | §9.9 | OS 拒绝是外层边界，句柄不能绕过沙箱 |
| 存储声明 | §9.10 | `managed_store` 必须覆盖配额、GC、崩溃恢复、加密、路径安全、删除 |
| 联邦投影 | §6.7 | 原生描述符投影为能力记录；保留 `source`、`native_id`、`version`、`provenance` |
| 原生身份 | §6.7 | MCP server/tool、A2A card/skill、D-Bus bus/path/interface/method、OpenAPI operationId |
| 命名空间映射 | §6.8 | 由 `registry + native_id` 生成确定性的 `cap://federation/...` 名称 |
| 外部信任 | §6.4 | 外部协议内容标 `origin=external`；未验签时不得保持 `system`，归一为 `unverified` |
| 审计链验证 | §10.5、§10.6 | 事件 schema、phase 规则、trace 一致、`audit_id` 唯一、`prev_hash` 链接 |
| 脱敏导出 | §10.6 | 目标、策略、回执、上下文引用替换为每次导出唯一的盐值承诺；链仍可验证 |
| 回放 | §10.6 | 同一幂等键重复请求只执行一次副作用 |
| 恢复对账 | §8.11、§10.5 | 只有 `effect.intent` 没有 outcome 时标记 `unknown` 并要求对账 |
| 跨用户 | §11.2 | 默认拒绝；显式开启且双方同意才放行 |
| 被攻破的 Bus | §3.6、§11.1 | 0.1 不声称 P0 防护；声明了即判不合约 |

**不在本阶段**：真实 OS 传输绑定（M2.1b）与同意消息流（M2.4b）。未实现的类型会抛 `NotImplementedError`，一致性运行器据此记为 `skip`。

## 2. 目录

```
impl/
  adapter.py            一致性适配器（tools/conformance_run.py --impl 的入口）
  osap/
    __init__.py         公共导出
    bus.py              握手、校验、路由、幂等、错误回执
    audit.py            §10.5、§10.6 审计链、脱敏导出、回放、恢复
    capability.py       §5.2–§5.6 能力凭证、衰减、绑定、撤销
    clock.py            单调时钟 deadline
    consent.py          §5.8 同意回执与能力范围校验
    context.py          §9 句柄、标签、黑板、对象、缓存、存储声明
    crypto.py           Ed25519 签名与规范化 JSON
    envelope.py         §7.1 校验（版本 → 类型 → schema）
    errors.py           §7.7 错误码与 OsapError
    federation.py       §6.7、§6.8 原生描述符投影与命名空间映射
    framing.py          §7.9 两种分帧绑定
    identity.py         注册、保留命名空间、App/公钥绑定
    idempotency.py      §7.8 幂等索引
    registry.py         §6 清单、能力记录、发现
    schema.py           JSON Schema 加载与错误映射
    task.py             §8 任务树、预算、取消、结果、handoff
  tests/                单元测试（unittest）
```

## 3. 运行

```bash
# 单元测试
python3 -m unittest discover -s impl/tests -t impl

# 只跑已实现的范围
python3 tools/conformance_run.py --impl impl/adapter.py --level C0,C1,C2,C3,C4,C5,C6,C7

# 全量：已实现的出 pass，其余按里程碑 skip
python3 tools/conformance_run.py --impl impl/adapter.py --format md --out report.md

# 三 Agent 端到端演示（注册 → 发现 → 同意 → 委派 → 上下文 → 审计）
python3 demo/run_demo.py
```

## 4. 当前一致性结果

```
python3 tools/conformance_run.py --impl impl/adapter.py
→ 68 cases [C0..C7]: 60 pass, 0 fail, 8 skip
```

| 等级 | 结果 | 说明 |
|---|---|---|
| C0 | 5 pass / 2 manual skip | 信封、分帧、幂等、单调时钟 |
| C1 | 6 pass | 注册、保留命名空间、验签、App/公钥绑定、轮换 |
| C2 | 5 pass / 1 manual skip | 清单索引、发现响应、TTL |
| C3 | 12 pass | 绑定、衰减、撤销、风险与回执 |
| C4 | 8 pass / 3 manual skip | 委派预算、结果契约、peer 会话、所有权、handoff |
| C5 | 11 pass | 解析授权、过期、标签继承、出口、黑板、删除、缓存、存储声明、记忆边界 |
| C6 | 7 pass / 1 manual skip | 三家原生注册表、MCP、A2A、D-Bus 投影与外部信任归一 |
| C7 | 6 pass / 1 manual skip | 审计链篡改、脱敏导出、跨用户、回放、恢复、被攻破 Bus 声明 |

60 条 automated 用例全部通过；剩余 8 条 skip 都是 manual 用例（C0-01、C0-06、C2-05、C4-01、C4-08、C4-09、C6-08、C7-01）。

C3 的 12 条都命中预期错误码，且实现被断言为“只在目标维度上失败”：C3-04…C3-07 的 `details.violations` 分别只有 `actions`、`resources`、`exp`、`depth`+`constraints.max_depth`。

C4 的 8 条同样逐条核对过拒绝原因：C4-02 是 `wall_ms` 超出父剩余 8000、C4-03 是 `result_schema` 不符、C4-04 是缺 `session_id`、C4-05 是 `subject` 不是发送方、C4-06 是 L3 handoff 无新回执、C4-07 是 `wall_ms` 已用 6000 > 预算 5000、C4-10 是 owner 已变为 calendar。

C5 的 5 条拒绝/接受和 6 条观察也都核对过实际原因：C5-01 只给了 `read` 缺 `resolve`、C5-02 过期早于夹具“现在”、C5-04 `secret` 出口无放行、C5-05 黑板归档且不晋升、C5-07 缓存 900 s 被钳到 600 s、C5-09 OS 权限先于任何授权、C5-10 只有 `task.read` 缺 `memory.read`；C5-03/06/08/11 的 `observe` 报告分别给出标签继承、引用检查与审计、缺失的存储职责、被禁止晋升的来源。

C6 的 7 条 automated 全部命中投影字段：C6-01/02/03 保留三家的 `native_id` 与 `system` 信任；C6-04 把 `calendar-server:create_event` 拆成 server/tool 并保留 `osap.calendar.event/v1`；C6-05 从 `#` 恢复 Agent Card 与 skill；C6-06 从四段式 D-Bus 名称恢复 bus/path/interface/method；C6-07 把外部 MCP 的 `system` 声明归一为 `unverified`，并标 `origin=external`。

C7 的 6 条 automated 同样逐条核对：C7-02 在 `events[1].prev_hash` 被改后于索引 1 断开并报 `AUDIT_CHAIN_INVALID`；C7-03 保留 hash/prev_hash、替换敏感字段后仍验证通过；C7-04 跨用户默认拒绝；C7-05 两次回放只有 1 次副作用；C7-06 只有 intent 时标 `unknown` 并告警；C7-07 声明 P0 防护被判不合约。

`python3 demo/run_demo.py` 把上述模块串成一条可复核路径：三个 Agent 注册、一次发现、一份 L3 回执、两次委派（supervisor → notes、supervisor → calendar）、一次上下文解析与 15 条审计事件。它用断言固定 C7-01 中可自动化的部分（单 trace、每跳 `causation_id`、链验证、脱敏后仍可验证、恢复不执行副作用），细节见 [`../demo/README.md`](../demo/README.md)。

## 5. 设计决定

### 5.1 校验顺序

`envelope.validate` 的次序是 **版本 → 消息类型 → JSON Schema**。

如果把 schema 放在最前，`{"type": "bogus"}` 会先被 `enum` 拒绝并报 `SCHEMA_INVALID`；但 §7.9 明确要求未知类型返回 `SCHEMA_UNSUPPORTED`。

“缺 `type`”仍按 `SCHEMA_INVALID` 处理：缺失字段是结构问题，不是未知类型。

### 5.2 消息型传输不加前缀

`encode_message` 原样返回对象，只做体积检查。给消息型绑定再套 4 字节长度前缀会让 C0-06 的观察结果变成“不一致”。

### 5.3 deadline 用单调时钟

`Deadline.from_envelope` 只从信封里取**预算**（`deadline - ts`），之后一律用 `time.monotonic()` 计算剩余时间。墙钟只用于解析，不参与判定。

### 5.4 签名覆盖规范化 JSON

`crypto.canonical_bytes` 对去掉 `signature` 字段的文档做 key 排序、最小分隔符的 UTF-8 JSON 编码，再签这段字节。它不是完整的 RFC 8785，但对 OSAP 会签的文档是确定性的，并已写进代码注释供其他实现复现。

### 5.5 注册的判定顺序

`Registrar.register` 依次检查：`from` 与自报 agent 一致 → 非保留命名空间 → agent 归属的 App 与自报 App 一致 → 清单存在 → 清单验签 → 公钥在清单中绑定 → 轮换宽限期。任何一步失败都返回 `AUTH_DENIED`，不泄漏具体是哪一步之外的信息。

### 5.6 注册表只索引“可验证且新鲜”的记录

- 清单：先过 schema，再验签，最后才写入索引（§6.1）。
- 能力记录：schema 通过后检查 `freshness.expires_at`，过期记录返回 `indexed=false`，不进入发现结果（§6.10）。
- 发现结果：`consent_hint` 直接取自记录里的静态策略，任何 `policy_verdict` 都视为不一致（§6.6、§6.9）。

### 5.7 衰减从“原始夹具”派生父凭证

C3-04…C3-07 用 `context` 指向未变异的 `examples/capability.json`，适配器据此合成父凭证：`cap_id = parent_cap_id`、`depth = depth - 1`。父凭证因此与子凭证只在被测维度上不同，不会因为共享变异而把违例“抵消”掉。

### 5.8 接收方从信封解析，而不是从凭证读取

`_receiver` 优先读 `to.agent`；若是 `to.capability`，则通过注册表解析声明该能力清单的 Agent。C3-01 把 `audience` 改成 notes 的 Agent，接收方仍解析为 calendar 的 Agent，所以报 `CAPABILITY_AUDIENCE_MISMATCH`——如果拿凭证自己的 `audience` 当接收方，这条用例会假通过。

### 5.9 “现在”用信封的 `ts`

能力有效性与回执过期都以信封 `ts` 为基准，而不是墙钟。夹具固定在 2026-11-10，这样用例不会随时间流逝而失效，也符合“判定同一条消息时要使用同一个时间基准”。

### 5.10 衰减的预算维度缺失视为放宽

§5.3 要求 `max_budget` 每个维度 ≤ 父预算。若父凭证限定了 `wall_ms`，子凭证却不写这一维，等于把它变成无界，实现判为 `max_budget.wall_ms` 违例；`max_uses` 与 `rate` 同理。

### 5.11 委派超预算与运行期超预算用不同错误码

§8.6 只说“超预算 MUST 返回 `TASK_BUDGET_EXCEEDED`”，但委派时“子预算 > 父剩余”是**拒绝签发**，不是执行中超支；规范也没有委派专用错误码。实现因此按 C4-02 的约定：委派超额报 `POLICY_DENIED`，执行期消耗超额报 `TASK_BUDGET_EXCEEDED`。

### 5.12 任务 `budget.depth` 是绝对深度

`examples/task.json` 的 `budget.depth = 1`，`delegate.json` 的子预算 `depth = 2`。实现把 `depth` 当作绝对委派深度：子任务必须等于父任务 + 1，与能力衰减里的 `depth` 规则一致，这样两条路径不会给出互相矛盾的判定。

### 5.13 handoff 不引入新状态

§8.9 明确“任务状态机不新增 `handoff_pending`”。`TaskBoard.handoff` 要么改了 `owner`/`assignee`/`authority`，要么原样返回 `rejected`；C4-11 的三项 `*_unchanged` 就是对这一点的断言。

### 5.14 取消跳过 detached 子树

`detached=true` 的子任务按 §8.7 可以继续运行，但必须失去父任务能力。实现直接跳过整棵 detached 子树（连它的后代也不取消），因为失去父能力的后代不应再被父链上的取消影响。这一条目前只有单元测试覆盖，C4-01 仍是 manual。

### 5.15 夹具的“现在”取句柄的 `created_at`

C5 没有信封，也没有统一的 `ts`。适配器用 `context-handle.json` 的 `created_at`（2026-11-10T10:14:45Z）作为判定基准，这样 C5-02 把 `expires_at` 改到 09:00:00Z 时必然已过期，而 C5-01/03/04/09/10 的 600 s TTL 仍然有效。用墙钟会让整组夹具随时间失效。

### 5.16 记忆句柄按命名空间识别

§9.3 只规定“长期记忆必须单独授权”，没有定义 wire format。实现把 `ctx://user/memory` 前缀（或 `scope=user` 且句柄含该前缀）视为记忆句柄，要求 `memory.read`；普通 `ctx://` 即使 `scope=user` 仍只需 `resolve`，避免把用户级上下文误判成记忆。

### 5.17 标签违规返回 `observe`，不硬拒绝

§9.4 说派生对象“MUST 继承不低于其来源的标签”，但没说违规时是拒绝解析还是只记录。实现选择“解析成功后报告 `lowered=true` / `effective_label`”，因为 C5-03 的预期就是 `observe`：拒绝派生与抬高标签都被视为合规。真正需要阻止的是出口，由 §9.8 的 `POLICY_CONSENT_REQUIRED` 负责。

### 5.18 身份与 OS 校验先于过期判定

`ContextFabric.resolve` 的顺序是 audience → `allowed_agents` → OS 权限 → 所需授权 → 过期 → 出口。若先看过期，一个无权使用该句柄的 Agent 就能通过 `CONTEXT_EXPIRED` 推断出句柄存在且曾有 TTL。C5-02 的 audience 与句柄一致，所以仍然报 `CONTEXT_EXPIRED`。

### 5.19 被引用对象的删除只墓碑化

§9.6 说被引用对象“SHOULD 延迟删除或标记墓碑”，§9.7 要求删除触发引用清理与审计。实现把“引用数 > 0 且 `hard_delete=true`”判为不合约（`deleted=false`、`tombstoned=false`），软删除则返回 `tombstoned=true`；两种情况都写 `audit_written=true`，因为 C5-06 断言的是“有引用检查与审计事件”，不是“真的删掉了”。

### 5.20 原生身份按内容解析，不按固定位置

D-Bus 的 `native_id` 同时含 bus、interface、path 与 interface.method，冒号又可能出现在各段里。实现先取首段为 bus、取以 `/` 开头的段为 path，再取剩余段中的 interface，最后从尾段剥离 `interface.` 得到 method。这样 C6-06 的 `session:org.example.Calendar:/org/example/Calendar:org.example.Calendar.CreateEvent` 能稳定还原为 bus=`session`、path=`/org/example/Calendar`、interface=`org.example.Calendar`、method=`CreateEvent`。

### 5.21 外部协议的信任只能降不能升

§6.4 要求外部内容默认最低信任，RFS 不得把未验证来源提升为 `system`。实现把 MCP、A2A、OpenAPI、`bridge` 视为外部：即使记录自称 `system`，投影也只报 `unverified`。这一层没有验签器，`verified` 同样降到 `unverified`，宁可保守也不伪造信任。

### 5.22 投影是只读的

`federation.project` 只读取并校验能力记录，不写入原生注册表，也不改写传入的字典；C6-08 的“原生变化后更新或失效”由 `refresh()` 提供新的 freshness 窗口，真正的监听与调度留给 Bus 的注册表缓存（§6.10）。

### 5.23 审计链只验证链接，不重算哈希

夹具里的 `hash` 是短占位串（如 `sha256:1f0c9a7e2b`），不是事件正文的真实摘要；§10.5 也没有规定审计事件的正则化编码。`verify_chain` 因此校验事件 schema、`phase` 规则、`trace_id` 一致性、`audit_id` 唯一性，以及 `prev_hash == previous.hash`，不重新计算正文哈希。乱改正文却保留原 hash 的情况只有真正的内容寻址实现才能发现，已在限制中登记。

### 5.24 脱敏用每次导出唯一的盐值承诺

§10.6 允许脱敏导出证明“链未被篡改 + 字段承诺一致”，但不能恢复明文。`redact_chain` 先验证原链，再把 `target`、`policy`、`consent_receipt_id`、`context_refs` 替换为 `sha256:<salt>:<value>` 的承诺；`hash`/`prev_hash` 原样保留，所以导出后仍能过 `verify_chain`。验证方只能比对承诺，不能反推明文。

### 5.25 `AUDIT_CHAIN_INVALID` 是领域扩展码

§10.5 要求审计校验失败时拒绝，但没有定义审计专用标准码。实现使用 `AUDIT_CHAIN_INVALID`：它不在 §7.7 的 27 个标准码内，也不在保留前缀（`AUTH_`…`TRANSPORT_`）内，因此 `is_standard()` 与 `is_extension()` 都为 false；报告据此把它标为领域扩展，而不是标准错误。

### 5.26 回放与恢复不执行副作用

`replay_effect` 用 `IdempotencyIndex` 把同一幂等键的多次调用折叠成一次副作用；`recover_effects` 只读审计事件，找出没有对应 `effect.executed.intent_ref` 的 `effect.intent`，把状态标为 `unknown` 并要求对账。两者都不调用真实工具，也不把“重放”当成对账。

## 6. 已知限制

1. **内存态**：幂等索引、注册表、轮换状态都在进程内，重启即丢；§7.8 要求可重建的持久索引，留给 M2.6。
2. **开发密钥环**：一致性适配器在导入时生成一次性 Ed25519 密钥并为示例 App 签清单。示例里的 `base64url-example-*` 是占位字符串，不是真实密钥。
3. **没有 OS 认证**：§4.2 的 `SO_PEERCRED`、audit token、package identity 都未实现；当前“App 身份”只来自清单签名。
4. **没有跨进程传输**：`stream` 与 `message` 只是编解码层，没有绑定到 UDS/XPC/D-Bus；由 M2.1b 处理。
5. **任务状态只在内存**：`TaskBoard` 没有持久化，重启后无法恢复任务树；§8.11 的 `effect.intent` 与对账也没有实现，C4-08/C4-09 因此仍是 manual。
6. **凭证只做结构校验**：`proof.sig` 未验证，`cap_id` 也未由 CA 签发密钥覆盖；需要把用户密钥分发与签名纳入 M2.4 之后的里程碑。
7. **`max_uses` 未计数**：衰减时比较上限，但使用次数没有落账，重放同一凭证不会被扣减。
8. **撤销只在内存**：`CapabilityAuthority.revoked` 是进程内集合，重启即丢，也没有广播；§5.5 要求撤销事件写入审计账本并通知受影响 Agent，留给 M2.6。
9. **委派未校验能力链**：`delegate` 只检查任务预算与深度，没有把 `delegated_capability` 与父能力凭证做完整衰减比对（夹具里没有父凭证）。
10. **上下文只在内存**：`ContextFabric` 的审计与黑板状态不持久化，也没有真正撤销句柄；§9.7 的“谁在何时解析了哪个句柄”目前只能读进程内列表。
11. **没有真实对象存储**：`delete_object` 只返回判定结果，不触碰文件系统；`storage_declaration` 只核对声明，不实现配额、GC 或加密。
12. **联邦只做投影**：没有监听原生注册表变化，也没有按 TTL 自动刷新；C6-08 仍是 manual。MCP/A2A/OpenAPI 的外部签名未验证，因此统一降为 `unverified`。
13. **审计链不重算正文哈希**：只验证事件 schema、trace、`audit_id` 与 `prev_hash` 链接；夹具的 hash 是占位串，规范也未固定编码。
14. **审计只在内存**：`ContextFabric`、`TaskBoard` 与审计模块都不持久化；重启恢复与真实回放需要持久账本，C7-01 仍是 manual。
15. **60 个 pass 覆盖全部 automated 用例**，但不覆盖 8 条 manual 的运行时、跨进程与崩溃恢复语义。

## 7. 与规范的偏差登记

| 位置 | 偏差 | 处理 |
|---|---|---|
| `welcome` 的 `body.schema` | 规范未定义 `osap.welcome/v1` 的字段 | 返回 `osap`、`session_id`、`app`、`features`、`limits`，等 M2.4 定稿后回写规范 |
| 未知但已定义的消息类型 | 规范未规定“已知类型尚未实现”的错误码 | 抛 `NotImplementedError`，由适配器记为 `skip` |
| 注册表索引失败的错误码 | 规范未为 RFS 定义专用错误码 | 沿用 C2-01/C2-06 的 `SCHEMA_INVALID`，与用例保持一致 |
| 签名规范化 | 未采用完整 RFC 8785 | 采用 key 排序的 UTF-8 JSON，并在 `crypto.py` 里写明；M4 打包时再对齐 |
| 能力凭证 `proof` | 规范要求“MUST 是签名对象”，实现未验签 | 只校验结构；密钥分发与验签待补 |
| 回执中的 `agent` | §5.8 未明确要求回执绑定能力 `subject` | 实现额外校验 `receipt.agent == capability.subject`，不改变任何用例结果 |
| `audience` 与 `actions` 的检查顺序 | 规范未规定 | 固定为 `cap_id` → `task_id` → `audience` → `actions` → `resources`，保证同一输入总是同一错误码 |
| 委派超预算的错误码 | §8.6 只定义了执行期超支 | 委派阶段用 `POLICY_DENIED`，执行期用 `TASK_BUDGET_EXCEEDED` |
| 记忆句柄的识别 | §9.3 未定义记忆 wire format | 按 `ctx://user/memory` 前缀识别，要求 `memory.read` |
| 标签违规的处理 | §9.4 未规定拒绝还是记录 | 解析成功后报告 `lowered`/`effective_label`，对应 C5-03 的 `observe` |
| 被引用对象的删除 | §9.6 用 SHOULD 描述墓碑 | 软删除墓碑化；硬删被引用对象判为不合约 |
| 原生 `native_id` 的格式 | §6.7 给的是建议映射，schema 只要求非空字符串 | 解析失败报 `SCHEMA_INVALID`，不静默投影成空字段 |
| 外部协议信任 | §6.4 要求最低信任，但未规定验签失败时的具体等级 | 一律降为 `unverified`；只有本实现能验证的本地来源才保留 `system` |
| 审计错误码 | §10.5 未定义审计专用标准码 | 使用领域扩展码 `AUDIT_CHAIN_INVALID`，并标明它既非标准码也不在保留前缀内 |
| 审计 hash | 规范未固定规范化编码，夹具 hash 是占位串 | 只验证链接与 schema，不重算正文摘要 |
| 任务状态机的非法转换 | 规范未规定错误码 | 用 `POLICY_DENIED` 并附带 `from`/`to` |
| 结果状态转换 | §8.8 未规定“结果消息自带 `task.status` 时如何校验” | 先校验结果契约，再走 §8.10 状态机；因此对从未启动的任务返回结果会被拒绝 |
| 委派的能力链 | §8.5 要求子能力满足全部衰减条件 | 任务侧只校验预算与深度；能力侧需要父凭证，未在夹具中提供 |
