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
| M1 可执行一致性 | ✅ 完成 | 68/68 用例（100%） | 2026-11-12 |
| M2 参考实现 MVP | ⬜ 未开始 | 0/7 子阶段 | — |
| M3 形式化不变量 | ⬜ 未开始 | 0/4 定理 | — |
| M4 标准打包 | ⬜ 未开始 | 0/4 产出 | — |
| M5 生态与采用 | ⬜ 未开始 | — | — |

仓库规模：

| 项目 | 数量 |
|---|---|
| 规范正文 | 131 节 |
| JSON Schema | 12（协议）+ 3（一致性：case / suite / report）= 15 |
| 示例 | 17 |
| 一致性用例 | 68 / 68 |
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
| `93f0d4e` | 2026-11-12 | 创建 `docs/progress.md`，拆分剩余用例 |
| `ba31745` | 2026-11-12 | **M1（续）**：C1 + C2 共 12 条，`examples/hello.json` |
| `043806f` | 2026-11-12 | 进展文档更新到 31/68 |
| `a34ec0f` | 2026-11-12 | **M1（续）**：C4 共 11 条；envelope 增加 peer/`session_id` 条件 |
| `b3b8ab5` | 2026-11-12 | **M1（续）**：C6 共 8 条（7 automated，1 manual） |
| `74a41ce` | 2026-11-12 | **M1（续）**：C5 共 11 条；新增上下文句柄与黑板夹具 |
| `012c9c7` | 2026-11-12 | **M1 完成**：C7 共 7 条；新增审计链夹具；报告纳入 schema 校验 |
| `e9079cc` | 2026-11-12 | M1 文档收尾（68/68）；`validate_examples.py` 扩到 24 项 |
| `32db5da` | 2026-11-13 | M1 复核：`--stub` 增加编号覆盖检查与夹具/mutation 实测 |

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

## 4. M1 — 可执行一致性（已完成）

### 4.1 交付物

| 文件 | 行数 | 作用 |
|---|---|---|
| `conformance/case.schema.json` | 161 | 单用例；`reject` 强制带 `error` |
| `conformance/suite.schema.json` | 20 | 按 level 分组的用例文件 |
| `conformance/report.schema.json` | 60 | 运行报告（standard §12.4） |
| `conformance/README.md` | 128 | 字段、mutation、适配器 API、新增流程 |
| `conformance/cases/C0-transport.json` | 125 | 7 条（5 automated，2 manual） |
| `conformance/cases/C1-identity.json` | 110 | 6 条（5 automated，1 `observe`） |
| `conformance/cases/C2-registry.json` | 109 | 6 条（4 automated，1 `observe`，1 manual） |
| `conformance/cases/C3-authorization.json` | 220 | 12 条（全 automated） |
| `conformance/cases/C4-collaboration.json` | 223 | 11 条（8 automated，3 manual） |
| `conformance/cases/C5-context.json` | 215 | 11 条（全 automated，其中 4 条 `observe`） |
| `conformance/cases/C6-federation.json` | 236 | 8 条（7 automated，1 manual） |
| `conformance/cases/C7-full.json` | 144 | 7 条（6 automated，1 manual） |
| `examples/hello.json` | 20 | 注册夹具（`osap.hello/v1`） |
| `examples/context-handle.json` | 19 | 上下文句柄夹具（标签、TTL、scope） |
| `examples/blackboard.json` | 23 | 任务黑板夹具（条目、版本、TTL） |
| `examples/audit-chain.json` | 52 | 3 条链式审计事件，止于 `effect.intent` |
| `tools/conformance_run.py` | 372 | 加载、校验、变异、执行、报告、报告 schema 校验 |

### 4.2 覆盖情况

