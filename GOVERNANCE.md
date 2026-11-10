# OSAP Governance

> 草案 · 2026-11-10

本文定义 OSAP 标准的版本、变更、评审与联络机制。除 §10 的许可与商标条款外，它是治理建议，不构成法律协议。

---

## 1. 目标

- 保持协议开放、可实现、可测试。
- 避免单一厂商控制核心语义。
- 在安全、隐私与互操作之间取得可审计的平衡。
- 与 MCP、A2A、IETF `agentproto`、OAuth WIMSE、AAIF/LF 等生态对齐，而不是重复定义。

---

## 2. 版本与发布

| 版本类型 | 规则 |
|---|---|
| **Major** | 不兼容变更；必须提供迁移指南与至少一个旧版本支持周期 |
| **Minor** | 向后兼容的新增；必须更新 changelog 与 schema |
| **Patch** | 澄清、勘误、非语义修改 |

- 规范版本与 wire version（信封 `osap` 字段）保持一致。
- 每个版本 MUST 包含：变更摘要、兼容性说明、安全影响、测试更新。
- 候选版本 SHOULD 保留至少 30 天的公开评审期。

---

## 3. 变更流程

1. **提案**：通过 issue 或 `proposals/NNNN-*.md` 提交问题、动机、设计、替代方案、安全/隐私影响。
2. **讨论**：公开讨论，至少两个独立实现方参与。
3. **原型**：涉及协议行为的提案 SHOULD 提供参考实现或伪代码。
4. **评审**：安全与隐私评审为必选项。
5. **共识**：以“没有持续、实质性的反对”为粗略共识标准。
6. **合并与发布**：更新规范、schema、测试与 changelog。

所有提交 MUST 带 DCO `Signed-off-by`（见 §10.1）；未签名的提交不得合并。

紧急安全问题可以走快速通道，但事后 MUST 公开说明。

---

## 4. 角色

| 角色 | 职责 |
|---|---|
| **Maintainer** | 合并提案、发布版本、维护 schema 与测试 |
| **Editor** | 维护规范文本与一致性 |
| **Implementer** | 提供参考实现与互操作报告 |
| **Security Reviewer** | 评审威胁模型、密码学、权限边界 |
| **Liaison** | 与外部标准组织联络 |

角色不绑定雇主；任何贡献者均可通过持续贡献成为 maintainer。

---

## 5. 一致性与参考实现

- 一致性等级见 [`docs/conformance.md`](docs/conformance.md)。
- 参考实现 MUST 通过其声明等级的全部测试。
- 参考实现 SHOULD 至少覆盖两个 OS 平台。
- 互操作报告 SHOULD 公开（脱敏后）。
- 标准不要求单一“官方实现”；允许多个独立实现。

---

## 6. Schema 与命名空间登记

- 核心 schema 由 maintainers 登记。
- 领域 schema 由提案人登记，需提供维护者、版本、验证规则与兼容性策略。
- 能力命名空间：
  - `cap://os/...` 保留给核心域；
  - `cap://<vendor-domain>/...` 用于厂商扩展；
  - 冲突使用反向域名消歧。
- 事件主题：
  - `event://os/...` 保留给系统事件；
  - `event://app.<app-id>/...` 用于 App 事件。

---

## 7. 安全披露

- 安全问题 MUST NOT 先公开利用细节。
- 应通过私有渠道联系 maintainers，并在 90 天内协调披露。
- 涉及用户数据、权限绕过、审计篡改的问题优先处理。
- 信任 profile、TCB 边界、payload 可见性或加密 profile 的变更 MUST 经过安全与隐私评审。
- 修复后 MUST 更新威胁模型与测试用例。

---

## 8. 隐私

- 规范与测试 MUST NOT 包含真实用户数据。
- 示例 MUST 使用保留域名、示例身份与合成数据。
- 审计/遥测的默认设置 MUST 遵循数据最小化。
- 任何跨设备/跨组织扩展 MUST 单独进行隐私影响评估。

---

## 9. 与外部标准组织的关系

建议的联络方向：

| 组织/项目 | 关系 |
|---|---|
| IETF `agentproto` | 对话管理、任务生命周期的上游对齐 |
| IETF OAuth / WIMSE | 委托授权、凭证、同意回执 |
| AAIF / Linux Foundation（MCP、A2A） | 工具与跨网络 Agent 语义 |
| AGNTCY | 联邦目录、传输、能力 schema |
| OS 厂商（Apple/Google/Microsoft） | 原生注册表 Bridge 与对端认证 |
| 桌面环境（GNOME/KDE） | Linux 本地 Bus 与 portal 集成 |

OSAP 的定位是**本地绑定/联邦层**，不替代上述协议。

---

## 10. 许可与贡献

| 内容 | 许可 |
|---|---|
| 规范文本（`docs/`） | Apache-2.0 |
| JSON Schema（`schemas/`） | Apache-2.0 |
| 示例（`examples/`） | Apache-2.0 |
| 工具与未来参考实现（`tools/`） | Apache-2.0 |

全仓库统一使用 **Apache License 2.0**，而不是“文档 CC + 代码 Apache”的拆分。原因：

- Apache-2.0 §3 提供明确的**专利授权**，并以发起专利诉讼作为终止条件；
- CC BY 4.0 第 2(b)(2) 条明确排除专利与商标授权，且 CC 不建议用于软件与 schema；
- 允许商业实现、修改、再分发与私有部署，适合厂商采用；
- 与 GPLv3 兼容（不与 GPLv2 兼容）；
- 有显式的贡献者授权条款（§5）与商标条款（§6）。

### 10.1 贡献

- 使用 **DCO 1.1**，不使用 CLA；每次提交 MUST 带 `Signed-off-by`。
- 贡献者保留版权，并授予项目 Apache-2.0 许可。
- 未签名的提交不得合并。
- 具体要求见 [`CONTRIBUTING.md`](CONTRIBUTING.md)。

### 10.2 商标与一致性标记

- Apache-2.0 §6 不授予 “OSAP” 名称或标志的商标权。
- 代码可自由使用；但 “OSAP-compatible”、“OSAP C4/C5” 等一致性标记
  MUST 基于 [`docs/conformance.md`](docs/conformance.md) 的测试结果，
  具体登记流程另行定义。
- 不得暗示项目方为第三方实现背书。

### 10.3 译本与派生版本

Apache-2.0 §4 要求修改过的文件带变更说明，且不得暗示为官方版本。对此：

- **派生版本**（译本、摘编、profile、改写）MUST 保留 [`LICENSE`](LICENSE) 与
  [`NOTICE`](NOTICE)，并按 §4(b) 显著标注“已修改”。
- **官方译本**由 Maintainer 发布，元数据标注 `translation: official`，
  并注明对应的原文版本与 commit。
- **其他译本** MUST 标注 `translation: unofficial`，MUST NOT 使用
  “OSAP-compatible”、“OSAP C4/C5” 等一致性标记，不得暗示为官方文本。
- 译本 MUST NOT 引入新的规范性要求；语义冲突时以原文（`docs/standard.md`）为准。
- 派生规范若改变协议语义，MUST 使用不同名称与命名空间，不得称为“OSAP 0.x”。

### 10.4 许可变更

- 已发布版本的许可不可撤销。
- 未来若调整许可（例如捐赠给基金会或提交 IETF），MUST 取得所有贡献者同意，
  并在新版本中说明；不得追溯修改已分发副本的条款。

---

## 11. 行为准则

- 以技术论证为主，不进行人身攻击。
- 尊重不同平台、不同厂商的实现约束。
- 对安全与隐私问题保持审慎。
- 欢迎独立实现与对抗性测试。
