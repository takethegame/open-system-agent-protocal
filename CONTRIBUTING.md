# Contributing to OSAP

> 2026-11-10

本仓库包含规范、JSON Schema、示例与校验工具。所有贡献均以
**Apache License 2.0** 授权，并要求 **DCO sign-off**。

---

## 1. 开发流程

1. 先开 issue 或 `proposals/NNNN-*.md`，说明问题、动机、设计、替代方案、安全与隐私影响。
2. 涉及协议行为的改动 SHOULD 附带参考实现或伪代码。
3. 修改规范时同步更新 `schemas/`、`examples/` 与 `docs/conformance.md`。
4. 提交前运行校验：

```bash
python3 tools/validate_examples.py
# OK: 20 checks passed
```

5. 变更流程、评审要求与版本规则见 [`GOVERNANCE.md`](GOVERNANCE.md)。

---

## 2. Developer Certificate of Origin (DCO)

本项目使用 [DCO 1.1](https://developercertificate.org/)，而不是 CLA。
每次提交都必须包含 sign-off：

```bash
git commit -s -m "spec: clarify Bus state vs memory"
```

生成的行形如：

```
Signed-off-by: Your Name <you@example.com>
```

使用真实姓名或稳定的身份标识均可，但必须与实际提交者一致。
未签名的提交会被要求补签（`git commit --amend -s`）后才能合并。

提交即表示你证明：

> By making a contribution to this project, I certify that:
>
> (a) The contribution was created in whole or in part by me and I have
> the right to submit it under the open source license indicated in the
> file; or
>
> (b) The contribution is based upon previous work that, to the best of my
> knowledge, is covered under an appropriate open source license and I have
> the right under that license to submit that work with modifications,
> whether created in whole or in part by me, under the same open source
> license (unless I am permitted to submit under a different license), as
> indicated in the file; or
>
> (c) The contribution was provided directly to me by some other person who
> certified (a), (b) or (c) and I have not modified it.
>
> (d) I understand and agree that this project and the contribution are
> public and that a record of the contribution (including all personal
> information I submit with it, including my sign-off) is maintained
> indefinitely and may be redistributed consistent with this project or the
> open source license(s) involved.

---

## 3. 内容规范

- **不要提交个人数据**：真实姓名、本机路径、设备名、邮箱之外的标识、真实联系人。
  示例一律使用 `com.example.*`、`example-user`、`example-device`。
- **不要提交密钥**：示例中的签名用占位符，不得包含可用私钥。
- **语言**：规范正文用中文；schema 标识符、字段名、错误码用英文。
- **术语**：与 `docs/standard.md` §2.2 保持一致；新增术语先改术语表。
- **引用他人规范**：MUST 转述并标注出处（名称、版本、链接）。
  单段逐字引用不得超过 2 句，且 MUST 注明来源与许可；
  MUST NOT 整段复制他人的规范、文档、博客或代码。
- **第三方名称**：只能用于说明互操作对象（指示性使用），
  MUST NOT 暗示对方背书、赞助或关联。
- **规范性措辞**：遵循 RFC 2119 / RFC 8174，只用 `MUST`、`SHOULD`、`MAY`
  及其否定形式，不混用“必须/应该/可以”的中文对应词作为规范等级。

---

## 4. 安全披露

安全问题时 MUST NOT 先公开利用细节。请通过私有渠道联系 maintainers，
并在 90 天内协调披露。详见 [`GOVERNANCE.md`](GOVERNANCE.md) §7。

---

## 5. 许可

除非文件头另有说明，提交到本仓库的内容均以
[Apache License 2.0](LICENSE) 授权，且不附加额外条款。
