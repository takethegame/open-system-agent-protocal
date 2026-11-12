# OSAP 进展记录

> 更新时间：2026-11-12
> 关联规划：[`roadmap.md`](roadmap.md)
> 性质：工作记录（非规范性）。规范性内容以 [`standard.md`](standard.md) 为准。

本文记录已完成的里程碑、验证证据、设计决定、已知限制，以及剩余工作的逐条拆分。每完成一个里程碑追加一节，不覆盖历史。

---

## 1. 当前快照

| 里程碑 | 状态 | 进度 | 完成日期 |
|---|---|---|---|
| M0 仓库可信化 | ✅ 完成 | 7/7 | 2026-11-12 |
| M1 可执行一致性 | 🟡 进行中 | 19/68 用例（28%） | — |
| M2 参考实现 MVP | ⬜ 未开始 | 0/7 子阶段 | — |
| M3 形式化不变量 | ⬜ 未开始 | 0/4 定理 | — |
| M4 标准打包 | ⬜ 未开始 | 0/4 产出 | — |
| M5 生态与采用 | ⬜ 未开始 | — | — |

仓库规模：

| 项目 | 数量 |
|---|---|
| 规范正文 | 131 节 |
| JSON Schema | 12（协议）+ 3（一致性：case / suite / report）= 15 |
| 示例 | 13 |
| 一致性用例 | 19 / 68 |
| 校验工具 | 4 |
| Markdown 文件 | 20 |
| 中英平行文档 | 8 对 |
| CI 工作流 | 1（Python 3.11 / 3.12） |

---

## 2. 提交时间线

| commit | 日期 | 内容 |
|---|---|---|
| `440dde5` | 2026-11-10 | first commit：规范、schema、示例骨架 |
| `0ea4714` | 2026-11-10 | version 1：补全 12 schema、13 示例、校验脚本 |
| `aa1a1d7` | 2026-11-11 | 收紧 handoff、同意绑定、一致性表述 |
| `d932070` | 2026-11-11 | 英文平行译本（7 个 `*.en.md`） |
| `1d38d32` | 2026-11-12 | **M0**：CI、安全策略、变更记录、路线图 |
| `f8e13bd` | 2026-11-12 | **M1（部分）**：C0 + C3 共 19 条可执行用例 |

---

## 3. M0 — 仓库可信化（已完成）

### 3.1 交付物

| 文件 | 行数 | 作用 |
|---|---|---|
| `.gitignore` | 20 | 忽略 `.idea/`、`__pycache__`、`.venv`、本地报告 |
| `requirements.txt` | 3 | `jsonschema` 4.18+、`referencing` 0.30+ |
| `.github/workflows/ci.yml` | 44 | 3.11/3.12 矩阵，4 个检查步骤 |
| `tools/check_schemas.py` | 108 | 元校验、`$id` 唯一性、`$ref` 目标 |
| `tools/check_docs.py` | 164 | JSON 块、围栏、断链、中英结构、敏感字符串 |
| `SECURITY.md` / `SECURITY.en.md` | 62 / 62 | 披露渠道、7/14/90 天时限、评审触发条件 |
| `CHANGELOG.md` | 82 | Keep a Changelog，回填 0.1 |
| `docs/roadmap.md` | 340 | M0–M5、决策闸门、风险登记 |
| `README.md` / `README.en.md` | 修改 | CI 徽章、文档表、仓库结构、校验命令 |

### 3.2 改名记录

| 项目 | 旧 | 新 |
|---|---|---|
| GitHub 仓库 | `takethegame/open-system-agent-protocal` | `takethegame/open-system-agent-protocol` |
| 本地目录 | `~/project/os-agent-communication-protocal` | `~/project/open-system-agent-protocol` |
| `origin` | `git@github.com:takethegame/open-system-agent-protocal.git` | `git@github.com:takethegame/open-system-agent-protocol.git` |

GitHub 侧由仓库管理员改名；本地由 `mv` + `git remote set-url` 完成，会话工作目录同步迁移。旧 URL 由 GitHub 重定向。

### 3.3 验证证据

```
python3 tools/check_schemas.py      → OK: 36 checks passed across 12 schemas
python3 tools/validate_examples.py  → OK: 20 checks passed
python3 tools/check_docs.py         → OK: 96 checks passed across 18 Markdown files
```

CI：

