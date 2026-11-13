# OSAP 路线图（0.1 → 0.2）

> 状态：工作计划（非规范性） · 2026-11-12
> 关联规范：[`standard.md`](standard.md) 0.1 Draft
> 进展记录：[`progress.md`](progress.md)
> 说明：本文只安排**怎么把 0.1 变成可信、可验证、可提交的草案**，不新增协议语义。任何语义变更仍须走 `GOVERNANCE.md` §3 的提案流程。

---

## 0. 原则

1. **先可测试，再可标准化**：没有可执行证据的声明，不写进对外材料。
2. **一个里程碑一个可验证增量**：每个里程碑必须有明确退出标准，未达标不进入下一阶段。
3. **不扩 0.1 范围**：0.1 只承诺 P0 信任 profile 与单用户、单设备；其余进 0.2 待办。
4. **中英文同步**：规范性改动同时更新 `*.md` 与 `*.en.md`，否则视为未完成。

---

## 1. 现状盘点

### 1.1 已有资产

| 资产 | 数量/状态 |
|---|---|
| 规范正文 | `docs/standard.md`，131 节，0.1 Draft |
| JSON Schema | 12 个（envelope、capability、task、manifest、capability-record、consent-receipt、consent-request、audit-event、discover、discover-result、delegate、handoff） |
| 示例 | 17 个（14 个通过 schema 校验，3 个为无独立 schema 的夹具） |
| 一致性用例 | 68 个（C0:7、C1:6、C2:6、C3:12、C4:11、C5:11、C6:8、C7:7），全部已机器可读 |
| 校验工具 | `tools/validate_examples.py`，输出 `OK: 24 checks passed` |
| 文档 | 7 组中英文平行版本 |
| 许可 | Apache-2.0 + DCO 1.1 |
| 参考实现 | **0** |
| CI | **0** |
| `CHANGELOG` / `SECURITY` / `.gitignore` | **均缺失** |

### 1.2 关键缺口

| 缺口 | 影响 | 归属里程碑 |
|---|---|---|
| 一致性用例不可执行 | 无法声明任何 C 等级 | M1 |
| 无参考实现 | 无法验证规范自洽，SDO 不会采纳 | M2 |
| 无 CI | 外部贡献者无法判断改动是否破坏规范 | M0 |
| 无形式化不变量 | “衰减/撤销单调”只是文字主张 | M3 |
| 规范是 umbrella 文档 | 无法直接提交 IETF | M4 |
| 仓库名拼写错误 | 对外发布不专业 | M0 |

---

## 2. 里程碑总览

| 里程碑 | 目标 | 主要交付物 | 退出标准 | 工作量 | 目标日期 |
|---|---|---|---|---|---|
| **M0** 仓库可信化 | 让外部人能一键验证 | CI、`.gitignore`、`CHANGELOG`、`SECURITY`、改名 | CI 在干净 checkout 上全绿 | 2 天 | 2026-11-14 |
| **M1** 可执行一致性 | 68 个用例变成机器可读 | `conformance/cases/`、runner、报告格式 | 68/68 用例可加载，报告通过 schema 校验 | 4 天 | 2026-11-20 |
| **M2** 参考实现 MVP | 跑通 C0–C3 + C4 主路径 | `impl/` 最小实现、2 App + 1 Agent 演示 | C0–C3 全绿，C4 主路径通过 | 4 周 | 2026-12-18 |
| **M3** 形式化不变量 | 证明权威单调性 | TLA+ 或 Alloy 模型 + 4 条定理 | 模型检查无违例 | 2 周 | 2026-12-31 |
| **M4** 标准打包 | 拆成可提交材料 | 2 个 IETF draft + Linux binding + ADR | 草案可独立阅读、无悬空引用 | 3 周 | 2027-01-30 |
| **M5** 生态与采用 | 拿到外部实现与评审 | 一致性登记、外部实现、安全审计 | ≥1 个非本项目实现通过 C2 | 持续 | 2027-Q1 起 |

