# Security Policy

## Supported versions

| Version | Supported |
|---|---|
| `0.4.x` and current `main` | Yes |
| `0.3.x` and earlier | No |

Security fixes target the latest supported line. This policy does not promise
support for third-party models, hosted services, adapters, datasets, FFmpeg
builds, or dependencies outside this repository.

## Report a vulnerability privately

Use GitHub private vulnerability reporting:

`https://github.com/avalonreset/legends-stable-audio-3/security/advisories/new`

Do not open a public issue for a suspected vulnerability, exposed credential,
model-access bypass, supply-chain compromise, path traversal, or arbitrary
command execution concern. Do not attach tokens, model files, private datasets,
licensed media, or sensitive local paths.

## Target-setting gate

The public repository does not exist yet. Before making it public, the release
owner must enable private vulnerability reporting and verify that the exact URL
above accepts a draft advisory. Publication remains blocked until that check
passes. No alternate email address is claimed by this project.

## What to include

- A concise description and affected version/commit.
- Reproduction steps using synthetic or non-sensitive fixtures.
- Impact and any known mitigations.
- Environment details without tokens or private paths.

Maintainers target an initial acknowledgement within 3 business days and a
status update within 10 business days. These are response goals, not guarantees.
Please allow coordinated remediation before public disclosure.

## Supply-chain boundary

The optional Underfit integration downloads third-party code only after an
explicit command and verifies its origin, pinned commit, required files, and
license hash before execution. Report any way those checks can be bypassed.
Model weights and adapters are never accepted as project security-report
attachments.
