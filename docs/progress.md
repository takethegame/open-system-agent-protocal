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
| M2 参考实现 MVP | 🟡 进行中 | M2.1a + M2.2 + M2.3 + M2.4 + M2.5a + M2.5b 完成（6/8 子阶段） | — |
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
| Markdown 文件 | 21 |
| 参考实现 | 15 个模块 + 适配器（2804 行）+ 201 个单元测试 |
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
| `add9162` | 2026-11-13 | M1 复核：`--stub` 增加编号覆盖检查与夹具/mutation 实测 |
| `eb19411` | 2026-11-13 | **M2.1a**：信封、错误模型、分帧、握手、幂等、单调时钟（32 tests；C0 5 pass） |
| `f8d37b7` | 2026-11-13 | **M2.2**：Ed25519 签名、注册、注册表（62 tests；累计 16 pass） |
| `a41ec78` | 2026-11-13 | **M2.3 + M2.4**：能力衰减、绑定、撤销、风险前置、回执（118 tests；累计 28 pass） |
| `2e05890` | 2026-11-14 | **M2.5a**：任务树、委派预算、取消、结果、handoff（160 tests；累计 36 pass） |
| `206008b` | 2026-11-14 | **M2.5b**：上下文织构、标签、出口、黑板、删除、缓存、存储声明（201 tests；累计 47 pass） |

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

## 5. M2 — 参考实现（进行中）

### 5.1 交付物

`impl/` 是 0.1 的最小参考实现，语言为 Python 3.11+，只新增 `cryptography` 一个依赖。

| 模块 | 行数 | 职责 | 章节 | 阶段 |
|---|---|---|---|---|
| `impl/osap/envelope.py` | 112 | 信封校验、路由键、任务 ID | §7.1 | M2.1a |
| `impl/osap/errors.py` | 105 | 27 个标准错误码、`retryable` 默认值 | §7.7 | M2.1a |
| `impl/osap/framing.py` | 92 | 流式前缀、消息型边界、8 MiB 上限 | §7.9、§7.10 | M2.1a |
| `impl/osap/clock.py` | 71 | 单调时钟 deadline | §7.8 | M2.1a |
| `impl/osap/idempotency.py` | 45 | 按 `id` 去重 | §7.8 | M2.1a |
| `impl/osap/bus.py` | 154 | 握手、校验、路由、幂等、错误回执 | §7.1、§7.9 | M2.1a |
| `impl/osap/schema.py` | 60 | schema 加载与错误映射 | — | M2.2 |
| `impl/osap/crypto.py` | 104 | Ed25519 签名与规范化 JSON | §4.5 | M2.2 |
| `impl/osap/identity.py` | 127 | 注册、保留命名空间、App/公钥绑定 | §4.1–§4.4 | M2.2 |
| `impl/osap/registry.py` | 208 | 清单、能力记录、发现、能力描述解析 | §6 | M2.2 |
| `impl/osap/capability.py` | 235 | 能力凭证、衰减、绑定、撤销、风险前置 | §5.2–§5.7 | M2.3 |
| `impl/osap/consent.py` | 120 | 同意回执与能力范围校验 | §5.8 | M2.4 |
| `impl/osap/task.py` | 425 | 任务树、预算、取消、结果、handoff | §8.2–§8.10 | M2.5a |
| `impl/osap/context.py` | 289 | 句柄、标签、黑板、对象、缓存、存储声明 | §9.2–§9.10 | M2.5b |
| `impl/adapter.py` | 614 | 一致性适配器 | — | M2.1a–M2.5b |

`impl/tests/` 有 201 个单元测试，覆盖分帧往返与边界、校验顺序、幂等、时钟回拨、错误码默认值、签名与篡改、注册拒绝路径、注册表 TTL 与发现过滤、衰减的十项规则（逐维度）、撤销级联、绑定三项、回执的校验顺序、任务状态机、取消传播、委派预算与深度、结果契约、handoff 的五类拒绝路径，以及上下文句柄的授权/过期/标签/出口/黑板/删除/缓存/存储/记忆边界。

### 5.2 验证证据

```
python3 -m unittest discover -s impl/tests -t impl
    → Ran 201 tests ... OK
python3 tools/conformance_run.py --impl impl/adapter.py
    → 68 cases [C0..C7]: 47 pass, 0 fail, 21 skip
```