依赖关系：

```
M0 ──> M1 ──> M2 ──> M4
                 └──> M3 ──> M4
M0 ──────────────────────> M5
```

---

## 3. 阶段详情

### M0 — 仓库可信化（2 天）

**任务**

- [x] 新建 `.gitignore`：`.idea/`、`__pycache__/`、`*.pyc`、`.DS_Store`、`.venv/`
- [x] 新建 `.github/workflows/ci.yml`，步骤：
  - [x] Python 依赖安装（`jsonschema`、`referencing`）
  - [x] `python3 tools/validate_examples.py`
  - [x] 12 个 schema 的 draft 2020-12 元校验（`tools/check_schemas.py`）
  - [x] 所有 Markdown 的 `json` 代码块可解析（`tools/check_docs.py`）
  - [x] 相对链接无断链（`tools/check_docs.py`）
  - [x] 中英文标题层级 / 代码围栏数量一致性（`tools/check_docs.py`）
- [x] 新建 `requirements.txt`
- [x] 新建 `CHANGELOG.md`（Keep a Changelog 格式，回填 0.1）
- [x] 新建 `SECURITY.md` / `SECURITY.en.md`（从 `GOVERNANCE.md` §7 抽取披露流程与时限）
- [x] 仓库改名 `open-system-agent-protocal` → `open-system-agent-protocol`（已完成：GitHub + 本地目录 + remote + 徽章）
- [x] 在 `README.md` / `README.en.md` 增加 CI 徽章

**当前状态**：M0 全部完成。本地校验输出：

```
tools/check_schemas.py     OK: 36 checks passed across 12 schemas
tools/validate_examples.py OK: 20 checks passed
tools/check_docs.py        OK: 96 checks passed across 18 Markdown files
```

**退出标准**

- 全新 clone 后，仅按 README 的三条命令即可复现全绿；
- CI 在 PR 与 `main` 上都运行；
- `git status` 在未改动时为空（`.idea` 已忽略）。

**风险**：改名会让旧链接 404。GitHub 会重定向仓库页，但不会重定向 Pages、package 名和已克隆的 remote，需要各自更新；本地目录与 remote 已在 2026-11-12 一并改好。

---

### M1 — 可执行一致性（4 天）

**设计**

```
conformance/
  README.md                 用例格式、适配器 API、新增流程
  case.schema.json          单个用例
  suite.schema.json         按 level 分组的用例文件
  report.schema.json        运行报告（对应 standard §12.4）
  cases/
    C0-transport.json       已完成（7）
    C1-identity.json        已完成（6）
    C2-registry.json        已完成（6）
    C3-authorization.json   已完成（12）
    C4-collaboration.json   已完成（11）
    C5-context.json         已完成（11）
    C6-federation.json      已完成（8）
    C7-full.json            已完成（7）
tools/
  conformance_run.py        加载 → 校验 → 应用 mutation → 调用适配器 → 生成报告
```

单个用例的形状：

```json
{
  "id": "C3-01",
  "level": "C3",
  "title": "audience mismatch is rejected",
  "mode": "automated",
  "operation": "use",
  "input": {
    "ref": "../../examples/capability.json",
    "context": ["../../examples/request.json"],
    "mutations": [
      { "op": "replace", "path": "/audience", "value": "agent://com.example.notes/agent#77" }
    ]
  },
  "expect": { "outcome": "reject", "error": "CAPABILITY_AUDIENCE_MISMATCH" }
}
```

**任务**

- [x] 定义用例 JSON Schema（`case` / `suite` / `report`）并纳入 CI
- [x] 把 68 个用例逐条迁移，保持 ID 与 `docs/conformance.md` 一致（68/68：C0 7 + C1 6 + C2 6 + C3 12 + C4 11 + C5 11 + C6 8 + C7 7）
- [x] mutation 引擎（内置在 runner：`replace` / `add` / `remove` / `extend` / `truncate`）
- [x] 实现 `conformance_run.py`：
  - [x] `--impl` 适配器接口（Python 文件，暴露 `conformance_check`）
  - [x] `--level` 过滤
  - [x] 输出 text / JSON / Markdown 三种报告
  - [x] 未实现的能力标记 `skip` 而非 `fail`
