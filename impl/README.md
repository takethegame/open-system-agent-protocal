# 参考实现（M2.1）

本目录是 OSAP 0.1 的最小参考实现。当前阶段对应路线图 **M2.1：信封 + 传输绑定 + 错误模型**。

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

**不在本阶段**：身份与签名（M2.2）、能力签发与衰减（M2.3）、同意回执（M2.4）、任务模型（M2.5）、审计链（M2.6）。这些消息类型会抛 `NotImplementedError`，一致性运行器据此记为 `skip`，不会伪装成 `pass`。

## 2. 目录

```
impl/
  adapter.py            一致性适配器（tools/conformance_run.py --impl 的入口）
  osap/
    __init__.py         公共导出
    bus.py              握手、校验、路由、幂等、错误回执
    clock.py            单调时钟 deadline
    envelope.py         §7.1 校验（版本 → 类型 → schema）
    errors.py           §7.7 错误码与 OsapError
    framing.py          §7.9 两种分帧绑定
    idempotency.py      §7.8 幂等索引
  tests/                单元测试（unittest）
```

## 3. 运行

```bash
# 单元测试
python3 -m unittest discover -s impl/tests -t impl

# 只跑已实现的范围
python3 tools/conformance_run.py --impl impl/adapter.py --level C0

# 全量：已实现的出 pass，其余按里程碑 skip
python3 tools/conformance_run.py --impl impl/adapter.py --format md --out report.md
```

## 4. 当前一致性结果

```
python3 tools/conformance_run.py --impl impl/adapter.py
→ 68 cases [C0..C7]: 5 pass, 0 fail, 63 skip
```

C0 的 7 条中，5 条 automated 全部通过；C0-01 与 C0-06 是 manual（需要真实连接与绑定声明）。

| 用例 | 断言 | 实现点 |
|---|---|---|
| C0-01 | 未握手前拒绝 `request` | `Bus.state == awaiting_hello` |
| C0-02 | 主版本不兼容 | `envelope.major_version` |
| C0-03 | 单帧超过 8 MiB | `framing.check_size` |
| C0-04 | 未知消息类型 | `KNOWN_TYPES` 先于 schema 判定 |
| C0-05 | 重复 `id` 不重复副作用 | `IdempotencyIndex.execute_once` |
| C0-06 | 消息型传输不加长度前缀 | `framing.encode_message` 原样返回 |
| C0-07 | 墙钟回拨不延长超时 | `Deadline` 只用单调时钟 |

## 5. 设计决定

### 5.1 校验顺序

`envelope.validate` 的次序是 **版本 → 消息类型 → JSON Schema**。

如果把 schema 放在最前，`{"type": "bogus"}` 会先被 `enum` 拒绝并报 `SCHEMA_INVALID`；但 §7.9 明确要求未知类型返回 `SCHEMA_UNSUPPORTED`。顺序反过来才能同时满足两处。

“缺 `type`”仍按 `SCHEMA_INVALID` 处理：缺失字段是结构问题，不是未知类型。

### 5.2 消息型传输不加前缀

`encode_message` 原样返回对象，只做体积检查。给消息型绑定再套 4 字节长度前缀会让 C0-06 的观察结果变成“不一致”，因此实现里没有统一的 `encode()` 默认路径会偷偷加前缀。

### 5.3 deadline 用单调时钟

`Deadline.from_envelope` 只从信封里取**预算**（`deadline - ts`），之后一律用 `time.monotonic()` 计算剩余时间。墙钟只用于解析，不参与判定，这样回拨 120 秒或挂起恢复都不会“复活”请求。

### 5.4 错误码不复制到多处

`errors.STANDARD_CODES` 是唯一来源；`tests/test_envelope.py` 校验 `retryable` 默认值与 §7.7 表格一致。新增标准错误码时只需改这一处。

## 6. 已知限制

1. **内存态**：幂等索引、连接状态都在进程内，重启即丢；§7.8 要求可重建的持久索引，留给 M2.6。
2. **没有真实密码学**：`auth.token` 只做结构校验，不做签名验证；M2.2 引入 Ed25519。
3. **没有跨进程传输**：`stream` 与 `message` 只是编解码层，没有绑定到 UDS/XPC/D-Bus；M2.7 的演示再落地。
4. **能力与策略缺席**：C1–C7 目前全部 `skip`，因此 5 个 pass 只证明信封与分帧，不证明授权。

## 7. 与规范的偏差登记

| 位置 | 偏差 | 处理 |
|---|---|---|
| `welcome` 的 `body.schema` | 规范未定义 `osap.welcome/v1` 的字段，只要求版本协商 | 实现返回 `osap`、`binding`、`max_frame_bytes`，等 M2.2 补齐 |
| 未知但已定义的消息类型 | 规范未规定“已知类型尚未实现”的错误码 | 抛 `NotImplementedError`，由适配器记为 `skip`，不占用错误码命名空间 |
