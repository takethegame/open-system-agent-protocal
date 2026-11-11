# Contributing to OSAP

> English translation of [CONTRIBUTING.md](CONTRIBUTING.md). The Chinese original prevails in case of conflict.

> 2026-11-10

This repository contains the specification, JSON Schema, examples, and validation tools. All contributions are
licensed under the **Apache License 2.0**, and require a **DCO sign-off**.

---

## 1. Development Process

1. First open an issue or `proposals/NNNN-*.md` describing the problem, motivation, design, alternatives, and security and privacy impact.
2. Changes involving protocol behavior SHOULD include a reference implementation or pseudocode.
3. When modifying the specification, update `schemas/`, `examples/`, and `docs/conformance.md` in sync.
4. Run validation before committing:

```bash
python3 tools/validate_examples.py
# OK: 20 checks passed
```

5. For the change process, review requirements, and versioning rules, see [`GOVERNANCE.md`](GOVERNANCE.en.md).

---

## 2. Developer Certificate of Origin (DCO)

This project uses the [DCO 1.1](https://developercertificate.org/), not a CLA.
Every commit must include a sign-off:

```bash
git commit -s -m "spec: clarify Bus state vs memory"
```

The generated line looks like:

```
Signed-off-by: Your Name <you@example.com>
```

You may use your real name or a stable identity, but it must match the actual committer.
Unsigned commits will be asked to add a sign-off (`git commit --amend -s`) before they can be merged.

By submitting, you certify:

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

## 3. Content Rules

- **Do not commit personal data**: real names, local machine paths, device names, identifiers other than email addresses, real contacts.
  Examples must always use `com.example.*`, `example-user`, `example-device`.
- **Do not commit secrets**: signatures in examples use placeholders and must not contain usable private keys.
- **Language**: the Chinese text is the normative original; `*.en.md` files are English parallel translations, and the Chinese original prevails in case of conflict; schema identifiers, field names, and error codes use English.
- **Terminology**: stay consistent with `docs/standard.en.md` §2.2; for new terms, change the glossary first.
- **Citing others' specifications**: MUST paraphrase and attribute the source (name, version, link).
  A verbatim quotation of a single paragraph must not exceed 2 sentences, and MUST note the source and license;
  MUST NOT copy entire paragraphs of others' specifications, documentation, blogs, or code.
- **Third-party names**: may only be used to describe interoperability targets (nominative use),
  MUST NOT imply endorsement, sponsorship, or affiliation by the other party.
- **Normative wording**: follow RFC 2119 / RFC 8174, using only `MUST`, `SHOULD`, `MAY`
  and their negative forms; do not mix in the Chinese equivalents ("必须/应该/可以") as normative levels.

---

## 4. Security Disclosure

For security issues, exploitation details MUST NOT be published first. Please contact the maintainers through a private channel,
and coordinate disclosure within 90 days. See [`GOVERNANCE.md`](GOVERNANCE.en.md) §7 for details.

---

## 5. License

Unless stated otherwise in the file header, content submitted to this repository is licensed under the
[Apache License 2.0](LICENSE), with no additional terms.
