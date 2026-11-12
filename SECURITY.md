# Security Policy

> 2026-11-12
> English version: [SECURITY.en.md](SECURITY.en.md)
> 规范性来源：[`GOVERNANCE.md`](GOVERNANCE.md) §7。

## 支持的版本

| 版本 | 安全修复 |
|---|---|
| 0.1.x（Draft） | ✅ 接受报告 |
| 更早的草稿 | ❌ 不单独维护 |

0.1 尚无参考实现，当前“安全”指的是**规范、JSON Schema、示例与校验工具**。

## 报告渠道

- 请使用 GitHub 的 **Private vulnerability reporting / Security Advisory**：
  `Security` 标签页 → `Report a vulnerability`。
- **不要**先开公开 issue，也不要在 PR 或讨论区贴利用细节。
- 若无法使用 GitHub，请通过仓库 `GOVERNANCE.md` §5 列出的维护者渠道私下联系。

## 报告应包含

1. 受影响的文件与版本（commit 或 tag）；
2. 问题类型（规范歧义、schema 过宽、示例不安全、校验工具缺陷）；
3. 最小复现（请求/响应、schema 片段或命令）；
4. 影响评估：是权限绕过、审计篡改、数据外泄，还是实现歧义；
5. 若有，建议的修复方向。

## 时限

| 阶段 | 目标 |
|---|---|
| 确认收到 | 7 天内 |
| 初步评估与分级 | 14 天内 |
| 协调披露 | 90 天内，或与报告者另行约定 |
| 修复后公告 | 在 `CHANGELOG.md` 记录，必要时发布安全公告 |

## 优先处理

- 能力凭证绕过（audience / task / subject / 衰减 / 撤销）；
- 同意回执伪造、重放或作用域逃逸；
- 审计链可篡改或可删除；
- 上下文句柄越权解析、`secret` 标签对象外泄；
- 跨用户或跨任务数据隔离失效。

## 安全评审触发条件

以下变更 MUST 经过安全与隐私评审（见 `GOVERNANCE.md` §7）：

- 信任 profile（P0 / P1）或 TCB 边界；
- payload 可见性、加密 profile、密钥管理；
- 对端认证方式、签名算法或规范化（JCS）规则；
- 审计事件的必填字段与保留策略。

## 修复后要求

- 更新威胁模型（`standard.md` §11）或新增条目；
- 在 `docs/conformance.md` 增加对应负向测试，再同步到 `conformance/cases/`；
- 若改动影响规范性语义，MUST 走 `GOVERNANCE.md` §3 的提案流程。

## 安全模型边界

- 0.1 只承诺 **P0 Trusted Bus**：Bus 可见信封与明文 `body`。
- 规范**不**保证对 Bus 的机密性；需要该性质请等待 0.2 的 P1 profile。
- OSAP 不提供内核级隔离，运行在现有 OS 沙箱与 IPC 之上。
- 提示注入的最终拦截依赖实现与模型层，协议只提供动作闸门与审计。