- [x] 用 `--stub` 代替独立的 stub 实现（无适配器时全部 `skip`）
- [x] 在 `docs/conformance.md` 增加“结构 / 格式 / 运行”三节（3.1–3.3，编号不变）
- [x] 迁移 C7 剩余 7 个用例

**当前状态**：68/68（C0 7 + C1 6 + C2 6 + C3 12 + C4 11 + C5 11 + C6 8 + C7 7）。`--stub` 输出

```
68 cases [C0, C1, C2, C3, C4, C5, C6, C7]: 0 pass, 0 fail, 68 skip
```

JSON 报告在 runner 内直接对照 `report.schema.json` 校验，CI 增加了对应步骤。用例分布、已知限制与规范歧义见 [`progress.md`](progress.md) §4.5–§4.6。

**退出标准**

- 68 个用例全部可加载，schema 校验通过；
- 用 `--stub` 跑 runner，输出 68 条 `skip`，报告通过 schema 校验；
- `--stub` 同时校验编号覆盖（与 `docs/conformance.md` 逐条相等）和夹具/mutation 可执行性；
- CI 中加入 `conformance_run.py --stub` 与 JSON 报告校验。

**注意**：`standard.md` §12.3 规定 `conformance.md` 是测试编号的唯一来源。迁移时**不得新增或重编号**；新增用例必须先改 `conformance.md`。

---

### M2 — 参考实现 MVP（4 周）

**范围（只做这些）**

| 组件 | 做 | 不做 |
|---|---|---|
| Bus Core | 连接、`hello`/`welcome`、信封校验、路由、幂等索引、背压 | 策略判定、签发、对象存储、持久化审计 |
| CA | 签发、衰减、绑定校验、撤销、`cap_id` 预约 | 跨设备信任根 |
| PCS | 风险分级、同意请求、回执签发、回执校验 | 可视化 UI |
| AL | append-only 内存/文件审计、哈希链 | 外部 SIEM 集成 |
| CF | **仅** `ctx://` 句柄 + 内存对象 + 解析审计 | 独立对象存储、信息流标签完整实现 |
| RFS | **仅** 本地 manifest 索引 + 静态 `consent_hint` | 外部注册表联邦适配器 |
| Bridge | 1 个（建议 MCP 或 D-Bus） | 厂商 SDK 适配 |

**建议技术栈**：Python 3.11+（asyncio）或 Go。优先 Python，因为 contributor 门槛低、与现有校验工具同语言。

**拆分**

- [x] M2.1a 信封 + 错误模型 + 两种分帧编解码（`impl/osap/`，C0 automated 5/5）
- [ ] M2.1b 真实传输绑定（Linux UDS stream + 一种 message 绑定，含对端认证与回环 demo）
- [ ] M2.2（5 天）身份与握手 + 保留命名空间 + 签名（Ed25519 / JWS）
- [ ] M2.3（6 天）能力模型：签发、衰减、绑定、撤销、`max_uses`、预算
- [ ] M2.4（4 天）同意：风险分级、`consent.request`/`grant`/`deny`、回执与 `cap_id` 预约顺序
- [ ] M2.5（6 天）任务：`request`/`result`、`delegate`、`handoff`、取消传播、budget
- [ ] M2.6（3 天）审计哈希链 + 任务 trace
- [ ] M2.7（3 天）演示：`notes-agent` + `calendar-agent` + `supervisor`，跑通“查找空档 → 征求同意 → 创建 tentative 事件”

**退出标准**

