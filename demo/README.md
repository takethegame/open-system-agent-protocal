# 三 Agent 演示（M2.7）

`demo/run_demo.py` 把参考实现串成一条可复核的端到端路径：`notes-agent` 与 `calendar-agent` 在同一个 `supervisor` 下完成一次“查笔记 → 找空档 → 准备 tentative 事件”的任务。它不引入新的协议语义，只调用 `impl/osap/` 中已经通过一致性用例的模块。

规范性内容以 [`../docs/standard.md`](../docs/standard.md) 为准；本目录只回答“这些模块如何协同”。

## 1. 运行

```bash
python3 -m pip install -r requirements.txt
python3 demo/run_demo.py
```

脚本只使用标准库与 `cryptography`，在任意工作目录运行都可以；不需要网络、不需要真实 App，也不读取墙钟。

预期结尾：

```text
== demo complete ==
registered=3 discovery=1 consent=1 delegated=2 context=1 audit=verified
trace=complete redaction=verified recovery=complete
```

任何一步不符合断言都会以非零状态退出，并打印 `demo assertion failed: ...`。CI 在单元测试之后执行同一条命令。

## 2. 演示了什么

| 步骤 | 调用 | 章节 | 对应用例 |
|---|---|---|---|
| 1. 清单与注册 | `crypto.sign_document`、`identity.Registrar` | §4.1–§4.5、§7.1 | C1-01…C1-06 |
| 2. 能力发现 | `registry.Registry.index_record` / `discover` | §6.5、§6.6 | C2-02、C2-03 |
| 3. 同意与能力 | `consent.validate`、`capability.CapabilityAuthority` | §5.2–§5.8 | C3-02、C3-03 |
| 4. 两次委派与结果 | `task.TaskBoard.delegate` / `transition` / `accept_result` | §8.3–§8.8 | C4-02、C4-03、C4-07 |
| 5. 上下文解析 | `context.ContextFabric.resolve` | §9.2–§9.4 | C5-01、C5-10 |
| 6. 审计链与导出 | `audit.verify_chain` / `redact_chain` / `recover_effects` / `trace_complete` | §8.11、§10.5–§10.6 | C7-02、C7-03、C7-06 |

任务树有两条并列支路：`supervisor → notes` 与 `supervisor → calendar`，因此跨过两个委派边界；三条 `trace_id` 相同的消息链（discover → notes delegate/result → calendar delegate/result）证明 trace 完整性。

## 3. C7-01 的手工复核

C7-01 仍是 manual 用例，因为它要求“真实三 App 集成 + 崩溃恢复”。本演示把可自动化的部分固定下来，便于逐条核对：

| C7-01 步骤 | 演示中的落点 |
|---|---|
| 运行三 App 的端到端任务 | 第 1–4 节，三个 Agent 各自注册并有任务或消息 |
| 检查每条消息的 `trace_id` 与 `causation_id` | `trace_messages`，由 `audit.trace_complete` 断言 |
| 按 `trace_id` 导出审计链 | `event_chain` 生成的链与消息共享 `TRACE` |
| 验证链完整性 | `audit.verify_chain` |
| 回放 trace 且不执行副作用 | `audit.recover_effects` 只读事件，不调用工具 |

真实的跨进程传输、持久账本与崩溃恢复仍不在本演示范围内，因此 C7-01 不改为 automated。

## 4. 确定性

- “现在”固定为 `2026-11-10T10:14:45Z`；能力有效期、句柄 TTL 与审计时间戳都以它为准，不使用墙钟。
- 每次运行生成新的 Ed25519 开发密钥，所以 `session_id` 与清单签名会变化；判定结果不变。
- 脱敏导出使用固定盐 `demo-export-salt`，便于对比；承诺值因此可复现，但真实导出必须每次生成新盐（`audit.redact_chain` 的默认行为）。

## 5. 不在演示范围内

1. **没有跨进程传输**：消息是内存字典，没有 UDS/XPC/D-Bus 绑定（M2.1b）。
2. **没有持久化**：任务树、能力、上下文与审计链都在进程内，重启即丢。
3. **没有真实 OS 句柄**：`ctx://` 解析只做授权与标签判定，不触碰系统联系人、文件或日历。
4. **外部协议未验签**：演示只用本地清单；MCP/A2A/OpenAPI 的信任归一由 C6 覆盖。
5. **`effect.*` 不真正写日历**：两段审计覆盖“意图 + 结果”的记账顺序，但不产生外部副作用。