| 等级 | 结果 | 覆盖点 |
|---|---|---|
| C0 | 5 pass / 2 manual skip | 版本、帧大小、未知类型、幂等、单调时钟 |
| C1 | 6 pass | 未注册、保留命名空间、验签失败、App 越权、轮换宽限、公钥未绑定 |
| C2 | 5 pass / 1 manual skip | 无签名清单、发现无泄漏、静态 `consent_hint`、TTL 过期、缺 `provenance` |
| C3 | 12 pass | audience/task/subject 绑定、四项衰减、撤销级联、L3 无回执、回执过期与范围不足 |
| C4 | 8 pass / 3 manual skip | 委派预算、结果契约、peer 会话、他人能力、handoff 重同意、运行期预算、所有权、拒绝 handoff |
| C5 | 11 pass | 解析授权、过期不续期、标签继承、出口同意、黑板清理、引用检查、缓存钳制、存储职责、OS 权限、记忆边界 |

C3 的 12 条不仅错误码匹配，`details.violations` 也被断言为只含目标维度：

| 用例 | 命中维度 |
|---|---|
| C3-04 | `["actions"]` |
| C3-05 | `["resources"]` |
| C3-06 | `["exp"]` |
| C3-07 | `["depth", "constraints.max_depth"]` |

C4 的 8 条 automated 全部通过，且每条都核对过拒绝原因：

| 用例 | 拒绝点 |
|---|---|
| C4-02 | 委派 `wall_ms=9000` > 父剩余 `8000` |
| C4-03 | 结果 `body.schema` 与 `result_schema` 不符 |
| C4-04 | `mode=peer` 但缺 `session_id`（信封 schema 的条件分支） |
| C4-05 | 凭证 `subject` 是 calendar，发送方是 orchestrator |
| C4-06 | L3 handoff 没有指向新 owner 的回执 |
| C4-07 | 已消耗 `wall_ms=6000` > 预算 `5000` |
| C4-10 | handoff 后 owner 已是 calendar，orchestrator 再发 `request` |
| C4-11 | 拒绝 handoff：`owner`/`budget`/`status` 三项均未变 |

C5 的 11 条同样逐条核对：

| 用例 | 实际判定 |
|---|---|
| C5-01 | 只有 `read`，缺 `resolve`，`details.required_action=resolve` |
| C5-02 | `expires_at=09:00Z` 早于夹具“现在”`10:14:45Z`，报 `CONTEXT_EXPIRED` |
| C5-03 | 声明 `public`、来源 `sensitive`，报告 `lowered=true`、`effective_label=sensitive` |
| C5-04 | `secret` + `egress=true` + 无用户放行，报 `POLICY_CONSENT_REQUIRED` |
| C5-05 | 黑板归档 2 条，`promoted_to_memory=false` |
| C5-06 | 引用数 2，软删除返回 `tombstoned=true` 且 `audit_written=true` |
| C5-07 | 请求 900 s 被钳到句柄 TTL 600 s，700 s 时 `cache_hit=false` |
| C5-08 | `managed_store` 缺配额、GC、崩溃恢复、加密、路径安全、删除六项职责 |
| C5-09 | `file://` 句柄在 `os_permission=denied` 时先被 OS 边界拒绝 |
| C5-10 | 记忆句柄只有 `task.read`，缺 `memory.read`，`required_action=memory.read` |
| C5-11 | 幂等索引、审计日志、任务树三项都被列为禁止晋升 |

C1-05 与 C2-03 是 `observe`：前者规范允许“拒绝或宽限期接受”，实现选择拒绝；后者报告实际观察到的字段。

### 5.3 设计决定