- C0–C3 全部 31 个用例通过；
- C4 的 11 个用例中至少 8 个通过（handoff、取消、预算必须过）；
- 演示可用一条命令启动并在终端输出完整 trace；
- 撤销传播在单机 P95 < 100 ms（自测口径，写入 `impl/README.md`）。

**风险**：容易过度设计。控制手段是“每个 PR 只对应一个 C 编号用例”。

---

### M3 — 形式化不变量（2 周，可与 M2 后半段并行）

**要证明的 4 条**

1. **衰减单调**：子能力的 `actions`/`resources`/`exp`/`max_uses`/`max_budget` 永不放宽（`standard.md` §5.3）。
2. **撤销级联**：父能力撤销后，任意深度子能力不可用（§5.5）。
3. **预算单调**：任一子任务消耗之和 ≤ 父任务预算（§8.6）。
4. **取消传播**：父任务取消后，子树不再产生新的 `result`（§8.7）。

**任务**

- [ ] 用 TLA+ 定义状态：`Capability`、`Task`、`Receipt`、`RevocationSet`
- [ ] 建模 `Issue`、`Attenuate`、`Revoke`、`Delegate`、`Cancel`、`Consume`
- [ ] 写出 4 条 `Invariant`，用 TLC 模型检查
- [ ] 用 Alloy 做补充（关系约束更直观），或只保留 TLA+
- [ ] 把模型与规范条文的对应关系写成表（`spec/formal/README.md`）
- [ ] 增加 §8.11 崩溃对账的三态模型（`intent` / `outcome` / `unknown`）

**退出标准**

- TLC 在限定状态空间内无违例；
- 每个不变量都能指回具体小节编号；
- 故意放宽一条约束时，模型检查能报出反例（证明模型不是空转）。

---

### M4 — 标准打包（3 周）

**产出**

1. **IETF individual draft A**：`Capability Tokens for Local Agent Delegation`
   - 来源：`standard.md` §5（能力模型）+ §10.4（回执）
   - 目标 WG：`agentproto`，备选 OAuth
   - 只写 token 格式、衰减规则、绑定、撤销，不写总线
2. **IETF individual draft B**：`Consent Receipt Binding for Task-Scoped Authorization`
   - 来源：§10.2–§10.5
   - 对齐 Kantara/ISO 27560 与 WIMSE
3. **Linux binding profile**（非 IETF）：
   - D-Bus 接口名、对象路径、方法签名
   - 与 `xdg-desktop-portal` 的映射表
   - `systemd --user` 单元与 socket activation 建议
4. **ADR 集**：把 `standard.md` §15 的 14 个开放问题逐条写成 `decisions/NNNN-*.md`，每条给出“暂定结论 + 触发重审条件”

**任务**

- [ ] 建立 `drafts/` 目录与 IETF xml2rfc v3 骨架
- [ ] 抽取 draft A，确保每个规范性语句都能指回 `standard.md`
- [ ] 抽取 draft B，补齐与 27560 的字段映射
- [ ] 写 Linux binding（含 3 个序列图）
- [ ] 写 §15 的 14 条 ADR
- [ ] 在 `GOVERNANCE.md` §9 更新联络状态

**退出标准**

- 两个 draft 可被 `xml2rfc` 编译为 txt/html；
- draft 内的引用不依赖未发布文档；
- 外部读者不看 `standard.md` 也能理解单个 draft。

**注意**：提交 IETF 涉及文档版权（IETF Trust）与 IPR 披露，须先按 `GOVERNANCE.md` §10.4 取得贡献者同意。

---

### M5 — 生态与采用（持续）

- [ ] 发布 0.1 Draft + 参考实现，打 tag `v0.1.0`
- [ ] 建立一致性登记表（`conformance/registry.md`），只登记可复现的报告
- [ ] 找 1–2 个外部实现做互操作（哪怕只是 C1–C2）
- [ ] 独立安全评审（重点：confused deputy、提示注入闸门、审计完整性）
- [ ] 学术投稿（系统/安全 workshop），材料来自 M3 与 M2 的测量
- [ ] 与 freedesktop / GNOME / KDE 就 binding profile 开 issue 讨论

