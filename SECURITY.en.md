# Security Policy

> 2026-11-12
> English translation of [SECURITY.md](SECURITY.md). The Chinese original prevails in case of conflict.
> Normative source: [`GOVERNANCE.en.md`](GOVERNANCE.en.md) §7.

## Supported versions

| Version | Security fixes |
|---|---|
| 0.1.x (Draft) | ✅ Reports accepted |
| Earlier drafts | ❌ Not maintained separately |

0.1 has no reference implementation. "Security" here refers to the **specification, JSON Schemas, examples, and validation tooling**.

## Reporting channel

- Use GitHub **Private vulnerability reporting / Security Advisory**:
  the `Security` tab → `Report a vulnerability`.
- Do **not** open a public issue first, and do not post exploitation details in a PR or discussion.
- If GitHub is unavailable, contact the maintainers privately through the channel listed in `GOVERNANCE.md` §5.

## What to include

1. Affected files and version (commit or tag);
2. Issue type (specification ambiguity, over-permissive schema, unsafe example, tooling defect);
3. Minimal reproduction (request/response, schema fragment, or command);
4. Impact assessment: authorization bypass, audit tampering, data exfiltration, or implementation ambiguity;
5. Suggested fix direction, if any.

## Timelines

| Stage | Target |
|---|---|
| Acknowledge receipt | Within 7 days |
| Initial assessment and triage | Within 14 days |
| Coordinated disclosure | Within 90 days, or as otherwise agreed with the reporter |
| Post-fix notice | Recorded in `CHANGELOG.md`; a security advisory if warranted |

## Priority classes

- Capability token bypass (audience / task / subject / attenuation / revocation);
- Consent receipt forgery, replay, or scope escape;
- Tamperable or deletable audit chain;
- Unauthorized context handle resolution, `secret`-labeled object egress;
- Broken cross-user or cross-task data isolation.

## Security review triggers

The following changes MUST go through security and privacy review (see `GOVERNANCE.md` §7):

- Trust profile (P0 / P1) or TCB boundary;
- Payload visibility, encryption profile, key management;
- Peer authentication method, signature algorithm, or canonicalization (JCS) rules;
- Required fields and retention policy of audit events.

## After a fix

- Update the threat model (`standard.md` §11) or add an entry;
- Add the corresponding negative test to `docs/conformance.md`, then mirror it into `conformance/cases/`;
- If normative semantics change, follow the proposal process in `GOVERNANCE.md` §3.

## Security model boundaries

- 0.1 commits only to the **P0 Trusted Bus**: the Bus can see the envelope and plaintext `body`.
- The specification **does not** guarantee confidentiality against the Bus; wait for the 0.2 P1 profile.
- OSAP provides no kernel-level isolation; it runs on top of existing OS sandboxes and IPC.
- Final prompt-injection defense depends on the implementation and model layer; the protocol only provides the action gate and audit.