| 决定 | 理由 |
|---|---|
| 校验顺序：版本 → 类型 → JSON Schema | §7.9 要求未知类型返回 `SCHEMA_UNSUPPORTED`；若先跑 schema，`enum` 会先报 `SCHEMA_INVALID` |
| 消息型绑定不设统一加前缀的 `encode()` 默认路径 | 避免 C0-06 的“再套一层长度前缀” |
| deadline 只保存预算，剩余时间一律用 `time.monotonic()` | 墙钟回拨或挂起恢复不得复活请求（C0-07） |
| `STANDARD_CODES` 单点定义 | 错误码只出现一次，测试反查 §7.7 的 `retryable` 列 |
| 签名覆盖“去掉 `signature` 后的 key 排序 JSON” | 确定性强、跨语言可复现；不是完整 RFC 8785，已在代码里写明 |
| 注册按固定顺序拒绝，不区分原因对外暴露 | 避免把“App 未注册”“公钥不匹配”变成探测信号（§4.1） |
| 清单先验签再索引，记录先验证再判 TTL | §6.1 与 §6.10 的顺序要求 |
| 已定义但未实现的消息类型抛 `NotImplementedError` | 不占用错误码命名空间，也不伪装成 `pass` |
| 衰减只从“原始夹具”派生父凭证 | C3-04…C3-07 的 `context` 指向未变异的能力夹具，适配器取 `cap_id = parent_cap_id`、`depth = depth - 1`；父与子只在被测维度不同，违例不会被共享变异抵消 |
| 接收方从信封解析，不从凭证读取 | 若拿凭证自己的 `audience` 当接收方，C3-01 会假通过；`to.capability` 经注册表解析到声明该能力的 Agent |
| 能力与回执的“现在”取信封 `ts` | 夹具固定在 2026-11-10，用例不会随时间失效，且同一条消息共享同一时间基准 |
| 回执校验顺序：决策 → 过期 → 范围 | 同一输入总是同一错误码；C3-10（同时过期且范围变窄）必须报 `POLICY_CONSENT_EXPIRED` |
| 父凭证限定的预算维度在子凭证缺失时视为放宽 | `max_budget` 省略某维等于无界，与 AI2“单调收窄”一致 |
| 委派超预算报 `POLICY_DENIED`，执行期超支报 `TASK_BUDGET_EXCEEDED` | §8.6 只定义执行期错误；委派是拒绝签发，规范无专用码，按 C4-02 的约定处理 |
| 任务 `budget.depth` 视为绝对深度 | 子任务 = 父任务 + 1，与能力衰减的 `depth` 规则一致，两条路径不会互相矛盾 |
| handoff 不引入新状态 | §8.9 明确不加 `handoff_pending`；拒绝时 `owner`/`budget`/`status` 原样返回 |
| 取消跳过整棵 detached 子树 | §8.7 允许 detached 子任务继续，且必须失去父能力，父链取消不应再影响它 |
| C5 的“现在”取句柄 `created_at` | 不应让夹具随墙钟失效；C5-02 的过期变异必须稳定能触发 |
| 记忆句柄按 `ctx://user/memory` 前缀识别 | §9.3 未定义记忆 wire format；普通 `ctx://` 的 `scope=user` 仍只需 `resolve` |
| 标签违规返回 `observe` 而非拒绝 | C5-03 的预期是 `observe`；拒绝派生与抬高标签都合规，真正阻止泄露的是出口策略 |
| 被引用对象的硬删判为不合约 | §9.6 用 SHOULD 描述墓碑；实现区分软删（墓碑）与硬删（拒绝），并总是写审计 |

### 5.4 登记的偏差

| 位置 | 偏差 | 处理 |
|---|---|---|
| `welcome.body.data` | 规范未定义 `osap.welcome/v1` 的字段 | 返回 `osap`、`session_id`、`app`、`features`、`limits`；M2.4 定稿后回写规范 |
| 已定义但未实现的消息类型 | 没有对应错误码 | 适配器记 `skip`，报告写明里程碑 |
| 签名规范化 | 未采用完整 RFC 8785 | 采用 key 排序 UTF-8 JSON；M4 打包时对齐 |
| 一致性适配器的开发密钥环 | 示例夹具的签名是占位串 | 适配器在导入时生成一次性 Ed25519 密钥签开发清单，真实执行验签路径 |
| 能力凭证 `proof` | §5.2 要求“MUST 是签名对象”，实现只校验结构 | 密钥分发与验签待补，尚未纳入任何里程碑 |
| 回执 `agent` 绑定 | §5.8 未明确要求 | 额外校验 `receipt.agent == capability.subject`，不改变用例结果 |
| `max_uses` 计数 | 规范要求“5 次上限”，实现只比较上限 | 未落账使用次数，重放同一凭证不会扣减 |
| 任务状态机的非法转换 | 规范未指定错误码 | 用 `POLICY_DENIED` 并附带 `from`/`to` |
| 结果消息自带 `task.status` | §8.8 未规定如何与状态机配合 | 先校验结果契约再走状态机；对从未启动的任务返回结果会被拒绝 |
| 委派的能力链 | §8.5 要求子能力满足全部衰减条件 | 任务侧只校验预算与深度，夹具没有提供父凭证 |
| 记忆句柄识别 | §9.3 未定义记忆 wire format | 按 `ctx://user/memory` 前缀识别，要求 `memory.read` |
| 标签违规处理 | §9.4 未规定拒绝还是记录 | 解析后报告 `lowered`/`effective_label`，对应 C5-03 的 `observe` |
| 对象硬删被引用对象 | §9.6 用 SHOULD 描述墓碑 | 判为不合约；软删返回墓碑并写审计 |

