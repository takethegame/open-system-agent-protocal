# 参考实现（M2.1 + M2.2）

本目录是 OSAP 0.1 的最小参考实现。已完成路线图的 **M2.1a（信封 + 分帧 + 错误模型）** 与 **M2.2（身份 + 签名 + 注册表）**。

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

**不在本阶段**：能力签发与衰减（M2.3）、同意回执（M2.4）、任务模型（M2.5）、审计链（M2.6）、真实 OS 传输绑定（M2.1b）。未实现的类型会抛 `NotImplementedError`，一致性运行器据此记为 `skip`。

## 2. 目录

```
impl/
  adapter.py            一致性适配器（tools/conformance_run.py --impl 的入口）
  osap/
    __init__.py         公共导出
    bus.py              握手、校验、路由、幂等、错误回执
    clock.py            单调时钟 deadline
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
python3 tools/conformance_run.py --impl impl/adapter.py --level C0,C1,C2

# 全量：已实现的出 pass，其余按里程碑 skip
python3 tools/conformance_run.py --impl impl/adapter.py --format md --out report.md
```

## 4. 当前一致性结果

```
python3 tools/conformance_run.py --impl impl/adapter.py
→ 68 cases [C0..C7]: 16 pass, 0 fail, 52 skip
```

| 等级 | 结果 | 说明 |
|---|---|---|
| C0 | 5 pass / 2 manual skip | 信封、分帧、幂等、单调时钟 |
| C1 | 6 pass | 注册、保留命名空间、验签、App/公钥绑定、轮换 |
| C2 | 5 pass / 1 manual skip | 清单索引、发现响应、TTL |

C3–C7 共 52 条由适配器显式 `skip`，报告里写明归属里程碑。

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

## 6. 已知限制

1. **内存态**：幂等索引、注册表、轮换状态都在进程内，重启即丢；§7.8 要求可重建的持久索引，留给 M2.6。
2. **开发密钥环**：一致性适配器在导入时生成一次性 Ed25519 密钥并为示例 App 签清单。示例里的 `base64url-example-*` 是占位字符串，不是真实密钥。
3. **没有 OS 认证**：§4.2 的 `SO_PEERCRED`、audit token、package identity 都未实现；当前“App 身份”只来自清单签名。
4. **没有跨进程传输**：`stream` 与 `message` 只是编解码层，没有绑定到 UDS/XPC/D-Bus；由 M2.1b 处理。
5. **能力与策略缺席**：C3 之后全部 `skip`，因此现有 16 个 pass 不证明授权或任务语义。

## 7. 与规范的偏差登记

| 位置 | 偏差 | 处理 |
|---|---|---|
| `welcome` 的 `body.schema` | 规范未定义 `osap.welcome/v1` 的字段 | 返回 `osap`、`session_id`、`app`、`features`、`limits`，等 M2.4 定稿后回写规范 |
| 未知但已定义的消息类型 | 规范未规定“已知类型尚未实现”的错误码 | 抛 `NotImplementedError`，由适配器记为 `skip` |
| 注册表索引失败的错误码 | 规范未为 RFS 定义专用错误码 | 沿用 C2-01/C2-06 的 `SCHEMA_INVALID`，与用例保持一致 |
| 签名规范化 | 未采用完整 RFC 8785 | 采用 key 排序的 UTF-8 JSON，并在 `crypto.py` 里写明；M4 打包时再对齐 |