| commit | 运行 | 结论 |
|---|---|---|
| `1d38d32` | [43196619992](https://github.com/takethegame/open-system-agent-protocol/actions/runs/43196619992) | ✅ success（3.11 + 3.12） |
| `f8e13bd` | [43207360154](https://github.com/takethegame/open-system-agent-protocol/actions/runs/43207360154) | in progress |

### 3.4 遗留风险

- 改名不会重定向 GitHub Pages 与 package 名；目前两者都未使用，暂不处理。
- `CHANGELOG.md` 仅英文，与中文原文的双语政策不一致；理由是条目对应英文 commit message，且属于流程文档而非规范。

---

## 4. M1 — 可执行一致性（进行中）

### 4.1 交付物

| 文件 | 行数 | 作用 |
|---|---|---|
| `conformance/case.schema.json` | 155 | 单用例；`reject` 强制带 `error` |
| `conformance/suite.schema.json` | 20 | 按 level 分组的用例文件 |
| `conformance/report.schema.json` | 60 | 运行报告（standard §12.4） |
| `conformance/README.md` | 128 | 字段、mutation、适配器 API、新增流程 |
| `conformance/cases/C0-transport.json` | 125 | 7 条（5 automated，2 manual） |
| `conformance/cases/C3-authorization.json` | 220 | 12 条（全 automated） |
| `tools/conformance_run.py` | 361 | 加载、校验、变异、执行、报告 |

### 4.2 覆盖情况

| 等级 | 已迁移 | 总数 | 状态 |
|---|---|---|---|
| C0 Transport | 7 | 7 | ✅ |
| C1 Identity | 0 | 6 | ⬜ |
| C2 Registry | 0 | 6 | ⬜ |
| C3 Authorization | 12 | 12 | ✅ |
| C4 Collaboration | 0 | 11 | ⬜ |
| C5 Context | 0 | 11 | ⬜ |
| C6 Federation | 0 | 8 | ⬜ |
| C7 Full | 0 | 7 | ⬜ |
| **合计** | **19** | **68** | **28%** |

### 4.3 设计决定

| 决定 | 理由 |
|---|---|
| mutation 由 runner 统一应用（RFC 6901） | 各实现不必重复解释变异语义，减少互操作分歧 |
| `expect.outcome` 三值：`accept` / `reject` / `observe` | `observe` 覆盖“视为不一致”类检查，避免把主观判断写成断言 |
| `reject` 必须带 `error` | 用 schema 强制，防止用例写出无法判定的期望 |
| `mode: manual` | 握手状态、时钟回拨、崩溃恢复需要运行时条件，标注而非伪造自动化 |
| 适配器返回 `{"outcome":"skip"}` | 能力子集实现可以显式跳过，其余异常一律 `fail` |
| 用例 `title` 用英文 | 便于外部实现者阅读，也是报告中的直接展示字段 |
| `--stub` 取代独立 stub 脚本 | 无适配器时全部 skip，同时仍校验用例格式 |

### 4.4 验证证据

```
python3 tools/check_schemas.py              → OK: 45 checks passed across 15 schemas
python3 tools/validate_examples.py          → OK: 20 checks passed
python3 tools/check_docs.py                 → OK: 100 checks passed across 19 Markdown files
python3 tools/conformance_run.py --stub     → 19 cases [C0, C3]: 0 pass, 0 fail, 19 skip
```

临时回显适配器（不随仓库发布）验证完整链路：

| 场景 | 结果 |
|---|---|
| 回显用例期望值 | 19 条中 17 pass、2 条 manual skip |
| mutation 生效检查（C3-01 / C3-09 / C3-10） | 通过 |
| 报告 JSON 对照 `report.schema.json` | 0 错误 |
| 错误适配器（全部返回 accept） | 12 fail，退出码 1 |
| `--stub` | 全部 skip，退出码 0 |

### 4.5 已知限制

1. **没有真实实现**：所有 `pass` 都来自回显适配器，只证明 runner 与用例自洽，不证明协议可实现。
2. **mutation 只作用于主夹具**：`input.mutations` 不能同时改 `context` 中的多个文档。需要多文档变异时，只能把被改文档设为主夹具（C3-10–C3-12 就是这么做的）。
3. **缺少运行时状态模型**：C4-01（取消传播）、C7-01（trace 完整性）这类断言依赖实现暴露状态，目前只能标 manual。
4. **适配器 API 未冻结**：`conformance_check(case, documents)` 可能在 M2 中调整。
5. **`observe` 用例需要人工判定**：报告只记录实际结果，不产生 pass/fail。

### 4.6 剩余 49 条用例拆分

预估口径：**S** < 1 小时（直接变异现有夹具），**M** 1–2 小时（需补充夹具或多文档状态），**L** > 2 小时（需运行时状态或人工步骤）。

#### C1 — Identity（6 条，全部需要身份夹具）

| ID | 场景 | 所需夹具/操作 | 方式 | 预估 |
|---|---|---|---|---|
| C1-01 | 未注册 Agent 连接 | 新增 `hello.json` | automated | M |
| C1-02 | 注册 `agent://system/...` | 新增 `registration.json`，改 `agent` | automated | S |
| C1-03 | App 签名不匹配 | `manifest.json` 改 `/signature` | automated | M |
| C1-04 | Agent 自称属于其他 App | `registration.json` 改 `app`/`agent` | automated | M |
| C1-05 | 密钥轮换后旧签名 | 需轮换状态与过渡期策略 | automated + `observe` | M |
| C1-06 | `hello.public_key` 未绑定 App 身份 | `hello.json` 去掉绑定字段 | automated | M |

#### C2 — Registry（6 条，多数可复用现有夹具）

| ID | 场景 | 所需夹具/操作 | 方式 | 预估 |
|---|---|---|---|---|
| C2-01 | 未签名清单 | `manifest.json` 删除 `/signature` | automated | S |
| C2-02 | 发现私有数据 | `discovery-result.json` 断言无 `data` 字段 | automated | S |
| C2-03 | 实时 `policy_verdict` / 缺 `consent_hint` | 变异 `discovery-result.json` | `observe` | S |
| C2-04 | 过期能力记录 | `capability-record.json` 改 `/freshness/expires_at` | automated | M |
| C2-05 | 原生能力删除 | 需要 TTL 推进 | manual | M |
| C2-06 | 联邦记录缺 `provenance` | 删除 `/provenance` | automated | S |

#### C4 — Collaboration（11 条，依赖任务与 handoff 夹具）

| ID | 场景 | 所需夹具/操作 | 方式 | 预估 |
|---|---|---|---|---|
| C4-01 | 父任务取消 | 需任务树运行时状态 | manual | L |
| C4-02 | 子预算超父剩余 | `delegate.json` 改 `/body/data/budget` | automated | M |
| C4-03 | 结果 schema 不匹配 | `result.json` 改 `/body/schema` | automated | S |
| C4-04 | peer 无 `session_id` | `request.json` 删除 `/session_id` | automated | S |
| C4-05 | peer 使用对方能力 | `request.json` + `delegate.json` 组合 | automated | M |
| C4-06 | handoff 未重新同意 L3 | `handoff.json` 去回执 + `risk=L3` | automated | M |
| C4-07 | 超预算 | 需累计消耗状态 | automated | M |
| C4-08 | Bus 重启后未完成任务 | 需重启流程与审计断言 | manual | L |
| C4-09 | 副作用前崩溃（只有 intent） | 需 intent/outcome 状态 | manual | L |
| C4-10 | handoff 后原 owner 仍发请求 | 需所有权状态 | automated | M |
| C4-11 | handoff 被拒绝 | 需状态与预算快照 | automated | M |

#### C5 — Context（11 条，当前完全没有夹具）

| ID | 场景 | 所需夹具/操作 | 方式 | 预估 |
|---|---|---|---|---|
| C5-01 | 无 `resolve` 能力解析句柄 | 新增 `context-handle.json` | automated | M |
| C5-02 | 过期句柄 | 改 `/ttl` 或 `/expires_at` | automated | S |
| C5-03 | 派生对象降低标签 | 需标签传播规则 | automated | M |
| C5-04 | `secret` 出口 | 改 `/label` 为 `secret` | automated | M |
| C5-05 | 任务结束黑板清理 | 新增 `blackboard.json` | automated | M |
| C5-06 | 删除对象引用检查 | 需对象引用状态 | automated | M |
| C5-07 | 缓存超过句柄 TTL | 需缓存状态 | automated | M |
| C5-08 | `managed_store` 无配额/GC | 声明检查 | `observe` | S |
| C5-09 | 句柄绕过 OS 权限 | 需 OS 句柄映射 | automated | M |
| C5-10 | 无 `memory.read` 读记忆 | 需记忆句柄夹具 | automated | M |
| C5-11 | 幂等索引当记忆检索 | 声明检查 | `observe` | S |

#### C6 — Federation（8 条，可复用能力记录）

| ID | 场景 | 所需夹具/操作 | 方式 | 预估 |
|---|---|---|---|---|
| C6-01 | AppFunction 投影 | `capability-record.json` 改 `source` | automated | M |
| C6-02 | App Intent 投影 | 同上 | automated | M |
| C6-03 | App Action 投影 | 同上 | automated | M |
| C6-04 | MCP tool 投影 | 同上，保留 server/tool | automated | M |
| C6-05 | A2A skill 投影 | 需 Agent Card 片段 | automated | M |
| C6-06 | D-Bus method 投影 | 需 bus/path/interface/method | automated | M |
| C6-07 | 外部内容 | 改 `/provenance/trust` | automated | S |
| C6-08 | 原生能力变更 | 需 TTL 推进 | manual | M |

#### C7 — Full（7 条，偏集成与人工）

| ID | 场景 | 所需夹具/操作 | 方式 | 预估 |
|---|---|---|---|---|
| C7-01 | 跨 3 个 App 的任务 | 需完整 trace | manual | L |
| C7-02 | 审计链篡改 | `audit-event.json` 改 `/prev_hash` | automated | S |
| C7-03 | 用户导出审计 | 需导出与脱敏规则 | automated | M |
| C7-04 | 跨用户请求 | 需多主体状态 | automated | M |
| C7-05 | 回放不重复副作用 | 需幂等索引状态 | automated | M |
| C7-06 | L3 只有 intent 无 outcome | 需 intent/outcome 状态 | manual | M |
| C7-07 | 被攻破的 Bus | 0.1 明确失败 | manual | M |

**总量估算**：S 约 9 条、M 约 30 条、L 约 10 条，合计约 **35–45 小时**。

### 4.7 夹具缺口

当前 `examples/` 缺少以下夹具，需在迁移前补齐：

| 夹具 | 用于 | 内容要点 |
|---|---|---|
| `hello.json` | C1-01、C1-06 | `osap`、`public_key`、`app`、`conformance` |
| `registration.json` | C1-02、C1-04 | `agent`、`app`、`public_key`、`proof` |
| `context-handle.json` | C5-01、C5-02、C5-04 | `ctx://`、`ttl`、`label`、`owner_task` |
| `blackboard.json` | C5-05 | `task_id`、`entries`、`ttl` |
| `audit-chain.json` | C7-02 | 至少 3 条带 `prev_hash` 的事件 |

C2/C4/C6 可复用现有 `manifest.json`、`discovery-result.json`、`capability-record.json`、`task.json`、`delegate.json`、`handoff.json`、`result.json`。

### 4.8 迁移顺序建议

1. **C2（6 条）**：成本最低，先验证 `manifest` / `capability-record` / `discovery` 的变异路径；
2. **C1（6 条）**：补 `hello.json` 与 `registration.json`，顺带补齐 M2 需要的握手夹具有；
3. **C4（11 条）**：先做 6 条 automated，manual 4 条留到 M2 有实现后；
4. **C6（8 条）**：一次性覆盖 6 种 source kind；
5. **C5（11 条）**：补上下文夹具后再做；
6. **C7（7 条）**：放最后，依赖 M2 的运行时可观测性。

---

## 5. 待确认的规范问题

迁移过程中暴露的歧义，需在 M1 结束前定稿（不改编号，只补语义）：

| 编号 | 问题 | 暂定处理 |
|---|---|---|
| C1-05 | 密钥轮换后旧签名“按策略”拒绝，缺少最低要求 | 写为 `observe`，并在 §4.5 补“过渡期 MUST 不超过 TTL” |
| C2-05 | “TTL 内失效”未说明失效上限 | 以 `freshness.expires_at` 为唯一判据 |
| C5-11 | “幂等索引/审计日志/任务树”如何判定被当记忆检索 | 依赖实现自证，标 `observe` |
| C7-07 | “被攻破的 Bus”在 0.1 的期望不明确 | 明确为“0.1 不提供该防护”，用例只记录 |

---

## 6. 下一步（按顺序）

1. 补 `hello.json`、`registration.json`、`context-handle.json`、`blackboard.json`、`audit-chain.json`；
2. 迁移 C2 + C1 共 12 条，使 M1 达到 31/68；
3. 迁移 C4 的 6 条 automated；
4. 迁移 C6 的 8 条；
5. 迁移 C5 + C7，M1 收尾；
6. 进入 M2.1（信封 + 错误模型）。

---

## 7. 变更记录

| 日期 | 变更 |
|---|---|
| 2026-11-12 | 创建本文；记录 M0 完成、M1 达到 19/68、剩余用例拆分 |