### 5.5 已知限制

1. 幂等索引、注册表、轮换状态都在内存，重启即丢；§7.8 要求可重建的持久索引，留给 M2.6。
2. `auth.token` 与能力 `proof.sig` 都只做结构校验，没有验签；密钥分发链路未实现。
3. 两种“绑定”目前只是编解码层，没有接到 UDS / XPC / D-Bus，也没有对端认证；由 M2.1b 处理。
4. §4.2 的 App 认证（`SO_PEERCRED`、audit token、package identity）未实现，当前 App 身份只来自清单签名。
5. 撤销集合只在内存，重启即丢，也没有广播；§5.5 要求写入审计账本并通知受影响 Agent，留给 M2.6。
6. `max_uses` 未计数，`rate` 未限流；衰减只比较声明值。
7. 任务树只在内存，重启即丢；§8.11 的 `effect.intent`、对账与恢复未实现，C4-08/C4-09 仍是 manual。
8. 上下文审计与黑板状态只在内存，没有真正撤销句柄；§9.7 的“谁在何时解析了哪个句柄”只能读进程内列表。
9. 没有真实对象存储：`delete_object` 只返回判定，不触碰文件系统；`storage_declaration` 只核对声明，不实现配额、GC 或加密。
10. 47 个 pass 只证明信封、分帧、身份、注册表、授权、任务主路径与上下文主路径；不证明联邦或审计哈希链。

### 5.6 M2 剩余工作

- [ ] **M2.1b**：真实传输绑定（Linux UDS + 一种 message 绑定），让 C0-01 与 C0-06 可执行；
- [x] **M2.2**：身份、签名、注册表（C1 全绿，C2 automated 全绿）；
- [x] **M2.3**：能力签发、衰减、绑定、撤销（C3-01…C3-08 全绿）；
- [x] **M2.4**：风险前置与同意回执校验（C3-09…C3-12 全绿）；
- [ ] **M2.4b**（后续）：`consent.request` / `grant` / `deny` 的消息流、回执签发、`cap_id` 预约顺序；当前只实现回执的校验侧；
- [x] **M2.5a**：任务树、委派、预算、取消、结果、handoff（C4 automated 8/8）；
- [x] **M2.5b**：上下文织构（C5 11/11）；
- [ ] **M2.5c**：联邦适配器（C6 8 条）；
- [ ] **M2.6**：审计哈希链与任务 trace（C7 7 条）；
- [ ] **M2.7**：三 Agent 演示。

---

## 6. 待确认的规范问题

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

## 7. 下一步（按顺序）

1. **M2.5c**：联邦适配器与命名空间映射，跑通 C6 的 8 条；
2. **M2.6**：审计哈希链与任务 trace，让撤销、取消与 handoff 事件真正落账；
3. **M2.4b**：同意消息流（`consent.request` / `grant` / `deny`）与回执签发；
4. **M2.1b**：真实传输绑定（可与 M2.5c 并行）；
5. 每个 PR 只对应一个 C 编号用例，避免过度设计。

---

## 8. 变更记录

| 日期 | 变更 |
|---|---|
| 2026-11-12 | 创建本文；记录 M0 完成、M1 达到 19/68、剩余用例拆分 |
| 2026-11-12 | M1 扩展到 31/68（C1 6 条、C2 6 条）；补 `examples/hello.json`；登记注册表错误码近似映射 |
| 2026-11-12 | M1 扩展到 42/68（C4 11 条）；envelope 增加 peer/`session_id` 条件；登记 `params` 状态模拟与委派预算错误码问题 |
| 2026-11-12 | M1 扩展到 50/68（C6 8 条）；登记 `origin` 在能力记录 schema 中缺少字段的问题 |
| 2026-11-12 | M1 扩展到 61/68（C5 11 条）；新增 `context-handle.json` 与 `blackboard.json`；登记夹具无 schema 的限制 |
| 2026-11-12 | **M1 完成**：68/68；新增 C7 与 `audit-chain.json`；JSON 报告纳入 schema 校验 |
| 2026-11-14 | **M2.5b**（`206008b`）：上下文织构（句柄授权、TTL、标签、出口、黑板、删除、缓存、存储声明、记忆边界）；C5 11/11，累计 47 pass |