| 等级 | 已迁移 | 总数 | 状态 |
|---|---|---|---|
| C0 Transport | 7 | 7 | ✅ |
| C1 Identity | 6 | 6 | ✅ |
| C2 Registry | 6 | 6 | ✅ |
| C3 Authorization | 12 | 12 | ✅ |
| C4 Collaboration | 11 | 11 | ✅ |
| C5 Context | 11 | 11 | ✅ |
| C6 Federation | 8 | 8 | ✅ |
| C7 Full | 7 | 7 | ✅ |
| **合计** | **68** | **68** | **100%** |

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
python3 tools/validate_examples.py          → OK: 24 checks passed
python3 tools/check_docs.py                 → OK: 104 checks passed across 20 Markdown files
python3 tools/conformance_run.py --stub     → 68 cases [C0, C1, C2, C3, C4, C5, C6, C7]: 0 pass, 0 fail, 68 skip
python3 tools/conformance_run.py --stub --format json --out conformance-report.json
                                            → summary: 68 total, 0 pass, 0 fail, 68 skip
                                            → report 通过 report.schema.json 校验
```

M1 收尾时的负向验证（均在临时目录，不随仓库发布）：

| 场景 | 结果 |
|---|---|
| 把某条用例的 `input.ref` 指向不存在的夹具 | 该条 `fail`，其余继续执行，退出码 1 |
| 把 mutation 的 `replace` 路径改成不存在的字段 | 该条 `fail`（`fixture error`） |
| 只加载 `C7-full.json` 跑 `check_ids` | 报 61 条缺号，退出码非 0 |
| 完整用例集合跑 `check_ids` | 通过 |

临时回显适配器（不随仓库发布）验证完整链路（C0–C3 共 19 条时）：

| 场景 | 结果 |
|---|---|
| 回显用例期望值 | 19 条中 17 pass、2 条 manual skip |
| mutation 生效检查（C3-01 / C3-09 / C3-10） | 通过 |
| 报告 JSON 对照 `report.schema.json` | 0 错误 |
| 错误适配器（全部返回 accept） | 12 fail，退出码 1 |
| `--stub` | 全部 skip，退出码 0 |

### 4.5 已知限制

1. **没有真实实现**：仓库内的 `--stub` 全部为 `skip`，不产生任何 `pass`。此前出现的 `pass` 都来自临时回显适配器，只证明 runner 与用例自洽，不证明协议可实现。
2. **mutation 只作用于主夹具**：`input.mutations` 不能同时改 `context` 中的多个文档。需要多文档变异时，只能把被改文档设为主夹具（C3-10–C3-12 就是这么做的）。
3. **缺少运行时状态模型**：C4-01（取消传播）、C7-01（trace 完整性）这类断言依赖实现暴露状态，目前只能标 manual。
4. **适配器 API 未冻结**：`conformance_check(case, documents)` 可能在 M2 中调整。
5. **`observe` 用例需要人工判定**：报告只记录实际结果，不产生 pass/fail。
6. **注册表错误码是近似映射**：C2-01 / C2-06 使用 `SCHEMA_INVALID`，但规范没有为注册表索引单独定义错误码；用例真正断言的是“索引 MUST 失败”，`notes` 已注明实现可返回领域前缀错误码。
7. **部分状态通过 `params` 模拟**：C4-07（已消耗预算）、C4-10（handoff 后的 owner）、C4-11（handoff 被拒绝）用 `params` 声明运行时前置状态，适配器需自行解释。这类用例可执行，但不如真实运行时模型严格。
8. **上下文夹具没有 JSON Schema**：`context-handle.json` 与 `blackboard.json` 的字段取自 §9.3–§9.5，但规范未定义 wire format，因此不纳入 `validate_examples.py`。字段调整不会触发 schema 校验。
9. **审计链错误码是扩展码**：C7-02 使用 `AUDIT_CHAIN_INVALID`，规范只要求“校验失败”，没有定义审计专用错误码。该码属于领域扩展命名空间，已在 `notes` 注明。

### 4.6 用例分布（迁移完成）

| 维度 | 数量 | 说明 |
|---|---|---|
| 总数 | 68 | C0 7 + C1 6 + C2 6 + C3 12 + C4 11 + C5 11 + C6 8 + C7 7 |
| automated | 60 | 其中 7 条为 `observe` |
| manual | 8 | C0-01、C0-06、C2-05、C4-01、C4-08、C4-09、C6-08、C7-01 |
| `observe` | 14 | 7 条 automated + 7 条 manual |

手动用例集中在三类：传输/时钟运行时（C0）、TTL 与生命周期（C2、C6）、崩溃与跨 App 集成（C4、C7）。`observe` 用例不产生自动判定，报告只记录实现的实际行为。

### 4.7 夹具缺口

全部夹具已就位：

| 夹具 | 用于 | 状态 |
|---|---|---|
| `hello.json` | C1 | ✅ |
| `context-handle.json` | C5 | ✅ |
| `blackboard.json` | C5 | ✅ |
| `audit-chain.json` | C7 | ✅ |

C2/C4/C6 复用 `manifest.json`、`discovery-result.json`、`capability-record.json`、`task.json`、`delegate.json`、`handoff.json`、`result.json`。

### 4.8 M1 退出标准

- [x] 68 个用例全部可加载，case / suite schema 校验通过；
- [x] `--stub` 输出 68 条 `skip`；
- [x] JSON 报告通过 `report.schema.json` 校验；
- [x] CI 同时运行用例检查与报告校验；
- [x] 编号覆盖：用例集合与 `docs/conformance.md` 表格逐条相等（缺号/多号即失败）；
- [x] 夹具可执行：`--stub` 也解析 `input.ref`、`context` 并应用全部 mutation，路径不存在即失败。

后续工作（不属于 M1 退出标准）：

- 用真实适配器跑通 C0–C3（M2）；
- 冻结适配器 API（M2.1）。

之后进入 M2.1（信封 + 错误模型）。

---

## 5. 待确认的规范问题

迁移过程中暴露的歧义。M1 用例已按暂定处理落盘，以下条目需在 M2 冻结适配器 API 前定稿（不改编号，只补语义）：

| 编号 | 问题 | 处理 | 状态 |
|---|---|---|---|
| C1-05 | 密钥轮换后旧签名“按策略”拒绝，缺少最低要求 | 写为 `observe`，建议 §4.5 补“过渡期 MUST 不超过 TTL” | ⬜ 待定 |
| C2-05 | “TTL 内失效”未说明失效上限 | 以 `freshness.expires_at` 为唯一判据 | ✅ 已采用 |
| C4-02 | 委派预算超过父剩余时应返回哪个错误码未定义 | 暂用 `POLICY_DENIED`，用例断言“拒绝委派”这一不变量 | ⬜ 待定 |
| C5-11 | “幂等索引/审计日志/任务树”如何判定被当记忆检索 | 依赖实现自证，标 `observe` | ⬜ 待定 |
| C6-07 | `origin=external` 在 `capability-record.schema.json` 中没有对应字段 | 用例把 `origin` 作为投影后的规范化输出断言；是否写入 schema 待定 | ⬜ 待定 |
| C7-02 | 审计链校验失败没有标准错误码 | 暂用扩展码 `AUDIT_CHAIN_INVALID`，用例断言“校验 MUST 失败” | ⬜ 待定 |
| C7-07 | “被攻破的 Bus”在 0.1 的期望不明确 | 明确为“0.1 不提供该防护”，用例只记录 | ⬜ 待定 |

---

## 6. 下一步（按顺序）

1. 以 M1 用例为验收标准进入 M2.1：信封 + 错误模型；
2. 在 M2 中把临时回显适配器替换为真实实现，先跑通 C0–C3；
3. 根据实现反馈修正规范歧义，再冻结适配器 API。

---

## 7. 变更记录

| 日期 | 变更 |
|---|---|
| 2026-11-12 | 创建本文；记录 M0 完成、M1 达到 19/68、剩余用例拆分 |
| 2026-11-12 | M1 扩展到 31/68（C1 6 条、C2 6 条）；补 `examples/hello.json`；登记注册表错误码近似映射 |
| 2026-11-12 | M1 扩展到 42/68（C4 11 条）；envelope 增加 peer/`session_id` 条件；登记 `params` 状态模拟与委派预算错误码问题 |
| 2026-11-12 | M1 扩展到 50/68（C6 8 条）；登记 `origin` 在能力记录 schema 中缺少字段的问题 |
| 2026-11-12 | M1 扩展到 61/68（C5 11 条）；新增 `context-handle.json` 与 `blackboard.json`；登记夹具无 schema 的限制 |
| 2026-11-12 | **M1 完成**：68/68；新增 C7 与 `audit-chain.json`；JSON 报告纳入 schema 校验 |