---

## 4. 0.2 范围冻结建议

以下内容**明确不在 0.1 交付范围**，在 M4 之后再讨论：

| 议题 | 现状 | 进入 0.2 的前置条件 |
|---|---|---|
| P1 Opaque Bus（HPKE） | 仅有方向描述 | 需要 wire format + 密钥发现 + 前向保密分析 |
| 跨设备 / 跨组织信任根 | 非目标 | 与 A2A、WIMSE、SPIFFE 的对齐方案 |
| 语义发现（embedding） | 开放问题 6 | 隐私影响评估 + 本地索引方案 |
| 多用户共享会话 | 开放问题 4 | 主体切换与数据边界模型 |
| 厂商 SDK 适配器 | 开放问题 9 | 至少一个厂商表达兴趣 |
| 多实例 Bus | 开放问题 14 | leader election 与审计分区设计 |

---

## 5. 决策闸门

| 闸门 | 时点 | 决策 | 不通过时 |
|---|---|---|---|
| **G1** | M1 结束 | 是否投入参考实现 | 若用例无法机器判定，先修规范歧义，不写实现 |
| **G2** | M2 结束 | 是否拆 IETF draft | 若 C3 用例通过率 < 90%，先修实现 |
| **G3** | M3 结束 | 是否对外发表形式化结果 | 若模型状态空间不足，扩大后再投 |
| **G4** | M4 结束 | 托管选择：LF/JDF vs AAIF vs 独立 | 未定则维持独立仓库，暂不宣称标准归属 |

---

## 6. 风险登记

| 风险 | 可能性 | 影响 | 缓解 | 触发信号 |
|---|---|---|---|---|
| 规范面太宽，实现永远追不上 | 高 | 高 | M2 严格限定范围；未实现部分标 `skip` | M2 超过 5 周 |
| IETF 认为与既有 WG 重复 | 中 | 中 | 只提交窄切片；先做 liaison 而非正式提交 | draft 无 WG 愿意 review |
| 厂商注册表封闭，联邦价值下降 | 中 | 高 | 定位为 projection/bridge，不要求厂商采用 | AppFunctions 开放第三方互调 |
| 形式化与实现脱节 | 中 | 中 | 模型只覆盖 §5/§8 的核心状态机 | 模型无法解释实现 bug |
| 单人维护导致中英文分叉 | 高 | 中 | CI 强制标题/围栏/链接一致性；ADR 记录语义变更 | 同一条文两版语义不同 |
| 改名导致外部引用失效 | 低 | 低 | CHANGELOG 记录 + GitHub 重定向 | — |

---

## 7. 度量指标

| 指标 | 目标（0.1 发布时） |
|---|---|
| C0–C3 用例通过率 | 100% |
| C4 用例通过率 | ≥ 80% |
| 示例 schema 校验 | 100% |
| 撤销传播 P95（单机） | < 100 ms |
| 权限绕过（负向用例漏判） | 0 |
| 审计链篡改检测 | 100% |
| 外部实现数 | ≥ 1（C2） |
| 中英文结构一致性 | 100%（CI 保证） |

---

## 8. 最近 7 天的具体动作

1. 建 `.gitignore`、`requirements.txt`、`SECURITY.md`、`CHANGELOG.md`
2. 建 `.github/workflows/ci.yml`，把现有校验脚本接进去
3. 定义 `conformance/case.schema.json`
4. 迁移 C0–C7 八个用例文件（共 68 条）
5. 写 `conformance_run.py` 的 `--stub` 模式
6. 仓库改名为 `protocol`，更新 README 徽章
7. 在 `docs/conformance.md` 加一节指向 `conformance/cases/`

完成后即可进入 M2 的第一个 PR（信封 + 错误模型）。
