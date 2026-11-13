# 参考实现（M2.1 – M2.4）

本目录是 OSAP 0.1 的最小参考实现。已完成路线图的 **M2.1a（信封 + 分帧 + 错误模型）**、**M2.2（身份 + 签名 + 注册表）**、**M2.3（能力模型）** 与 **M2.4（同意回执）**。

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

**不在本阶段**：任务模型（M2.5）、审计链（M2.6）、真实 OS 传输绑定（M2.1b）。未实现的类型会抛 `NotImplementedError`，一致性运行器据此记为 `skip`。

## 2. 目录

```
impl/
  adapter.py            一致性适配器（tools/conformance_run.py --impl 的入口）
  osap/
    __init__.py         公共导出
    bus.py              握手、校验、路由、幂等、错误回执
    capability.py       §5.2–§5.6 能力凭证、衰减、绑定、撤销
    clock.py            单调时钟 deadline
    consent.py          §5.8 同意回执与能力范围校验
    crypto.py           Ed25519 签名与规范化 JSON
    envelope.py         §7.1 校验（版本 → 类型 → schema）
    errors.py           §7.7 错误码与 OsapError
    framing.py          §7.9 两种分帧绑定
    identity.py         注册、保留命名空间、App/公钥绑定
    idempotency.py      §7.8 幂等索引
    registry.py         §6 清单、能力记录、发现
    schema.py           JSON Schema 加载与错误映射
  tests/                单元测试（unittest）
```

## 3. 运行

```bash
# 单元测试
python3 -m unittest discover -s impl/tests -t impl

# 只跑已实现的范围
python3 tools/conformance_run.py --impl impl/adapter.py --level C0,C1,C2,C3

# 全量：已实现的出 pass，其余按里程碑 skip
python3 tools/conformance_run.py --impl impl/adapter.py --format md --out report.md
```

## 4. 当前一致性结果

```
python3 tools/conformance_run.py --impl impl/adapter.py
→ 68 cases [C0..C7]: 28 pass, 0 fail, 40 skip
```

| 等级 | 结果 | 说明 |
|---|---|---|
| C0 | 5 pass / 2 manual skip | 信封、分帧、幂等、单调时钟 |
| C1 | 6 pass | 注册、保留命名空间、验签、App/公钥绑定、轮换 |
| C2 | 5 pass / 1 manual skip | 清单索引、发现响应、TTL |
| C3 | 12 pass | 绑定、衰减、撤销、风险与回执 |

C4–C7 共 37 条由适配器显式 `skip`，报告里写明归属里程碑。剩余的 3 条 skip 是 manual 用例（C0-01、C0-06、C2-05）。

C3 的 12 条都命中预期错误码，且实现被断言为“只在目标维度上失败”：C3-04…C3-07 的 `details.violations` 分别只有 `actions`、`resources`、`exp`、`depth`+`constraints.max_depth`。

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

## 6. 已知限制

1. **内存态**：幂等索引、注册表、轮换状态都在进程内，重启即丢；§7.8 要求可重建的持久索引，留给 M2.6。
2. **开发密钥环**：一致性适配器在导入时生成一次性 Ed25519 密钥并为示例 App 签清单。示例里的 `base64url-example-*` 是占位字符串，不是真实密钥。
3. **没有 OS 认证**：§4.2 的 `SO_PEERCRED`、audit token、package identity 都未实现；当前“App 身份”只来自清单签名。
4. **没有跨进程传输**：`stream` 与 `message` 只是编解码层，没有绑定到 UDS/XPC/D-Bus；由 M2.1b 处理。
5. **凭证只做结构校验**：`proof.sig` 未验证，`cap_id` 也未由 CA 签发密钥覆盖；需要把用户密钥分发与签名纳入 M2.4 之后的里程碑。
6. **`max_uses` 未计数**：衰减时比较上限，但使用次数没有落账，重放同一凭证不会被扣减。
7. **撤销只在内存**：`CapabilityAuthority.revoked` 是进程内集合，重启即丢，也没有广播；§5.5 要求撤销事件写入审计账本并通知受影响 Agent，留给 M2.6。
8. **任务与策略仍缺席**：C4 之后全部 `skip`，因此 28 个 pass 不证明任务语义、上下文或审计。

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
