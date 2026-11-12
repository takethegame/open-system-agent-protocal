# OSAP Conformance Cases

本目录把 [`docs/conformance.md`](../docs/conformance.md) 中的测试表变成可执行用例。**编号的唯一来源仍是 `docs/conformance.md`**：新增或修改用例，先改文档，再改这里。

---

## 1. 目录结构

```
conformance/
  README.md            本文件
  case.schema.json     单个用例的 schema
  suite.schema.json    用例文件（按 level 分组）的 schema
  report.schema.json   运行报告的 schema（对应 standard.md §12.4）
  cases/
    C0-transport.json
    C3-authorization.json
    ...                每个 level 一个文件
```

用例文件形如：

```json
{
  "level": "C3",
  "cases": [ { "id": "C3-01", "...": "..." } ]
}
```

---

## 2. 用例字段

| 字段 | 必填 | 说明 |
|---|---|---|
| `id` | ✅ | `C<level>-<nn>`，必须与 `docs/conformance.md` 一致 |
| `level` | ✅ | `C0`–`C7`，必须与所在文件相同 |
| `title` | ✅ | 一句话描述，英文 |
| `mode` | | `automated`（默认）或 `manual` |
| `preconditions` | | 运行前必须成立的状态 |
| `operation` | | `handshake` / `send` / `frame` / `use` / `attenuate` / `delegate` / `handoff` / `cancel` / `discover` / `resolve` / `restart` / `replay` / `clock` |
| `input` | automated 必填 | 见下 |
| `steps` | manual 必填 | 人工执行步骤 |
| `expect` | ✅ | 见下 |
| `audit` | | 期望出现在审计中的事件类型 |
| `notes` | | 补充说明 |

`input`：

| 字段 | 说明 |
|---|---|
| `ref` | 主夹具路径，相对用例文件 |
| `context` | 额外夹具（信封、回执、任务），按顺序传入适配器 |
| `mutations` | 只作用于主夹具，在调用适配器前应用 |
| `params` | 无夹具时使用，直接交给适配器 |

---

## 3. Mutation

| `op` | 语义 |
|---|---|
| `replace` | 目标必须存在，替换值 |
| `add` | 对对象赋值；对数组按索引插入，`-` 表示追加 |
| `remove` | 删除目标 |
| `extend` | 目标与 `value` 都必须是数组，追加 |
| `truncate` | 目标必须是数组，`value` 为保留长度 |

`path` 使用 JSON Pointer（RFC 6901），例如 `/constraints/expires_at`。

---

## 4. 期望语义

| `outcome` | 含义 |
|---|---|
| `accept` | 操作成功；可用 `state` 断言副作用（只比较列出的键） |
| `reject` | 操作失败，且 `error` 与规范错误码一致 |
| `observe` | 没有自动判定，报告记录观察结果；用于“视为不一致”类检查 |

`reject` 必须带 `error`，由 `case.schema.json` 强制。

---

## 5. 适配器 API

适配器是一个 Python 文件，暴露：

```python
def conformance_check(case: dict, documents: dict) -> dict:
    """返回 {"outcome": "accept"|"reject", "error": "...", "state": {...}}。"""
```

`documents` 的结构：

- `documents["primary"]`：应用 mutation 后的主夹具（没有 `ref` 时为 `None`）；
- `documents["context"]`：应用 mutation 后的上下文夹具列表；
- `case["input"].get("params")`：无夹具参数。

超出实现范围时返回 `{"outcome": "skip", "reason": "..."}`，runner 记为 `skip`；其他异常一律记为 `fail`。

---

## 6. 运行

```bash
# 只校验用例格式，不执行（CI 使用）
python3 tools/conformance_run.py --stub

# 对实现运行
python3 tools/conformance_run.py --impl path/to/adapter.py

# 只跑某些等级，输出 Markdown 或 JSON
python3 tools/conformance_run.py --impl adapter.py --level C0,C3 --format md --out report.md
```

退出码：有任何 `fail` 时为 1；全部 `pass`/`skip` 时为 0。

报告遵循 `report.schema.json`，可直接作为一致性声明附件。

---

## 7. 新增用例

1. 在 `docs/conformance.md` 的对应等级表格中新增一行（编号连续）；
2. 在 `conformance/cases/C<n>-*.json` 添加用例，`title` 用英文；
3. 本地跑 `--stub` 确认格式合法；
4. 若该用例改变了规范性行为，同时更新 `docs/standard.md` 与英文译本。
